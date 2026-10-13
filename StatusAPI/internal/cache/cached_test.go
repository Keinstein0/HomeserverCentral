package cache

import (
	"context"
	"sync"
	"sync/atomic"
	"testing"
	"time"

	"homeservercentral/statusapi/internal/checker"
)

// countingChecker counts how many times Check is invoked.
type countingChecker struct {
	id, name string
	calls    *atomic.Int64
	delay    time.Duration
}

func (c countingChecker) ID() string   { return c.id }
func (c countingChecker) Name() string { return c.name }
func (c countingChecker) Check(ctx context.Context) checker.CheckResult {
	c.calls.Add(1)
	if c.delay > 0 {
		select {
		case <-time.After(c.delay):
		case <-ctx.Done():
		}
	}
	return checker.CheckResult{ID: c.id, Name: c.name, Status: checker.StatusOK}
}

func TestCachedChecker_ServesFreshCache(t *testing.T) {
	var calls atomic.Int64
	inner := countingChecker{id: "svc", name: "Service", calls: &calls}
	cc := NewCachedChecker(inner, time.Minute)

	for i := 0; i < 5; i++ {
		r := cc.Check(context.Background())
		if r.Status != checker.StatusOK {
			t.Fatalf("expected UP, got %s", r.Status)
		}
	}
	if got := calls.Load(); got != 1 {
		t.Fatalf("expected 1 downstream call, got %d", got)
	}
}

func TestCachedChecker_RefetchesAfterTTLExpiry(t *testing.T) {
	var calls atomic.Int64
	inner := countingChecker{id: "svc", name: "Service", calls: &calls}
	cc := NewCachedChecker(inner, 30*time.Millisecond)

	_ = cc.Check(context.Background())
	time.Sleep(50 * time.Millisecond)
	_ = cc.Check(context.Background())

	if got := calls.Load(); got != 2 {
		t.Fatalf("expected 2 downstream calls after TTL expiry, got %d", got)
	}
}

// TestCachedChecker_SingleflightCollapsesConcurrentMisses launches many
// goroutines that all miss the cache at once while the underlying check is
// slow. singleflight must collapse them into a single downstream probe.
func TestCachedChecker_SingleflightCollapsesConcurrentMisses(t *testing.T) {
	var calls atomic.Int64
	inner := countingChecker{
		id:    "svc",
		name:  "Service",
		calls: &calls,
		delay: 40 * time.Millisecond, // slow so concurrent callers overlap
	}
	cc := NewCachedChecker(inner, time.Hour) // long TTL so second wave is served from cache

	const n = 50
	var wg sync.WaitGroup
	wg.Add(n)
	start := make(chan struct{})
	for i := 0; i < n; i++ {
		go func() {
			defer wg.Done()
			<-start
			_ = cc.Check(context.Background())
		}()
	}
	close(start)
	wg.Wait()

	if got := calls.Load(); got != 1 {
		t.Fatalf("expected exactly 1 downstream call under concurrency, got %d", got)
	}

	// A follow-up call within the TTL must NOT trigger another probe.
	_ = cc.Check(context.Background())
	if got := calls.Load(); got != 1 {
		t.Fatalf("expected still 1 downstream call, got %d", got)
	}
}

func TestCachedChecker_InvalidateAndSetTTL(t *testing.T) {
	var calls atomic.Int64
	inner := countingChecker{id: "svc", name: "Service", calls: &calls}
	cc := NewCachedChecker(inner, time.Hour)

	_ = cc.Check(context.Background())
	cc.Invalidate()
	_ = cc.Check(context.Background())
	if got := calls.Load(); got != 2 {
		t.Fatalf("expected 2 calls after invalidate, got %d", got)
	}

	// Shrinking TTL to zero forces immediate re-fetch on next call.
	cc.SetTTL(0)
	_ = cc.Check(context.Background())
	if got := calls.Load(); got != 3 {
		t.Fatalf("expected 3 calls after SetTTL(0), got %d", got)
	}
}
