// Package checker defines the core abstractions for the Status API service
// monitoring: the Status enum, the CheckResult model, and the ServiceChecker
// interface that every monitored service must implement.
package checker

import (
	"context"
	"time"
)

// Status represents the operational health of a monitored service.
type Status string

const (
	// StatusOK means the service is responding as expected.
	StatusOK Status = "UP"
	// StatusDegraded means the service is reachable but not fully healthy
	// (e.g. slow responses, partial failures, upstream connectivity issues).
	StatusDegraded Status = "DEGRADED"
	// StatusDown means the service is unreachable or returning errors.
	StatusDown Status = "DOWN"
)

// CheckResult is the standardized health report produced by every checker.
type CheckResult struct {
	ID             string                 `json:"id"`
	Name           string                 `json:"name"`
	Status         Status                 `json:"status"`
	ResponseTimeMs int64                  `json:"response_time_ms"`
	Message        string                 `json:"message,omitempty"`
	Details        map[string]interface{} `json:"details,omitempty"`
	LastChecked    time.Time              `json:"last_checked"`
}

// ServiceChecker is implemented by every monitored service. Implementations
// encapsulate the custom probing logic for their target.
type ServiceChecker interface {
	// ID returns the unique, stable identifier of the service (used in URLs).
	ID() string
	// Name returns a human-readable service name.
	Name() string
	// Check performs a single health probe against the target service and
	// returns a CheckResult. It must respect the provided context (timeouts,
	// cancellation).
	Check(ctx context.Context) CheckResult
}
