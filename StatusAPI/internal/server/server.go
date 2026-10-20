// Package server wires the registry and HTTP handlers for the Status API.
package server

import (
	"context"
	"encoding/json"
	"log"
	"net/http"
	"sync"
	"time"

	"homeservercentral/statusapi/internal/checker"
	"homeservercentral/statusapi/internal/registry"
)

// Server is the Status API HTTP server.
type Server struct {
	registry *registry.Registry
	logger   *log.Logger
	srv      *http.Server
}

// New builds a Server with the given registry.
func New(reg *registry.Registry, logger *log.Logger) *Server {
	s := &Server{registry: reg, logger: logger}
	mux := http.NewServeMux()
	mux.HandleFunc("GET /healthz", s.handleHealthz)
	mux.HandleFunc("GET /services", s.handleListServices)
	mux.HandleFunc("GET /services/{id}", s.handleServiceStatus)
	mux.HandleFunc("GET /status", s.handleAggregatedStatus)

	s.srv = &http.Server{
		Addr:              ":5001",
		Handler:           mux,
		ReadHeaderTimeout: 10 * time.Second,
		ReadTimeout:       15 * time.Second,
		WriteTimeout:      15 * time.Second,
		IdleTimeout:       60 * time.Second,
	}
	return s
}

// SetAddr overrides the listen address (e.g. ":5001"). It must be called
// before ListenAndServe.
func (s *Server) SetAddr(addr string) {
	s.srv.Addr = addr
}

// ListenAndServe starts the HTTP server.
func (s *Server) ListenAndServe() error {
	s.logger.Printf("status-api listening on %s", s.srv.Addr)
	return s.srv.ListenAndServe()
}

// Shutdown gracefully stops the server.
func (s *Server) Shutdown(ctx context.Context) error {
	return s.srv.Shutdown(ctx)
}

// writeJSON serializes v as JSON and writes it with the given status code.
func (s *Server) writeJSON(w http.ResponseWriter, status int, v interface{}) {
	w.Header().Set("Content-Type", "application/json")
	w.WriteHeader(status)
	if err := json.NewEncoder(w).Encode(v); err != nil {
		s.logger.Printf("failed to encode response: %v", err)
	}
}

// handleHealthz is the Status API's own self-health check.
func (s *Server) handleHealthz(w http.ResponseWriter, r *http.Request) {
	s.writeJSON(w, http.StatusOK, map[string]string{"status": "UP"})
}

// handleListServices returns metadata for all registered services.
func (s *Server) handleListServices(w http.ResponseWriter, r *http.Request) {
	s.writeJSON(w, http.StatusOK, s.registry.Metadata())
}

// handleServiceStatus returns the (cached or live) health of one service.
func (s *Server) handleServiceStatus(w http.ResponseWriter, r *http.Request) {
	id := r.PathValue("id")
	c, ok := s.registry.Get(id)
	if !ok {
		s.writeJSON(w, http.StatusNotFound, map[string]string{"error": "service not found"})
		return
	}
	result := c.Check(r.Context())
	s.writeJSON(w, http.StatusOK, result)
}

// aggregatedStatus is the response body for GET /status.
type aggregatedStatus struct {
	Overall  checker.Status        `json:"overall_status"`
	Count    int                   `json:"count"`
	Up       int                   `json:"up"`
	Degraded int                   `json:"degraded"`
	Down     int                   `json:"down"`
	Services []checker.CheckResult `json:"services"`
}

// handleAggregatedStatus runs every registered checker concurrently and
// returns the combined status. The overall status is the worst individual
// status (DOWN beats DEGRADED beats UP).
func (s *Server) handleAggregatedStatus(w http.ResponseWriter, r *http.Request) {
	checkers := s.registry.List()
	ctx := r.Context()

	results := make([]checker.CheckResult, len(checkers))
	var wg sync.WaitGroup
	for i, c := range checkers {
		wg.Add(1)
		go func(idx int, chk checker.ServiceChecker) {
			defer wg.Done()
			results[idx] = chk.Check(ctx)
		}(i, c)
	}
	wg.Wait()

	var up, degraded, down int
	var overall = StatusOKValue()
	for _, res := range results {
		switch res.Status {
		case checker.StatusOK:
			up++
		case checker.StatusDegraded:
			degraded++
		case checker.StatusDown:
			down++
		}
		overall = worst(overall, res.Status)
	}

	s.writeJSON(w, http.StatusOK, aggregatedStatus{
		Overall:  overall,
		Count:    len(results),
		Up:       up,
		Degraded: degraded,
		Down:     down,
		Services: results,
	})
}

// StatusOKValue returns the OK status sentinel for aggregation seeding.
func StatusOKValue() checker.Status { return checker.StatusOK }

// worst returns the more severe of two statuses.
func worst(a, b checker.Status) checker.Status {
	rank := func(s checker.Status) int {
		switch s {
		case checker.StatusOK:
			return 0
		case checker.StatusDegraded:
			return 1
		case checker.StatusDown:
			return 2
		default:
			return 2
		}
	}
	if rank(b) > rank(a) {
		return b
	}
	return a
}
