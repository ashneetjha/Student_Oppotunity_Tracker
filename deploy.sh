#!/usr/bin/env bash
set -Eeuo pipefail

PROJECT_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$PROJECT_ROOT"

REPO_URL="https://github.com/ashneetjha/Student_Oppotunity_Tracker.git"
SERVICE_NAME="student-opportunity-tracker-api"
VERCEL_PROJECT_NAME="student-opportunity-tracker"

BACKEND_BUILD='pip install -r backend/requirements.txt && PYTHONPATH=. python backend/seed.py'
BACKEND_START='uvicorn backend.app.main:app --host 0.0.0.0 --port $PORT'

log(){ printf "\n\033[1;36m==> %s\033[0m\n" "$1"; }
ok(){ printf "\033[1;32m[OK]\033[0m %s\n" "$1"; }
die(){ printf "\033[1;31m[ERROR]\033[0m %s\n" "$1" >&2; exit 1; }

[[ -f index.html ]] || die "Run this from the project root."
[[ -f backend/requirements.txt ]] || die "backend/requirements.txt missing."
[[ -f backend/app/main.py ]] || die "backend/app/main.py missing."

# Safe ignores
touch .gitignore
for x in ".env" ".env.*" "!.env.example" ".venv/" "venv/" "backend/venv/" "__pycache__/" "*.pyc" ".pytest_cache/" ".DS_Store" ".vercel/" "*.db" "*.sqlite" "*.sqlite3"; do
  grep -qxF "$x" .gitignore 2>/dev/null || printf '%s\n' "$x" >> .gitignore
done

# CLIs
command -v gh >/dev/null 2>&1 || brew install gh
command -v render >/dev/null 2>&1 || brew install render
command -v vercel >/dev/null 2>&1 || npm install -g vercel

gh auth status >/dev/null 2>&1 || gh auth login --hostname github.com --git-protocol https --web
ok "GitHub authenticated"

# Render: use API key, not render login (avoids slow_down)
if [[ -z "${RENDER_API_KEY:-}" ]]; then
  echo
  echo "Create a Render API key: Render Dashboard -> Account Settings -> API Keys -> Create API Key"
  echo "Paste it below. It is used only by this process and is NOT saved."
  read -r -s -p "Render API key (rnd_...): " RENDER_API_KEY
  echo
fi
[[ -n "${RENDER_API_KEY:-}" ]] || die "No Render API key provided."
export RENDER_API_KEY

# Select first workspace
WS_JSON="$(render workspaces --output json)"
WS_ID="$(WS_JSON="$WS_JSON" python3 - <<'PY'
import json, os
d=json.loads(os.environ["WS_JSON"])
xs=d if isinstance(d,list) else d.get("workspaces", d.get("items", d.get("data", [])))
if not xs: raise SystemExit("No Render workspace found.")
print(xs[0]["id"])
PY
)"
render workspace set "$WS_ID" >/dev/null 2>&1 || true
ok "Render API authentication/workspace ready"

# Git init + remote
if [[ ! -d .git ]]; then git init; fi
git branch -M main
if git remote get-url origin >/dev/null 2>&1; then
  git remote set-url origin "$REPO_URL"
else
  git remote add origin "$REPO_URL"
fi

if ! gh repo view ashneetjha/Student_Oppotunity_Tracker >/dev/null 2>&1; then
  gh repo create ashneetjha/Student_Oppotunity_Tracker --public --source . --remote origin
fi

# FIRST COMMIT/PUSH
log "Committing project to GitHub"
git add -A
git rm --cached --ignore-unmatch .env >/dev/null 2>&1 || true
if ! git diff --cached --quiet; then git commit -m "feat: complete Student Opportunity Tracker prototype"; fi
git push -u origin main
ok "GitHub push complete: $REPO_URL"

# Initial Vercel deploy
log "Initial Vercel deployment"
vercel whoami >/dev/null 2>&1 || vercel login
VOUT="$(vercel --prod --yes --name "$VERCEL_PROJECT_NAME" 2>&1)"
printf '%s\n' "$VOUT"
VERCEL_URL="$(printf '%s\n' "$VOUT" | grep -Eo 'https://[A-Za-z0-9._-]+\.vercel\.app' | tail -1 || true)"
[[ -n "$VERCEL_URL" ]] || die "Could not determine Vercel URL."

# Render service create/update
log "Deploying FastAPI backend"
SERVICES="$(render services --output json)"
EXISTS="$(SERVICES="$SERVICES" python3 - "$SERVICE_NAME" <<'PY'
import json, os, sys
name=sys.argv[1]
d=json.loads(os.environ["SERVICES"])
xs=d if isinstance(d,list) else d.get("services", d.get("items", d.get("data", [])))
print("1" if any(isinstance(x,dict) and x.get("name")==name for x in xs) else "0")
PY
)"

if [[ "$EXISTS" == "1" ]]; then
  render services update "$SERVICE_NAME" \
    --repo "$REPO_URL" --branch main --runtime python --region singapore \
    --build-command "$BACKEND_BUILD" --start-command "$BACKEND_START" \
    --auto-deploy \
    --env-var "DATABASE_URL=sqlite:///./opportunity_tracker.db" \
    --env-var "JWT_SECRET=student-opportunity-tracker-demo-secret-2026" \
    --env-var "JWT_ALGORITHM=HS256" \
    --env-var "ACCESS_TOKEN_EXPIRE_MINUTES=1440" \
    --env-var "FRONTEND_URL=$VERCEL_URL" \
    --output json
  render deploys create "$SERVICE_NAME" --wait --output json || true
else
  render services create \
    --name "$SERVICE_NAME" --type web_service --runtime python \
    --region singapore --plan free --repo "$REPO_URL" --branch main \
    --auto-deploy --build-command "$BACKEND_BUILD" --start-command "$BACKEND_START" \
    --env-var "DATABASE_URL=sqlite:///./opportunity_tracker.db" \
    --env-var "JWT_SECRET=student-opportunity-tracker-demo-secret-2026" \
    --env-var "JWT_ALGORITHM=HS256" \
    --env-var "ACCESS_TOKEN_EXPIRE_MINUTES=1440" \
    --env-var "FRONTEND_URL=$VERCEL_URL" \
    --output json
fi

# Discover Render URL
SERVICES="$(render services --output json)"
RENDER_URL="$(SERVICES="$SERVICES" python3 - "$SERVICE_NAME" <<'PY'
import json, os, sys
name=sys.argv[1]
d=json.loads(os.environ["SERVICES"])
def walk(x):
    if isinstance(x,dict):
        if x.get("name")==name:
            for k in ("url","serviceUrl","service_url"):
                if isinstance(x.get(k),str) and x[k].startswith("http"): return x[k].rstrip("/")
            sd=x.get("serviceDetails")
            if isinstance(sd,dict) and isinstance(sd.get("url"),str): return sd["url"].rstrip("/")
        for v in x.values():
            r=walk(v)
            if r: return r
    elif isinstance(x,list):
        for v in x:
            r=walk(v)
            if r: return r
    return ""
print(walk(d))
PY
)"
[[ -n "$RENDER_URL" ]] || RENDER_URL="https://${SERVICE_NAME}.onrender.com"
ok "Render URL: $RENDER_URL"

# Rewrite localhost API URLs
python3 - "$RENDER_URL/api" <<'PY'
from pathlib import Path
import re, sys
api=sys.argv[1].rstrip("/")
patterns=[
 r'http://127\.0\.0\.1:8000/api',
 r'http://localhost:8000/api',
 r'http://127\.0\.0\.1:8000',
 r'http://localhost:8000'
]
n=0
for p in Path(".").rglob("*"):
    if not p.is_file() or p.suffix not in {".js",".html"}: continue
    if any(x in p.parts for x in [".git",".venv","venv","node_modules","backend"]): continue
    s=p.read_text(errors="ignore"); t=s
    for pat in patterns:
        t,c=re.subn(pat,api,t); n+=c
    if t!=s:
        p.write_text(t); print("Updated",p)
print("API replacements:",n)
PY

# Final commit/push
log "Pushing frontend -> deployed backend integration"
git add -A
git rm --cached --ignore-unmatch .env >/dev/null 2>&1 || true
if ! git diff --cached --quiet; then git commit -m "fix: connect frontend to deployed FastAPI backend"; fi
git push origin main

# Final Vercel redeploy
log "Final Vercel deployment"
VOUT="$(vercel --prod --yes --name "$VERCEL_PROJECT_NAME" 2>&1)"
printf '%s\n' "$VOUT"
FINAL_VERCEL_URL="$(printf '%s\n' "$VOUT" | grep -Eo 'https://[A-Za-z0-9._-]+\.vercel\.app' | tail -1 || true)"
[[ -n "$FINAL_VERCEL_URL" ]] && VERCEL_URL="$FINAL_VERCEL_URL"

# Smoke tests
log "Smoke testing"
curl -fsS "$RENDER_URL/api/health" >/dev/null && echo "[OK] Render health" || echo "[WARN] Render health not ready"
curl -fsS "$RENDER_URL/docs" >/dev/null && echo "[OK] Swagger" || echo "[WARN] Swagger not ready"
curl -fsSI "$VERCEL_URL" >/dev/null && echo "[OK] Vercel frontend" || echo "[WARN] Vercel frontend not ready"

echo
echo "============================================================"
echo "DEPLOYMENT COMPLETE"
echo "GitHub:  https://github.com/ashneetjha/Student_Oppotunity_Tracker"
echo "Frontend: $VERCEL_URL"
echo "Backend:  $RENDER_URL"
echo "Swagger:  $RENDER_URL/docs"
echo "Student:  student@example.com / Student@123"
echo "Admin:    admin@example.com / Admin@123"
echo "============================================================"
