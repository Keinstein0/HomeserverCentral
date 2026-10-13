package checker

import (
	"encoding/json"
	"fmt"
	"strings"
)

// --- AuthServiceChecker -------------------------------------------------------

// NewAuthServiceChecker probes the Matrix Auth Gateway /healthz endpoint.
// The current auth gateway returns the plain text "ok" with a 200 status when
// healthy. The validator accepts any 2xx body containing "ok"; if the gateway
// later evolves to return a JSON payload, the validator still accepts a 200
// response so the service is reported UP.
func NewAuthServiceChecker(authServiceURL string) *HTTPHealthChecker {
	url := strings.TrimRight(authServiceURL, "/") + "/healthz"
	return NewHTTPHealthChecker(
		"auth-gateway",
		"Matrix Auth Gateway",
		url,
		WithBodyValidator(func(body []byte) error {
			trimmed := strings.TrimSpace(string(body))
			if !strings.EqualFold(trimmed, "ok") && !strings.Contains(strings.ToLower(trimmed), `"status"`) {
				return fmt.Errorf("unexpected health body: %q", trimmed)
			}
			return nil
		}),
	)
}

// --- MatrixHomeserverChecker (Tuwunel) ---------------------------------------

// NewMatrixHomeserverChecker probes the Matrix homeserver /_matrix/client/versions
// endpoint, verifying core homeserver responsiveness. Per the Matrix spec the
// endpoint returns a JSON object with a "versions" array.
func NewMatrixHomeserverChecker(homeserverURL string) *HTTPHealthChecker {
	url := strings.TrimRight(homeserverURL, "/") + "/_matrix/client/versions"
	return NewHTTPHealthChecker(
		"tuwunel",
		"Matrix Homeserver",
		url,
		WithBodyValidator(func(body []byte) error {
			var payload struct {
				Versions []string `json:"versions"`
			}
			if err := json.Unmarshal(body, &payload); err != nil {
				return fmt.Errorf("invalid JSON: %v", err)
			}
			if len(payload.Versions) == 0 {
				return fmt.Errorf("no matrix versions reported")
			}
			return nil
		}),
	)
}

// --- HomepageChecker ---------------------------------------------------------

// NewHomepageChecker probes the Homepage (Svelte frontend) reachability.
func NewHomepageChecker(homepageURL string) *HTTPHealthChecker {
	return NewHTTPHealthChecker(
		"homepage",
		"Svelte Frontend",
		strings.TrimRight(homepageURL, "/")+"/",
	)
}

// --- CaddyChecker ------------------------------------------------------------

// NewCaddyChecker probes the Caddy reverse proxy, validating ingress routing
// and frontend reachability through the public entrypoint.
func NewCaddyChecker(caddyURL string) *HTTPHealthChecker {
	return NewHTTPHealthChecker(
		"caddy",
		"Caddy Reverse Proxy",
		strings.TrimRight(caddyURL, "/")+"/",
	)
}
