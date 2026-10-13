// Package registry holds the thread-safe collection of registered
// ServiceChecker instances used by the HTTP server to route status requests.
package registry

import (
	"sort"
	"sync"

	"homeservercentral/statusapi/internal/checker"
)

// ServiceMeta is the lightweight metadata returned by GET /services.
type ServiceMeta struct {
	ID   string `json:"id"`
	Name string `json:"name"`
}

// Registry is a thread-safe collection of ServiceChecker instances keyed by ID.
type Registry struct {
	mu       sync.RWMutex
	checkers map[string]checker.ServiceChecker
}

// New creates an empty Registry.
func New() *Registry {
	return &Registry{checkers: make(map[string]checker.ServiceChecker)}
}

// Register adds a checker to the registry, keyed by its ID. Registering an
// existing ID overwrites the previous entry.
func (r *Registry) Register(c checker.ServiceChecker) {
	r.mu.Lock()
	defer r.mu.Unlock()
	r.checkers[c.ID()] = c
}

// Get returns the checker for the given id and whether it was found.
func (r *Registry) Get(id string) (checker.ServiceChecker, bool) {
	r.mu.RLock()
	defer r.mu.RUnlock()
	c, ok := r.checkers[id]
	return c, ok
}

// List returns all registered checkers in a stable, ID-sorted order so that
// GET /services output is deterministic.
func (r *Registry) List() []checker.ServiceChecker {
	r.mu.RLock()
	defer r.mu.RUnlock()
	out := make([]checker.ServiceChecker, 0, len(r.checkers))
	for _, c := range r.checkers {
		out = append(out, c)
	}
	sort.Slice(out, func(i, j int) bool { return out[i].ID() < out[j].ID() })
	return out
}

// Metadata returns the {id,name} summary for every registered service, sorted
// by ID (used by GET /services).
func (r *Registry) Metadata() []ServiceMeta {
	entries := r.List()
	meta := make([]ServiceMeta, len(entries))
	for i, c := range entries {
		meta[i] = ServiceMeta{ID: c.ID(), Name: c.Name()}
	}
	return meta
}
