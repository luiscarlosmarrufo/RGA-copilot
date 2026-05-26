# Docker rules

1. **Multi-stage builds.** Each Dockerfile has at least `base`, `dev`, `prod` targets. Dev mounts source; prod copies built artifacts only.
2. **No secrets in images.** `.env` is never `COPY`ed in. Secrets are injected at runtime.
3. **No client data in images.** `data/private/` is `.dockerignore`d.
4. **Pinned base images.** Use specific tags / digests, not `:latest`.
5. **Non-root user** in the runtime stage. `USER app` (or similar) before `CMD`.
6. **Healthchecks.** Each service that responds to HTTP has a `HEALTHCHECK` and the compose service has one too.
7. **Single responsibility per service.** `api`, `worker`, `scheduler`, `web`, `redis` — never combine.
8. **Postgres is Supabase**, not a container. Do not add a `postgres` service to compose.
9. **Logs to stdout/stderr.** No log files inside containers.
10. **Layer cache hygiene.** Dependency install before source copy; lockfiles drive cache invalidation.
11. **Reproducible builds.** Pin Python / Node base versions; commit lockfiles.
12. **`docker-compose.dev.yml`** is the only place dev-only behavior lives (hot reload, source mounts). Production compose is clean.
