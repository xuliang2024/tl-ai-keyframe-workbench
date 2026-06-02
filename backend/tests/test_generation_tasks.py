import asyncio

from fastapi.testclient import TestClient

from app.api.v1 import generation_tasks
from app.integrations.apiz_generation import ApizGenerationClient
from app.main import app
from app.services.database_store import store
from conftest import auth_headers


class DummyStorage:
    bucket = "sut-www-51sut-com"

    def upload_bytes(self, object_key: str, data: bytes, content_type: str) -> str:
        assert data == b"png-bytes"
        assert content_type == "image/png"
        return f"https://cdn.51sut.com/{object_key}"


def test_create_text_to_image_task(monkeypatch) -> None:
    store.reset()

    async def fake_generate_image(self, **kwargs):
        return {
            "model": "openai/gpt-image-2",
            "data": [{"b64_json": "cG5nLWJ5dGVz", "size": "3840x2160"}],
            "usage": {"generated_images": 1},
        }

    monkeypatch.setattr(generation_tasks.ApizGenerationClient, "generate_image", fake_generate_image)
    monkeypatch.setattr(generation_tasks, "get_object_storage_client", lambda: DummyStorage())

    client = TestClient(app)
    client.headers.update(auth_headers(client, username="gen_text_image"))
    response = client.post(
        "/api/v1/generation-tasks",
        json={"prompt": "雨夜街头的女主角", "aspect_ratio": "16:9", "project_id": None},
    )

    assert response.status_code == 200
    body = response.json()
    assert body["status"] == "queued"
    assert body["task_type"] == "text_to_image"
    assert body["provider"] == "apiz"
    assert body["model_name"] == "openai/gpt-image-2"
    assert body["size"] == "4K"
    assert body["prompt"] == "雨夜街头的女主角"

    task_response = client.get(f"/api/v1/generation-tasks/{body['task_id']}")
    assert task_response.status_code == 200
    task_body = task_response.json()
    assert task_body["task_id"] == body["task_id"]
    assert task_body["status"] == "succeeded"
    assert task_body["images"][0]["url"].startswith("https://cdn.51sut.com/media/unassigned/generated/images/")
    assert task_body["images"][0]["media_file_id"]
    assert "b64_json" not in task_body["images"][0] or task_body["images"][0]["b64_json"] is None


def test_list_generation_tasks_supports_filters(monkeypatch) -> None:
    store.reset()

    async def fake_generate_image(self, **kwargs):
        return {
            "model": "openai/gpt-image-2",
            "data": [{"b64_json": "cG5nLWJ5dGVz", "size": "3840x2160"}],
        }

    monkeypatch.setattr(generation_tasks.ApizGenerationClient, "generate_image", fake_generate_image)
    monkeypatch.setattr(generation_tasks, "get_object_storage_client", lambda: DummyStorage())

    client = TestClient(app)
    headers = auth_headers(client, username="gen_task_list")
    project = client.post("/api/v1/projects", json={"name": "任务列表项目"}, headers=headers).json()
    created = client.post(
        "/api/v1/generation-tasks",
        json={
            "prompt": "列表测试图",
            "aspect_ratio": "16:9",
            "project_id": project["id"],
        },
        headers=headers,
    ).json()

    list_response = client.get(
        "/api/v1/generation-tasks",
        params={"status": "succeeded", "task_type": "text_to_image", "project_id": project["id"]},
        headers=headers,
    )
    assert list_response.status_code == 200
    items = list_response.json()["items"]
    assert [item["task_id"] for item in items] == [created["task_id"]]


def test_apiz_extracts_object_image_urls_once() -> None:
    image_url = "https://example.com/generated.png"
    task_payload = {
        "result": {"images": [{"url": image_url, "width": 1088, "height": 608}]},
        "output": {"images": [{"url": image_url, "width": 1088, "height": 608}]},
    }

    assert ApizGenerationClient._extract_urls(task_payload, key="images") == [image_url]


def test_create_image_to_image_task(monkeypatch) -> None:
    store.reset()
    captured = {}

    async def fake_generate_image(self, **kwargs):
        captured.update(kwargs)
        return {
            "model": "openai/gpt-image-2/edit",
            "data": [{"b64_json": "cG5nLWJ5dGVz", "size": "2160x3840"}],
        }

    monkeypatch.setattr(generation_tasks.ApizGenerationClient, "generate_image", fake_generate_image)
    monkeypatch.setattr(generation_tasks, "get_object_storage_client", lambda: DummyStorage())

    client = TestClient(app)
    client.headers.update(auth_headers(client, username="gen_image_to_image"))
    response = client.post(
        "/api/v1/generation-tasks",
        json={
            "task_type": "image_to_image",
            "prompt": "保持人物一致，改成电影海报光影",
            "aspect_ratio": "9:16",
            "image": "data:image/png;base64,abc",
        },
    )

    assert response.status_code == 200
    body = response.json()
    assert body["status"] == "queued"
    assert body["task_type"] == "image_to_image"
    assert body["model_name"] == "openai/gpt-image-2/edit"
    assert captured["image"] == "data:image/png;base64,abc"
    assert captured["resolution"] == "4K"

    task_response = client.get(f"/api/v1/generation-tasks/{body['task_id']}")
    assert task_response.status_code == 200
    task_body = task_response.json()
    assert task_body["status"] == "succeeded"
    assert task_body["images"][0]["url"].startswith("https://cdn.51sut.com/media/unassigned/generated/images/")
    assert task_body["images"][0]["media_file_id"]


def test_generation_task_auto_applies_project_style(monkeypatch) -> None:
    store.reset()
    captured = {}
    client = TestClient(app)
    client.headers.update(auth_headers(client, username="gen_project_style"))
    project = client.post(
        "/api/v1/projects",
        json={"name": "风格项目", "description": "", "aspect_ratio": "9:16"},
    ).json()
    media_file = asyncio.run(
        store.create_media_file(
            project_id=project["id"],
            file_type="image",
            bucket="sut-www-51sut-com",
            object_key="media/style/reference.png",
            url="https://cdn.51sut.com/media/style/reference.png",
            mime_type="image/png",
        )
    )
    assert media_file
    update_response = client.patch(
        f"/api/v1/projects/{project['id']}",
        json={
            "style_prompt": "统一风格：雾灯、胶片颗粒、冷暖对比",
            "style_reference_image_file_id": media_file.id,
            "auto_apply_style_prompt": True,
            "auto_apply_style_reference": True,
        },
    )
    assert update_response.status_code == 200
    assert update_response.json()["style_reference_image_url"] == media_file.url

    async def fake_generate_image(self, **kwargs):
        captured.update(kwargs)
        return {
            "model": "openai/gpt-image-2/edit",
            "data": [{"b64_json": "cG5nLWJ5dGVz", "size": "2160x3840"}],
        }

    monkeypatch.setattr(generation_tasks.ApizGenerationClient, "generate_image", fake_generate_image)
    monkeypatch.setattr(generation_tasks, "get_object_storage_client", lambda: DummyStorage())

    response = client.post(
        "/api/v1/generation-tasks",
        json={
            "task_type": "text_to_image",
            "prompt": "年轻邮差，深绿色旧制服",
            "aspect_ratio": "9:16",
            "project_id": project["id"],
        },
    )

    assert response.status_code == 200
    body = response.json()
    assert body["task_type"] == "image_to_image"
    assert "年轻邮差，深绿色旧制服" in body["prompt"]
    assert "统一风格：雾灯、胶片颗粒、冷暖对比" in body["prompt"]
    assert captured["prompt"] == body["prompt"]
    assert captured["image"] == [media_file.url]

    task_response = client.get(f"/api/v1/generation-tasks/{body['task_id']}")
    assert task_response.status_code == 200
    task_body = task_response.json()
    assert task_body["status"] == "succeeded"
    assert task_body["images"][0]["url"].startswith(
        f"https://cdn.51sut.com/media/{project['id']}/generated/images/"
    )


def test_keyframe_generation_auto_applies_asset_references(monkeypatch) -> None:
    store.reset()
    captured = {}
    client = TestClient(app)
    client.headers.update(auth_headers(client, username="gen_keyframe_refs"))
    project = client.post("/api/v1/projects", json={"name": "关键帧资产参考"}).json()
    media_file = asyncio.run(
        store.create_media_file(
            project_id=project["id"],
            file_type="image",
            bucket="sut-www-51sut-com",
            object_key="media/assets/jianglan.png",
            url="https://cdn.51sut.com/media/assets/jianglan.png",
            mime_type="image/png",
        )
    )
    assert media_file
    asset_response = client.post(
        f"/api/v1/projects/{project['id']}/assets",
        json={
            "name": "江岚",
            "type": "角色",
            "description": "主角",
            "image_file_id": media_file.id,
        },
    )
    assert asset_response.status_code == 201
    frame_response = client.post(
        f"/api/v1/projects/{project['id']}/frames",
        json={
            "summary": "江岚进入审判中枢",
            "current_prompt": "江岚站在金色 AI 法庭前",
        },
    )
    assert frame_response.status_code == 201

    async def fake_generate_image(self, **kwargs):
        captured.update(kwargs)
        return {
            "model": "openai/gpt-image-2/edit",
            "data": [{"b64_json": "cG5nLWJ5dGVz", "size": "3840x2160"}],
        }

    monkeypatch.setattr(generation_tasks.ApizGenerationClient, "generate_image", fake_generate_image)
    monkeypatch.setattr(generation_tasks, "get_object_storage_client", lambda: DummyStorage())

    response = client.post(
        "/api/v1/generation-tasks",
        json={
            "prompt": "江岚站在金色 AI 法庭前，紧张地举起黑匣",
            "project_id": project["id"],
            "frame_id": frame_response.json()["id"],
            "image_type": "keyframe",
        },
    )

    assert response.status_code == 200
    body = response.json()
    assert body["task_type"] == "image_to_image"
    assert "Asset reference requirements" in body["prompt"]
    assert "江岚" in body["prompt"]
    assert captured["image"] == media_file.url

    task = asyncio.run(store.get_generation_task(body["task_id"]))
    assert task
    assert task.request_payload["frame_id"] == frame_response.json()["id"]
    assert task.request_payload["reference_assets"] == [
        {
            "asset_id": asset_response.json()["id"],
            "name": "江岚",
            "type": "角色",
            "image_file_id": media_file.id,
            "url": media_file.url,
        }
    ]


def test_project_style_reference_can_be_cleared() -> None:
    store.reset()
    client = TestClient(app)
    client.headers.update(auth_headers(client, username="gen_clear_style"))
    project = client.post("/api/v1/projects", json={"name": "清除参考图"}).json()
    media_file = asyncio.run(
        store.create_media_file(
            project_id=project["id"],
            file_type="image",
            bucket="sut-www-51sut-com",
            object_key="media/style/reference.png",
            url="https://cdn.51sut.com/media/style/reference.png",
            mime_type="image/png",
        )
    )
    assert media_file

    set_response = client.patch(
        f"/api/v1/projects/{project['id']}",
        json={"style_reference_image_file_id": media_file.id, "auto_apply_style_reference": True},
    )
    assert set_response.status_code == 200
    assert set_response.json()["style_reference_image_file_id"] == media_file.id

    clear_response = client.patch(
        f"/api/v1/projects/{project['id']}",
        json={"style_reference_image_file_id": None, "auto_apply_style_reference": False},
    )
    assert clear_response.status_code == 200
    assert clear_response.json()["style_reference_image_file_id"] is None
    assert clear_response.json()["style_reference_image_url"] is None
    assert clear_response.json()["auto_apply_style_reference"] is False


def test_image_to_image_requires_image() -> None:
    store.reset()
    client = TestClient(app)
    client.headers.update(auth_headers(client, username="gen_requires_image"))
    response = client.post(
        "/api/v1/generation-tasks",
        json={"task_type": "image_to_image", "prompt": "改成赛博朋克", "aspect_ratio": "1:1"},
    )

    assert response.status_code == 422


def test_video_task_uses_apiz_provider(monkeypatch) -> None:
    store.reset()
    captured = {}

    async def fake_generate_video(self, **kwargs):
        captured.update(kwargs)
        return {
            "model": "st-ai/super-seed2-lite",
            "data": [{"url": "https://example.com/generated.mp4"}],
            "usage": {"task_id": "task_123"},
        }

    monkeypatch.setattr(generation_tasks.ApizGenerationClient, "generate_video", fake_generate_video)
    client = TestClient(app)
    client.headers.update(auth_headers(client, username="gen_video"))

    response = client.post(
        "/api/v1/generation-tasks",
        json={"task_type": "text_to_video", "prompt": "雨夜街头镜头推进", "aspect_ratio": "16:9"},
    )

    assert response.status_code == 200
    body = response.json()
    assert body["status"] == "queued"
    assert body["task_type"] == "text_to_video"
    assert body["provider"] == "apiz"
    assert body["model_name"] == "st-ai/super-seed2-lite"

    task_response = client.get(f"/api/v1/generation-tasks/{body['task_id']}")
    assert task_response.status_code == 200
    task_body = task_response.json()
    assert task_body["status"] == "succeeded"
    assert captured["model"] == "st-ai/super-seed2-lite"
    assert captured["ratio"] == "16:9"
