# Manual Deployment Guide

## Deploying Code Changes

### 1. Figure out which services are affected

Check what files changed in your commit:

```bash
git diff HEAD~1 --stat
```

| Files changed in | Service(s) to rebuild |
|---|---|
| `web/` | web |
| `apiserver/` | api, worker, beat-worker, migrator |
| `admin/` | admin |
| `space/` | space |
| `nginx/` | proxy |

### 2. Build the affected image(s)

From the **plane repo root**:

```bash
# Frontend (web)
docker build -t rememberizer/plane-frontend:local -f web/Dockerfile.web .

# Backend (api, worker, beat-worker, migrator — all share the same image)
docker build -t rememberizer/plane-backend:local -f apiserver/Dockerfile.api apiserver/

# Admin
docker build -t rememberizer/plane-admin:local -f admin/Dockerfile.admin .

# Space
docker build -t rememberizer/plane-space:local -f space/Dockerfile.space .

# Proxy
docker build -t rememberizer/plane-proxy:local -f nginx/Dockerfile nginx/
```

### 3. Push to registry

```bash
docker push rememberizer/plane-frontend:local
# or whichever image you built
```

### 4. Restart the affected deployment(s)

```bash
kubectl rollout restart deployment/<service> -n ea-tracker
```

For example, a frontend-only change:
```bash
kubectl rollout restart deployment/web -n ea-tracker
```

A backend change (restart all backend services):
```bash
kubectl rollout restart deployment/api deployment/worker deployment/beat-worker -n ea-tracker
```

If k8s doesn't pick up the new image (same tag), force it:
```bash
kubectl patch deployment <service> -n ea-tracker \
  -p "{\"spec\":{\"template\":{\"metadata\":{\"annotations\":{\"redeploy-timestamp\":\"$(date +%s)\"}}}}}"
```

### 5. If there are DB migrations

Delete and recreate the migrator pod (it's a one-shot Pod, not a Deployment):
```bash
kubectl delete pod migrator -n ea-tracker --ignore-not-found
kubectl apply -f deploy/kubernetes/k8s/migrator-pod.yaml -n ea-tracker
```

### 6. Verify

```bash
kubectl get pods -n ea-tracker
kubectl logs deployment/<service> -n ea-tracker --tail=50
```

## Quick Reference

| Service | Image | Dockerfile |
|---|---|---|
| web | `rememberizer/plane-frontend:local` | `web/Dockerfile.web` |
| api, worker, beat-worker, migrator | `rememberizer/plane-backend:local` | `apiserver/Dockerfile.api` |
| admin | `rememberizer/plane-admin:local` | `admin/Dockerfile.admin` |
| space | `rememberizer/plane-space:local` | `space/Dockerfile.space` |
| proxy | `rememberizer/plane-proxy:local` | `nginx/Dockerfile` |
| live | `makeplane/plane-live:stable` | (upstream, not built locally) |

## Config Changes

- **Non-secret config** (`k8s/plane-config.yaml`): edit, commit, then `kubectl apply -f deploy/kubernetes/k8s/plane-config.yaml -n ea-tracker` and restart affected services.
- **Secrets** (`plane-secrets.yaml`, `docker-registry-secret.yaml`): these files are **not in the repo**. Edit them wherever you store them and `kubectl apply` directly.
