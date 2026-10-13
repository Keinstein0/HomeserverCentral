// Package cache implements the lazy, on-demand TTL caching decorator for
// ServiceChecker instances. It collapses concurrent cache misses into a
// single downstream probe (singleflight semantics implemented on top of the
// standard library), preventing thundering herds.
package cache

import (
	"context"
	"sync"
	"time"

	"homeservercentral/statusapi/internal/checker"
)

// CachedChecker wraps a ServiceChecker with an in-memory TTL cache and
// singleflight stampede protection. When the cache is fresh, Check returns
// immediately; when it is expired, concurrent callers share the result of a
// single underlying Check call.
type CachedChecker struct {
	inner checker.ServiceChecker
	ttl   time.Duration

	// dataMu guards the cached result and its timestamp.
	dataMu    sync.Mutex
	result    checker.CheckResult
	fetchedAt time.Time

	// callMu + callDone implement singleflight: at most one goroutine performs
	// a downstream probe at a time; concurrent callers wait on callDone.
	callMu   sync.Mutex
	callDone chan struct{}
}

// NewCachedChecker wraps the given checker with a TTL-based cache.
func NewCachedChecker(inner checker.ServiceChecker, ttl time.Duration) *CachedChecker {
	return &CachedChecker{inner: inner, ttl: ttl}
}

// ID forwards to the underlying checker.
func (c *CachedChecker) ID() string { return c.inner.ID() }

// Name forwards to the underlying checker.
func (c *CachedChecker) Name() string { return c.inner.Name() }

// Check returns the cached CheckResult if it is younger than the TTL,
// otherwise it refreshes the cache (collapsing concurrent refreshes into a
// single downstream probe) and returns the fresh result.
func (c *CachedChecker) Check(ctx context.Context) checker.CheckResult {
	// Fast path: serve a fresh cache without touching the refresh lock.
	c.dataMu.Lock()
	if !c.fetchedAt.IsZero() && time.Since(c.fetchedAt) < c.ttl {
		r := c.result
		c.dataMu.Unlock()
		return r
	}
	c.dataMu.Unlock()

	// Acquire the refresh lock so only one goroutine coordinates the probe.
	c.callMu.Lock()

	// If another goroutine is already refreshing, wait for it.
	if c.callDone != nil {
		done := c.callDone
		c.callMu.Unlock()
		select {
		case <-done:
		case <-ctx.Done():
			// Context cancelled while waiting. Serve whatever we have.
			return c.snapshot()
		}
		// The refresh finished; the cache should now be populated. Serve it.
		return c.snapshot()
	}

	// No refresh in flight — start one.
	done := make(chan struct{})
	c.callDone = done
	c.callMu.Unlock()

	// Perform the downstream probe. This is the only place a real health
	// check runs for an expired cache, regardless of how many callers are
	// concurrently waiting on `done`.
	fresh := c.inner.Check(ctx)

	c.dataMu.Lock()
	c.result = fresh
	c.fetchedAt = time.Now()
	c.dataMu.Unlock()

	// Clear the in-flight marker and signal waiters.
	c.callMu.Lock()
	c.callDone = nil
	c.callMu.Unlock()

	close(done)
	return fresh
}

// snapshot returns a copy of the cached result under the data lock.
func (c *CachedChecker) snapshot() checker.CheckResult {
	c.dataMu.Lock()
	defer c.dataMu.Unlock()
	return c.result
}

// SetTTL updates the cache TTL at runtime (thread-safe).
func (c *CachedChecker) SetTTL(ttl time.Duration) {
	c.dataMu.Lock()
	c.ttl = ttl
	c.dataMu.Unlock()
}

// Invalidate forces the next Check to refresh the cache (thread-safe).
func (c *CachedChecker) Invalidate() {
	c.dataMu.Lock()
	c.fetchedAt = time.Time{}
	c.dataMu.Unlock()
}
