package registry

import (
	"context"
	"testing"

	"homeservercentral/statusapi/internal/checker"
)

type fakeChecker struct {
	id, name string
}

func (f fakeChecker) ID() string   { return f.id }
func (f fakeChecker) Name() string { return f.name }
func (f fakeChecker) Check(_ context.Context) checker.CheckResult {
	return checker.CheckResult{ID: f.id, Name: f.name, Status: checker.StatusOK}
}

func TestRegistry_RegisterGetListMetadata(t *testing.T) {
	r := New()
	r.Register(fakeChecker{id: "c", name: "C"})
	r.Register(fakeChecker{id: "a", name: "A"})
	r.Register(fakeChecker{id: "b", name: "B"})

	got, ok := r.Get("b")
	if !ok || got.ID() != "b" {
		t.Fatalf("expected to find b")
	}
	if _, ok := r.Get("missing"); ok {
		t.Fatalf("unexpected find for missing id")
	}

	ids := make([]string, 0)
	for _, c := range r.List() {
		ids = append(ids, c.ID())
	}
	want := []string{"a", "b", "c"}
	for i := range want {
		if ids[i] != want[i] {
			t.Fatalf("expected sorted %v, got %v", want, ids)
		}
	}

	meta := r.Metadata()
	if len(meta) != 3 || meta[0].ID != "a" || meta[2].ID != "c" {
		t.Fatalf("unexpected metadata: %+v", meta)
	}
}

func TestRegistry_Overwrite(t *testing.T) {
	r := New()
	r.Register(fakeChecker{id: "x", name: "Old"})
	r.Register(fakeChecker{id: "x", name: "New"})
	if len(r.List()) != 1 {
		t.Fatalf("expected single entry after overwrite, got %d", len(r.List()))
	}
	if r.List()[0].Name() != "New" {
		t.Fatalf("expected overwritten name, got %q", r.List()[0].Name())
	}
}
