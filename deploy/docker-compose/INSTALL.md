# CubePlex on docker-compose — Install Guide

`docker compose up -d` deploys CubePlex (backend + frontend + Postgres +
Redis + rustfs S3 store) on one host, using the same container images as the
Kubernetes deployment mode — only the orchestration differs.

**The full, maintained install guide lives on the docs site:**
[cubeplex.ai/docs/deployment/docker-compose](https://cubeplex.ai/docs/deployment/docker-compose)

It covers prerequisites, building images, the four required config files
(`.env`, `opensandbox.toml`, and two YAML files), bringing the stack up/down,
verification, and troubleshooting.

This directory holds the scripts and config templates the guide walks
through: `compose.yaml`, `.env.example`,
`config/*.example`, and `scripts/{up,smoke-test,e2e}.sh`. See
[README.md](README.md) for the short quickstart.
