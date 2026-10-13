package server

import (
	"context"
	"encoding/json"
	"net/http"
	"net/http/httptest"
	"sync"
	"testing"
	"time"

	"homeservercentral/statusapi/internal/checker"
	"homeservercentral/statusapi/internal/registry"
)

type stubChecker struct {
	id, name string
	status   checker.Status
}

func (s stubChecker) ID() string   { return s.id }
func (s stubChecker) Name() string { return s.name }
func (s stubChecker) Check(_ context.Context) checker.CheckResult {
	return checker.CheckResult{ID: s.id, Name: s.name, Status: s.status, LastChecked: time.Now().UTC()}
}

func newServer(t *testing.T) *httptest.Server {
	t.Helper()
	reg := registry.New()
	reg.Register(stubChecker{id: "auth-gateway", name: "Matrix Auth Gateway", status: checker.StatusOK})
	reg.Register(stubChecker{id: "tuwunel", name: "Matrix Homeserver", status: checker.StatusDegraded})
	srv := New(reg, nil)
	ts := httptest.NewServer(srv.srv.Handler)
	t.Cleanup(ts.Close)
	return ts
}

func TestServer_Healthz(t *testing.T) {
	ts := newServer(t)
	resp, err := http.Get(ts.URL + "/healthz")
	if err != nil {
		t.Fatal(err)
	}
	defer resp.Body.Close()
	if resp.StatusCode != http.StatusOK {
		t.Fatalf("expected 200, got %d", resp.StatusCode)
	}
}

func TestServer_ListServices(t *testing.T) {
	ts := newServer(t)
	resp, err := http.Get(ts.URL + "/services")
	if err != nil {
		t.Fatal(err)
	}
	defer resp.Body.Close()

	var meta []registry.ServiceMeta
	if err := json.NewDecoder(resp.Body).Decode(&meta); err != nil {
		t.Fatal(err)
	}
	if len(meta) != 2 || meta[0].ID != "auth-gateway" {
		t.Fatalf("unexpected metadata: %+v", meta)
	}
}

func TestServer_ServiceStatus_NotFound(t *testing.T) {
	ts := newServer(t)
	resp, err := http.Get(ts.URL + "/services/missing")
	if err != nil {
		t.Fatal(err)
	}
	defer resp.Body.Close()
	if resp.StatusCode != http.StatusNotFound {
		t.Fatalf("expected 404, got %d", resp.StatusCode)
	}
}

func TestServer_ServiceStatus_OK(t *testing.T) {
	ts := newServer(t)
	resp, err := http.Get(ts.URL + "/services/auth-gateway")
	if err != nil {
		t.Fatal(err)
	}
	defer resp.Body.Close()

	var res checker.CheckResult
	if err := json.NewDecoder(resp.Body).Decode(&res); err != nil {
		t.Fatal(err)
	}
	if res.ID != "auth-gateway" || res.Status != checker.StatusOK {
		t.Fatalf("unexpected result: %+v", res)
	}
}

func TestServer_AggregatedStatus(t *testing.T) {
	ts := newServer(t)
	resp, err := http.Get(ts.URL + "/status")
	if err != nil {
		t.Fatal(err)
	}
	defer resp.Body.Close()

	var agg aggregatedStatus
	if err := json.NewDecoder(resp.Body).Decode(&agg); err != nil {
		t.Fatal(err)
	}
	if agg.Count != 2 || agg.Up != 1 || agg.Degraded != 1 || agg.Down != 0 {
		t.Fatalf("unexpected counts: %+v", agg)
	}
	if agg.Overall != checker.StatusDegraded {
		t.Fatalf("expected overall DEGRADED, got %s", agg.Overall)
	}
}

// Ensure concurrent checks under the aggregate endpoint do not race.
func TestServer_AggregatedStatus_Concurrent(t *testing.T) {
	ts := newServer(t)
	var wg sync.WaitGroup
	for i := 0; i < 20; i++ {
		wg.Add(1)
		go func() {
			defer wg.Done()
			resp, err := http.Get(ts.URL + "/status")
			if err != nil {
				t.Error(err)
				return
			}
			resp.Body.Close()
		}()
	}
	wg.Wait()
}
