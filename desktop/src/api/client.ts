const configuredApiBaseUrl = import.meta.env.VITE_API_BASE_URL;
const localApiBaseUrls = [
  "/api/v1",
  "http://127.0.0.1:18081/api/v1",
  "http://127.0.0.1:18082/api/v1",
  "http://127.0.0.1:18080/api/v1",
  "http://127.0.0.1:8000/api/v1",
];
const API_BASE_URLS = import.meta.env.DEV
  ? configuredApiBaseUrl && isLocalApiBaseUrl(configuredApiBaseUrl)
    ? [configuredApiBaseUrl, ...localApiBaseUrls.filter((baseUrl) => baseUrl !== configuredApiBaseUrl)]
    : [...localApiBaseUrls, ...(configuredApiBaseUrl ? [configuredApiBaseUrl] : [])]
  : configuredApiBaseUrl
    ? [configuredApiBaseUrl]
    : localApiBaseUrls;

let activeApiBaseUrl: string | null = null;
const AUTH_STORAGE_KEY = "framelab.auth";

type AuthTokens = {
  accessToken: string;
  refreshToken: string;
};

let authTokens = readStoredAuthTokens();

export type Project = {
  id: string;
  name: string;
  description: string;
  aspect_ratio: string;
  status: string;
  style_prompt: string;
  style_reference_image_file_id: string | null;
  style_reference_image_url?: string | null;
  auto_apply_style_prompt: boolean;
  auto_apply_style_reference: boolean;
  created_at: string;
  updated_at: string;
};

export type ProjectScript = {
  project_id: string;
  content: string;
  updated_at: string;
};

export type Asset = {
  id: string;
  project_id: string;
  type: string;
  name: string;
  description: string;
  default_prompt: string;
  tags: string[];
  image_file_id: string | null;
  image_url?: string | null;
  sort_order: number;
  created_at: string;
  updated_at: string;
};

export type PublicAsset = Omit<Asset, "project_id"> & {
  status: string;
};

export type PublicAssetImage = {
  id: string;
  public_asset_id: string;
  media_file_id: string;
  image_url?: string | null;
  role: string;
  title: string;
  description: string;
  prompt: string;
  scene_prompt: string;
  angle: string;
  tags: string[];
  is_primary: boolean;
  sort_order: number;
  source_type?: string;
  generation_task_id?: string | null;
  generation_prompt?: string;
  created_by_user_id?: string | null;
  created_by_name?: string | null;
  created_at: string;
  updated_at: string;
};

export type PublicAssetImagePayload = {
  media_file_id: string;
  role?: string;
  title?: string;
  description?: string;
  prompt?: string;
  scene_prompt?: string;
  angle?: string;
  tags?: string[];
  is_primary?: boolean;
  sort_order?: number;
};

export type AssetPayload = {
  name: string;
  type: string;
  description?: string;
  default_prompt?: string;
  tags?: string[];
  image_file_id?: string | null;
  sort_order?: number;
};

export type MediaFileType = "image" | "video";

export type MediaUploadUrlPayload = {
  filename: string;
  file_type: MediaFileType;
  mime_type: string;
  size_bytes?: number;
  project_id?: string | null;
  metadata?: Record<string, unknown>;
};

export type MediaUploadUrl = {
  media_file_id: string;
  file_type: MediaFileType;
  bucket: string;
  object_key: string;
  upload_url: string;
  upload_method: "PUT";
  upload_headers: Record<string, string>;
  public_url: string;
  expires_in: number;
};

export type MediaFile = {
  id: string;
  project_id: string | null;
  file_type: string;
  bucket: string;
  object_key: string;
  url: string;
  mime_type: string;
  width: number | null;
  height: number | null;
  duration_ms: number | null;
  size_bytes: number | null;
  metadata: Record<string, unknown>;
  status: string;
  created_at: string;
  updated_at: string;
};

export type Frame = {
  id: string;
  project_id: string;
  order_index: number;
  summary: string;
  duration_ms: number;
  people: string;
  dialogue: string;
  action: string;
  emotion: string;
  note: string;
  current_prompt: string;
  selected_version_id: string | null;
  versions: FrameVersion[];
  created_at: string;
  updated_at: string;
};

export type FrameVersion = {
  id: string;
  frame_id: string;
  version_no: number;
  image_file_id: string | null;
  image_url?: string | null;
  generation_task_id: string | null;
  prompt: string;
  note: string;
  metadata: Record<string, unknown>;
  created_at: string;
};

export type FrameVersionPayload = {
  image_file_id?: string | null;
  generation_task_id?: string | null;
  prompt?: string;
  note?: string;
  metadata?: Record<string, unknown>;
  select?: boolean;
};

export type User = {
  id: string;
  email: string;
  username: string;
  display_name: string;
  avatar_url: string | null;
  status: string;
  created_at: string;
  updated_at: string;
  last_login_at: string | null;
};

export type AuthTokenResponse = {
  access_token: string;
  refresh_token: string;
  token_type: "bearer";
  user: User;
};

export type RegisterPayload = {
  email: string;
  username: string;
  password: string;
  display_name?: string;
};

export type LoginPayload = {
  login: string;
  password: string;
};

export type McpTokenCreateResponse = {
  id: string;
  name: string;
  token: string;
  created_at: string;
};

export async function apiGet<T>(path: string): Promise<T> {
  return requestJson<T>(path);
}

export async function apiPost<T>(path: string, body: unknown): Promise<T> {
  return requestJson<T>(path, {
    method: "POST",
    headers: {
      "Content-Type": "application/json",
    },
    body: JSON.stringify(body),
  });
}

export async function apiPatch<T>(path: string, body: unknown): Promise<T> {
  return requestJson<T>(path, {
    method: "PATCH",
    headers: {
      "Content-Type": "application/json",
    },
    body: JSON.stringify(body),
  });
}

export async function apiPut<T>(path: string, body: unknown): Promise<T> {
  return requestJson<T>(path, {
    method: "PUT",
    headers: {
      "Content-Type": "application/json",
    },
    body: JSON.stringify(body),
  });
}

export async function apiDelete(path: string): Promise<void> {
  await requestVoid(path, {
    method: "DELETE",
  });
}

export function healthCheck() {
  return apiGet<{ status: string; app: string; env: string }>("/health");
}

export function hasStoredAuthSession() {
  return Boolean(authTokens?.accessToken && authTokens.refreshToken);
}

export function loginUser(payload: LoginPayload) {
  return authenticate("/auth/login", payload);
}

export function registerUser(payload: RegisterPayload) {
  return authenticate("/auth/register", payload);
}

export function getCurrentUser() {
  return apiGet<User>("/auth/me");
}

export function createMcpToken(name = "codex-opencode") {
  return apiPost<McpTokenCreateResponse>("/auth/mcp-tokens", { name });
}

export async function logoutUser() {
  const refreshToken = authTokens?.refreshToken;
  clearAuthSession();
  if (!refreshToken) {
    return;
  }

  try {
    await apiPost<{ status: string }>("/auth/logout", { refresh_token: refreshToken });
  } catch {
    // Logout should clear the local session even when the backend is unavailable.
  }
}

export function clearAuthSession() {
  setAuthTokens(null);
}

export function listProjects() {
  return apiGet<{ items: Project[] }>("/projects");
}

export function createProject(payload: Pick<Project, "name" | "description" | "aspect_ratio">) {
  return apiPost<Project>("/projects", payload);
}

export function updateProject(
  projectId: string,
  payload: Partial<
    Pick<
      Project,
      | "name"
      | "description"
      | "aspect_ratio"
      | "status"
      | "style_prompt"
      | "style_reference_image_file_id"
      | "auto_apply_style_prompt"
      | "auto_apply_style_reference"
    >
  >,
) {
  return apiPatch<Project>(`/projects/${projectId}`, payload);
}

export function deleteProject(projectId: string) {
  return apiDelete(`/projects/${projectId}`);
}

export async function loadOrCreateWorkbenchProject() {
  const projects = await listProjects();

  if (projects.items.length > 0) {
    return projects.items[0];
  }

  return createProject({
    name: "MVP 闭环测试项目",
    description: "由前端自动创建，用于验证 Electron + React + FastAPI 链路。",
    aspect_ratio: "16:9",
  });
}

export function loadProjectScript(projectId: string) {
  return apiGet<ProjectScript>(`/projects/${projectId}/script`);
}

export function updateProjectScript(projectId: string, content: string) {
  return apiPut<ProjectScript>(`/projects/${projectId}/script`, { content });
}

export function deleteProjectScript(projectId: string) {
  return apiDelete(`/projects/${projectId}/script`);
}

export function loadProjectFrames(projectId: string) {
  return apiGet<{ project_id: string; items: Frame[] }>(`/projects/${projectId}/frames`);
}

export function updateFrame(frameId: string, payload: Partial<Pick<Frame, "summary" | "duration_ms" | "people" | "dialogue" | "action" | "emotion" | "note" | "current_prompt" | "selected_version_id">>) {
  return apiPatch<Frame>(`/frames/${frameId}`, payload);
}

export function createFrameVersion(frameId: string, payload: FrameVersionPayload) {
  return apiPost<FrameVersion>(`/frames/${frameId}/versions`, payload);
}

export function selectFrameVersion(frameId: string, versionId: string) {
  return apiPost<Frame>(`/frames/${frameId}/versions/select`, { version_id: versionId });
}

export function loadProjectAssets(projectId: string) {
  return apiGet<{ project_id: string; items: Asset[] }>(`/projects/${projectId}/assets`);
}

export function loadPublicAssets(params: { type?: string; keyword?: string } = {}) {
  const searchParams = new URLSearchParams();
  if (params.type && params.type !== "全部") {
    searchParams.set("type", params.type);
  }
  if (params.keyword?.trim()) {
    searchParams.set("keyword", params.keyword.trim());
  }
  const query = searchParams.toString();
  return apiGet<{ items: PublicAsset[] }>(`/public-assets${query ? `?${query}` : ""}`);
}

export function loadPublicAsset(publicAssetId: string) {
  return apiGet<PublicAsset>(`/public-assets/${publicAssetId}`);
}

export function loadPublicAssetImages(publicAssetId: string) {
  return apiGet<{ public_asset_id: string; items: PublicAssetImage[] }>(`/public-assets/${publicAssetId}/images`);
}

export function createPublicAssetImage(publicAssetId: string, payload: PublicAssetImagePayload) {
  return apiPost<PublicAssetImage>(`/public-assets/${publicAssetId}/images`, payload);
}

export function deletePublicAssetImage(imageId: string) {
  return apiDelete(`/public-assets/images/${imageId}`);
}

export function importPublicAssetsToProject(
  projectId: string,
  payload: { public_asset_ids: string[]; copy_media?: boolean },
) {
  return apiPost<{ project_id: string; items: Asset[]; errors: Array<{ public_asset_id: string; detail: string }> }>(
    `/projects/${projectId}/assets/import-public`,
    payload,
  );
}

export function createProjectAsset(projectId: string, payload: AssetPayload) {
  return apiPost<Asset>(`/projects/${projectId}/assets`, payload);
}

export function updateAsset(assetId: string, payload: Partial<AssetPayload>) {
  return apiPatch<Asset>(`/assets/${assetId}`, payload);
}

export function deleteAsset(assetId: string) {
  return apiDelete(`/assets/${assetId}`);
}

export function createMediaUploadUrl(payload: MediaUploadUrlPayload) {
  return apiPost<MediaUploadUrl>("/media/upload-url", payload);
}

export function completeMediaUpload(
  mediaFileId: string,
  payload: Partial<Pick<MediaFile, "width" | "height" | "duration_ms" | "size_bytes" | "metadata">> = {},
) {
  return apiPost<MediaFile>(`/media/${mediaFileId}/complete`, payload);
}

export function loadMediaFile(mediaFileId: string) {
  return apiGet<MediaFile>(`/media/${mediaFileId}`);
}

export async function uploadMediaFile(file: File, fileType: MediaFileType, projectId?: string | null) {
  const upload = await createMediaUploadUrl({
    filename: file.name,
    file_type: fileType,
    mime_type: file.type,
    size_bytes: file.size,
    project_id: projectId ?? null,
  });

  const response = await fetch(upload.upload_url, {
    method: upload.upload_method,
    headers: upload.upload_headers,
    body: file,
  });

  if (!response.ok) {
    throw new Error(`Upload failed: ${response.status} ${response.statusText}`);
  }

  return completeMediaUpload(upload.media_file_id, { size_bytes: file.size });
}

export type GenerationTaskPayload = {
  task_type?: "text_to_image" | "image_to_image" | "image_edit" | "text_to_video" | "frames_to_video";
  prompt: string;
  aspect_ratio: string;
  image?: string | string[];
  size?: string;
  project_id?: string;
  frame_id?: string;
  asset_ids?: string[];
  auto_apply_asset_references?: boolean;
  image_type?: "style" | "character" | "scene" | "prop" | "keyframe";
  target?: {
    type: "public_asset_gallery" | "project_asset" | "keyframe" | "video";
    id?: string;
    public_asset_id?: string;
    title?: string;
    role?: string;
    angle?: string;
    description?: string;
    tags?: string[];
  };
  references?: Array<{ type: string; id?: string; url?: string; title?: string }>;
};

export type GenerationTaskResult = {
  task_id: string;
  status: "queued" | "running" | "succeeded" | "failed" | "canceled";
  task_type: "text_to_image" | "image_to_image" | "image_edit" | "text_to_video" | "frames_to_video";
  provider: string;
  model_name: string;
  prompt: string;
  aspect_ratio: string;
  size: string;
  target_type?: string | null;
  target_id?: string | null;
  target_payload?: Record<string, unknown>;
  reference_payload?: Array<Record<string, unknown>>;
  images: Array<{ url?: string; b64_json?: string; size?: string; media_file_id?: string; object_key?: string }>;
  error_message?: string | null;
};

export function createGenerationTask(payload: GenerationTaskPayload) {
  return apiPost<GenerationTaskResult>("/generation-tasks", payload);
}

export function loadGenerationTask(taskId: string) {
  return apiGet<GenerationTaskResult>(`/generation-tasks/${taskId}`);
}

export function loadGenerationTasks(
  params: {
    status?: GenerationTaskResult["status"];
    task_type?: GenerationTaskResult["task_type"];
    project_id?: string;
    target_type?: string;
    target_id?: string;
    limit?: number;
  } = {},
) {
  const searchParams = new URLSearchParams();
  if (params.status) {
    searchParams.set("status", params.status);
  }
  if (params.task_type) {
    searchParams.set("task_type", params.task_type);
  }
  if (params.project_id) {
    searchParams.set("project_id", params.project_id);
  }
  if (params.target_type) {
    searchParams.set("target_type", params.target_type);
  }
  if (params.target_id) {
    searchParams.set("target_id", params.target_id);
  }
  if (params.limit) {
    searchParams.set("limit", String(params.limit));
  }
  const query = searchParams.toString();
  return apiGet<{ items: GenerationTaskResult[] }>(`/generation-tasks${query ? `?${query}` : ""}`);
}

async function readApiError(response: Response): Promise<string> {
  const fallback = `API request failed: ${response.status} ${response.statusText}`;
  try {
    const body = (await response.json()) as { detail?: unknown };
    if (typeof body.detail === "string") {
      return body.detail;
    }
    if (body.detail) {
      return JSON.stringify(body.detail);
    }
  } catch {
    return fallback;
  }
  return fallback;
}

async function requestJson<T>(
  path: string,
  init?: RequestInit,
  options?: { skipAuth?: boolean; skipRefresh?: boolean },
): Promise<T> {
  const response = await request(path, init, options);
  return response.json() as Promise<T>;
}

async function requestVoid(path: string, init?: RequestInit): Promise<void> {
  await request(path, init);
}

async function request(path: string, init?: RequestInit, options: { skipAuth?: boolean; skipRefresh?: boolean } = {}): Promise<Response> {
  const candidates = activeApiBaseUrl
    ? [activeApiBaseUrl, ...API_BASE_URLS.filter((baseUrl) => baseUrl !== activeApiBaseUrl)]
    : API_BASE_URLS;
  let lastError: unknown = null;

  for (const baseUrl of candidates) {
    try {
      let response = await fetch(`${baseUrl}${path}`, withAuthHeaders(init, options.skipAuth));
      if (response.status === 401 && !options.skipRefresh && authTokens?.refreshToken) {
        const refreshed = await refreshAuthSession(baseUrl);
        if (refreshed) {
          response = await fetch(`${baseUrl}${path}`, withAuthHeaders(init, options.skipAuth));
        } else {
          notifyAuthExpired();
        }
      }
      if (response.ok) {
        activeApiBaseUrl = baseUrl;
        return response;
      }

      lastError = new Error(await readApiError(response));
      if (!shouldTryNextBackend(response)) {
        throw lastError;
      }
    } catch (error) {
      lastError = error;
      if (
        baseUrl === configuredApiBaseUrl
        || error instanceof Error && !isRetryableApiError(error)
      ) {
        throw error;
      }
    }
  }

  throw normalizeApiError(lastError);
}

async function authenticate(path: "/auth/login" | "/auth/register", payload: LoginPayload | RegisterPayload) {
  const response = await requestJson<AuthTokenResponse>(
    path,
    {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
      },
      body: JSON.stringify(payload),
    },
    { skipAuth: true, skipRefresh: true },
  );
  persistAuthResponse(response);
  return response;
}

async function refreshAuthSession(preferredBaseUrl?: string) {
  const refreshToken = authTokens?.refreshToken;
  if (!refreshToken) {
    return false;
  }

  const candidates = preferredBaseUrl
    ? [preferredBaseUrl, ...API_BASE_URLS.filter((baseUrl) => baseUrl !== preferredBaseUrl)]
    : API_BASE_URLS;

  for (const baseUrl of candidates) {
    try {
      const response = await fetch(`${baseUrl}/auth/refresh`, {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
        },
        body: JSON.stringify({ refresh_token: refreshToken }),
      });
      if (!response.ok) {
        continue;
      }

      const body = (await response.json()) as AuthTokenResponse;
      persistAuthResponse(body);
      activeApiBaseUrl = baseUrl;
      return true;
    } catch {
      continue;
    }
  }

  setAuthTokens(null);
  return false;
}

function persistAuthResponse(response: AuthTokenResponse) {
  setAuthTokens({
    accessToken: response.access_token,
    refreshToken: response.refresh_token,
  });
}

function withAuthHeaders(init: RequestInit | undefined, skipAuth = false): RequestInit | undefined {
  if (skipAuth || !authTokens?.accessToken) {
    return init;
  }

  const headers = new Headers(init?.headers);
  headers.set("Authorization", `Bearer ${authTokens.accessToken}`);
  return {
    ...init,
    headers,
  };
}

function setAuthTokens(tokens: AuthTokens | null) {
  authTokens = tokens;
  if (typeof window === "undefined") {
    return;
  }

  if (!tokens) {
    window.localStorage.removeItem(AUTH_STORAGE_KEY);
    return;
  }

  window.localStorage.setItem(AUTH_STORAGE_KEY, JSON.stringify(tokens));
}

function readStoredAuthTokens(): AuthTokens | null {
  if (typeof window === "undefined") {
    return null;
  }

  try {
    const value = window.localStorage.getItem(AUTH_STORAGE_KEY);
    if (!value) {
      return null;
    }
    const parsed = JSON.parse(value) as Partial<AuthTokens>;
    if (typeof parsed.accessToken === "string" && typeof parsed.refreshToken === "string") {
      return {
        accessToken: parsed.accessToken,
        refreshToken: parsed.refreshToken,
      };
    }
  } catch {
    window.localStorage.removeItem(AUTH_STORAGE_KEY);
  }

  return null;
}

function notifyAuthExpired() {
  setAuthTokens(null);
  if (typeof window !== "undefined") {
    window.dispatchEvent(new CustomEvent("framelab:auth-expired"));
  }
}

function shouldTryNextBackend(response: Response) {
  return [404, 500, 502, 503, 504].includes(response.status);
}

function isRetryableApiError(error: Error) {
  return error.name === "TypeError" || error.message.includes("Failed to fetch") || error.message.includes("NetworkError");
}

function isLocalApiBaseUrl(baseUrl: string) {
  return baseUrl.startsWith("/")
    || baseUrl.startsWith("http://127.0.0.1:")
    || baseUrl.startsWith("http://localhost:");
}

function normalizeApiError(error: unknown) {
  if (error instanceof Error) {
    if (isRetryableApiError(error)) {
      return new Error("无法连接后端服务，请确认 FastAPI 已启动，或配置 VITE_API_BASE_URL。");
    }
    return error;
  }
  return new Error("API 请求失败");
}
