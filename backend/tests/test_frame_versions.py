import asyncio

from fastapi.testclient import TestClient

from app.main import app
from app.services.database_store import store


def test_frame_version_create_list_and_select() -> None:
    store.reset()
    client = TestClient(app)
    project = client.post("/api/v1/projects", json={"name": "关键帧版本项目"}).json()
    frames = client.get(f"/api/v1/projects/{project['id']}/frames").json()["items"]
    frame_id = frames[0]["id"]
    media_file = asyncio.run(
        store.create_media_file(
            project_id=project["id"],
            file_type="image",
            bucket="sut-www-51sut-com",
            object_key="media/generated/frame.png",
            url="https://cdn.51sut.com/media/generated/frame.png",
            mime_type="image/png",
        )
    )
    assert media_file

    create_response = client.post(
        f"/api/v1/frames/{frame_id}/versions",
        json={
            "image_file_id": media_file.id,
            "prompt": "雨夜码头关键帧",
            "note": "雨夜码头",
            "select": True,
        },
    )

    assert create_response.status_code == 201
    version = create_response.json()
    assert version["version_no"] == 1
    assert version["image_url"] == media_file.url

    frames_response = client.get(f"/api/v1/projects/{project['id']}/frames")
    assert frames_response.status_code == 200
    frame = frames_response.json()["items"][0]
    assert frame["selected_version_id"] == version["id"]
    assert frame["current_prompt"] == "雨夜码头关键帧"
    assert frame["versions"][0]["image_url"] == media_file.url

    select_response = client.post(
        f"/api/v1/frames/{frame_id}/versions/select",
        json={"version_id": version["id"]},
    )
    assert select_response.status_code == 200
    assert select_response.json()["selected_version_id"] == version["id"]
