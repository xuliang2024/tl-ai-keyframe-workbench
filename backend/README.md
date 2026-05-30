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
    project = client.create_project(name="Rain Night", aspect_ratio="16:9")
    client.update_script(project["id"], "A short script...")
    task = client.create_generation_task(
        project_id=project["id"],
        frame_id="<frame-id>",
        image_type="keyframe",
        prompt="The protagonist opens the encrypted black box in the AI court.",
    )
```

For `image_type="keyframe"`, FrameLab automatically attaches the project's current
asset images as reference images. Pass `asset_ids=[...]` to restrict references to
specific characters, props, or scenes, or set `auto_apply_asset_references=False`
to disable this behavior.

CLI keyframe example:

```bash
framelab generate \
  --project-id <project-id> \
  --frame-id <frame-id> \
  --image-type keyframe \
  --prompt "The protagonist opens the encrypted black box in the AI court."
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
