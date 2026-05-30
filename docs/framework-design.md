# 系统框架设计

本文档描述 FrameLab 从纯 HTML 原型演进到可开发应用时的整体框架。后端使用 FastAPI 提供接口服务，前端使用 Electron + React 构建桌面工作台。

## 设计目标

- 前端保持桌面应用体验，负责项目编排、时间轴编辑、资产管理和生成结果预览。
- 后端提供稳定的业务 API，负责数据持久化、文件上传、模型调用、任务状态流转和后续导出。
- 图片和视频模型由后端按配置选择，前端不提供模型切换入口。
- Electron 主进程只处理桌面能力，比如窗口、文件选择、本地缓存目录和安全桥接。
- React 渲染进程不直接访问数据库、不直接持有模型密钥，统一通过 FastAPI 接口访问业务能力。
- AI 生成任务全部异步化，避免图片或视频生成阻塞界面。

## 总体架构

```mermaid
flowchart LR
  User[创作者] --> Desktop[Electron Desktop App]
  Desktop --> Main[Electron Main Process]
  Desktop --> Renderer[React Renderer]
  Renderer --> API[FastAPI Backend]
  Main --> LocalFS[本地文件系统]
  API --> DB[(MySQL)]
  API --> Storage[对象存储 TOS/S3]
  API --> Queue[任务队列 Redis]
  Worker[Generation Worker] --> Queue
  Worker --> AI[AI 模型服务]
  Worker --> Storage
  Worker --> DB
```

## 后端架构

FastAPI 后端按“接口层 -> 服务层 -> 仓储层 -> 基础设施层”拆分。

```text
backend/
  app/
    main.py
    core/
      config.py
      logging.py
      security.py
      exceptions.py
    api/
      v1/
        router.py
        projects.py
        scripts.py
        assets.py
        frames.py
        media.py
        generation_tasks.py
        video_segments.py
    schemas/
      project.py
      asset.py
      frame.py
      media.py
      generation_task.py
    models/
      project.py
      asset.py
      frame.py
      media.py
      generation_task.py
    services/
      project_service.py
      asset_service.py
      frame_service.py
      media_service.py
      generation_service.py
      prompt_service.py
    repositories/
      project_repo.py
      asset_repo.py
      frame_repo.py
      media_repo.py
      generation_task_repo.py
    integrations/
      object_storage.py
      openai_image.py
      seedance_video.py
    workers/
      generation_worker.py
    db/
      session.py
      migrations/
    tests/
```

### 接口层

接口层只做请求校验、权限校验、调用服务和返回响应，不写复杂业务逻辑。

核心 API 模块：

| 模块 | 职责 |
| --- | --- |
| `projects.py` | 项目列表、项目创建、项目设置、项目删除 |
| `scripts.py` | 剧本文本读取与保存 |
| `assets.py` | 资产库 CRUD、资产图片替换、资产排序 |
| `frames.py` | 关键帧 CRUD、时间轴排序、版本切换、引用关系 |
| `media.py` | 本地文件上传、远程文件登记、文件元信息读取 |
| `generation_tasks.py` | 创建生成任务、查询任务状态、取消任务、重试任务 |
| `video_segments.py` | 后续帧转视频片段管理 |

### 服务层

服务层承载业务规则。

- `ProjectService`：创建项目时初始化默认剧本和首个关键帧。
- `AssetService`：维护资产类型、标签、图片文件关联和排序。
- `FrameService`：维护关键帧顺序、帧详情、版本选择和引用资产。
- `MediaService`：处理上传、对象存储、图片尺寸解析和文件记录。
- `GenerationService`：创建任务、组装模型请求、调度 Worker、处理成功或失败结果。
- `PromptService`：根据剧本、资产、帧详情和 `@` 引用组装生成提示词。

### 模型选择边界

模型切换属于后端能力，不进入 React 创作界面。

- 前端创建生成任务时只传 `task_type`、目标对象、提示词、引用素材和画幅等创作参数。
- 前端不传 `provider`、`model_name`，也不渲染图片模型或视频模型选择控件。
- 后端通过配置或管理接口维护默认模型，例如图片生成、图片编辑、帧图转视频分别对应不同默认模型。
- `GenerationService` 根据 `task_type` 和请求上下文解析实际模型，再写入 `generation_tasks.provider`、`generation_tasks.model_name`，用于审计、重试和排查。
- Worker 只信任任务表中的后端解析结果，不从前端 payload 读取模型名。

### 仓储层

仓储层负责数据库读写，接口保持稳定，方便将来替换 ORM 或优化查询。

推荐组合：

- ORM：SQLAlchemy 2.x
- 数据迁移：Alembic
- 数据校验：Pydantic v2
- 数据库：MySQL 8.x
- 异步驱动：`asyncmy`

### 任务系统

图片生成、图片编辑、视频生成都进入 `generation_tasks` 表，并由队列异步执行。

MVP 可先用：

- Redis + RQ / ARQ：简单、够用、容易排查。
- 后续需要复杂工作流时再升级 Celery 或 Temporal。

任务状态流转：

```mermaid
stateDiagram-v2
  [*] --> queued
  queued --> running
  running --> succeeded
  running --> failed
  queued --> cancelled
  failed --> queued: retry
  succeeded --> [*]
  cancelled --> [*]
```

Worker 成功后需要写入：

- `media_files`：生成图片或视频文件。
- `frame_versions`：如果目标是关键帧图片。
- `video_segments`：如果目标是视频片段。
- `generation_tasks.response_payload`：保存模型返回的关键参数。

### 后端接口示例

```text
GET    /api/v1/projects
POST   /api/v1/projects
GET    /api/v1/projects/{project_id}
PATCH  /api/v1/projects/{project_id}
DELETE /api/v1/projects/{project_id}

GET    /api/v1/projects/{project_id}/script
PUT    /api/v1/projects/{project_id}/script

GET    /api/v1/projects/{project_id}/assets
POST   /api/v1/projects/{project_id}/assets
PATCH  /api/v1/assets/{asset_id}
DELETE /api/v1/assets/{asset_id}

GET    /api/v1/projects/{project_id}/frames
POST   /api/v1/projects/{project_id}/frames
PATCH  /api/v1/frames/{frame_id}
DELETE /api/v1/frames/{frame_id}
POST   /api/v1/frames/{frame_id}/versions/select

POST   /api/v1/media/upload

POST   /api/v1/generation-tasks
GET    /api/v1/generation-tasks/{task_id}
POST   /api/v1/generation-tasks/{task_id}/retry
POST   /api/v1/generation-tasks/{task_id}/cancel
```

## 前端架构

Electron + React 前端分为主进程、预加载脚本和渲染进程。

```text
desktop/
  electron/
    main.ts
    preload.ts
    ipc/
      file-dialog.ts
      app-config.ts
  src/
    app/
      App.tsx
      router.tsx
      providers.tsx
    pages/
      ProjectListPage.tsx
      WorkbenchPage.tsx
    features/
      project/
      script/
      assets/
      timeline/
      frame-detail/
      prompt-dock/
      generation/
    components/
      layout/
      ui/
    api/
      client.ts
      projects.ts
      assets.ts
      frames.ts
      media.ts
      generationTasks.ts
    store/
      project-store.ts
      workbench-store.ts
    types/
      project.ts
      asset.ts
      frame.ts
      media.ts
    styles/
```

### Electron 主进程

主进程负责桌面环境能力，不写业务逻辑。

- 创建主窗口。
- 管理应用菜单、窗口尺寸和退出行为。
- 选择本地图片或导出目录。
- 提供安全 IPC，不暴露 Node.js 全局对象给 React。
- 启动或检测本地 FastAPI 服务。

### Preload 安全桥

`preload.ts` 只暴露少量受控 API：

```ts
window.desktop = {
  selectImageFile: () => Promise<FileSelection>,
  selectExportDirectory: () => Promise<string | null>,
  getAppVersion: () => Promise<string>,
  openExternal: (url: string) => Promise<void>
}
```

React 渲染进程通过 HTTP 访问后端，通过 `window.desktop` 访问桌面能力。

### React 渲染进程

推荐技术栈：

- 构建：Vite
- UI：React + TypeScript
- 数据请求：TanStack Query
- 局部状态：Zustand
- 表单：React Hook Form
- 样式：Tailwind CSS 或 CSS Modules
- 图标：lucide-react

页面结构：

```text
WorkbenchPage
  TopBar
  ProjectSidebar
  ScriptPanel
  AssetLibraryPanel
  TimelinePanel
  FrameDetailPanel
  PromptDock
```

状态划分：

- 服务端状态：项目、资产、关键帧、生成任务，交给 TanStack Query 缓存和刷新。
- 界面状态：当前选中项目、选中帧、面板展开、拖拽中状态，交给 Zustand。
- 表单草稿：帧详情编辑、资产编辑、项目设置，保存在组件或表单库里。

## 前后端通信

React 统一通过 `api/client.ts` 调用 FastAPI。

```mermaid
sequenceDiagram
  participant UI as React UI
  participant API as FastAPI
  participant DB as MySQL
  participant Q as Redis Queue
  participant W as Worker

  UI->>API: POST /generation-tasks
  API->>DB: create generation_tasks(status=queued)
  API->>Q: enqueue task_id
  API-->>UI: task_id
  UI->>API: GET /generation-tasks/{task_id}
  W->>Q: consume task
  W->>DB: status=running
  W->>DB: save media/version, status=succeeded
  UI->>API: refetch task/frame versions
```

任务状态可以先用轮询：

- 图片任务：每 1 到 2 秒刷新。
- 视频任务：每 3 到 5 秒刷新。

后续如果任务量变大，再增加 WebSocket 或 Server-Sent Events。

## 配置设计

后端 `.env`：

```text
APP_ENV=development
PUBLIC_API_BASE_URL=https://api.51sut.com
SITE_PUBLIC_BASE_URL=https://www.51sut.com
DATABASE_URL=mysql+asyncmy://user:pass@127.0.0.1:3306/keyframe_workbench?charset=utf8mb4
REDIS_URL=redis://localhost:6379/0
STORAGE_PROVIDER=tos
STORAGE_BUCKET=sut-media-51sut-com
STORAGE_REGION=cn-guangzhou
STORAGE_ENDPOINT=tos-cn-guangzhou.volces.com
STORAGE_PUBLIC_BASE_URL=https://cdn.51sut.com
STORAGE_CDN_CNAME=cdn.51sut.com.volcgslb.com
STORAGE_IMAGE_PREFIX=generated/images
STORAGE_VIDEO_PREFIX=generated/videos
SITE_STORAGE_BUCKET=sut-www-51sut-com
SITE_STORAGE_PUBLIC_BASE_URL=https://www.51sut.com
SITE_STORAGE_CDN_CNAME=www.51sut.com.volcgslb.com
OPENAI_API_KEY=
SEEDANCE_API_KEY=
IMAGE_GENERATION_PROVIDER=openai
IMAGE_GENERATION_MODEL=gpt-image-2
IMAGE_EDIT_PROVIDER=openai
IMAGE_EDIT_MODEL=gpt-image-2
VIDEO_GENERATION_PROVIDER=seedance
VIDEO_GENERATION_MODEL=seedance-2
```

前端 `.env`：

```text
VITE_API_BASE_URL=https://api.51sut.com/api/v1
VITE_SITE_PUBLIC_BASE_URL=https://www.51sut.com
VITE_CDN_BASE_URL=https://cdn.51sut.com
```

前端环境变量只保存 API 地址等界面运行配置，不保存模型供应商、模型名或模型密钥。

Electron 打包后可以选择两种模式：

- 本地服务模式：Electron 启动内置 FastAPI 服务，适合单机桌面工具。
- 远程服务模式：Electron 连接线上 FastAPI，适合多人协作和统一计费。

MVP 建议先做本地服务模式，后续需要账号、同步和团队协作时再切远程服务模式。

## 安全边界

- 模型 API Key 只放在后端，不进入 React。
- 模型供应商和模型名只由后端配置或管理接口控制，不进入普通前端生成表单。
- Electron 渲染进程关闭 Node.js 集成，启用 `contextIsolation`。
- 上传文件限制 MIME、大小和扩展名。
- 对象存储使用后端签名上传或后端转存。
- 所有写接口保留操作日志字段或 `updated_at`，方便排查覆盖问题。

## 开发启动方式

开发阶段建议三个进程：

```bash
# 后端接口
cd backend
uvicorn app.main:app --reload --host 127.0.0.1 --port 8000

# 任务 Worker
cd backend
python -m app.workers.generation_worker

# Electron + React
cd desktop
npm run dev
```

## MVP 开发顺序

1. 搭建 FastAPI 项目、数据库连接和迁移系统。
2. 实现项目、剧本、资产、关键帧、帧版本接口。
3. 搭建 Electron + React 工程，复刻当前 HTML 原型布局。
4. 接入 TanStack Query，完成项目数据真实读写。
5. 实现媒体上传和资产图片替换。
6. 实现图片生成任务队列和帧版本写入。
7. 实现任务状态轮询、失败重试和版本切换。
8. 预留视频片段接口，再接入后端默认视频模型。

## 与表结构的关系

本框架设计与 [表结构设计](schema-design.md) 对应：

- 后端 `models/` 对应数据库表。
- 后端 `schemas/` 对应接口请求和响应。
- 后端 `services/` 对应项目、资产、关键帧、生成任务等业务流程。
- 前端 `features/` 对应工作台里的功能区域。
- `generation_tasks` 是前端点击生成后与 Worker 之间的核心协议。
