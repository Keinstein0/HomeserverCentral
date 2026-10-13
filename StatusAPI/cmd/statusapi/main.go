// Command statusapi is the entrypoint for the Status API microservice.
package main

import (
	"context"
	"log"
	"net/http"
	"os"
	"os/signal"
	"strconv"
	"syscall"
	"time"

	"homeservercentral/statusapi/internal/cache"
	"homeservercentral/statusapi/internal/checker"
	"homeservercentral/statusapi/internal/registry"
	"homeservercentral/statusapi/internal/server"
)

// envOr returns the named environment variable or the provided default.
func envOr(key, def string) string {
	if v := os.Getenv(key); v != "" {
		return v
	}
	return def
}

// envIntOr returns the named integer environment variable or the default.
func envIntOr(key string, def int) int {
	if v := os.Getenv(key); v != "" {
		if n, err := strconv.Atoi(v); err == nil {
			return n
		}
	}
	return def
}

func main() {
	logger := log.New(os.Stdout, "status-api: ", log.LstdFlags|log.Lmsgprefix)

	port := envOr("PORT", "5001")
	cacheTTL := time.Duration(envIntOr("CACHE_TTL_SECONDS", 10)) * time.Second

	authURL := envOr("AUTH_SERVICE_URL", "http://matrix-auth-gateway:5000")
	homeserverURL := envOr("HOMESERVER_URL", "http://tuwunel:8008")
	homepageURL := envOr("HOMEPAGE_URL", "http://homepage:5173")
	caddyURL := envOr("CADDY_URL", "http://caddy")

	reg := registry.New()

	// Register each concrete checker wrapped in a lazy TTL cache so that
	// bursts of requests are served from the cache and at most one
	// downstream probe runs per TTL window per service (singleflight).
	register := func(c checker.ServiceChecker) {
		reg.Register(cache.NewCachedChecker(c, cacheTTL))
	}
	register(checker.NewAuthServiceChecker(authURL))
	register(checker.NewMatrixHomeserverChecker(homeserverURL))
	register(checker.NewHomepageChecker(homepageURL))
	register(checker.NewCaddyChecker(caddyURL))

	srv := server.New(reg, logger)
	srv.SetAddr(":" + port)

	// Graceful shutdown on SIGINT/SIGTERM.
	ctx, stop := signal.NotifyContext(context.Background(), syscall.SIGINT, syscall.SIGTERM)
	defer stop()

	errCh := make(chan error, 1)
	go func() {
		if err := srv.ListenAndServe(); err != nil && err != http.ErrServerClosed {
			errCh <- err
		}
	}()

	select {
	case err := <-errCh:
		logger.Fatalf("server error: %v", err)
	case <-ctx.Done():
		logger.Println("shutdown signal received, draining...")
		shutdownCtx, cancel := context.WithTimeout(context.Background(), 10*time.Second)
		defer cancel()
		if err := srv.Shutdown(shutdownCtx); err != nil {
			logger.Printf("graceful shutdown failed: %v", err)
		}
		logger.Println("server stopped")
	}
}
