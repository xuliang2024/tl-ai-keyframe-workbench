from fastapi.testclient import TestClient

from app.main import app
from app.services.database_store import store
from conftest import auth_headers


def test_project_script_asset_frame_minimal_loop() -> None:
    store.reset()
    client = TestClient(app)
    headers = auth_headers(client)

    project_response = client.post(
        "/api/v1/projects",
        json={"name": "最小闭环测试项目", "description": "接口集成测试"},
        headers=headers,
    )
    assert project_response.status_code == 201
    project = project_response.json()
    project_id = project["id"]

    list_response = client.get("/api/v1/projects", headers=headers)
    assert list_response.status_code == 200
    assert list_response.json()["items"][0]["id"] == project_id

    script_response = client.put(
        f"/api/v1/projects/{project_id}/script",
        json={"content": "镜头一：角色站在工作台前，准备生成关键帧。"},
        headers=headers,
    )
    assert script_response.status_code == 200
    assert "镜头一" in script_response.json()["content"]

    asset_response = client.post(
        f"/api/v1/projects/{project_id}/assets",
        json={
            "name": "主角",
            "type": "role",
            "description": "测试角色",
            "default_prompt": "短发主角，蓝色外套",
            "tags": ["主角", "锁脸"],
        },
        headers=headers,
    )
    assert asset_response.status_code == 201
    assert asset_response.json()["name"] == "主角"
    assert asset_response.json()["default_prompt"] == "短发主角，蓝色外套"

    frame_list_response = client.get(f"/api/v1/projects/{project_id}/frames", headers=headers)
    assert frame_list_response.status_code == 200
    assert len(frame_list_response.json()["items"]) == 1

    frame_response = client.post(
        f"/api/v1/projects/{project_id}/frames",
        json={
            "summary": "主角检查生成结果",
            "duration_ms": 2500,
            "current_prompt": "@主角 站在屏幕前查看关键帧",
        },
        headers=headers,
    )
    assert frame_response.status_code == 201
    assert frame_response.json()["order_index"] == 2

    updated_frame_response = client.patch(
        f"/api/v1/frames/{frame_response.json()['id']}",
        json={"emotion": "专注", "action": "轻点生成按钮"},
        headers=headers,
    )
    assert updated_frame_response.status_code == 200
    assert updated_frame_response.json()["emotion"] == "专注"


def test_project_crud() -> None:
    store.reset()
    client = TestClient(app)
    headers = auth_headers(client)

    create_response = client.post(
        "/api/v1/projects",
        json={"name": "旧项目名", "description": "旧描述", "aspect_ratio": "16:9"},
        headers=headers,
    )
    assert create_response.status_code == 201
    project_id = create_response.json()["id"]

    update_response = client.patch(
        f"/api/v1/projects/{project_id}",
        json={"name": "新项目名", "description": "新描述", "aspect_ratio": "9:16"},
        headers=headers,
    )
    assert update_response.status_code == 200
    assert update_response.json()["name"] == "新项目名"
    assert update_response.json()["aspect_ratio"] == "9:16"

    delete_response = client.delete(f"/api/v1/projects/{project_id}", headers=headers)
    assert delete_response.status_code == 204

    list_response = client.get("/api/v1/projects", headers=headers)
    assert list_response.status_code == 200
    assert list_response.json()["items"] == []


def test_projects_are_isolated_by_user() -> None:
    store.reset()
    client = TestClient(app)
    user_a_headers = auth_headers(client, username="project_owner_a")
    user_b_headers = auth_headers(client, username="project_owner_b")

    create_response = client.post(
        "/api/v1/projects",
        json={"name": "A 的项目"},
        headers=user_a_headers,
    )
    assert create_response.status_code == 201
    project_id = create_response.json()["id"]

    user_b_list_response = client.get("/api/v1/projects", headers=user_b_headers)
    assert user_b_list_response.status_code == 200
    assert user_b_list_response.json()["items"] == []

    user_b_get_response = client.get(f"/api/v1/projects/{project_id}", headers=user_b_headers)
    assert user_b_get_response.status_code == 404


def test_project_script_crud() -> None:
    store.reset()
    client = TestClient(app)
    headers = auth_headers(client)

    project_response = client.post(
        "/api/v1/projects",
        json={"name": "剧本 CRUD 项目", "description": "验证剧本保存"},
        headers=headers,
    )
    assert project_response.status_code == 201
    project_id = project_response.json()["id"]

    get_empty_response = client.get(f"/api/v1/projects/{project_id}/script", headers=headers)
    assert get_empty_response.status_code == 200
    assert get_empty_response.json()["content"] == ""

    create_response = client.put(
        f"/api/v1/projects/{project_id}/script",
        json={"content": "第一版剧本"},
        headers=headers,
    )
    assert create_response.status_code == 200
    assert create_response.json()["content"] == "第一版剧本"

    update_response = client.put(
        f"/api/v1/projects/{project_id}/script",
        json={"content": "第二版剧本"},
        headers=headers,
    )
    assert update_response.status_code == 200
    assert update_response.json()["content"] == "第二版剧本"

    get_updated_response = client.get(f"/api/v1/projects/{project_id}/script", headers=headers)
    assert get_updated_response.status_code == 200
    assert get_updated_response.json()["content"] == "第二版剧本"

    delete_response = client.delete(f"/api/v1/projects/{project_id}/script", headers=headers)
    assert delete_response.status_code == 204

    get_deleted_response = client.get(f"/api/v1/projects/{project_id}/script", headers=headers)
    assert get_deleted_response.status_code == 200
    assert get_deleted_response.json()["content"] == ""

    missing_response = client.put(
        "/api/v1/projects/missing-project/script",
        json={"content": "不会写入"},
        headers=headers,
    )
    assert missing_response.status_code == 404


def test_project_asset_crud() -> None:
    store.reset()
    client = TestClient(app)
    headers = auth_headers(client)

    project_response = client.post(
        "/api/v1/projects",
        json={"name": "资产 CRUD 项目", "description": "验证资产库"},
        headers=headers,
    )
    assert project_response.status_code == 201
    project_id = project_response.json()["id"]

    empty_list_response = client.get(f"/api/v1/projects/{project_id}/assets", headers=headers)
    assert empty_list_response.status_code == 200
    assert empty_list_response.json()["items"] == []

    create_response = client.post(
        f"/api/v1/projects/{project_id}/assets",
        json={
            "name": "雨夜街道",
            "type": "场景",
            "description": "霓虹雨夜街道",
            "default_prompt": "雨夜街道，湿润地面反光",
            "tags": ["场景", "雨夜"],
            "sort_order": 2,
        },
        headers=headers,
    )
    assert create_response.status_code == 201
    asset = create_response.json()
    asset_id = asset["id"]
    assert asset["name"] == "雨夜街道"
    assert asset["tags"] == ["场景", "雨夜"]

    update_response = client.patch(
        f"/api/v1/assets/{asset_id}",
        json={
            "name": "雨夜巷口",
            "description": "窄巷、积水、霓虹反射",
            "default_prompt": "雨夜巷口，积水反光，电影感",
            "tags": ["场景", "巷口"],
            "sort_order": 1,
        },
        headers=headers,
    )
    assert update_response.status_code == 200
    updated_asset = update_response.json()
    assert updated_asset["name"] == "雨夜巷口"
    assert updated_asset["default_prompt"] == "雨夜巷口，积水反光，电影感"
    assert updated_asset["tags"] == ["场景", "巷口"]
    assert updated_asset["sort_order"] == 1

    list_response = client.get(f"/api/v1/projects/{project_id}/assets", headers=headers)
    assert list_response.status_code == 200
    assert list_response.json()["items"][0]["id"] == asset_id

    delete_response = client.delete(f"/api/v1/assets/{asset_id}", headers=headers)
    assert delete_response.status_code == 204

    deleted_list_response = client.get(f"/api/v1/projects/{project_id}/assets", headers=headers)
    assert deleted_list_response.status_code == 200
    assert deleted_list_response.json()["items"] == []

    missing_update_response = client.patch(
        "/api/v1/assets/missing-asset",
        json={"name": "不存在"},
        headers=headers,
    )
    assert missing_update_response.status_code == 404
