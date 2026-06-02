from fastapi.testclient import TestClient

from app.api.v1 import media
from app.main import app
from app.services.database_store import store
from conftest import auth_headers


class DummyStorage:
    bucket = "sut-www-51sut-com"

    def public_url(self, object_key: str) -> str:
        return f"https://cdn.51sut.com/{object_key}"

    def generate_presigned_put_url(self, object_key: str, expires_in: int) -> str:
        return f"https://sut-www-51sut-com.tos-cn-guangzhou.volces.com/{object_key}?signed=1&expires={expires_in}"


def test_create_image_upload_url_and_complete(monkeypatch) -> None:
    store.reset()
    monkeypatch.setattr(media, "get_object_storage_client", lambda: DummyStorage())
    client = TestClient(app)
    headers = auth_headers(client)

    project_response = client.post("/api/v1/projects", json={"name": "上传测试"}, headers=headers)
    project_id = project_response.json()["id"]

    upload_response = client.post(
        "/api/v1/media/upload-url",
        json={
            "project_id": project_id,
            "filename": "角色图.png",
            "file_type": "image",
            "mime_type": "image/png",
            "size_bytes": 1234,
        },
        headers=headers,
    )

    assert upload_response.status_code == 200
    upload = upload_response.json()
    assert upload["bucket"] == "sut-www-51sut-com"
    assert upload["upload_method"] == "PUT"
    assert upload["upload_headers"] == {"Content-Type": "image/png"}
    assert upload["public_url"].startswith("https://cdn.51sut.com/media/")
    assert "/images/" in upload["object_key"]
    assert upload["object_key"].endswith("-file.png")

    complete_response = client.post(
        f"/api/v1/media/{upload['media_file_id']}/complete",
        json={"width": 1024, "height": 768, "metadata": {"usage": "asset"}},
        headers=headers,
    )

    assert complete_response.status_code == 200
    media_file = complete_response.json()
    assert media_file["status"] == "uploaded"
    assert media_file["width"] == 1024
    assert media_file["height"] == 768
    assert media_file["metadata"]["original_filename"] == "角色图.png"
    assert media_file["metadata"]["usage"] == "asset"


def test_asset_response_includes_media_image_url(monkeypatch) -> None:
    store.reset()
    monkeypatch.setattr(media, "get_object_storage_client", lambda: DummyStorage())
    client = TestClient(app)
    headers = auth_headers(client)

    project_response = client.post(
        "/api/v1/projects",
        json={"name": "资产图片回读测试"},
        headers=headers,
    )
    project_id = project_response.json()["id"]
    upload_response = client.post(
        "/api/v1/media/upload-url",
        json={
            "project_id": project_id,
            "filename": "asset.png",
            "file_type": "image",
            "mime_type": "image/png",
            "size_bytes": 10,
        },
        headers=headers,
    )
    media_file_id = upload_response.json()["media_file_id"]
    public_url = upload_response.json()["public_url"]

    asset_response = client.post(
        f"/api/v1/projects/{project_id}/assets",
        json={
            "name": "带图资产",
            "type": "role",
            "image_file_id": media_file_id,
        },
        headers=headers,
    )

    assert asset_response.status_code == 201
    assert asset_response.json()["image_file_id"] == media_file_id
    assert asset_response.json()["image_url"] == public_url

    list_response = client.get(f"/api/v1/projects/{project_id}/assets", headers=headers)
    assert list_response.status_code == 200
    assert list_response.json()["items"][0]["image_url"] == public_url


def test_create_video_upload_url(monkeypatch) -> None:
    store.reset()
    monkeypatch.setattr(media, "get_object_storage_client", lambda: DummyStorage())
    client = TestClient(app)
    headers = auth_headers(client)

    upload_response = client.post(
        "/api/v1/media/upload-url",
        json={
            "filename": "preview.mp4",
            "file_type": "video",
            "mime_type": "video/mp4",
            "size_bytes": 9876,
        },
        headers=headers,
    )

    assert upload_response.status_code == 200
    upload = upload_response.json()
    assert "/unassigned/videos/" in upload["object_key"]
    assert upload["public_url"].endswith(".mp4")


def test_rejects_mismatched_mime_type(monkeypatch) -> None:
    store.reset()
    monkeypatch.setattr(media, "get_object_storage_client", lambda: DummyStorage())
    client = TestClient(app)
    headers = auth_headers(client)

    response = client.post(
        "/api/v1/media/upload-url",
        json={
            "filename": "not-video.png",
            "file_type": "video",
            "mime_type": "image/png",
            "size_bytes": 100,
        },
        headers=headers,
    )

    assert response.status_code == 422


def test_rejects_unknown_project(monkeypatch) -> None:
    store.reset()
    monkeypatch.setattr(media, "get_object_storage_client", lambda: DummyStorage())
    client = TestClient(app)
    headers = auth_headers(client)

    response = client.post(
        "/api/v1/media/upload-url",
        json={
            "project_id": "missing-project",
            "filename": "asset.png",
            "file_type": "image",
            "mime_type": "image/png",
        },
        headers=headers,
    )

    assert response.status_code == 404
