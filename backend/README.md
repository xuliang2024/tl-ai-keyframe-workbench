# Backend

FastAPI backend for FrameLab.

## Development

```bash
cd backend
python3 -m venv .venv
source .venv/bin/activate
pip install -e ".[dev]"
uvicorn app.main:app --reload --host 127.0.0.1 --port 8000
```

Health check:

```text
GET http://127.0.0.1:8000/api/v1/health
```

Authentication:

```text
POST /api/v1/auth/register
POST /api/v1/auth/login
POST /api/v1/auth/refresh
POST /api/v1/auth/logout
GET  /api/v1/auth/me
POST /api/v1/auth/mcp-tokens
GET  /api/v1/auth/mcp-tokens
DELETE /api/v1/auth/mcp-tokens/{token_id}
```

Default web access tokens are long-lived: `AUTH_ACCESS_TOKEN_EXPIRES_MINUTES=525600`
and `AUTH_REFRESH_TOKEN_EXPIRES_DAYS=3650`.

LLM configuration check:

```text
GET  http://127.0.0.1:8000/api/v1/llm/config
POST http://127.0.0.1:8000/api/v1/llm/chat
```

## SDK / CLI / MCP

Install the backend package in editable mode to expose the `framelab` CLI:

```bash
pip install -e ".[dev]"
framelab --help
```

Python SDK example:

```python
from app.sdk import FrameLabClient

with FrameLabClient("http://127.0.0.1:8000/api/v1") as client:
    auth = client.login(login="user_1ff4vbit", password="<password>")
    client.set_access_token(auth["access_token"])
    project = client.create_project(name="Rain Night", aspect_ratio="16:9")
    client.update_script(project["id"], "A short script...")
    task = client.create_generation_task(
        project_id=project["id"],
        frame_id="<frame-id>",
        image_type="keyframe",
        prompt="The protagonist opens the encrypted black box in the AI court.",
    )
```

Create a long-lived MCP token through the SDK:

```python
from app.sdk import FrameLabClient

with FrameLabClient("http://127.0.0.1:8000/api/v1") as client:
    auth = client.login(login="user_1ff4vbit", password="<password>")
    client.set_access_token(auth["access_token"])
    mcp_token = client.create_mcp_token(name="local mastra agent")
    print(mcp_token["token"])
```

For `image_type="keyframe"`, FrameLab automatically attaches the project's current
asset images as reference images. Pass `asset_ids=[...]` to restrict references to
specific characters, props, or scenes, or set `auto_apply_asset_references=False`
to disable this behavior.

CLI keyframe example:

```bash
export FRAMELAB_API_TOKEN="<access_token>"
framelab generate \
  --project-id <project-id> \
  --frame-id <frame-id> \
  --image-type keyframe \
  --prompt "The protagonist opens the encrypted black box in the AI court."
```

CLI token signing:

```bash
framelab auth login --login user_1ff4vbit --password '<password>'
framelab --token '<access_token>' auth mcp-token create --name 'local mastra agent'
```

MCP endpoints:

```text
GET  /api/v1/mcp/tools
GET  /api/v1/mcp/tools/{tool_name}
POST /api/v1/mcp-http
GET  /api/v1/mcp-http
DELETE /api/v1/mcp-http
```

The MCP HTTP endpoint implements a lightweight Streamable HTTP JSON-RPC surface with
`initialize`, `tools/list`, and `tools/call`.
