# syntax=docker/dockerfile:1

# =============================================================================
# Builder stage - compile a statically linked, CGO-disabled binary.
# =============================================================================
FROM golang:1.24-alpine AS builder

WORKDIR /src

# Cache module step. go.mod has no external dependencies, but this keeps the
# build layer-cacheable if that ever changes.
COPY StatusAPI/go.mod ./StatusAPI/go.mod
RUN cd StatusAPI && go mod download

# Copy the rest of the source and build.
COPY StatusAPI/ ./StatusAPI/

RUN cd StatusAPI && \
    CGO_ENABLED=0 GOOS=linux GOARCH=amd64 \
    go build -trimpath -ldflags="-s -w" -o /out/statusapi ./cmd/statusapi

# =============================================================================
# Runtime stage - minimal image with curl available for the compose healthcheck.
# =============================================================================
FROM alpine:3

# curl is used by the docker-compose healthcheck (mirrors the Auth Service).
RUN apk add --no-cache ca-certificates curl && \
    addgroup -S app && adduser -S -G app app

COPY --from=builder /out/statusapi /usr/local/bin/statusapi

USER app
EXPOSE 5001

ENTRYPOINT ["statusapi"]
