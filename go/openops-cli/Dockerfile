# syntax=docker/dockerfile:1
#
# Build a partir da RAIZ do repositório:
#   docker build -f go/openops-cli/Dockerfile -t openops-cli .
#
# Imagem final baseada em Alpine (poucos MB) com o binário estático do
# CLI — sem toolchain Go nenhum na imagem que roda de verdade.

FROM golang:1.22-alpine AS builder

WORKDIR /src
COPY go/openops-cli/ .
RUN CGO_ENABLED=0 go build -ldflags="-s -w" -o /openops-cli .

FROM alpine:3.20

RUN adduser -D -u 1000 -s /sbin/nologin openops
COPY --from=builder /openops-cli /usr/local/bin/openops-cli

USER openops
WORKDIR /workspace
ENTRYPOINT ["openops-cli"]
CMD ["--help"]
