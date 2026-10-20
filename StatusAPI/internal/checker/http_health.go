package checker

import (
	"context"
	"fmt"
	"io"
	"net/http"
	"strings"
	"time"
)

// BodyValidator inspects the raw response body and returns nil if the body
// is acceptable, or an error describing why it is not (which will be surfaced
// as a DEGRADED/DOWN message). It allows custom checkers to validate
// service-specific payloads without re-implementing the HTTP plumbing.
type BodyValidator func(body []byte) error

// HTTPHealthChecker is a reusable, generic checker parameterized by target
// URL, HTTP method, timeout, and expected status code. Concrete checkers can
// embed or compose it and supply a BodyValidator for service-specific logic.
type HTTPHealthChecker struct {
	id             string
	name           string
	url            string
	method         string
	timeout        time.Duration
	expectedStatus int
	validateBody   BodyValidator
	client         *http.Client
}

// HTTPHealthCheckerOption configures an HTTPHealthChecker at construction.
type HTTPHealthCheckerOption func(*HTTPHealthChecker)

// WithMethod overrides the default HTTP method (GET).
func WithMethod(m string) HTTPHealthCheckerOption {
	return func(c *HTTPHealthChecker) { c.method = m }
}

// WithTimeout overrides the default request timeout.
func WithTimeout(d time.Duration) HTTPHealthCheckerOption {
	return func(c *HTTPHealthChecker) { c.timeout = d }
}

// WithExpectedStatus overrides the expected success status code (default 200).
func WithExpectedStatus(code int) HTTPHealthCheckerOption {
	return func(c *HTTPHealthChecker) { c.expectedStatus = code }
}

// WithBodyValidator attaches a payload validator to the checker.
func WithBodyValidator(v BodyValidator) HTTPHealthCheckerOption {
	return func(c *HTTPHealthChecker) { c.validateBody = v }
}

// NewHTTPHealthChecker builds a generic HTTP health checker.
func NewHTTPHealthChecker(id, name, url string, opts ...HTTPHealthCheckerOption) *HTTPHealthChecker {
	c := &HTTPHealthChecker{
		id:             id,
		name:           name,
		url:            url,
		method:         http.MethodGet,
		timeout:        5 * time.Second,
		expectedStatus: http.StatusOK,
	}
	for _, opt := range opts {
		opt(c)
	}
	c.client = &http.Client{Timeout: c.timeout}
	return c
}

// ID returns the checker identifier.
func (c *HTTPHealthChecker) ID() string { return c.id }

// Name returns the human-readable service name.
func (c *HTTPHealthChecker) Name() string { return c.name }

// URL returns the target URL (useful for diagnostics/tests).
func (c *HTTPHealthChecker) URL() string { return c.url }

// Check performs an HTTP probe against the configured target and returns a
// CheckResult. A successful probe (expected status + valid body) yields
// StatusOK. A non-expected status yields StatusDegraded when the service is
// still responding, and connectivity/timeout errors yield StatusDown.
func (c *HTTPHealthChecker) Check(ctx context.Context) CheckResult {
	result := CheckResult{
		ID:          c.id,
		Name:        c.name,
		LastChecked: time.Now().UTC(),
	}

	req, err := http.NewRequestWithContext(ctx, c.method, c.url, nil)
	if err != nil {
		result.Status = StatusDown
		result.Message = fmt.Sprintf("failed to build request: %v", err)
		return result
	}
	req.Header.Set("Accept", "application/json")
	req.Header.Set("User-Agent", "status-api/1.0")

	start := time.Now()
	resp, err := c.client.Do(req)
	elapsed := time.Since(start)
	result.ResponseTimeMs = elapsed.Milliseconds()

	if err != nil {
		result.Status = StatusDown
		result.Message = fmt.Sprintf("request failed: %v", err)
		return result
	}
	defer func() { _ = resp.Body.Close() }()

	body, _ := io.ReadAll(io.LimitReader(resp.Body, 1<<16)) // cap at 64KB

	result.Details = map[string]interface{}{
		"status_code": resp.StatusCode,
		"url":         c.url,
	}

	if resp.StatusCode != c.expectedStatus {
		result.Status = StatusDegraded
		result.Message = fmt.Sprintf("unexpected status %d (expected %d)", resp.StatusCode, c.expectedStatus)
		if len(body) > 0 {
			result.Details["body"] = strings.TrimSpace(string(body))
		}
		return result
	}

	if c.validateBody != nil {
		if verr := c.validateBody(body); verr != nil {
			result.Status = StatusDegraded
			result.Message = verr.Error()
			if len(body) > 0 {
				result.Details["body"] = strings.TrimSpace(string(body))
			}
			return result
		}
	}

	result.Status = StatusOK
	result.Message = "ok"
	return result
}
