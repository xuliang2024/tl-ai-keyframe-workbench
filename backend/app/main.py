from pathlib import Path

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import PlainTextResponse

from app.api.v1.router import api_router
from app.core.config import settings
from app.services.database_store import store


def create_app() -> FastAPI:
    app = FastAPI(title=settings.app_name)

    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.backend_cors_origins,
        allow_origin_regex=r"^http://(localhost|127\.0\.0\.1):\d+$",
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    @app.on_event("startup")
    async def ensure_database_schema() -> None:
        await store.ensure_schema()

    @app.get("/cli", response_class=PlainTextResponse, include_in_schema=False)
    async def cli_installer() -> str:
        return build_cli_installer_script()

    app.include_router(api_router, prefix=settings.api_v1_prefix)
    return app


app = create_app()


def build_cli_installer_script() -> str:
    backend_dir = Path(__file__).resolve().parents[1]
    return f"""#!/usr/bin/env sh
set -eu

FRAMELAB_BACKEND_DIR={sh_quote(str(backend_dir))}
COMMAND="${{1:-install}}"
if [ "$COMMAND" = "-h" ] || [ "$COMMAND" = "--help" ]; then
  COMMAND="help"
fi
if [ "${{COMMAND#--}}" != "$COMMAND" ]; then
  COMMAND="install"
elif [ "$#" -gt 0 ]; then
  shift
fi
if [ "${{1:-}}" = "framelab" ]; then shift; fi

API_URL="http://127.0.0.1:18081/api/v1"
MCP_URL="http://127.0.0.1:18081/api/v1/mcp-http"
TOKEN=""
CLIENT=""
SAVE_ENV=".env.local"
INSTALL_BIN=0
CONFIGURE_AGENT=0

usage() {{
  cat <<'USAGE'
Usage:
  curl -fsSL http://127.0.0.1:18081/cli | sh -s -- install framelab [options]
  curl -fsSL http://127.0.0.1:18081/cli | sh -s -- --token TOKEN

Options:
  --api-url URL          FrameLab REST API URL
  --mcp-url URL          FrameLab MCP HTTP URL
  --token TOKEN          MCP token to save as FRAMELAB_MCP_TOKEN
  --client NAME          Agent client: auto, codex, or opencode. Defaults to auto when a token is provided.
  --save-env FILE        Directory env file to update, default .env.local
  --install-bin          Install the framelab CLI into the active Python environment
  --configure-agent      Configure the selected agent when possible
USAGE
}}

while [ "$#" -gt 0 ]; do
  case "$1" in
    --api-url) API_URL="$2"; shift 2 ;;
    --mcp-url) MCP_URL="$2"; shift 2 ;;
    --token) TOKEN="$2"; shift 2 ;;
    --client) CLIENT="$2"; shift 2 ;;
    --save-env) SAVE_ENV="$2"; shift 2 ;;
    --install-bin) INSTALL_BIN=1; shift ;;
    --configure-agent) CONFIGURE_AGENT=1; shift ;;
    -h|--help) usage; exit 0 ;;
    *) echo "Unknown option: $1" >&2; usage; exit 2 ;;
  esac
done

if [ "$COMMAND" = "help" ]; then
  usage
  exit 0
fi

if [ "$COMMAND" != "install" ]; then
  echo "Unknown command: $COMMAND" >&2
  usage
  exit 2
fi

find_python() {{
  for candidate in python3 python; do
    if command -v "$candidate" >/dev/null 2>&1; then
      if "$candidate" - <<'PY' >/dev/null 2>&1
import sys
raise SystemExit(0 if sys.version_info >= (3, 11) else 1)
PY
      then
        echo "$candidate"
        return 0
      fi
    fi
  done
  return 1
}}

ensure_line() {{
  file="$1"
  line="$2"
  touch "$file"
  if ! grep -qxF "$line" "$file"; then
    printf '%s\\n' "$line" >> "$file"
  fi
}}

set_env_value() {{
  file="$1"
  key="$2"
  value="$3"
  touch "$file"
  escaped=$(printf '%s' "$value" | sed "s/'/'\\\\''/g")
  if grep -q "^${{key}}=" "$file"; then
    tmp="${{file}}.tmp.$$"
    sed "s|^${{key}}=.*|${{key}}='${{escaped}}'|" "$file" > "$tmp"
    mv "$tmp" "$file"
  else
    printf "%s='%s'\\n" "$key" "$escaped" >> "$file"
  fi
}}

PYTHON=$(find_python || true)
if [ -z "$PYTHON" ]; then
  echo "Python 3.11+ is required to install framelab CLI." >&2
  exit 1
fi

if [ "$INSTALL_BIN" -eq 1 ] || ! command -v framelab >/dev/null 2>&1; then
  "$PYTHON" -m pip install -e "$FRAMELAB_BACKEND_DIR"
fi

set_env_value "$SAVE_ENV" "FRAMELAB_API_URL" "$API_URL"
set_env_value "$SAVE_ENV" "FRAMELAB_MCP_URL" "$MCP_URL"
if [ -n "$TOKEN" ]; then
  set_env_value "$SAVE_ENV" "FRAMELAB_MCP_TOKEN" "$TOKEN"
  set_env_value "$SAVE_ENV" "FRAMELAB_API_TOKEN" "$TOKEN"
fi

ensure_line ".gitignore" "$SAVE_ENV"
if [ -f ".envrc" ] || command -v direnv >/dev/null 2>&1; then
  ensure_line ".envrc" "source_env_if_exists $SAVE_ENV"
fi

if [ -z "$CLIENT" ] && [ -n "$TOKEN" ]; then
  CLIENT="auto"
fi

if [ -n "$CLIENT" ]; then
  CONFIGURE_AGENT=1
fi

if [ "$CONFIGURE_AGENT" -eq 1 ] && [ -n "$CLIENT" ]; then
  if [ "$CLIENT" = "auto" ]; then
    FOUND_AGENT=0
    if command -v codex >/dev/null 2>&1; then
      FOUND_AGENT=1
      FRAMELAB_MCP_TOKEN="$TOKEN" codex mcp add framelab --url "$MCP_URL" --bearer-token-env-var FRAMELAB_MCP_TOKEN || true
    fi
    if command -v opencode >/dev/null 2>&1; then
      FOUND_AGENT=1
      echo "OpenCode detected. If prompted, add remote MCP framelab with URL $MCP_URL and Authorization: Bearer \\$FRAMELAB_MCP_TOKEN."
      opencode mcp add || true
    fi
    if [ "$FOUND_AGENT" -eq 0 ]; then
      echo "No supported agent command found; installed framelab CLI and saved environment only." >&2
    fi
  elif [ "$CLIENT" = "codex" ]; then
    if command -v codex >/dev/null 2>&1; then
      FRAMELAB_MCP_TOKEN="$TOKEN" codex mcp add framelab --url "$MCP_URL" --bearer-token-env-var FRAMELAB_MCP_TOKEN || true
    else
      echo "codex command not found; installed framelab CLI only." >&2
    fi
  elif [ "$CLIENT" = "opencode" ]; then
    if command -v opencode >/dev/null 2>&1; then
      echo "OpenCode detected. If prompted, add remote MCP framelab with URL $MCP_URL and Authorization: Bearer \\$FRAMELAB_MCP_TOKEN."
      opencode mcp add || true
    else
      echo "opencode command not found; installed framelab CLI only." >&2
    fi
  else
    echo "Unknown client '$CLIENT'; installed framelab CLI only." >&2
  fi
fi

echo "FrameLab CLI installed."
framelab --help >/dev/null
echo "Saved directory environment to $SAVE_ENV."
"""


def sh_quote(value: str) -> str:
    return "'" + value.replace("'", "'\\''") + "'"
