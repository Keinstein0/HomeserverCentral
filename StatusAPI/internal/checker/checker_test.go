package checker

import (
	"context"
	"errors"
	"net/http"
	"net/http/httptest"
	"testing"
	"time"
)

var errBadBody = errors.New("bad body")

func TestHTTPHealthChecker_OK(t *testing.T) {
	srv := httptest.NewServer(http.HandlerFunc(func(w http.ResponseWriter, r *http.Request) {
		w.WriteHeader(http.StatusOK)
		_, _ = w.Write([]byte("ok"))
	}))
	defer srv.Close()

	c := NewHTTPHealthChecker("svc", "Service", srv.URL,
		WithExpectedStatus(http.StatusOK),
		WithBodyValidator(func(b []byte) error {
			if string(b) != "ok" {
				return errBadBody
			}
			return nil
		}))
	res := c.Check(context.Background())
	if res.Status != StatusOK {
		t.Fatalf("expected UP, got %s (%s)", res.Status, res.Message)
	}
	if res.ID != "svc" || res.Name != "Service" {
		t.Fatalf("unexpected id/name: %+v", res)
	}
	if res.ResponseTimeMs < 0 {
		t.Fatalf("negative response time")
	}
}

func TestHTTPHealthChecker_UnexpectedStatus_Degraded(t *testing.T) {
	srv := httptest.NewServer(http.HandlerFunc(func(w http.ResponseWriter, r *http.Request) {
		w.WriteHeader(http.StatusServiceUnavailable)
	}))
	defer srv.Close()

	c := NewHTTPHealthChecker("svc", "Service", srv.URL)
	res := c.Check(context.Background())
	if res.Status != StatusDegraded {
		t.Fatalf("expected DEGRADED, got %s", res.Status)
	}
}

func TestHTTPHealthChecker_Unreachable_Down(t *testing.T) {
	c := NewHTTPHealthChecker("svc", "Service", "http://127.0.0.1:1/healthz", WithTimeout(200*time.Millisecond))
	res := c.Check(context.Background())
	if res.Status != StatusDown {
		t.Fatalf("expected DOWN, got %s (%s)", res.Status, res.Message)
	}
}

func TestHTTPHealthChecker_BodyValidatorFails_Degraded(t *testing.T) {
	srv := httptest.NewServer(http.HandlerFunc(func(w http.ResponseWriter, r *http.Request) {
		w.WriteHeader(http.StatusOK)
		_, _ = w.Write([]byte("boom"))
	}))
	defer srv.Close()

	c := NewHTTPHealthChecker("svc", "Service", srv.URL, WithBodyValidator(func(b []byte) error {
		return errBadBody
	}))
	res := c.Check(context.Background())
	if res.Status != StatusDegraded {
		t.Fatalf("expected DEGRADED, got %s", res.Status)
	}
}

func TestMatrixHomeserverChecker_ValidVersions(t *testing.T) {
	srv := httptest.NewServer(http.HandlerFunc(func(w http.ResponseWriter, r *http.Request) {
		w.Header().Set("Content-Type", "application/json")
		_, _ = w.Write([]byte(`{"versions":["v1.0","v1.1"]}`))
	}))
	defer srv.Close()

	c := NewMatrixHomeserverChecker(srv.URL)
	res := c.Check(context.Background())
	if res.Status != StatusOK {
		t.Fatalf("expected UP, got %s (%s)", res.Status, res.Message)
	}
}

func TestMatrixHomeserverChecker_EmptyVersions_Degraded(t *testing.T) {
	srv := httptest.NewServer(http.HandlerFunc(func(w http.ResponseWriter, r *http.Request) {
		_, _ = w.Write([]byte(`{"versions":[]}`))
	}))
	defer srv.Close()

	c := NewMatrixHomeserverChecker(srv.URL)
	res := c.Check(context.Background())
	if res.Status != StatusDegraded {
		t.Fatalf("expected DEGRADED, got %s (%s)", res.Status, res.Message)
	}
}

func TestAuthServiceChecker_OK_PlainText(t *testing.T) {
	srv := httptest.NewServer(http.HandlerFunc(func(w http.ResponseWriter, r *http.Request) {
		w.WriteHeader(http.StatusOK)
		_, _ = w.Write([]byte("ok"))
	}))
	defer srv.Close()

	c := NewAuthServiceChecker(srv.URL)
	res := c.Check(context.Background())
	if res.Status != StatusOK {
		t.Fatalf("expected UP, got %s (%s)", res.Status, res.Message)
	}
}
