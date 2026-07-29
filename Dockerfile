FROM golang:1.26-bookworm AS builder

WORKDIR /src

COPY moon-bridge/go.mod moon-bridge/go.sum ./
RUN go mod download

COPY moon-bridge/ ./
RUN CGO_ENABLED=0 GOOS=linux go build -trimpath -ldflags="-s -w" -o /out/moonbridge ./cmd/moonbridge

FROM gcr.io/distroless/static-debian12:nonroot

WORKDIR /app
COPY --from=builder /out/moonbridge /app/moonbridge

EXPOSE 38440
USER nonroot:nonroot
ENTRYPOINT ["/app/moonbridge"]
CMD ["-config", "/config/config.yml", "-addr", "0.0.0.0:38440"]
