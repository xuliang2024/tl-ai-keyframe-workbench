import asyncio

from fastapi.testclient import TestClient

from app.api.v1 import generation_tasks
from app.main import app
from app.services.database_store import store
from conftest import auth_headers


class DummyStorage:
    bucket = "sut-www-51sut-com"

    def upload_bytes(self, object_key: str, data: bytes, content_type: str) -> str:
        assert data == b"png-bytes"
        assert content_type == "image/png"
        return f"https://cdn.51sut.com/{object_key}"


def test_public_asset_import_copies_asset_and_media_record() -> None:
    store.reset()
    public_media = asyncio.run(
        store.create_media_file(
            project_id=None,
            owner_user_id=None,
            file_type="image",
            bucket="tl-keyframe",
            object_key="media/public/hero.png",
            url="http://127.0.0.1:8000/uploads/media/public/hero.png",
            mime_type="image/png",
            metadata={"usage": "public_asset"},
        )
    )
    assert public_media
    public_media = asyncio.run(store.complete_media_file(public_media.id, width=512, height=768))
    assert public_media
    public_asset = asyncio.run(
        store.create_public_asset(
            name="公共主角",
            type="角色",
            description="公共库里的角色设定",
            default_prompt="黑色短发，蓝色外套",
            tags=["角色", "公共"],
            image_file_id=public_media.id,
        )
    )
    assert public_asset

    client = TestClient(app)
    headers = auth_headers(client)
    project = client.post("/api/v1/projects", json={"name": "导入测试"}, headers=headers).json()

    list_response = client.get("/api/v1/public-assets", headers=headers)
    assert list_response.status_code == 200
    assert list_response.json()["items"][0]["image_url"] == public_media.url

    import_response = client.post(
        f"/api/v1/projects/{project['id']}/assets/import-public",
        json={"public_asset_ids": [public_asset.id]},
        headers=headers,
    )

    assert import_response.status_code == 200
    body = import_response.json()
    assert body["errors"] == []
    assert len(body["items"]) == 1
    imported = body["items"][0]
    assert imported["id"] != public_asset.id
    assert imported["name"] == public_asset.name
    assert imported["image_file_id"] != public_media.id
    assert imported["image_url"].endswith(".png")

    project_assets = client.get(f"/api/v1/projects/{project['id']}/assets", headers=headers).json()["items"]
    assert project_assets[0]["id"] == imported["id"]

    client.patch(f"/api/v1/assets/{imported['id']}", json={"name": "项目内主角"}, headers=headers)
    unchanged_public_asset = asyncio.run(store.get_public_asset(public_asset.id))
    assert unchanged_public_asset
    assert unchanged_public_asset.name == "公共主角"


def test_public_asset_images_api_returns_gallery_and_primary_fallback() -> None:
    store.reset()
    primary_media = asyncio.run(
        store.create_media_file(
            project_id=None,
            owner_user_id=None,
            file_type="image",
            bucket="tl-keyframe",
            object_key="media/public/primary.png",
            url="https://cdn.51sut.com/media/public/primary.png",
            mime_type="image/png",
            metadata={"usage": "public_asset"},
        )
    )
    gallery_media = asyncio.run(
        store.create_media_file(
            project_id=None,
            owner_user_id=None,
            file_type="image",
            bucket="tl-keyframe",
            object_key="media/public/front.png",
            url="https://cdn.51sut.com/media/public/front.png",
            mime_type="image/png",
            metadata={"usage": "public_asset_gallery"},
        )
    )
    assert primary_media and gallery_media
    public_asset = asyncio.run(
        store.create_public_asset(
            name="图集角色",
            type="角色",
            description="用于图集测试",
            default_prompt="白色背景角色资产图",
            image_file_id=primary_media.id,
        )
    )
    assert public_asset

    client = TestClient(app)
    headers = auth_headers(client)

    fallback_response = client.get(f"/api/v1/public-assets/{public_asset.id}/images", headers=headers)
    assert fallback_response.status_code == 200
    fallback_items = fallback_response.json()["items"]
    assert fallback_items[0]["role"] == "primary"
    assert fallback_items[0]["image_url"] == primary_media.url

    create_response = client.post(
        f"/api/v1/public-assets/{public_asset.id}/images",
        json={
            "media_file_id": gallery_media.id,
            "role": "front",
            "title": "正面全身",
            "description": "正面角度",
            "prompt": "正面全身角色图",
            "angle": "front",
            "tags": ["正面"],
            "is_primary": True,
        },
        headers=headers,
    )
    assert create_response.status_code == 201
    created = create_response.json()
    assert created["image_url"] == gallery_media.url
    assert created["is_primary"] is True

    list_response = client.get(f"/api/v1/public-assets/{public_asset.id}/images", headers=headers)
    assert list_response.status_code == 200
    items = list_response.json()["items"]
    assert len(items) == 1
    assert items[0]["title"] == "正面全身"


def test_public_asset_generation_task_writes_gallery_image(monkeypatch) -> None:
    store.reset()
    primary_media = asyncio.run(
        store.create_media_file(
            project_id=None,
            owner_user_id=None,
            file_type="image",
            bucket="tl-keyframe",
            object_key="media/public/primary.png",
            url="https://cdn.51sut.com/media/public/primary.png",
            mime_type="image/png",
            metadata={"usage": "public_asset"},
        )
    )
    assert primary_media
    public_asset = asyncio.run(
        store.create_public_asset(
            name="任务角色",
            type="角色",
            description="公共角色",
            default_prompt="固定角色设定",
            image_file_id=primary_media.id,
        )
    )
    assert public_asset

    async def fake_generate_image(self, **kwargs):
        assert kwargs["image"] == primary_media.url
        assert "固定角色设定" in kwargs["prompt"]
        assert "雨夜奔跑" in kwargs["prompt"]
        return {
            "model": "openai/gpt-image-2/edit",
            "data": [{"b64_json": "cG5nLWJ5dGVz", "size": "2160x3840"}],
        }

    monkeypatch.setattr(generation_tasks.ApizGenerationClient, "generate_image", fake_generate_image)
    monkeypatch.setattr(generation_tasks, "get_object_storage_client", lambda: DummyStorage())

    client = TestClient(app)
    headers = auth_headers(client, username="public_asset_generator")
    response = client.post(
        "/api/v1/generation-tasks",
        json={
            "prompt": "雨夜奔跑",
            "aspect_ratio": "9:16",
            "target": {
                "type": "public_asset_gallery",
                "public_asset_id": public_asset.id,
                "title": "雨夜奔跑",
                "role": "generated",
            },
        },
        headers=headers,
    )
    assert response.status_code == 200
    task_id = response.json()["task_id"]

    task_response = client.get(f"/api/v1/generation-tasks/{task_id}", headers=headers)
    assert task_response.status_code == 200
    assert task_response.json()["status"] == "succeeded"

    task_list_response = client.get(
        f"/api/v1/generation-tasks?target_type=public_asset_gallery&target_id={public_asset.id}&limit=20",
        headers=headers,
    )
    assert task_list_response.status_code == 200
    assert [item["task_id"] for item in task_list_response.json()["items"]] == [task_id]

    images_response = client.get(f"/api/v1/public-assets/{public_asset.id}/images", headers=headers)
    assert images_response.status_code == 200
    items = images_response.json()["items"]
    generated = [item for item in items if item["generation_task_id"] == task_id]
    assert len(generated) == 1
    assert generated[0]["source_type"] == "generated"
    assert generated[0]["created_by_name"] == "public_asset_generator"
