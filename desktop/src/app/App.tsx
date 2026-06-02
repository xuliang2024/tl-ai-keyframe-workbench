import {
  Activity,
  ArrowRight,
  ArrowUp,
  Bot,
  Clapperboard,
  ChevronLeft,
  ChevronRight,
  Clock,
  ExternalLink,
  FolderKanban,
  Image,
  KeyRound,
  LogOut,
  Palette,
  Plus,
  Save,
  ScrollText,
  Sparkles,
  Trash2,
  Upload,
  UserCircle,
  UserPlus,
  Wifi,
  X,
} from "lucide-react";
import { type CSSProperties, type FormEvent, type KeyboardEvent, useEffect, useMemo, useRef, useState } from "react";

import {
  createProjectAsset,
  createMcpToken,
  createPublicAssetImage,
  createProject as apiCreateProject,
  deleteAsset,
  deletePublicAssetImage,
  deleteProject as apiDeleteProject,
  deleteProjectScript,
  createGenerationTask,
  createFrameVersion,
  clearAuthSession,
  getCurrentUser,
  healthCheck,
  hasStoredAuthSession,
  importPublicAssetsToProject,
  listProjects,
  loadPublicAsset,
  loadPublicAssets,
  loadPublicAssetImages,
  loadProjectAssets,
  loadGenerationTask,
  loadGenerationTasks,
  loadProjectFrames,
  loadProjectScript,
  loginUser,
  logoutUser,
  registerUser,
  uploadMediaFile,
  updateAsset,
  updateFrame,
  updateProjectScript,
  updateProject as apiUpdateProject,
  selectFrameVersion as apiSelectFrameVersion,
  type Asset as BackendAsset,
  type Frame,
  type GenerationTaskResult,
  type Project,
  type ProjectScript,
  type PublicAsset,
  type PublicAssetImage,
  type User,
} from "../api/client";
import frameLabLogoUrl from "../assets/brand/framelab-logo.png";
import clayStopmotionStyleUrl from "../assets/style-cases/clay-stopmotion.webp";
import cinematicNoirStyleUrl from "../assets/style-cases/cinematic-noir.webp";
import cyberpunkNeonStyleUrl from "../assets/style-cases/cyberpunk-neon.webp";
import documentaryNaturalStyleUrl from "../assets/style-cases/documentary-natural.webp";
import inkWuxiaStyleUrl from "../assets/style-cases/ink-wuxia.webp";
import nordicMinimalStyleUrl from "../assets/style-cases/nordic-minimal.webp";
import retroHkStyleUrl from "../assets/style-cases/retro-hk.webp";
import softAnimeStyleUrl from "../assets/style-cases/soft-anime.webp";
import surrealPopStyleUrl from "../assets/style-cases/surreal-pop.webp";
import watercolorFairyStyleUrl from "../assets/style-cases/watercolor-fairy.webp";
import { useWorkbenchStore } from "../store/workbench-store";

const ASPECT_RATIOS = ["16:9", "9:16", "1:1", "4:3", "3:4", "21:9"];
const ASSET_TYPES = ["全部", "角色", "场景", "道具", "其他"] as const;
const ASSET_IMAGE_RATIOS: Record<Exclude<AssetType, "全部">, string> = {
  角色: "9:16",
  场景: "16:9",
  道具: "1:1",
  其他: "1:1",
};
const PALETTES = [
  ["#bfdbfe", "#fde68a", "#fecaca"],
  ["#a7f3d0", "#bfdbfe", "#fbcfe8"],
  ["#c7d2fe", "#bbf7d0", "#fed7aa"],
  ["#fde68a", "#bae6fd", "#d8b4fe"],
  ["#fecaca", "#bbf7d0", "#bfdbfe"],
];

const COVER_THEMES = [
  {
    background:
      "radial-gradient(circle at 18% 24%, rgba(133, 176, 255, 0.95), transparent 26%), radial-gradient(circle at 80% 20%, rgba(32, 211, 182, 0.7), transparent 30%), linear-gradient(135deg, #12204a 0%, #0b1325 52%, #07111e 100%)",
    accent: "#69d7ff",
  },
  {
    background:
      "radial-gradient(circle at 22% 18%, rgba(255, 205, 92, 0.85), transparent 24%), radial-gradient(circle at 72% 28%, rgba(255, 101, 122, 0.62), transparent 32%), linear-gradient(135deg, #35202a 0%, #121827 54%, #09111d 100%)",
    accent: "#ffd166",
  },
  {
    background:
      "radial-gradient(circle at 18% 18%, rgba(54, 211, 153, 0.88), transparent 26%), radial-gradient(circle at 78% 32%, rgba(79, 140, 255, 0.72), transparent 34%), linear-gradient(135deg, #0b2c29 0%, #111827 56%, #070d18 100%)",
    accent: "#36d399",
  },
  {
    background:
      "radial-gradient(circle at 20% 26%, rgba(187, 134, 252, 0.86), transparent 26%), radial-gradient(circle at 82% 18%, rgba(32, 211, 182, 0.58), transparent 28%), linear-gradient(135deg, #241b4b 0%, #111827 58%, #080b14 100%)",
    accent: "#bb86fc",
  },
  {
    background:
      "radial-gradient(circle at 18% 20%, rgba(125, 249, 255, 0.82), transparent 24%), radial-gradient(circle at 76% 26%, rgba(246, 195, 91, 0.64), transparent 32%), linear-gradient(135deg, #10243c 0%, #0c1826 50%, #070b12 100%)",
    accent: "#7df9ff",
  },
  {
    background:
      "radial-gradient(circle at 20% 20%, rgba(255, 255, 255, 0.42), transparent 22%), radial-gradient(circle at 76% 28%, rgba(79, 140, 255, 0.86), transparent 32%), linear-gradient(135deg, #293047 0%, #141a28 54%, #080b12 100%)",
    accent: "#9fb8ff",
  },
];

function BrandMark() {
  return (
    <span className="brand-mark" aria-hidden="true">
      <img src={frameLabLogoUrl} alt="" />
    </span>
  );
}

type Page = "projects" | "public-assets" | "project-settings" | "script" | "style" | "assets" | "workbench";
type ProjectPage = Exclude<Page, "projects" | "public-assets">;
type AuthMode = "login" | "register";
type AuthDraft = {
  email: string;
  username: string;
  displayName: string;
  login: string;
  password: string;
};
type AppRoute = {
  page: Page;
  projectId: string | null;
  assetId: string | null;
  publicAssetId: string | null;
};
type AssetType = (typeof ASSET_TYPES)[number];
type AssetPanel = "role" | "scene" | "prop" | "shot" | "movement" | "projectFrames" | "other" | "mention" | null;

type FrameStory = {
  summary: string;
  duration: string;
  people: string;
  dialogue: string;
  action: string;
  emotion: string;
  note: string;
};

type FrameVersion = {
  id?: string;
  imageFileId?: string | null;
  generationTaskId?: string | null;
  prompt: string;
  note: string;
  colors: string[];
  image?: string;
};

type UiFrame = {
  id: string;
  prompt: string;
  story: FrameStory;
  versions: FrameVersion[];
  currentVersion: number;
};

type AssetItem = {
  id?: string;
  imageFileId?: string | null;
  sortOrder?: number;
  name: string;
  type: Exclude<AssetType, "全部">;
  desc: string;
  prompt: string;
  tags: string;
  colors: string[];
  image?: string;
};

type ProjectForm = {
  name: string;
  description: string;
  aspect_ratio: string;
  style_prompt: string;
  style_reference_image_file_id: string | null;
  style_reference_image_url?: string | null;
  auto_apply_style_prompt: boolean;
  auto_apply_style_reference: boolean;
};

type StyleReferenceImage = {
  id: string;
  fileId: string;
  url: string;
};

type StyleCase = {
  id: string;
  name: string;
  image: string;
  prompt: string;
};

function createEmptyProjectDraft(): ProjectForm {
  return {
    name: "",
    description: "",
    aspect_ratio: "16:9",
    style_prompt: "",
    style_reference_image_file_id: null,
    style_reference_image_url: null,
    auto_apply_style_prompt: false,
    auto_apply_style_reference: false,
  };
}

function toCssAspectRatio(value: string | undefined) {
  const [width, height] = (value || "16:9").split(":").map((item) => Number(item));
  if (!width || !height) {
    return "16 / 9";
  }
  return `${width} / ${height}`;
}

function assetImageRatio(asset: AssetItem) {
  return ASSET_IMAGE_RATIOS[asset.type] ?? "1:1";
}

function assetImageCssAspectRatio(asset: AssetItem) {
  return toCssAspectRatio(assetImageRatio(asset));
}

function assetImagePadding(asset: AssetItem) {
  const [width, height] = assetImageRatio(asset).split(":").map((value) => Number(value));
  if (!width || !height) {
    return "100%";
  }
  return `${(height / width) * 100}%`;
}

const DEMO_ASSETS: AssetItem[] = [
  {
    name: "女主 A",
    type: "角色",
    desc: "短发，米色风衣，雨夜故事主角",
    prompt: "短发女主，米色风衣，脸部保持一致",
    tags: "主角,锁脸,风衣",
    colors: ["#bfdbfe", "#fde68a", "#fecaca"],
  },
  {
    name: "神秘男人",
    type: "角色",
    desc: "黑色长大衣，撑黑伞，压迫感",
    prompt: "神秘男人，黑色长大衣，撑黑伞",
    tags: "配角,黑伞,悬疑",
    colors: ["#cbd5e1", "#93c5fd", "#d8b4fe"],
  },
  {
    name: "雨夜街道",
    type: "场景",
    desc: "霓虹灯、湿润地面、雨水反光",
    prompt: "雨夜街道，霓虹灯，湿润地面反光",
    tags: "主场景,夜景,雨",
    colors: ["#93c5fd", "#a7f3d0", "#fde68a"],
  },
  {
    name: "黑色轿车",
    type: "道具",
    desc: "车灯穿过雨幕，推动剧情",
    prompt: "黑色轿车旁，车灯穿过雨幕",
    tags: "车辆,车灯,剧情道具",
    colors: ["#94a3b8", "#fca5a5", "#bfdbfe"],
  },
  {
    name: "构图参考",
    type: "其他",
    desc: "人物居中，车灯作为背景压力",
    prompt: "参考构图图，人物居中，背景有纵深",
    tags: "构图,参考",
    colors: ["#bbf7d0", "#fde68a", "#bfdbfe"],
  },
];

const QUICK_CHIPS = {
  role: [
    ["女主", "短发女主，米色风衣，脸部保持一致"],
    ["男人", "神秘男人，黑色长大衣，撑黑伞"],
    ["无人物", "无人物，只保留环境"],
  ],
  scene: [
    ["雨夜街道", "雨夜街道，霓虹灯，湿润地面反光"],
    ["黑车旁", "黑色轿车旁，车灯穿过雨幕"],
    ["窗边", "室内窗边，冷色月光"],
  ],
  prop: [
    ["黑伞", "手持黑伞"],
    ["手机", "手机屏幕发出微光"],
    ["围巾", "红色围巾在风中飘动"],
  ],
  shot: [
    ["平视", "平视镜头"],
    ["低角度", "低角度镜头"],
    ["俯拍", "俯拍镜头"],
    ["远景", "远景，展示人物和环境关系"],
    ["大远景", "大远景，突出环境和空间感"],
    ["中景", "中景，人物动作清楚"],
    ["近景", "近景，突出表情"],
    ["特写", "特写，突出面部或道具细节"],
  ],
  movement: [
    ["推进", "镜头轻微推进"],
    ["拉远", "镜头轻微拉远"],
    ["横移", "横向构图，适合后续跟拍"],
    ["固定", "固定机位，画面稳定"],
  ],
  other: [
    ["构图图", "参考上传的构图图，保持画面布局"],
    ["光影", "参考光影样张，保持光线氛围"],
    ["色彩", "参考色彩样张，保持整体色调"],
  ],
};

const STYLE_CASES: StyleCase[] = [
  {
    id: "cinematic-noir",
    name: "雨夜黑色电影",
    image: cinematicNoirStyleUrl,
    prompt: "电影黑色风格，雨夜城市巷道，湿润地面反光，低调高反差布光，冷蓝阴影与暖色霓虹，高级胶片颗粒，真实电影质感。",
  },
  {
    id: "soft-anime",
    name: "柔和手绘动画",
    image: softAnimeStyleUrl,
    prompt: "柔和手绘动画电影风格，细腻背景绘制，暖色夕光，低饱和粉彩，轻微纸张纹理，温柔自然光，画面干净有呼吸感。",
  },
  {
    id: "ink-wuxia",
    name: "东方水墨武侠",
    image: inkWuxiaStyleUrl,
    prompt: "东方水墨武侠风格，山寺云雾，留白构图，墨色层次与朱砂点缀，笔触优雅，诗意空间感，古典电影镜头。",
  },
  {
    id: "cyberpunk-neon",
    name: "赛博霓虹雨街",
    image: cyberpunkNeonStyleUrl,
    prompt: "赛博朋克霓虹风格，未来雨夜街市，品红与青蓝灯牌，金属和玻璃反射，浓密空气透视，镜头光晕，强烈都市压迫感。",
  },
  {
    id: "nordic-minimal",
    name: "北欧极简冷调",
    image: nordicMinimalStyleUrl,
    prompt: "北欧极简影像风格，雪地与浅木色空间，自然柔光，灰蓝低饱和色调，大面积留白，安静、克制、现代设计感。",
  },
  {
    id: "retro-hk",
    name: "港片复古胶片",
    image: retroHkStyleUrl,
    prompt: "90年代香港电影胶片风格，钨丝灯暖光，青绿色阴影，狭窄室内与街巷，轻微颗粒和晕影，怀旧但真实的电影色彩。",
  },
  {
    id: "watercolor-fairy",
    name: "水彩童话梦境",
    image: watercolorFairyStyleUrl,
    prompt: "梦幻水彩童话风格，月光森林，透明水洗质感，柔和花朵微光，纸张肌理，低对比、轻盈、温柔的奇幻氛围。",
  },
  {
    id: "clay-stopmotion",
    name: "黏土定格动画",
    image: clayStopmotionStyleUrl,
    prompt: "黏土定格动画风格，手工微缩场景，圆润造型，可触摸的黏土材质，温暖棚拍灯光，轻微手作瑕疵，童趣但精致。",
  },
  {
    id: "documentary-natural",
    name: "自然纪实摄影",
    image: documentaryNaturalStyleUrl,
    prompt: "自然纪实摄影风格，真实环境光，手持抓拍感，色彩克制，柔和对比，人物与生活场景有温度，像纪录片剧照。",
  },
  {
    id: "surreal-pop",
    name: "超现实流行色",
    image: surrealPopStyleUrl,
    prompt: "超现实流行艺术风格，高饱和撞色，沙漠汽车旅馆与漂浮几何体，硬朗阳光阴影，广告大片般清晰、俏皮、奇异。",
  },
];

function useHashRoute(): AppRoute {
  const [route, setRoute] = useState<AppRoute>(() => parseHashRoute(window.location.hash));

  useEffect(() => {
    if (!window.location.hash) {
      window.location.replace("#/projects");
      return;
    }

    const onHashChange = () => setRoute(parseHashRoute(window.location.hash));
    window.addEventListener("hashchange", onHashChange);
    onHashChange();
    return () => window.removeEventListener("hashchange", onHashChange);
  }, []);

  return route;
}

export function App() {
  const selectedFrameId = useWorkbenchStore((state) => state.selectedFrameId);
  const setSelectedFrameId = useWorkbenchStore((state) => state.setSelectedFrameId);
  const fileInputRef = useRef<HTMLInputElement | null>(null);
  const assetReferenceFileInputRef = useRef<HTMLInputElement | null>(null);
  const publicAssetGalleryFileInputRef = useRef<HTMLInputElement | null>(null);
  const assetGridRef = useRef<HTMLDivElement | null>(null);
  const styleFileInputRef = useRef<HTMLInputElement | null>(null);
  const styleUploadSlotRef = useRef(0);
  const route = useHashRoute();
  const activePage = route.page;
  const [authUser, setAuthUser] = useState<User | null>(null);
  const [authMode, setAuthMode] = useState<AuthMode>("login");
  const [authChecking, setAuthChecking] = useState(true);
  const [authSubmitting, setAuthSubmitting] = useState(false);
  const [authError, setAuthError] = useState("");
  const [mcpToken, setMcpToken] = useState("");
  const [isCreatingMcpToken, setIsCreatingMcpToken] = useState(false);
  const [authDraft, setAuthDraft] = useState<AuthDraft>({
    email: "",
    username: "",
    displayName: "",
    login: "",
    password: "",
  });
  const [project, setProject] = useState<Project | null>(null);
  const [script, setScript] = useState<ProjectScript | null>(null);
  const [scriptText, setScriptText] = useState("");
  const [projects, setProjects] = useState<Project[]>([]);
  const [selectedProjectId, setSelectedProjectId] = useState<string | null>(null);
  const [projectDraft, setProjectDraft] = useState<ProjectForm>(() => createEmptyProjectDraft());
  const [frames, setFrames] = useState<UiFrame[]>(() => createInitialFrames());
  const [selectedIndex, setSelectedIndex] = useState(0);
  const [detailIndex, setDetailIndex] = useState<number | null>(null);
  const [selectedFrameRefs, setSelectedFrameRefs] = useState<number[]>([]);
  const [prompt, setPrompt] = useState("");
  const [selectedChips, setSelectedChips] = useState<Record<string, string[]>>({
    style: ["电影写实，浅景深，高级光影"],
  });
  const [assetPanel, setAssetPanel] = useState<AssetPanel>(null);
  const [assets, setAssets] = useState<AssetItem[]>([]);
  const [assetFilter, setAssetFilter] = useState<AssetType>("全部");
  const [selectedAsset, setSelectedAsset] = useState(0);
  const [isAssetEditing, setIsAssetEditing] = useState(false);
  const [assetDraft, setAssetDraft] = useState<AssetItem>(() => createEmptyAsset());
  const [assetColumnCount, setAssetColumnCount] = useState(1);
  const [assetImageRatioMap, setAssetImageRatioMap] = useState<Record<string, number>>({});
  const [isSavingAsset, setIsSavingAsset] = useState(false);
  const [isGeneratingAssetImage, setIsGeneratingAssetImage] = useState(false);
  const [assetGenerationStatus, setAssetGenerationStatus] = useState("");
  const [assetReferenceImages, setAssetReferenceImages] = useState<StyleReferenceImage[]>([]);
  const [isPublicAssetPickerOpen, setIsPublicAssetPickerOpen] = useState(false);
  const [publicAssets, setPublicAssets] = useState<AssetItem[]>([]);
  const [publicAssetFilter, setPublicAssetFilter] = useState<AssetType>("全部");
  const [publicAssetKeyword, setPublicAssetKeyword] = useState("");
  const [selectedPublicAssetIds, setSelectedPublicAssetIds] = useState<string[]>([]);
  const [isImportingPublicAssets, setIsImportingPublicAssets] = useState(false);
  const [isLoadingPublicAssets, setIsLoadingPublicAssets] = useState(false);
  const [publicAssetDetail, setPublicAssetDetail] = useState<AssetItem | null>(null);
  const [publicAssetDetailImages, setPublicAssetDetailImages] = useState<PublicAssetImage[]>([]);
  const [selectedPublicAssetImageIndex, setSelectedPublicAssetImageIndex] = useState(0);
  const [isLoadingPublicAssetImages, setIsLoadingPublicAssetImages] = useState(false);
  const [isUploadingPublicAssetImages, setIsUploadingPublicAssetImages] = useState(false);
  const [isDeletingPublicAssetImage, setIsDeletingPublicAssetImage] = useState(false);
  const [publicAssetGenerationPrompt, setPublicAssetGenerationPrompt] = useState("");
  const [publicAssetGenerationTasks, setPublicAssetGenerationTasks] = useState<GenerationTaskResult[]>([]);
  const [isSubmittingPublicAssetGeneration, setIsSubmittingPublicAssetGeneration] = useState(false);
  const [isLoadingPublicAssetGenerationTasks, setIsLoadingPublicAssetGenerationTasks] = useState(false);
  const [styleReferenceImages, setStyleReferenceImages] = useState<StyleReferenceImage[]>([]);
  const [isGeneratingStyleImage, setIsGeneratingStyleImage] = useState(false);
  const [styleGenerationStatus, setStyleGenerationStatus] = useState("");
  const [styleReferencePrompt, setStyleReferencePrompt] = useState("");
  const [statusText, setStatusText] = useState("正在连接后端...");
  const [isCreatingProject, setIsCreatingProject] = useState(false);
  const [isCreateProjectDialogOpen, setIsCreateProjectDialogOpen] = useState(false);
  const [newProjectName, setNewProjectName] = useState("");
  const [isSavingScript, setIsSavingScript] = useState(false);
  const [isGenerating, setIsGenerating] = useState(false);
  const [generationError, setGenerationError] = useState("");
  const [toastText, setToastText] = useState("");

  const currentFrame = frames[selectedIndex] ?? frames[0];
  const currentProject = useMemo(
    () => projects.find((item) => item.id === selectedProjectId) ?? null,
    [projects, selectedProjectId],
  );
  const generatedCount = frames.filter((frame) => Boolean(currentVersion(frame))).length;
  const assetGenerationPrompt = buildAssetGenerationPrompt(assetDraft);
  const assetReferenceImageUrls = assetReferenceImages.map((item) => item.url);
  const assetGenerationMode: "text_to_image" | "image_to_image" = assetReferenceImageUrls.length ? "image_to_image" : "text_to_image";
  const canSubmitAssetGeneration = Boolean(assetDraft.id && assetGenerationPrompt);
  const canSubmitStyleGeneration = Boolean(currentProject && styleReferencePrompt.trim());
  const styleReferenceImageUrls = styleReferenceImages.map((item) => item.url);
  const selectedLabels = useMemo(() => {
    const chipTexts = Object.values(selectedChips).flat();
    const frameTexts = selectedFrameRefs.map((index) => {
      const version = currentVersion(frames[index]);
      return `参考项目第 ${index + 1} 帧：${version ? version.note : "空白帧"}`;
    });
    return [...chipTexts, ...frameTexts];
  }, [frames, selectedChips, selectedFrameRefs]);

  useEffect(() => {
    async function restoreAuthSession() {
      if (!hasStoredAuthSession()) {
        setAuthChecking(false);
        setStatusText("请先登录后端账号");
        return;
      }

      try {
        const user = await getCurrentUser();
        setAuthUser(user);
        setStatusText(`已登录：${displayUserName(user)}`);
      } catch (error) {
        console.error(error);
        clearAuthSession();
        setStatusText("登录已过期，请重新登录");
      } finally {
        setAuthChecking(false);
      }
    }

    const onAuthExpired = () => {
      resetWorkbenchState();
      setAuthUser(null);
      setStatusText("登录已过期，请重新登录");
      setAuthError("登录已过期，请重新登录");
    };

    window.addEventListener("framelab:auth-expired", onAuthExpired);
    void restoreAuthSession();
    return () => window.removeEventListener("framelab:auth-expired", onAuthExpired);
  }, []);

  useEffect(() => {
    if (!authUser) {
      return;
    }

    async function loadWorkbench() {
      try {
        const list = await listProjects();
        setProjects(list.items);
        setStatusText("项目列表已连接后端");
      } catch (error) {
        console.error(error);
        setStatusText("后端未连接，已进入前端演示模式");
      }
    }

    void loadWorkbench();
  }, [authUser, setSelectedFrameId]);

  useEffect(() => {
    if (activePage === "projects" || !route.projectId || projects.length === 0) {
      return;
    }

    const nextProject = projects.find((item) => item.id === route.projectId);
    if (!nextProject) {
      showToast("项目不存在或已被删除");
      navigateToProjects();
      return;
    }
    if (selectedProjectId === route.projectId && project?.id === route.projectId) {
      return;
    }

    void openProject(nextProject).then(() => {
      setStatusText(`已打开：${nextProject.name}`);
    });
  }, [activePage, project?.id, projects, route.projectId, selectedProjectId]);

  useEffect(() => {
    if (activePage !== "assets") {
      return;
    }

    if (!route.assetId) {
      if (isAssetEditing) {
        setIsAssetEditing(false);
      }
      return;
    }

    const nextIndex = assets.findIndex((item) => item.id === route.assetId);
    if (nextIndex === -1 || (isAssetEditing && assetDraft.id === route.assetId)) {
      return;
    }

    selectAssetForEditor(nextIndex);
  }, [activePage, assetDraft.id, assets, isAssetEditing, route.assetId]);

  useEffect(() => {
    if (!toastText) {
      return;
    }
    const timer = window.setTimeout(() => setToastText(""), 1600);
    return () => window.clearTimeout(timer);
  }, [toastText]);

  useEffect(() => {
    const element = assetGridRef.current;
    if (!element) {
      return;
    }

    const updateColumnCount = () => {
      setAssetColumnCount(Math.max(1, Math.floor((element.clientWidth + 2) / 222)));
    };

    updateColumnCount();
    const observer = new ResizeObserver(updateColumnCount);
    observer.observe(element);
    return () => observer.disconnect();
  }, [activePage, assetFilter, assets.length, isAssetEditing]);

  useEffect(() => {
    if (projectDraft.style_reference_image_file_id && projectDraft.style_reference_image_url) {
      setStyleReferenceImages([
        {
          id: projectDraft.style_reference_image_file_id,
          fileId: projectDraft.style_reference_image_file_id,
          url: projectDraft.style_reference_image_url,
        },
      ]);
      return;
    }

    setStyleReferenceImages([]);
  }, [projectDraft.style_reference_image_file_id, projectDraft.style_reference_image_url]);

  useEffect(() => {
    if (activePage === "public-assets" && route.publicAssetId) {
      return;
    }
    if (!isPublicAssetPickerOpen && activePage !== "public-assets") {
      return;
    }

    let canceled = false;
    async function loadLibrary() {
      setIsLoadingPublicAssets(true);
      try {
        const list = await loadPublicAssets({
          type: publicAssetFilter,
          keyword: publicAssetKeyword,
        });
        if (!canceled) {
          setPublicAssets(list.items.map((asset) => mapPublicAsset(asset)));
        }
      } catch (error) {
        if (!canceled) {
          showToast(error instanceof Error ? error.message : "公共资产库加载失败");
        }
      } finally {
        if (!canceled) {
          setIsLoadingPublicAssets(false);
        }
      }
    }

    const timer = window.setTimeout(() => {
      void loadLibrary();
    }, 180);
    return () => {
      canceled = true;
      window.clearTimeout(timer);
    };
  }, [activePage, isPublicAssetPickerOpen, publicAssetFilter, publicAssetKeyword, route.publicAssetId]);

  useEffect(() => {
    if (activePage !== "public-assets" || !route.publicAssetId) {
      if (activePage === "public-assets") {
        setPublicAssetDetail(null);
      }
      return;
    }
    if (publicAssetDetail?.id === route.publicAssetId) {
      return;
    }

    let canceled = false;
    async function loadDetail() {
      try {
        setPublicAssetDetail(null);
        const asset = await loadPublicAsset(route.publicAssetId as string);
        if (!canceled) {
          setPublicAssetDetail(mapPublicAsset(asset));
        }
      } catch (error) {
        if (!canceled) {
          showToast(error instanceof Error ? error.message : "公共资产详情加载失败");
          navigateToPublicAssets();
        }
      }
    }

    void loadDetail();
    return () => {
      canceled = true;
    };
  }, [activePage, publicAssetDetail?.id, route.publicAssetId]);

  useEffect(() => {
    if (!publicAssetDetail?.id) {
      setPublicAssetDetailImages([]);
      setSelectedPublicAssetImageIndex(0);
      return;
    }

    const publicAssetId = publicAssetDetail.id;
    let canceled = false;
    async function loadImages() {
      setIsLoadingPublicAssetImages(true);
      setSelectedPublicAssetImageIndex(0);
      try {
        const result = await loadPublicAssetImages(publicAssetId);
        if (!canceled) {
          setPublicAssetDetailImages(result.items);
        }
      } catch (error) {
        if (!canceled) {
          setPublicAssetDetailImages([]);
          showToast(error instanceof Error ? error.message : "公共资产图集加载失败");
        }
      } finally {
        if (!canceled) {
          setIsLoadingPublicAssetImages(false);
        }
      }
    }

    void loadImages();
    return () => {
      canceled = true;
    };
  }, [publicAssetDetail?.id]);

  useEffect(() => {
    if (!publicAssetDetail?.id) {
      setPublicAssetGenerationTasks([]);
      return;
    }

    let canceled = false;
    async function loadTasks() {
      setIsLoadingPublicAssetGenerationTasks(true);
      try {
        const result = await loadGenerationTasks({
          target_type: "public_asset_gallery",
          target_id: publicAssetDetail?.id,
          limit: 20,
        });
        if (!canceled) {
          setPublicAssetGenerationTasks(result.items);
        }
      } catch (error) {
        if (!canceled) {
          showToast(error instanceof Error ? error.message : "公共资产生成任务加载失败");
        }
      } finally {
        if (!canceled) {
          setIsLoadingPublicAssetGenerationTasks(false);
        }
      }
    }

    void loadTasks();
    return () => {
      canceled = true;
    };
  }, [publicAssetDetail?.id]);

  useEffect(() => {
    if (!publicAssetDetail?.id) {
      return;
    }
    const hasRunningTask = publicAssetGenerationTasks.some((task) => task.status === "queued" || task.status === "running");
    if (!hasRunningTask) {
      return;
    }
    const timer = window.setInterval(() => {
      void refreshPublicAssetGenerationState({ selectLatestGeneratedImage: true });
    }, 3500);
    return () => window.clearInterval(timer);
  }, [publicAssetDetail?.id, publicAssetGenerationTasks]);

  function showToast(text: string) {
    setToastText(text);
  }

  async function copyMcpCommand() {
    const command = `curl -fsSL http://127.0.0.1:18081/cli | sh -s -- --token '${mcpTokenForPrompt}'`;
    if (!mcpToken) {
      showToast("先生成 MCP Token，再复制接入命令");
      return;
    }

    try {
      await navigator.clipboard.writeText(command);
      showToast("接入命令已复制");
    } catch (error) {
      console.error(error);
      showToast("复制失败，请手动选择命令");
    }
  }

  async function generateMcpToken() {
    if (isCreatingMcpToken) {
      return;
    }

    setIsCreatingMcpToken(true);
    try {
      const token = await createMcpToken(`codex-opencode-${Date.now()}`);
      setMcpToken(token.token);
      showToast("MCP Token 已生成，接入指令已包含 token");
    } catch (error) {
      showToast(error instanceof Error ? error.message : "生成 MCP Token 失败");
    } finally {
      setIsCreatingMcpToken(false);
    }
  }

  function updateAuthDraft(key: keyof typeof authDraft, value: string) {
    setAuthDraft((item) => ({ ...item, [key]: value }));
  }

  async function submitAuth(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    if (authSubmitting) {
      return;
    }

    setAuthSubmitting(true);
    setAuthError("");
    try {
      const response =
        authMode === "login"
          ? await loginUser({
              login: authDraft.login.trim(),
              password: authDraft.password,
            })
          : await registerUser({
              email: authDraft.email.trim(),
              username: authDraft.username.trim(),
              display_name: authDraft.displayName.trim(),
              password: authDraft.password,
            });
      setAuthUser(response.user);
      setStatusText(`已登录：${displayUserName(response.user)}`);
      setAuthDraft({
        email: "",
        username: "",
        displayName: "",
        login: "",
        password: "",
      });
      showToast(authMode === "login" ? "登录成功" : "注册成功");
    } catch (error) {
      setAuthError(error instanceof Error ? error.message : "登录失败");
    } finally {
      setAuthSubmitting(false);
    }
  }

  async function handleLogout() {
    await logoutUser();
    resetWorkbenchState();
    setAuthUser(null);
    setStatusText("已退出登录");
    showToast("已退出登录");
    navigateToProjects();
  }

  function resetWorkbenchState() {
    setProject(null);
    setScript(null);
    setScriptText("");
    setProjects([]);
    setSelectedProjectId(null);
    setProjectDraft(createEmptyProjectDraft());
    const emptyFrames = createInitialFrames();
    setFrames(emptyFrames);
    setSelectedIndex(0);
    setSelectedFrameId(emptyFrames[0].id);
    setDetailIndex(null);
    setSelectedFrameRefs([]);
    setPrompt("");
    setAssets([]);
    setAssetDraft(createEmptyAsset());
    setAssetReferenceImages([]);
    setStyleReferenceImages([]);
    setMcpToken("");
    setSelectedAsset(0);
    setIsAssetEditing(false);
  }

  function assetToReferenceImages(asset: AssetItem): StyleReferenceImage[] {
    if (!asset.image) {
      return [];
    }

    const referenceId = asset.imageFileId || asset.id || `${asset.name}-${asset.image}`;
    return [
      {
        id: referenceId,
        fileId: asset.imageFileId || referenceId,
        url: asset.image,
      },
    ];
  }

  function navigateToProjects() {
    window.location.hash = "/projects";
  }

  function navigateToPublicAssets() {
    setPublicAssetDetail(null);
    window.location.hash = "/public-assets";
  }

  function navigateToPublicAssetDetail(assetId: string) {
    window.location.hash = `/public-assets/${encodeURIComponent(assetId)}`;
  }

  function navigateToProjectPage(page: ProjectPage, projectId = currentProject?.id) {
    if (!projectId) {
      showToast("先选择或新建一个项目");
      navigateToProjects();
      return;
    }

    const segmentByPage: Record<ProjectPage, string> = {
      "project-settings": "settings",
      script: "script",
      style: "style",
      assets: "assets",
      workbench: "keyframes",
    };
    window.location.hash = `/projects/${projectId}/${segmentByPage[page]}`;
  }

  function navigateToAssetDetail(assetId: string, projectId = currentProject?.id) {
    if (!projectId) {
      navigateToProjects();
      return;
    }

    window.location.hash = assetDetailHash(projectId, assetId);
  }

  async function openProject(nextProject: Project) {
    setSelectedProjectId(nextProject.id);
    setProject(nextProject);
    setProjectDraft({
      name: nextProject.name,
      description: nextProject.description,
      aspect_ratio: nextProject.aspect_ratio || "16:9",
      style_prompt: nextProject.style_prompt || "",
      style_reference_image_file_id: nextProject.style_reference_image_file_id,
      style_reference_image_url: nextProject.style_reference_image_url,
      auto_apply_style_prompt: nextProject.auto_apply_style_prompt,
      auto_apply_style_reference: nextProject.auto_apply_style_reference,
    });
    setStyleReferencePrompt("");
    setStatusText(`正在打开：${nextProject.name}`);

    const [nextScript, nextFrames, nextAssets] = await Promise.all([
      loadOrCreateProjectScript(nextProject.id),
      loadProjectFrames(nextProject.id),
      loadProjectAssets(nextProject.id),
    ]);

    setScript(nextScript);
    setScriptText(nextScript.content);
    setAssets(nextAssets.items.map((asset) => mapBackendAsset(asset)));
    setSelectedAsset(0);
    const firstAsset = nextAssets.items[0] ? mapBackendAsset(nextAssets.items[0]) : createEmptyAsset();
    setAssetDraft(firstAsset);
    setAssetReferenceImages(assetToReferenceImages(firstAsset));
    setIsAssetEditing(false);

    const mappedFrames = mapBackendFrames(nextFrames.items);
    if (mappedFrames.length) {
      setFrames(mappedFrames);
      setSelectedIndex(0);
      setSelectedFrameId(mappedFrames[0].id);
      setPrompt(currentVersion(mappedFrames[0])?.prompt || mappedFrames[0].prompt || "");
    } else {
      const emptyFrame = createEmptyFrame();
      setFrames([emptyFrame]);
      setSelectedIndex(0);
      setSelectedFrameId(emptyFrame.id);
      setPrompt("");
    }
  }

  async function checkBackend() {
    try {
      const result = await healthCheck();
      setStatusText(`${result.app}: ${result.status}`);
      showToast("后端连接正常");
    } catch (error) {
      setStatusText(error instanceof Error ? error.message : "后端检查失败");
      showToast("后端检查失败");
    }
  }

  function selectFrame(index: number) {
    const nextFrame = frames[index];
    if (!nextFrame) {
      return;
    }
    setSelectedIndex(index);
    setSelectedFrameId(nextFrame.id);
    setPrompt(currentVersion(nextFrame)?.prompt || nextFrame.prompt || "");
  }

  function updateCurrentFrame(updater: (frame: UiFrame) => UiFrame) {
    setFrames((items) => items.map((frame, index) => (index === selectedIndex ? updater(frame) : frame)));
  }

  function updateDetailStory(index: number, key: keyof FrameStory, value: string) {
    setFrames((items) =>
      items.map((frame, frameIndex) =>
        frameIndex === index ? { ...frame, story: { ...frame.story, [key]: value } } : frame,
      ),
    );
  }

  function insertFrameAfter(index: number) {
    const nextFrame = createEmptyFrame();
    setFrames((items) => [...items.slice(0, index + 1), nextFrame, ...items.slice(index + 1)]);
    setSelectedFrameRefs((items) => items.map((ref) => (ref > index ? ref + 1 : ref)));
    setDetailIndex((value) => (value !== null && value > index ? value + 1 : value));
    setTimeout(() => selectFrame(index + 1), 0);
    showToast(`已在第 ${index + 1} 帧后插入新帧`);
  }

  function deleteFrame(index: number) {
    if (frames.length <= 1) {
      showToast("至少保留一帧");
      return;
    }
    const nextFrames = frames.filter((_, frameIndex) => frameIndex !== index);
    setFrames(nextFrames);
    setSelectedFrameRefs((items) => items.filter((ref) => ref !== index).map((ref) => (ref > index ? ref - 1 : ref)));
    setDetailIndex((value) => {
      if (value === index) {
        return null;
      }
      return value !== null && value > index ? value - 1 : value;
    });
    const nextIndex = Math.min(index, nextFrames.length - 1);
    setSelectedIndex(nextIndex);
    setSelectedFrameId(nextFrames[nextIndex].id);
    setPrompt(currentVersion(nextFrames[nextIndex])?.prompt || nextFrames[nextIndex].prompt || "");
    showToast(`已删除第 ${index + 1} 帧`);
  }

  function toggleChip(group: keyof typeof QUICK_CHIPS | "style", value: string, label?: string) {
    if (assetPanel === "mention") {
      insertMention(label ?? value);
      return;
    }

    setSelectedChips((items) => {
      const groupValues = items[group] ?? [];
      const isActive = groupValues.includes(value);
      const nextValues = isActive ? groupValues.filter((item) => item !== value) : [...(group === "prop" ? groupValues : []), value];
      return { ...items, [group]: nextValues };
    });
  }

  function insertMention(label: string) {
    const nextPrompt = `${prompt}${prompt && !prompt.endsWith(" ") ? " " : ""}@${label} `;
    setPrompt(nextPrompt);
    updateCurrentFrame((frame) => ({ ...frame, prompt: nextPrompt }));
    setAssetPanel(null);
  }

  function toggleAssetPanel(panel: Exclude<AssetPanel, null | "mention">) {
    setAssetPanel((value) => (value === panel ? null : panel));
  }

  function toggleFrameReference(index: number) {
    if (assetPanel === "mention") {
      insertMention(`第${index + 1}帧`);
      return;
    }
    setSelectedFrameRefs((items) => (items.includes(index) ? items.filter((item) => item !== index) : [...items, index]));
  }

  async function selectFrameVersion(index: number, versionIndex: number) {
    const frame = frames[index];
    const version = frame?.versions[versionIndex];
    if (!frame || !version) {
      return;
    }

    setFrames((items) =>
      items.map((item, itemIndex) => (itemIndex === index ? { ...item, currentVersion: versionIndex } : item)),
    );
    selectFrame(index);
    setPrompt(version.prompt || frame.prompt || "");

    if (!version.id) {
      return;
    }

    try {
      await apiSelectFrameVersion(frame.id, version.id);
    } catch (error) {
      showToast(error instanceof Error ? error.message : "版本选择保存失败");
    }
  }

  function magicPrompt() {
    const base = prompt.trim() || "主体清晰，动作明确，适合作为视频关键帧";
    const nextPrompt = `${base}，构图干净，光影自然，画面稳定`;
    setPrompt(nextPrompt);
    updateCurrentFrame((frame) => ({ ...frame, prompt: nextPrompt }));
    showToast("已润色提示词");
  }

  async function generateImage() {
    const fullPrompt = [prompt.trim(), ...selectedLabels].filter(Boolean).join("，");
    if (!fullPrompt || isGenerating) {
      showToast("先输入文字，或从素材库选参考");
      return;
    }

    setIsGenerating(true);
    setGenerationError("");
    updateCurrentFrame((frame) => ({
      ...frame,
      prompt: fullPrompt,
      story: {
        ...frame.story,
        action: frame.story.action || fullPrompt,
        summary: frame.story.summary || fullPrompt,
      },
    }));

    try {
      if (currentProject && currentFrame?.id) {
        await updateFrame(currentFrame.id, {
          current_prompt: fullPrompt,
          summary: currentFrame.story.summary || fullPrompt,
          action: currentFrame.story.action || fullPrompt,
        });
      }
      const response = await createGenerationTask({
        task_type: "text_to_image",
        prompt: fullPrompt,
        aspect_ratio: currentProject?.aspect_ratio || project?.aspect_ratio || "16:9",
        project_id: currentProject?.id,
        frame_id: currentFrame?.id,
        image_type: "keyframe",
        auto_apply_asset_references: true,
      });
      setStatusText(`任务已提交：${response.task_id}`);
      const completedTask = await waitForGenerationTask(response.task_id);
      if (completedTask.status === "succeeded") {
        await addVersionFromTask(fullPrompt, completedTask);
        setStatusText(`已生成 ${completedTask.size} 图片`);
        showToast("已生成到当前帧");
      } else {
        setGenerationError(completedTask.error_message || "生成任务失败");
        setStatusText(`任务${completedTask.status === "canceled" ? "已取消" : "失败"}`);
      }
    } catch (error) {
      setGenerationError(error instanceof Error ? error.message : "生成失败");
      addMockVersion(fullPrompt, true);
      showToast("接口未返回图片，已生成占位版本");
    } finally {
      setIsGenerating(false);
    }
  }

  async function addVersionFromTask(fullPrompt: string, task: GenerationTaskResult) {
    const image = task.images[0];
    const imageSrc = image?.url || (image?.b64_json ? `data:image/png;base64,${image.b64_json}` : undefined);
    const note = fullPrompt.length > 18 ? `${fullPrompt.slice(0, 18)}...` : fullPrompt;

    if (currentProject && currentFrame?.id && image?.media_file_id) {
      const version = await createFrameVersion(currentFrame.id, {
        image_file_id: image.media_file_id,
        generation_task_id: task.task_id,
        prompt: fullPrompt,
        note,
        metadata: {
          aspect_ratio: task.aspect_ratio,
          size: task.size,
          model_name: task.model_name,
          object_key: image.object_key,
        },
        select: true,
      });
      addSavedVersion(fullPrompt, note, version.id, version.image_file_id, version.generation_task_id, version.image_url || imageSrc);
      return;
    }

    addMockVersion(fullPrompt, false, imageSrc);
  }

  function addSavedVersion(
    fullPrompt: string,
    note: string,
    id?: string,
    imageFileId?: string | null,
    generationTaskId?: string | null,
    image?: string,
  ) {
    setFrames((items) =>
      items.map((frame) => {
        if (frame.id !== currentFrame?.id) {
          return frame;
        }
        const version: FrameVersion = {
          id,
          imageFileId,
          generationTaskId,
          prompt: fullPrompt,
          note,
          colors: PALETTES[(selectedIndex + frame.versions.length) % PALETTES.length],
          image,
        };
        return {
          ...frame,
          prompt: fullPrompt,
          story: {
            ...frame.story,
            action: frame.story.action || fullPrompt,
            summary: frame.story.summary || fullPrompt,
          },
          versions: [...frame.versions, version],
          currentVersion: frame.versions.length,
        };
      }),
    );
  }

  function addMockVersion(fullPrompt: string, shiftPalette: boolean, image?: string) {
    setFrames((items) =>
      items.map((frame, index) => {
        if (index !== selectedIndex) {
          return frame;
        }
        const version: FrameVersion = {
          prompt: fullPrompt,
          note: fullPrompt.length > 18 ? `${fullPrompt.slice(0, 18)}...` : fullPrompt,
          colors: PALETTES[(selectedIndex + frame.versions.length + (shiftPalette ? 1 : 0)) % PALETTES.length],
          image,
        };
        return {
          ...frame,
          versions: [...frame.versions, version],
          currentVersion: frame.versions.length,
        };
      }),
    );
  }

  function fillDemo() {
    const demo = [
      "女主站在雨夜街道，远处黑色轿车亮起车灯。",
      "女主听到刹车声，紧张地回头看向镜头。",
      "神秘男人撑黑伞从车门后出现。",
    ];
    const stories: FrameStory[] = [
      {
        summary: "女主独自站在雨夜街道中央，远处黑色轿车亮起车灯。",
        duration: "3 秒",
        people: "女主",
        dialogue: "无对白",
        action: "站在雨夜街道，远处黑色轿车亮起车灯。",
        emotion: "警觉、紧张",
        note: "画面重点是雨水反光、车灯压迫感和女主的孤立感。",
      },
      {
        summary: "女主听到身后刹车声后迅速回头，进入紧张反应。",
        duration: "2 秒",
        people: "女主",
        dialogue: "无对白",
        action: "听到刹车声，回头看向镜头。",
        emotion: "惊讶、戒备",
        note: "需要表现动作瞬间和紧张情绪。",
      },
      {
        summary: "神秘男人从黑色轿车旁出现，撑着黑伞制造压迫感。",
        duration: "4 秒",
        people: "神秘男人",
        dialogue: "无对白",
        action: "撑黑伞从车门后出现。",
        emotion: "冷静、压迫感",
        note: "脸部可以半遮挡，画面要有悬疑感。",
      },
    ];
    const nextFrames = demo.map((item, index) => ({
      id: `demo-frame-${index + 1}`,
      prompt: item,
      story: stories[index],
      versions: [{ prompt: item, note: `${item.slice(0, 18)}...`, colors: PALETTES[index] }],
      currentVersion: 0,
    }));
    setFrames(nextFrames);
    setSelectedIndex(0);
    setSelectedFrameId(nextFrames[0].id);
    setPrompt(nextFrames[0].prompt);
    setDetailIndex(null);
    showToast("已填入示例帧");
  }

  async function saveProjectSettings() {
    if (!currentProject) {
      showToast("先新建一个项目");
      return;
    }
    if (!projectDraft.name.trim()) {
      showToast("项目名字不能为空");
      return;
    }

    try {
      const updatedProject = await apiUpdateProject(currentProject.id, {
        name: projectDraft.name.trim(),
        description: projectDraft.description,
        aspect_ratio: projectDraft.aspect_ratio,
      });
      setProject(updatedProject);
      setProjects((items) => items.map((item) => (item.id === updatedProject.id ? updatedProject : item)));
      setProjectDraft({
        name: updatedProject.name,
        description: updatedProject.description,
        aspect_ratio: updatedProject.aspect_ratio,
        style_prompt: updatedProject.style_prompt || "",
        style_reference_image_file_id: updatedProject.style_reference_image_file_id,
        style_reference_image_url: updatedProject.style_reference_image_url,
        auto_apply_style_prompt: updatedProject.auto_apply_style_prompt,
        auto_apply_style_reference: updatedProject.auto_apply_style_reference,
      });
      showToast("项目设置已保存");
    } catch (error) {
      showToast(error instanceof Error ? error.message : "保存项目失败");
    }
  }

  async function saveProjectStyle() {
    if (!currentProject) {
      showToast("先选择或新建一个项目");
      return;
    }

    try {
      const updatedProject = await apiUpdateProject(currentProject.id, {
        style_prompt: projectDraft.style_prompt,
        style_reference_image_file_id: projectDraft.style_reference_image_file_id,
        auto_apply_style_prompt: projectDraft.auto_apply_style_prompt,
        auto_apply_style_reference: projectDraft.auto_apply_style_reference,
      });
      setProject(updatedProject);
      setProjects((items) => items.map((item) => (item.id === updatedProject.id ? updatedProject : item)));
      setProjectDraft((item) => ({
        ...item,
        style_prompt: updatedProject.style_prompt || "",
        style_reference_image_file_id: updatedProject.style_reference_image_file_id,
        style_reference_image_url: updatedProject.style_reference_image_url ?? item.style_reference_image_url,
        auto_apply_style_prompt: updatedProject.auto_apply_style_prompt,
        auto_apply_style_reference: updatedProject.auto_apply_style_reference,
      }));
      showToast("风格设置已保存");
    } catch (error) {
      showToast(error instanceof Error ? error.message : "保存风格失败");
    }
  }

  function applyStyleCase(styleCase: StyleCase) {
    setProjectDraft((item) => ({
      ...item,
      style_prompt: styleCase.prompt,
      style_reference_image_file_id: null,
      style_reference_image_url: styleCase.image,
      auto_apply_style_prompt: true,
    }));
    setStyleReferencePrompt(styleCase.prompt);
    setStyleReferenceImages([]);
    setStyleGenerationStatus("");
    showToast(`已套用风格案例：${styleCase.name}`);
  }

  async function handleStyleReferenceImages(files: FileList | null | undefined) {
    const selectedFiles = Array.from(files ?? []);
    if (selectedFiles.length === 0) {
      return;
    }
    if (!currentProject) {
      showToast("先选择或新建一个项目");
      return;
    }

    try {
      const uploadSlot = styleUploadSlotRef.current;
      const mediaFiles = await Promise.all(
        selectedFiles.map((file) => uploadMediaFile(file, "image", currentProject.id)),
      );
      const nextReferences = mediaFiles.map((mediaFile) => ({
        id: mediaFile.id,
        fileId: mediaFile.id,
        url: mediaFile.url,
      }));
      setStyleReferenceImages((items) => {
        const nextItems = [...items];

        if (uploadSlot >= 0 && uploadSlot < nextItems.length) {
          nextItems.splice(uploadSlot, selectedFiles.length, ...nextReferences);
        } else {
          nextItems.push(...nextReferences);
        }

        return nextItems;
      });
      showToast(`已上传 ${selectedFiles.length} 张参考图，将使用图生图方式`);
    } catch (error) {
      showToast(error instanceof Error ? error.message : "上传风格参考图失败");
    }
  }

  async function generateStyleReferenceImage(mode: "text_to_image" | "image_to_image") {
    if (!currentProject) {
      showToast("先选择或新建一个项目");
      return;
    }
    if (isGeneratingStyleImage) {
      return;
    }

    const promptText = styleReferencePrompt.trim();
    if (!promptText) {
      showToast("先填写风格参考图生成提示词");
      return;
    }
    const referenceImages = styleReferenceImages.map((item) => item.url);
    if (mode === "image_to_image" && referenceImages.length === 0) {
      showToast("先上传至少一张参考图");
      return;
    }

    setIsGeneratingStyleImage(true);
    setStyleGenerationStatus("正在提交风格参考图生成任务...");
    try {
      const task = await createGenerationTask({
        task_type: mode,
        prompt: promptText,
        aspect_ratio: currentProject.aspect_ratio || projectDraft.aspect_ratio || "16:9",
        image:
          mode === "image_to_image"
            ? referenceImages.length === 1
              ? referenceImages[0]
              : referenceImages
            : undefined,
        project_id: currentProject.id,
        image_type: "style",
      });
      setStyleGenerationStatus(`任务已提交：${task.task_id}`);
      const completedTask = await waitForGenerationTask(task.task_id, {
        intervalMs: 2000,
        onPoll: (latestTask, elapsedSeconds) => {
          if (latestTask.status === "running") {
            setStyleGenerationStatus(`风格参考图生成中，已等待 ${elapsedSeconds} 秒...`);
          } else if (latestTask.status === "queued") {
            setStyleGenerationStatus(`任务排队中，已等待 ${elapsedSeconds} 秒...`);
          }
        },
      });
      if (completedTask.status !== "succeeded") {
        throw new Error(completedTask.error_message || "风格参考图生成失败");
      }

      const generatedImage = completedTask.images[0];
      if (!generatedImage?.url || !generatedImage.media_file_id) {
        throw new Error("生成任务没有返回已转存的图片记录");
      }

      const updatedProject = await apiUpdateProject(currentProject.id, {
        style_prompt: projectDraft.style_prompt,
        style_reference_image_file_id: generatedImage.media_file_id,
        auto_apply_style_prompt: projectDraft.auto_apply_style_prompt,
        auto_apply_style_reference: projectDraft.auto_apply_style_reference,
      });
      setProject(updatedProject);
      setProjects((items) => items.map((item) => (item.id === updatedProject.id ? updatedProject : item)));
      setProjectDraft((item) => ({
        ...item,
        style_prompt: updatedProject.style_prompt || "",
        style_reference_image_file_id: updatedProject.style_reference_image_file_id,
        style_reference_image_url: updatedProject.style_reference_image_url,
        auto_apply_style_prompt: updatedProject.auto_apply_style_prompt,
        auto_apply_style_reference: updatedProject.auto_apply_style_reference,
      }));
      setStyleGenerationStatus("风格参考图已生成并保存");
      showToast(mode === "image_to_image" ? "图生图已保存到风格设置" : "文生图已保存到风格设置");
    } catch (error) {
      const message = error instanceof Error ? error.message : "风格参考图生成失败";
      setStyleGenerationStatus(message);
      showToast(message);
    } finally {
      setIsGeneratingStyleImage(false);
    }
  }

  async function saveProjectScript() {
    if (!currentProject) {
      showToast("先选择或新建一个项目");
      return;
    }
    if (isSavingScript) {
      return;
    }

    setIsSavingScript(true);
    try {
      const nextScript = await updateProjectScript(currentProject.id, scriptText);
      setScript(nextScript);
      setProjects((items) =>
        items.map((item) =>
          item.id === currentProject.id ? { ...item, updated_at: nextScript.updated_at } : item,
        ),
      );
      showToast("剧本已保存");
    } catch (error) {
      showToast(error instanceof Error ? error.message : "保存剧本失败");
    } finally {
      setIsSavingScript(false);
    }
  }

  async function clearProjectScript() {
    if (!currentProject) {
      showToast("先选择或新建一个项目");
      return;
    }
    if (!scriptText.trim()) {
      showToast("剧本已经是空的");
      return;
    }
    const confirmed = window.confirm("清空当前项目的剧本内容？");
    if (!confirmed) {
      return;
    }

    try {
      await deleteProjectScript(currentProject.id);
      const nextScript = await loadProjectScript(currentProject.id);
      setScript(nextScript);
      setScriptText("");
      setProjects((items) =>
        items.map((item) =>
          item.id === currentProject.id ? { ...item, updated_at: nextScript.updated_at } : item,
        ),
      );
      showToast("剧本已清空");
    } catch (error) {
      showToast(error instanceof Error ? error.message : "清空剧本失败");
    }
  }

  function updateProjectDraft(key: "name" | "description" | "aspect_ratio" | "style_prompt", value: string) {
    setProjectDraft((item) => ({ ...item, [key]: value }));
  }

  function updateProjectDraftValue<K extends keyof ProjectForm>(key: K, value: ProjectForm[K]) {
    setProjectDraft((item) => ({ ...item, [key]: value }));
  }

  function openCreateProjectDialog() {
    setNewProjectName("");
    setIsCreateProjectDialogOpen(true);
  }

  function closeCreateProjectDialog() {
    if (isCreatingProject) {
      return;
    }
    setIsCreateProjectDialogOpen(false);
    setNewProjectName("");
  }

  function handleCreateProjectDialogKeyDown(event: KeyboardEvent<HTMLFormElement>) {
    if (event.key === "Escape") {
      closeCreateProjectDialog();
    }
  }

  async function createProject(event?: FormEvent<HTMLFormElement>) {
    event?.preventDefault();
    if (isCreatingProject) {
      return;
    }
    const projectName = newProjectName.trim();
    if (!projectName) {
      showToast("请填写项目名字");
      return;
    }

    setIsCreatingProject(true);
    try {
      const nextProject = await apiCreateProject({
        name: projectName,
        description: "补充这个视频项目的故事方向、用途和制作备注。",
        aspect_ratio: "16:9",
      });
      setProjects((items) => [nextProject, ...items]);
      setIsCreateProjectDialogOpen(false);
      setNewProjectName("");
      await openProject(nextProject);
      navigateToProjectPage("project-settings", nextProject.id);
      showToast("已新建项目");
    } catch (error) {
      showToast(error instanceof Error ? error.message : "新建项目失败");
    } finally {
      setIsCreatingProject(false);
    }
  }

  async function selectProject(nextProject: Project) {
    if (nextProject.id === selectedProjectId) {
      navigateToProjectPage("project-settings", nextProject.id);
      return;
    }
    try {
      await openProject(nextProject);
      navigateToProjectPage("project-settings", nextProject.id);
      setStatusText(`已打开：${nextProject.name}`);
    } catch (error) {
      showToast(error instanceof Error ? error.message : "打开项目失败");
    }
  }

  async function deleteCurrentProject() {
    if (!currentProject) {
      return;
    }

    const confirmed = window.confirm(`删除项目「${currentProject.name}」？相关剧本、帧和资产也会从后端移除。`);
    if (!confirmed) {
      return;
    }

    try {
      await apiDeleteProject(currentProject.id);
      const remaining = projects.filter((item) => item.id !== currentProject.id);
      setProjects(remaining);
      setProject(null);
      setSelectedProjectId(null);
      setProjectDraft(createEmptyProjectDraft());
      setAssets([]);
      setAssetDraft(createEmptyAsset());
      setAssetReferenceImages([]);
      setSelectedAsset(0);
      setIsAssetEditing(false);
      navigateToProjects();
      showToast("项目已删除");
    } catch (error) {
      showToast(error instanceof Error ? error.message : "删除项目失败");
    }
  }

  function selectAssetForEditor(index: number) {
    setSelectedAsset(index);
    const nextAsset = assets[index];
    if (!nextAsset) {
      return;
    }
    setAssetDraft(nextAsset);
    setAssetReferenceImages(assetToReferenceImages(nextAsset));
    setAssetGenerationStatus("");
    setIsAssetEditing(true);
  }

  function openAssetEditor(index: number) {
    const nextAsset = assets[index];
    if (!nextAsset) {
      return;
    }

    selectAssetForEditor(index);
    if (nextAsset.id) {
      navigateToAssetDetail(nextAsset.id);
    }
  }

  function closeAssetEditor() {
    setIsAssetEditing(false);
    navigateToProjectPage("assets");
  }

  async function createAsset() {
    if (!currentProject) {
      showToast("先选择或新建一个项目");
      navigateToProjects();
      return;
    }
    const type = assetFilter === "全部" ? "角色" : assetFilter;
    try {
      const asset = await createProjectAsset(currentProject.id, {
        name: "未命名资产",
        type,
        description: "补充这个资产的外观、用途和关键特征",
        default_prompt: "",
        tags: ["新资产"],
        sort_order: assets.length,
      });
      const item = mapBackendAsset(asset);
      setAssets((items) => [item, ...items]);
      setSelectedAsset(0);
      setAssetDraft(item);
      setAssetReferenceImages(assetToReferenceImages(item));
      setAssetGenerationStatus("");
      setIsAssetEditing(true);
      if (item.id) {
        navigateToAssetDetail(item.id);
      }
      showToast("已新建资产");
    } catch (error) {
      showToast(error instanceof Error ? error.message : "新建资产失败");
    }
  }

  function openPublicAssetPicker() {
    if (!currentProject) {
      showToast("先选择或新建一个项目");
      navigateToProjects();
      return;
    }
    setSelectedPublicAssetIds([]);
    setIsPublicAssetPickerOpen(true);
  }

  function togglePublicAssetSelection(assetId: string | undefined) {
    if (!assetId) {
      return;
    }
    setSelectedPublicAssetIds((ids) =>
      ids.includes(assetId) ? ids.filter((id) => id !== assetId) : [...ids, assetId],
    );
  }

  async function importSelectedPublicAssets() {
    if (!currentProject) {
      showToast("先选择或新建一个项目");
      return;
    }
    if (selectedPublicAssetIds.length === 0 || isImportingPublicAssets) {
      return;
    }

    setIsImportingPublicAssets(true);
    try {
      const result = await importPublicAssetsToProject(currentProject.id, {
        public_asset_ids: selectedPublicAssetIds,
        copy_media: true,
      });
      const importedItems = result.items.map((asset) => mapBackendAsset(asset));
      setAssets((items) => [...importedItems, ...items]);
      setSelectedPublicAssetIds([]);
      if (isPublicAssetPickerOpen) {
        setIsPublicAssetPickerOpen(false);
      }
      if (result.errors.length) {
        showToast(`已导入 ${importedItems.length} 个资产，${result.errors.length} 个失败`);
      } else {
        showToast(`已导入 ${importedItems.length} 个公共资产`);
      }
    } catch (error) {
      showToast(error instanceof Error ? error.message : "公共资产导入失败");
    } finally {
      setIsImportingPublicAssets(false);
    }
  }

  async function handlePublicAssetGalleryUpload(files: FileList | null | undefined) {
    const selectedFiles = Array.from(files ?? []);
    if (!publicAssetDetail?.id || selectedFiles.length === 0 || isUploadingPublicAssetImages) {
      return;
    }

    setIsUploadingPublicAssetImages(true);
    try {
      const createdImages: PublicAssetImage[] = [];
      for (const [index, file] of selectedFiles.entries()) {
        const mediaFile = await uploadMediaFile(file, "image", null);
        const title = file.name.replace(/\.[^.]+$/, "");
        const image = await createPublicAssetImage(publicAssetDetail.id, {
          media_file_id: mediaFile.id,
          role: "reference",
          title,
          sort_order: publicAssetDetailImages.length + index,
          is_primary: !publicAssetDetail.image && publicAssetDetailImages.length === 0 && index === 0,
        });
        createdImages.push(image);
      }

      setPublicAssetDetailImages((items) => [...items, ...createdImages]);
      setSelectedPublicAssetImageIndex(publicAssetDetailImages.length);
      const primaryImage = createdImages.find((image) => image.is_primary && image.image_url);
      if (primaryImage?.image_url) {
        const updatedAsset = {
          ...publicAssetDetail,
          image: primaryImage.image_url,
          imageFileId: primaryImage.media_file_id,
        };
        setPublicAssetDetail(updatedAsset);
        setPublicAssets((items) => items.map((item) => (item.id === updatedAsset.id ? updatedAsset : item)));
      }
      showToast(`已上传 ${createdImages.length} 张图集图片`);
    } catch (error) {
      showToast(error instanceof Error ? error.message : "公共资产图集上传失败");
    } finally {
      setIsUploadingPublicAssetImages(false);
      if (publicAssetGalleryFileInputRef.current) {
        publicAssetGalleryFileInputRef.current.value = "";
      }
    }
  }

  async function refreshPublicAssetGenerationState(options: { selectLatestGeneratedImage?: boolean } = {}) {
    if (!publicAssetDetail?.id) {
      return;
    }
    try {
      const [tasksResult, imagesResult] = await Promise.all([
        loadGenerationTasks({
          target_type: "public_asset_gallery",
          target_id: publicAssetDetail.id,
          limit: 20,
        }),
        loadPublicAssetImages(publicAssetDetail.id),
      ]);
      setPublicAssetGenerationTasks(tasksResult.items);
      setPublicAssetDetailImages(imagesResult.items);
      if (options.selectLatestGeneratedImage) {
        const latestSucceededTask = tasksResult.items.find((task) => task.status === "succeeded");
        const generatedIndex = latestSucceededTask
          ? imagesResult.items.findIndex((image) => image.generation_task_id === latestSucceededTask.task_id)
          : -1;
        if (generatedIndex >= 0) {
          setSelectedPublicAssetImageIndex(generatedIndex);
        }
      }
    } catch (error) {
      showToast(error instanceof Error ? error.message : "公共资产生成状态刷新失败");
    }
  }

  async function submitPublicAssetGeneration() {
    const promptText = publicAssetGenerationPrompt.trim();
    if (!publicAssetDetail?.id || !promptText || isSubmittingPublicAssetGeneration) {
      return;
    }

    setIsSubmittingPublicAssetGeneration(true);
    try {
      const task = await createGenerationTask({
        prompt: promptText,
        aspect_ratio: assetImageRatio(publicAssetDetail),
        image: publicAssetDetailImageUrl,
        target: {
          type: "public_asset_gallery",
          public_asset_id: publicAssetDetail.id,
          title: promptText.slice(0, 18),
          role: "generated",
          description: promptText,
          tags: ["AI生成"],
        },
        references: selectedPublicAssetImage
          ? [
              {
                type: "public_asset_image",
                id: selectedPublicAssetImage.id,
                url: selectedPublicAssetImage.image_url ?? undefined,
                title: selectedPublicAssetImage.title,
              },
            ]
          : [],
      });
      setPublicAssetGenerationTasks((items) => [task, ...items.filter((item) => item.task_id !== task.task_id)]);
      setPublicAssetGenerationPrompt("");
      showToast("已提交生成任务");
      window.setTimeout(() => {
        void refreshPublicAssetGenerationState({ selectLatestGeneratedImage: true });
      }, 1200);
    } catch (error) {
      showToast(error instanceof Error ? error.message : "公共资产生成任务提交失败");
    } finally {
      setIsSubmittingPublicAssetGeneration(false);
    }
  }

  async function deleteSelectedPublicAssetImage() {
    if (!selectedPublicAssetImage || !canDeleteSelectedPublicAssetImage || isDeletingPublicAssetImage) {
      return;
    }

    const confirmed = window.confirm(`删除图集图片「${selectedPublicAssetImage.title || roleLabel(selectedPublicAssetImage.role)}」？`);
    if (!confirmed) {
      return;
    }

    setIsDeletingPublicAssetImage(true);
    try {
      await deletePublicAssetImage(selectedPublicAssetImage.id);
      setPublicAssetDetailImages((items) => {
        const nextItems = items.filter((item) => item.id !== selectedPublicAssetImage.id);
        setSelectedPublicAssetImageIndex((index) => Math.max(0, Math.min(index, nextItems.length - 1)));
        return nextItems;
      });
      showToast("图集图片已删除");
    } catch (error) {
      showToast(error instanceof Error ? error.message : "删除图集图片失败");
    } finally {
      setIsDeletingPublicAssetImage(false);
    }
  }

  async function saveAssetEditor() {
    if (!assetDraft.name.trim()) {
      showToast("资产名称不能为空");
      return;
    }
    if (!assetDraft.id) {
      showToast("资产还没有同步到后台");
      return;
    }
    if (isSavingAsset) {
      return;
    }

    setIsSavingAsset(true);
    try {
      const updatedAsset = await updateAsset(assetDraft.id, assetItemToPayload(assetDraft));
      if (!isBackendAsset(updatedAsset)) {
        throw new Error("后端资产保存接口返回不完整，请重启后端服务后再试");
      }
      const updatedItem = mapBackendAsset(updatedAsset, assetDraft.image);
      setAssets((items) => items.map((item) => (item.id === updatedItem.id ? updatedItem : item)));
      setAssetDraft(updatedItem);
      closeAssetEditor();
      showToast("资产已保存");
    } catch (error) {
      showToast(error instanceof Error ? error.message : "保存资产失败");
    } finally {
      setIsSavingAsset(false);
    }
  }

  async function generateAssetImage(mode: "text_to_image" | "image_to_image", referenceImages = assetReferenceImageUrls) {
    if (!assetDraft.id) {
      showToast("先保存资产后再生成图片");
      return;
    }
    if (isGeneratingAssetImage) {
      return;
    }

    const promptText = buildAssetGenerationPrompt(assetDraft);
    if (!promptText) {
      showToast("先填写默认提示词或资产描述");
      return;
    }
    if (mode === "image_to_image" && referenceImages.length === 0) {
      showToast("先上传或添加至少一张参考图");
      return;
    }

    setIsGeneratingAssetImage(true);
    setAssetGenerationStatus("正在提交图片生成任务...");
    try {
      const task = await createGenerationTask({
        task_type: mode,
        prompt: promptText,
        aspect_ratio: assetImageRatio(assetDraft),
        image:
          mode === "image_to_image"
            ? referenceImages.length === 1
              ? referenceImages[0]
              : referenceImages
            : undefined,
        project_id: currentProject?.id ?? undefined,
        image_type: assetImageType(assetDraft),
      });
      setAssetGenerationStatus(`任务已提交：${task.task_id}`);
      const completedTask = await waitForGenerationTask(task.task_id, {
        intervalMs: 2000,
        onPoll: (latestTask, elapsedSeconds) => {
          if (latestTask.status === "running") {
            setAssetGenerationStatus(`图片生成中，已等待 ${elapsedSeconds} 秒...`);
          } else if (latestTask.status === "queued") {
            setAssetGenerationStatus(`任务排队中，已等待 ${elapsedSeconds} 秒...`);
          }
        },
      });
      if (completedTask.status !== "succeeded") {
        throw new Error(completedTask.error_message || "图片生成任务失败");
      }

      const generatedImage = completedTask.images[0];
      if (!generatedImage?.url || !generatedImage.media_file_id) {
        throw new Error("生成任务没有返回已转存的图片记录");
      }
      const nextAsset = {
        ...assetDraft,
        image: generatedImage.url,
        imageFileId: generatedImage.media_file_id,
      };
      const updatedAsset = await updateAsset(assetDraft.id, assetItemToPayload(nextAsset));
      const updatedItem = mapBackendAsset(updatedAsset, generatedImage.url);
      setAssets((items) => items.map((item) => (item.id === updatedItem.id ? updatedItem : item)));
      setAssetDraft(updatedItem);
      setAssetReferenceImages(assetToReferenceImages(updatedItem));
      setAssetGenerationStatus("图片已生成并保存");
      showToast(mode === "image_to_image" ? "图生图已保存到资产" : "文生图已保存到资产");
    } catch (error) {
      const message = error instanceof Error ? error.message : "资产图片生成失败";
      setAssetGenerationStatus(message);
      showToast(message);
    } finally {
      setIsGeneratingAssetImage(false);
    }
  }

  async function deleteAssetEditor() {
    if (!assetDraft.id) {
      return;
    }
    const confirmed = window.confirm(`删除资产「${assetDraft.name}」？`);
    if (!confirmed) {
      return;
    }

    try {
      await deleteAsset(assetDraft.id);
      const nextAssets = assets.filter((item) => item.id !== assetDraft.id);
      setAssets(nextAssets);
      setSelectedAsset(0);
      const nextAsset = nextAssets[0] ?? createEmptyAsset();
      setAssetDraft(nextAsset);
      setAssetReferenceImages(assetToReferenceImages(nextAsset));
      closeAssetEditor();
      showToast("资产已删除");
    } catch (error) {
      showToast(error instanceof Error ? error.message : "删除资产失败");
    }
  }

  async function handleAssetImage(file: File | undefined) {
    if (!file) {
      return;
    }
    try {
      const mediaFile = await uploadMediaFile(file, "image", currentProject?.id);
      setAssetDraft((item) => ({ ...item, image: mediaFile.url, imageFileId: mediaFile.id }));
      setAssetReferenceImages([{ id: mediaFile.id, fileId: mediaFile.id, url: mediaFile.url }]);
      setAssetGenerationStatus("图片已上传，保存资产后生效");
      showToast("图片已上传");
    } catch (error) {
      const dataUrl = await fileToDataUrl(file);
      const localId = `local-${file.name}-${Date.now()}`;
      setAssetDraft((item) => ({ ...item, image: dataUrl }));
      setAssetReferenceImages([{ id: localId, fileId: localId, url: dataUrl }]);
      showToast(error instanceof Error ? `上传失败：${error.message}` : "上传失败，已临时预览");
    }
  }

  async function handleAssetReferenceImages(files: FileList | null | undefined) {
    const selectedFiles = Array.from(files ?? []);
    if (selectedFiles.length === 0) {
      return;
    }

    const uploadedReferences: StyleReferenceImage[] = [];
    for (const file of selectedFiles) {
      try {
        const mediaFile = await uploadMediaFile(file, "image", currentProject?.id);
        uploadedReferences.push({
          id: mediaFile.id,
          fileId: mediaFile.id,
          url: mediaFile.url,
        });
      } catch (error) {
        const dataUrl = await fileToDataUrl(file);
        const localId = `local-${file.name}-${Date.now()}`;
        uploadedReferences.push({
          id: localId,
          fileId: localId,
          url: dataUrl,
        });
        showToast(error instanceof Error ? `部分参考图上传失败：${error.message}` : "部分参考图上传失败，已临时预览");
      }
    }

    setAssetReferenceImages((items) => [...items, ...uploadedReferences]);
    setAssetGenerationStatus(`已添加 ${uploadedReferences.length} 张参考图，将使用图生图方式`);
  }

  const filteredAssets = assets
    .map((asset, index) => ({ asset, index }))
    .filter(({ asset }) => assetFilter === "全部" || asset.type === assetFilter);
  const assetMasonryColumns = buildAssetMasonryColumns(filteredAssets, assetColumnCount, assetImageRatioMap);

  const activeProjects = projects.filter((item) => item.status === "active").length;
  const latestProject = projects[0] ?? null;
  const mcpTokenForPrompt = mcpToken || "<点击上方按钮生成 MCP token>";
  const styleReferenceCards: Array<StyleReferenceImage | null> = [...styleReferenceImages, null];
  const projectImageAspectRatio = toCssAspectRatio(projectDraft.aspect_ratio || currentProject?.aspect_ratio);
  const styleReferencePreviewStyle: CSSProperties = {
    aspectRatio: projectImageAspectRatio,
    ...(projectDraft.style_reference_image_url
      ? { backgroundImage: `url(${projectDraft.style_reference_image_url})` }
      : {}),
  };
  const selectedPublicAssetImage = publicAssetDetailImages[selectedPublicAssetImageIndex] ?? null;
  const publicAssetDetailImageUrl = selectedPublicAssetImage?.image_url ?? publicAssetDetail?.image;
  const publicAssetDetailPreviewImageUrl = publicAssetDetailImageUrl
    ? tosCompressedImageUrl(publicAssetDetailImageUrl, { width: 1800, quality: 82 })
    : undefined;
  const canDeleteSelectedPublicAssetImage =
    Boolean(selectedPublicAssetImage) && !selectedPublicAssetImage?.id.startsWith("primary-");

  if (authChecking) {
    return (
      <div className="app auth-app">
        <main className="auth-page">
          <section className="auth-card auth-card-loading">
            <BrandMark />
            <strong>正在恢复登录状态</strong>
          </section>
        </main>
      </div>
    );
  }

  if (!authUser) {
    return (
      <AuthScreen
        authDraft={authDraft}
        authError={authError}
        authMode={authMode}
        authSubmitting={authSubmitting}
        onCheckBackend={checkBackend}
        onDraftChange={updateAuthDraft}
        onModeChange={(mode) => {
          setAuthMode(mode);
          setAuthError("");
        }}
        onSubmit={submitAuth}
        statusText={statusText}
      />
    );
  }

  function styleReferenceCardStyle(
    index: number,
    reference: StyleReferenceImage | null,
    aspectRatio = projectImageAspectRatio,
  ): CSSProperties & Record<"--x" | "--y" | "--tilt" | "--z", string> {
    const visibleIndex = Math.min(index, 4);
    return {
      aspectRatio,
      backgroundImage: reference ? `url(${reference.url})` : undefined,
      "--x": `${visibleIndex * 40}px`,
      "--y": `${visibleIndex * 7}px`,
      "--tilt": `${index % 2 === 0 ? -8 : 6}deg`,
      "--z": String(index + 1),
    };
  }

  return (
    <div className="app">
      <header className="topbar">
        <button className="brand" type="button" onClick={checkBackend}>
          <BrandMark />
          <strong>图片关键帧生成工作台</strong>
          <span>{statusText}</span>
        </button>
        <nav className="project-nav" aria-label="项目页面">
          <button
            className={activePage === "projects" ? "active" : ""}
            type="button"
            onClick={navigateToProjects}
            aria-current={activePage === "projects" ? "page" : undefined}
          >
            <FolderKanban size={15} />
            项目
          </button>
          <button
            className={activePage === "public-assets" ? "active" : ""}
            type="button"
            onClick={navigateToPublicAssets}
            aria-current={activePage === "public-assets" ? "page" : undefined}
          >
            <Sparkles size={15} />
            公共库
          </button>
          {currentProject ? (
            <>
              <button
                className={activePage === "project-settings" ? "active" : ""}
                type="button"
                onClick={() => navigateToProjectPage("project-settings")}
                aria-current={activePage === "project-settings" ? "page" : undefined}
              >
                <Save size={15} />
                设置
              </button>
              <button
                className={activePage === "script" ? "active" : ""}
                type="button"
                onClick={() => navigateToProjectPage("script")}
                aria-current={activePage === "script" ? "page" : undefined}
              >
                <ScrollText size={15} />
                剧本
              </button>
              <button
                className={activePage === "style" ? "active" : ""}
                type="button"
                onClick={() => navigateToProjectPage("style")}
                aria-current={activePage === "style" ? "page" : undefined}
              >
                <Palette size={15} />
                风格
              </button>
              <button
                className={activePage === "assets" ? "active" : ""}
                type="button"
                onClick={() => navigateToProjectPage("assets")}
                aria-current={activePage === "assets" ? "page" : undefined}
              >
                <Image size={15} />
                资产
              </button>
              <button
                className={activePage === "workbench" ? "active" : ""}
                type="button"
                onClick={() => navigateToProjectPage("workbench")}
                aria-current={activePage === "workbench" ? "page" : undefined}
              >
                <Clapperboard size={15} />
                关键帧
              </button>
            </>
          ) : null}
        </nav>
        <div className="top-actions">
          <div className="user-menu" title={authUser.email}>
            <UserCircle size={16} />
            <span>{displayUserName(authUser)}</span>
          </div>
          <button type="button" onClick={handleLogout}>
            <LogOut size={15} />
            退出
          </button>
        </div>
      </header>

      {activePage === "projects" ? (
        <main className="project-list-page">
          <section className="projects-hero">
            <div className="projects-hero-glow" aria-hidden="true" />
            <div className="projects-hero-text">
              <span className="projects-eyebrow">KEYFRAME&nbsp;STUDIO</span>
              <h1>项目工作台</h1>
              <p>从剧本、风格到关键帧，一处掌控你的每一个视频创作项目。</p>
            </div>
            <button
              className="projects-new-btn"
              type="button"
              onClick={openCreateProjectDialog}
              disabled={isCreatingProject}
            >
              <Plus size={18} />
              {isCreatingProject ? "新建中…" : "新建项目"}
            </button>
          </section>

          <div className="projects-stats">
            <article className="stat-card stat-indigo">
              <span className="stat-icon">
                <FolderKanban size={18} />
              </span>
              <div className="stat-body">
                <span className="stat-label">项目总数</span>
                <strong className="stat-value">{projects.length}</strong>
              </div>
            </article>
            <article className="stat-card stat-emerald">
              <span className="stat-icon">
                <Activity size={18} />
              </span>
              <div className="stat-body">
                <span className="stat-label">进行中</span>
                <strong className="stat-value">{activeProjects}</strong>
              </div>
            </article>
            <article className="stat-card stat-amber">
              <span className="stat-icon">
                <Clock size={18} />
              </span>
              <div className="stat-body">
                <span className="stat-label">最近更新</span>
                <strong className="stat-value stat-value-sm">
                  {latestProject ? formatDate(latestProject.updated_at) : "—"}
                </strong>
              </div>
            </article>
            <article className="stat-card stat-sky">
              <span className="stat-icon">
                <Wifi size={18} />
              </span>
              <div className="stat-body">
                <span className="stat-label">连接状态</span>
                <strong className="stat-value stat-value-sm">
                  {statusText.includes("后端未连接") ? "演示模式" : "已连接"}
                </strong>
              </div>
            </article>
          </div>

          <section className="agent-connect">
            <div className="agent-connect-head">
              <span className="agent-connect-icon" aria-hidden="true">
                <Bot size={18} />
              </span>
              <div>
                <span className="projects-eyebrow">AGENT MCP</span>
                <h2>发给 Agent，让它自己接入</h2>
              </div>
              <button
                className="agent-token-btn"
                type="button"
                onClick={generateMcpToken}
                disabled={isCreatingMcpToken}
              >
                <KeyRound size={15} />
                {isCreatingMcpToken ? "生成中..." : mcpToken ? "重新生成通用命令" : "生成通用命令"}
              </button>
            </div>
            <div className="agent-command-grid">
              <article className="agent-command-card agent-command-wide">
                <div className="agent-command-title">
                  <strong>通用一键命令</strong>
                  <span>复制到任意 Agent 或终端，在项目目录执行</span>
                </div>
                <div className="agent-command-body">
                  <pre><code>{`curl -fsSL http://127.0.0.1:18081/cli | sh -s -- --token '${mcpTokenForPrompt}'`}</code></pre>
                  <button
                    className="agent-copy-btn"
                    type="button"
                    onClick={copyMcpCommand}
                    disabled={!mcpToken}
                    aria-label="复制 Agent MCP 接入命令"
                  >
                    复制
                  </button>
                </div>
              </article>
            </div>
          </section>

          <section className="projects-collection">
            <div className="projects-collection-head">
              <h2>全部项目</h2>
              <span className="projects-count-pill">{projects.length} 个项目</span>
            </div>
            {projects.length ? (
              <div className="projects-grid">
                {projects.map((item, index) => (
                  <button
                    className={currentProject?.id === item.id ? "project-card active" : "project-card"}
                    key={item.id}
                    type="button"
                    style={{ animationDelay: `${Math.min(index, 8) * 55}ms` }}
                    onClick={() => selectProject(item)}
                    aria-label={`打开项目 ${item.name}`}
                  >
                    <span
                      className="project-cover"
                      style={projectCoverStyle(item.id)}
                    >
                      <span className="project-cover-noise" aria-hidden="true" />
                      <span className="project-cover-stage" aria-hidden="true">
                        <span className="project-cover-filmstrip">
                          <span />
                          <span />
                          <span />
                          <span />
                          <span />
                        </span>
                        <span className="project-cover-frame main" />
                        <span className="project-cover-frame side" />
                        <span className="project-cover-focus" />
                        <span className="project-cover-timeline">
                          <span />
                          <span />
                          <span />
                          <span />
                        </span>
                      </span>
                      <span className="project-cover-ratio">{item.aspect_ratio}</span>
                      <span className="project-cover-open">
                        打开 <ArrowRight size={13} />
                      </span>
                    </span>
                    <span className="project-card-body">
                      <span className="project-card-name">{item.name}</span>
                      <span className="project-card-desc">{item.description || "暂无项目描述"}</span>
                    </span>
                    <span className="project-card-foot">
                      <small className="project-card-time">
                        <Clock size={12} />
                        {formatDate(item.updated_at)}
                      </small>
                      <small className="project-status">
                        <span className="project-status-dot" />
                        {item.status === "active" ? "进行中" : item.status}
                      </small>
                    </span>
                  </button>
                ))}
              </div>
            ) : (
              <div className="empty-state">
                <span className="empty-state-art" aria-hidden="true">
                  <FolderKanban size={26} />
                </span>
                <strong>还没有项目</strong>
                <span>新建一个项目后，再进入项目设置、剧本、资产库和关键帧页面。</span>
                <button
                  className="projects-new-btn"
                  type="button"
                  onClick={openCreateProjectDialog}
                  disabled={isCreatingProject}
                >
                  <Plus size={16} />
                  {isCreatingProject ? "新建中…" : "新建项目"}
                </button>
              </div>
            )}
          </section>
        </main>
      ) : null}

      {isCreateProjectDialogOpen ? (
        <div
          className="create-project-overlay"
          onClick={(event) => event.target === event.currentTarget && closeCreateProjectDialog()}
        >
          <form className="create-project-dialog" onSubmit={createProject} onKeyDown={handleCreateProjectDialogKeyDown}>
            <div className="create-project-head">
              <div>
                <span className="projects-eyebrow">NEW PROJECT</span>
                <h2>新建项目</h2>
              </div>
              <button
                className="icon-btn"
                type="button"
                onClick={closeCreateProjectDialog}
                disabled={isCreatingProject}
                aria-label="关闭新建项目弹框"
              >
                <X size={16} />
              </button>
            </div>
            <label className="create-project-field">
              <span>项目名字</span>
              <input
                autoFocus
                maxLength={120}
                placeholder="例如：雨夜追踪短片"
                value={newProjectName}
                onChange={(event) => setNewProjectName(event.target.value)}
              />
            </label>
            <div className="create-project-actions">
              <button type="button" onClick={closeCreateProjectDialog} disabled={isCreatingProject}>
                取消
              </button>
              <button className="primary-action" type="submit" disabled={isCreatingProject || !newProjectName.trim()}>
                <Plus size={16} />
                {isCreatingProject ? "新建中…" : "创建项目"}
              </button>
            </div>
          </form>
        </div>
      ) : null}

      {activePage === "public-assets" ? (
        <main className={route.publicAssetId ? "public-assets-page public-assets-detail-shell" : "public-assets-page"}>
          {route.publicAssetId ? (
            <section className="public-asset-detail-page">
              <PublicAssetDetailView
                asset={publicAssetDetail}
                canDeleteSelectedImage={canDeleteSelectedPublicAssetImage}
                detailImageUrl={publicAssetDetailPreviewImageUrl}
                galleryFileInputRef={publicAssetGalleryFileInputRef}
                images={publicAssetDetailImages}
                isDeletingImage={isDeletingPublicAssetImage}
                isLoadingImages={isLoadingPublicAssetImages}
                isLoadingTasks={isLoadingPublicAssetGenerationTasks}
                isSubmittingGeneration={isSubmittingPublicAssetGeneration}
                isUploadingImages={isUploadingPublicAssetImages}
                onBack={navigateToPublicAssets}
                onDeleteImage={deleteSelectedPublicAssetImage}
                onGenerationPromptChange={setPublicAssetGenerationPrompt}
                onImageSelect={setSelectedPublicAssetImageIndex}
                onRefreshGenerationState={() => refreshPublicAssetGenerationState({ selectLatestGeneratedImage: true })}
                onSubmitGeneration={submitPublicAssetGeneration}
                onUploadImages={handlePublicAssetGalleryUpload}
                generationPrompt={publicAssetGenerationPrompt}
                generationTasks={publicAssetGenerationTasks}
                selectedImage={selectedPublicAssetImage}
                selectedImageIndex={selectedPublicAssetImageIndex}
              />
            </section>
          ) : (
            <section className="public-assets-library">
              <PanelHead title="公共资产库" subtitle="点击资产查看大图和详细信息">{null}</PanelHead>
              <div className="public-assets-body">
                <div className="public-assets-tools">
                  <input
                    placeholder="搜索公共资产"
                    value={publicAssetKeyword}
                    onChange={(event) => setPublicAssetKeyword(event.target.value)}
                  />
                  <div className="asset-filter">
                    {ASSET_TYPES.map((type) => (
                      <button
                        className={publicAssetFilter === type ? "active" : ""}
                        key={type}
                        type="button"
                        onClick={() => setPublicAssetFilter(type)}
                      >
                        {type}
                      </button>
                    ))}
                  </div>
                </div>
                {isLoadingPublicAssets ? (
                  <div className="empty-state">
                    <strong>正在加载公共资产</strong>
                    <span>公共素材正在同步。</span>
                  </div>
                ) : publicAssets.length ? (
                  <div className="public-assets-grid">
                    {publicAssets.map((asset) => (
                      <article className="public-library-card" key={asset.id}>
                        <button type="button" onClick={() => asset.id && navigateToPublicAssetDetail(asset.id)}>
                          <AssetThumb asset={asset} />
                          <span>
                            <strong>{asset.name}</strong>
                            <small>
                              {asset.type} · {asset.desc || "公共资产"}
                            </small>
                          </span>
                        </button>
                      </article>
                    ))}
                  </div>
                ) : (
                  <div className="empty-state">
                    <strong>还没有公共资产</strong>
                    <span>公共资产入库后，会在这里统一展示并支持导入项目。</span>
                  </div>
                )}
              </div>
            </section>
          )}
        </main>
      ) : null}

      {activePage === "project-settings" ? (
        <main className="route-page">
          <section className="project-settings">
            <PanelHead title="项目设置" subtitle="项目名称、描述和宽高比">
              <div className="top-actions">
                <button type="button" onClick={deleteCurrentProject} disabled={!currentProject}>
                  <Trash2 size={15} />
                  删除
                </button>
                <button type="button" onClick={saveProjectSettings} disabled={!currentProject}>
                  保存设置
                </button>
              </div>
            </PanelHead>
            <div className="project-settings-body">
              <div className="project-summary-strip">
                <div>
                  <span>当前项目</span>
                  <strong>{currentProject?.name ?? "未选择项目"}</strong>
                </div>
                <div>
                  <span>最后更新</span>
                  <strong>{currentProject ? formatDate(currentProject.updated_at) : "-"}</strong>
                </div>
                <div>
                  <span>默认比例</span>
                  <strong>{projectDraft.aspect_ratio}</strong>
                </div>
              </div>
              <Field label="项目名字">
                <input value={projectDraft.name} onChange={(event) => updateProjectDraft("name", event.target.value)} />
              </Field>
              <Field label="项目描述">
                <textarea value={projectDraft.description} onChange={(event) => updateProjectDraft("description", event.target.value)} />
              </Field>
              <Field label="图片宽高比">
                <select value={projectDraft.aspect_ratio} onChange={(event) => updateProjectDraft("aspect_ratio", event.target.value)}>
                  {ASPECT_RATIOS.map((ratio) => (
                    <option key={ratio}>{ratio}</option>
                  ))}
                </select>
              </Field>
            </div>
          </section>
        </main>
      ) : null}

      {activePage === "script" ? (
        <main className="script-page">
          <section className="script-editor">
            <PanelHead title="项目剧本" subtitle={script?.updated_at ? `最后更新：${formatDate(script.updated_at)}` : "只编辑剧本文本"}>
              <div className="top-actions">
                <button type="button" onClick={clearProjectScript} disabled={!currentProject || isSavingScript}>
                  <Trash2 size={15} />
                  清空
                </button>
                <button type="button" onClick={saveProjectScript} disabled={!currentProject || isSavingScript}>
                  <Save size={15} />
                  {isSavingScript ? "保存中" : "保存剧本"}
                </button>
              </div>
            </PanelHead>
            <div className="script-body">
              <Field label="剧本内容" meta={`${Array.from(scriptText).length} 字`}>
                <textarea
                  className="script-text"
                  placeholder="在这里写这个视频项目的剧本内容。可以包含故事梗概、分场、对白、人物行动和镜头意图。"
                  value={scriptText}
                  onChange={(event) => setScriptText(event.target.value)}
                />
              </Field>
            </div>
          </section>
        </main>
      ) : null}

      {activePage === "style" ? (
        <main className="route-page">
          <section className="style-settings">
            <PanelHead title="风格设置" subtitle="统一后续作图的画面风格和参考图">
              <div className="top-actions">
                <button
                  type="button"
                  onClick={() => {
                    updateProjectDraftValue("style_reference_image_file_id", null);
                    updateProjectDraftValue("style_reference_image_url", null);
                    updateProjectDraftValue("auto_apply_style_reference", false);
                    setStyleReferenceImages([]);
                  }}
                  disabled={!projectDraft.style_reference_image_file_id && styleReferenceImages.length === 0}
                >
                  <X size={15} />
                  清除参考图
                </button>
                <button type="button" onClick={saveProjectStyle} disabled={!currentProject}>
                  <Save size={15} />
                  保存风格
                </button>
              </div>
            </PanelHead>
            <div className="style-settings-body">
              <div className="style-canvas">
                <div
                  className={projectDraft.style_reference_image_url ? "style-reference-preview has-image" : "style-reference-preview"}
                  style={styleReferencePreviewStyle}
                >
                  <span>{projectDraft.style_reference_image_url ? "风格参考图" : "未添加参考图，将使用文生图"}</span>
                </div>
                <div className="style-apply-summary">
                  <div>
                    <span>生成方式</span>
                    <strong>{projectDraft.style_reference_image_url ? "图生图：参考已上传图片" : "文生图：仅使用提示词"}</strong>
                  </div>
                  <div>
                    <span>当前风格</span>
                    <strong>{projectDraft.style_prompt.trim() || "未填写风格提示词"}</strong>
                  </div>
                </div>
              </div>
              <div className="style-options">
                <label className="check-line">
                  <input
                    type="checkbox"
                    checked={projectDraft.auto_apply_style_prompt}
                    onChange={(event) => updateProjectDraftValue("auto_apply_style_prompt", event.target.checked)}
                  />
                  自动追加风格提示词
                </label>
                <label className="check-line">
                  <input
                    type="checkbox"
                    checked={projectDraft.auto_apply_style_reference}
                    onChange={(event) => updateProjectDraftValue("auto_apply_style_reference", event.target.checked)}
                  />
                  自动带入风格参考图
                </label>
              </div>
              <Field label="项目风格提示词">
                <textarea
                  className="style-prompt-text"
                  placeholder="这里写会保存到项目里的统一风格，例如：宫崎骏风格，柔和自然光，手绘动画质感。"
                  value={projectDraft.style_prompt}
                  onChange={(event) => updateProjectDraft("style_prompt", event.target.value)}
                />
              </Field>
              <section className="style-case-panel" aria-label="风格案例">
                <div className="style-case-head">
                  <div>
                    <strong>风格案例</strong>
                    <span>10 组可直接套用的风格图和提示词</span>
                  </div>
                  <span className="style-mode-pill">Imagegen</span>
                </div>
                <div className="style-case-grid">
                  {STYLE_CASES.map((styleCase) => (
                    <article className="style-case-card" key={styleCase.id}>
                      <button
                        className="style-case-image"
                        type="button"
                        onClick={() => applyStyleCase(styleCase)}
                        aria-label={`套用风格案例 ${styleCase.name}`}
                      >
                        <img src={styleCase.image} alt="" aria-hidden="true" />
                      </button>
                      <div className="style-case-body">
                        <div className="style-case-title">
                          <strong>{styleCase.name}</strong>
                          <button type="button" onClick={() => applyStyleCase(styleCase)}>
                            套用
                          </button>
                        </div>
                        <p>{styleCase.prompt}</p>
                      </div>
                    </article>
                  ))}
                </div>
              </section>
              <div className="style-submit-box">
                <div className="style-composer-main">
                  <div className="style-reference-stack" aria-label="风格参考图">
                    {styleReferenceCards.map((reference, index) => (
                      <div
                        className="style-reference-card"
                        key={reference?.id ?? "empty-reference"}
                        style={styleReferenceCardStyle(index, reference, "3 / 4")}
                      >
                        <button
                          className={reference ? "style-upload-card has-image" : "style-upload-card"}
                          type="button"
                          title={reference ? "更换参考图" : "上传参考图"}
                          onClick={() => {
                            styleUploadSlotRef.current = index;
                            if (styleFileInputRef.current) {
                              styleFileInputRef.current.value = "";
                              styleFileInputRef.current.click();
                            }
                          }}
                        >
                          {reference ? null : <Plus size={22} />}
                        </button>
                        {reference ? (
                          <button
                            className="style-reference-delete"
                            type="button"
                            title="删除参考图"
                            onClick={(event) => {
                              event.stopPropagation();
                              setStyleReferenceImages((items) => items.filter((item) => item.id !== reference.id));
                            }}
                          >
                            <X size={13} />
                          </button>
                        ) : null}
                      </div>
                    ))}
                  </div>
                  <div className="prompt-area">
                    <textarea
                      placeholder="只描述这次要生成或修改的风格参考图，不会保存为项目风格提示词。"
                      value={styleReferencePrompt}
                      onChange={(event) => setStyleReferencePrompt(event.target.value)}
                    />
                    <div className="style-composer-status">
                      <b>风格任务</b>
                      {styleGenerationStatus ? (
                        <span>{styleGenerationStatus}</span>
                      ) : !styleReferencePrompt.trim() ? (
                        <span>填写生成参考图的提示词后再提交</span>
                      ) : styleReferenceImageUrls.length ? (
                        <span>已添加 {styleReferenceImageUrls.length} 张参考图，将使用图生图方式</span>
                      ) : (
                        <span>未添加参考图，将使用文生图方式</span>
                      )}
                    </div>
                  </div>
                  <input
                    hidden
                    ref={styleFileInputRef}
                    type="file"
                    accept="image/*"
                    multiple
                    onChange={(event) => {
                      void handleStyleReferenceImages(event.currentTarget.files);
                      event.currentTarget.value = "";
                    }}
                  />
                </div>
                <div className="style-composer-footer">
                  <div className="style-composer-controls">
                    <span className="style-mode-pill">{styleReferenceImageUrls.length ? "图生图" : "文生图"}</span>
                    <span className="style-mode-pill">风格参考</span>
                  </div>
                  <div className="style-composer-submit">
                    <span className="count">{styleReferenceImageUrls.length} / 张</span>
                    <button
                      className={canSubmitStyleGeneration ? "send ready" : "send"}
                      disabled={isGeneratingStyleImage || !canSubmitStyleGeneration}
                      title="提交风格参考图生成任务"
                      type="button"
                      onClick={() =>
                        generateStyleReferenceImage(styleReferenceImageUrls.length ? "image_to_image" : "text_to_image")
                      }
                    >
                      {isGeneratingStyleImage ? <Bot size={22} /> : <ArrowUp size={24} />}
                    </button>
                  </div>
                </div>
              </div>
            </div>
          </section>
        </main>
      ) : null}

      {activePage === "assets" ? (
        <main className="asset-page">
          {!isAssetEditing ? (
            <section className="asset-main">
              <PanelHead title="项目资产库" subtitle="角色、场景、道具和其他参考素材">
                <div className="top-actions">
                  <div className="asset-filter">
                    {ASSET_TYPES.map((type) => (
                      <button
                        className={assetFilter === type ? "active" : ""}
                        key={type}
                        type="button"
                        onClick={() => setAssetFilter(type)}
                      >
                        {type}
                      </button>
                    ))}
                  </div>
                  <button type="button" onClick={createAsset}>
                    <Plus size={15} />
                    新建资产
                  </button>
                  <button type="button" onClick={openPublicAssetPicker}>
                    <Image size={15} />
                    公共库导入
                  </button>
                </div>
              </PanelHead>
              <div className="asset-list">
                {filteredAssets.length ? (
                  <div className="asset-grid" ref={assetGridRef}>
                    {assetMasonryColumns.map((column, columnIndex) => (
                      <div className="asset-masonry-column" key={`asset-column-${columnIndex}`}>
                        {column.map(({ asset, index }) => (
                          <article
                            className={[
                              "asset-card",
                              asset.image ? "has-asset-image" : "no-asset-image",
                              selectedAsset === index ? "active" : "",
                            ]
                              .filter(Boolean)
                              .join(" ")}
                            key={asset.id ?? `${asset.name}-${index}`}
                          >
                            <button className="asset-card-button" type="button" onClick={() => openAssetEditor(index)}>
                              <AssetThumb
                                asset={asset}
                                onImageRatioLoad={(ratio) => {
                                  setAssetImageRatioMap((items) =>
                                    items[assetRatioKey(asset)] === ratio ? items : { ...items, [assetRatioKey(asset)]: ratio },
                                  );
                                }}
                              />
                              <span className="asset-card-meta">
                                <strong>{asset.name}</strong>
                                <small>
                                  {asset.type} · {asset.desc}
                                </small>
                              </span>
                            </button>
                            {asset.id && currentProject ? (
                              <a
                                className="asset-detail-link"
                                href={assetDetailUrl(currentProject.id, asset.id)}
                                onClick={(event) => event.stopPropagation()}
                                title="打开资产详情独立链接"
                              >
                                <ExternalLink size={13} />
                                详情链接
                              </a>
                            ) : null}
                          </article>
                        ))}
                      </div>
                    ))}
                  </div>
                ) : (
                  <div className="empty-state">
                    <strong>还没有资产</strong>
                    <span>新建角色、场景或道具后，可以在关键帧提示词里复用这些素材。</span>
                    <button type="button" onClick={createAsset}>
                      <Plus size={15} />
                      新建资产
                    </button>
                  </div>
                )}
              </div>
            </section>
          ) : (
            <section className="asset-editor">
              <PanelHead title={`编辑资产：${assetDraft.name}`} subtitle="维护可复用参考图和描述">
                <div className="top-actions">
                  <button type="button" onClick={closeAssetEditor}>
                    返回列表
                  </button>
                  <button type="button" onClick={deleteAssetEditor} disabled={!assetDraft.id || isSavingAsset}>
                    <Trash2 size={15} />
                    删除
                  </button>
                  <button type="button" onClick={saveAssetEditor} disabled={isSavingAsset}>
                    <Save size={15} />
                    {isSavingAsset ? "保存中" : "保存资产"}
                  </button>
                </div>
              </PanelHead>
              <div className="editor-body">
                <div className="editor-preview">
                  <div
                    className={assetDraft.image ? "editor-art has-image" : "editor-art"}
                    style={assetVisualStyle(assetDraft)}
                  >
                    {assetDraft.name}
                  </div>
                  <button type="button" onClick={() => fileInputRef.current?.click()}>
                    <Upload size={15} />
                    替换图片
                  </button>
                  <input
                    hidden
                    ref={fileInputRef}
                    type="file"
                    accept="image/*"
                    onChange={(event) => {
                      void handleAssetImage(event.currentTarget.files?.[0]);
                      event.currentTarget.value = "";
                    }}
                  />
                </div>
                <div className="editor-form">
                  <div className="editor-row">
                    <Field label="资产名称">
                      <input value={assetDraft.name} onChange={(event) => setAssetDraft({ ...assetDraft, name: event.target.value })} />
                    </Field>
                    <Field label="资产类型">
                      <select
                        value={assetDraft.type}
                        onChange={(event) => setAssetDraft({ ...assetDraft, type: event.target.value as AssetItem["type"] })}
                      >
                        {ASSET_TYPES.filter((type) => type !== "全部").map((type) => (
                          <option key={type}>{type}</option>
                        ))}
                      </select>
                    </Field>
                  </div>
                  <Field label="资产描述">
                    <textarea value={assetDraft.desc} onChange={(event) => setAssetDraft({ ...assetDraft, desc: event.target.value })} />
                  </Field>
                  <Field label="默认提示词">
                    <textarea
                      value={assetDraft.prompt}
                      onChange={(event) => setAssetDraft({ ...assetDraft, prompt: event.target.value })}
                    />
                  </Field>
                  <Field label="标签">
                    <input value={assetDraft.tags} onChange={(event) => setAssetDraft({ ...assetDraft, tags: event.target.value })} />
                  </Field>
                </div>
              </div>
              <div className="style-submit-box asset-generation-box">
                <div className="style-composer-main asset-composer-main">
                  <div className="style-reference-stack asset-reference-stack" aria-label="资产参考图">
                    {[...assetReferenceImages, null].map((reference, index) => (
                      <div
                        className="style-reference-card asset-reference-card"
                        key={reference?.id ?? "empty-asset-reference"}
                        style={styleReferenceCardStyle(index, reference)}
                      >
                        <button
                          className={reference ? "style-upload-card has-image" : "style-upload-card"}
                          type="button"
                          title={reference ? "更换资产参考图" : "上传资产参考图"}
                          onClick={() => {
                            if (assetReferenceFileInputRef.current) {
                              assetReferenceFileInputRef.current.value = "";
                              assetReferenceFileInputRef.current.click();
                            }
                          }}
                        >
                          {reference ? null : <Plus size={22} />}
                        </button>
                        {reference ? (
                          <button
                            className="style-reference-delete"
                            type="button"
                            title="删除参考图"
                            onClick={(event) => {
                              event.stopPropagation();
                              setAssetReferenceImages((items) => items.filter((item) => item.id !== reference.id));
                            }}
                          >
                            <X size={13} />
                          </button>
                        ) : null}
                      </div>
                    ))}
                    <input
                      hidden
                      ref={assetReferenceFileInputRef}
                      type="file"
                      accept="image/*"
                      multiple
                      onChange={(event) => {
                        void handleAssetReferenceImages(event.currentTarget.files);
                        event.currentTarget.value = "";
                      }}
                    />
                  </div>
                  <div className="prompt-area">
                    <textarea
                      placeholder="上传参考图、输入文字，描述你想生成的资产图片。"
                      value={assetDraft.prompt}
                      onChange={(event) => setAssetDraft({ ...assetDraft, prompt: event.target.value })}
                    />
                    <div className="style-composer-status">
                      <b>资产任务</b>
                      {assetGenerationStatus ? (
                        <span>{assetGenerationStatus}</span>
                      ) : !assetDraft.id ? (
                        <span>先保存资产后再提交生成</span>
                      ) : !assetGenerationPrompt ? (
                        <span>填写文字或资产描述后生成</span>
                      ) : assetReferenceImageUrls.length ? (
                        <span>已添加 {assetReferenceImageUrls.length} 张参考图，将使用图生图方式</span>
                      ) : (
                        <span>未添加参考图，将使用文生图方式</span>
                      )}
                    </div>
                  </div>
                </div>
                <div className="style-composer-footer">
                  <div className="style-composer-controls">
                    <span className="style-mode-pill">{assetGenerationMode === "image_to_image" ? "图生图" : "文生图"}</span>
                    <span className="style-mode-pill">资产图片</span>
                  </div>
                  <div className="style-composer-submit">
                    <span className="count">{assetReferenceImageUrls.length} / 张</span>
                    <button
                      className={canSubmitAssetGeneration ? "send ready" : "send"}
                      disabled={isGeneratingAssetImage || !canSubmitAssetGeneration}
                      title="提交资产图片生成任务"
                      type="button"
                      onClick={() => generateAssetImage(assetGenerationMode)}
                    >
                      {isGeneratingAssetImage ? <Bot size={22} /> : <ArrowUp size={24} />}
                    </button>
                  </div>
                </div>
              </div>
            </section>
          )}
        </main>
      ) : null}

      {activePage === "workbench" ? (
        <main className="workspace">
          <section className="timeline">
            <div className="timeline-head">
              <div>
                <h1>图片帧时间轴</h1>
                <p>点选帧格，下面的大输入舱会把结果生成到这一帧。</p>
              </div>
              <div className="timeline-actions">
                <button type="button" onClick={fillDemo}>
                  填入示例
                </button>
              </div>
            </div>
            <div className="rail-wrap">
              <div className="rail">
                {frames.map((frame, index) => (
                  <FrameCard
                    active={selectedFrameId === frame.id}
                    frame={frame}
                    index={index}
                    key={frame.id}
                    onDelete={deleteFrame}
                    onDetail={() => {
                      setDetailIndex(detailIndex === index ? null : index);
                      selectFrame(index);
                    }}
                    onInsert={insertFrameAfter}
                    onSelect={selectFrame}
                    onVersion={(versionIndex) => {
                      void selectFrameVersion(index, versionIndex);
                    }}
                  />
                ))}
              </div>
            </div>
          </section>

          <section className="jimeng-box">
            <AssetPopover
              activePanel={assetPanel}
              frames={frames}
              onCreateAsset={createAsset}
              onToggleChip={toggleChip}
              onToggleFrame={toggleFrameReference}
              selectedChips={selectedChips}
              selectedFrameRefs={selectedFrameRefs}
            />

            <div className="input-row">
              <div className="prompt-area">
                <textarea
                  placeholder="输入文字，描述你想生成的图片。需要参考图时，从下方素材库选择。"
                  value={prompt}
                  onChange={(event) => {
                    setPrompt(event.target.value);
                    updateCurrentFrame((frame) => ({ ...frame, prompt: event.target.value }));
                    if (event.target.value.includes("@")) {
                      setAssetPanel("mention");
                    }
                  }}
                />
                <div className="selected-line">
                  <b>第 {selectedIndex + 1} 帧</b>
                  {selectedLabels.length ? (
                    selectedLabels.map((label) => (
                      <span className="pill-small" key={label}>
                        {label.split("，")[0]}
                      </span>
                    ))
                  ) : (
                    <span>可快速选择角色、场景、道具、镜头、运动，也可以输入 @ 调资产。</span>
                  )}
                </div>
              </div>
            </div>

            {generationError ? <div className="error-state">{generationError}</div> : null}

            <div className="toolbar">
              <div className="tool-left">
                <button
                  className="tool"
                  type="button"
                  onClick={() => {
                    setPrompt(`${prompt}${prompt && !prompt.endsWith(" ") ? " " : ""}@`);
                    setAssetPanel("mention");
                  }}
                >
                  @
                </button>
                {[
                  ["role", "角色"],
                  ["scene", "场景"],
                  ["prop", "道具"],
                  ["shot", "镜头"],
                  ["movement", "运动"],
                  ["projectFrames", "项目帧"],
                  ["other", "其他"],
                ].map(([panel, label]) => (
                  <button className="tool" key={panel} type="button" onClick={() => toggleAssetPanel(panel as Exclude<AssetPanel, null | "mention">)}>
                    {label}
                  </button>
                ))}
                <button className="tool blue" type="button" onClick={magicPrompt}>
                  <Sparkles size={16} />
                  润色
                </button>
              </div>
              <div className="tool-right">
                <span className="count">{generatedCount} / 张</span>
                <button
                  className={prompt.trim() || selectedLabels.length ? "send ready" : "send"}
                  disabled={isGenerating}
                  title="生成到当前帧"
                  type="button"
                  onClick={generateImage}
                >
                  {isGenerating ? <Bot size={22} /> : <ArrowUp size={24} />}
                </button>
              </div>
            </div>
          </section>

          {detailIndex !== null && frames[detailIndex] ? (
            <DetailModal
              frame={frames[detailIndex]}
              index={detailIndex}
              onClose={() => setDetailIndex(null)}
              onStoryChange={updateDetailStory}
            />
          ) : null}
        </main>
      ) : null}

      {isPublicAssetPickerOpen ? (
        <div className="public-asset-overlay" role="dialog" aria-modal="true" aria-label="公共资产库">
          <section className="public-asset-dialog">
            <div className="public-asset-head">
              <div>
                <h2>公共资产库</h2>
                <p>选择资产后会复制到当前项目资产库。</p>
              </div>
              <button type="button" className="icon-button" onClick={() => setIsPublicAssetPickerOpen(false)} title="关闭">
                <X size={16} />
              </button>
            </div>
            <div className="public-asset-toolbar">
              <input
                placeholder="搜索公共资产"
                value={publicAssetKeyword}
                onChange={(event) => setPublicAssetKeyword(event.target.value)}
              />
              <div className="asset-filter">
                {ASSET_TYPES.map((type) => (
                  <button
                    className={publicAssetFilter === type ? "active" : ""}
                    key={type}
                    type="button"
                    onClick={() => setPublicAssetFilter(type)}
                  >
                    {type}
                  </button>
                ))}
              </div>
            </div>
            <div className="public-asset-list">
              {isLoadingPublicAssets ? (
                <div className="empty-state">
                  <strong>正在加载公共资产</strong>
                  <span>稍等片刻，素材正在整理。</span>
                </div>
              ) : publicAssets.length ? (
                <div className="public-asset-grid">
                  {publicAssets.map((asset) => {
                    const selected = Boolean(asset.id && selectedPublicAssetIds.includes(asset.id));
                    return (
                      <button
                        className={selected ? "public-asset-card selected" : "public-asset-card"}
                        key={asset.id}
                        type="button"
                        onClick={() => togglePublicAssetSelection(asset.id)}
                      >
                        <AssetThumb asset={asset} />
                        <span>
                          <strong>{asset.name}</strong>
                          <small>
                            {asset.type} · {asset.desc || "公共资产"}
                          </small>
                        </span>
                      </button>
                    );
                  })}
                </div>
              ) : (
                <div className="empty-state">
                  <strong>没有匹配的公共资产</strong>
                  <span>换一个关键词或筛选类型再试。</span>
                </div>
              )}
            </div>
            <div className="public-asset-footer">
              <span>已选择 {selectedPublicAssetIds.length} 个</span>
              <button
                type="button"
                disabled={selectedPublicAssetIds.length === 0 || isImportingPublicAssets}
                onClick={importSelectedPublicAssets}
              >
                <Plus size={15} />
                {isImportingPublicAssets ? "导入中" : "导入到项目"}
              </button>
            </div>
          </section>
        </div>
      ) : null}

      <div className={toastText ? "toast show" : "toast"}>{toastText}</div>
    </div>
  );
}

function PublicAssetDetailView({
  asset,
  canDeleteSelectedImage,
  detailImageUrl,
  galleryFileInputRef,
  generationPrompt,
  generationTasks,
  images,
  isDeletingImage,
  isLoadingImages,
  isLoadingTasks,
  isSubmittingGeneration,
  isUploadingImages,
  onBack,
  onDeleteImage,
  onGenerationPromptChange,
  onImageSelect,
  onRefreshGenerationState,
  onSubmitGeneration,
  onUploadImages,
  selectedImage,
  selectedImageIndex,
}: {
  asset: AssetItem | null;
  canDeleteSelectedImage: boolean;
  detailImageUrl?: string;
  galleryFileInputRef: { current: HTMLInputElement | null };
  generationPrompt: string;
  generationTasks: GenerationTaskResult[];
  images: PublicAssetImage[];
  isDeletingImage: boolean;
  isLoadingImages: boolean;
  isLoadingTasks: boolean;
  isSubmittingGeneration: boolean;
  isUploadingImages: boolean;
  onBack: () => void;
  onDeleteImage: () => void;
  onGenerationPromptChange: (value: string) => void;
  onImageSelect: (index: number) => void;
  onRefreshGenerationState: () => void;
  onSubmitGeneration: () => void;
  onUploadImages: (files: FileList | null | undefined) => void;
  selectedImage: PublicAssetImage | null;
  selectedImageIndex: number;
}) {
  if (!asset) {
    return (
      <div className="public-asset-detail-loading">
        <strong>正在加载公共资产</strong>
      </div>
    );
  }

  const selectedImageTitle = selectedImage
    ? [selectedImage.title || roleLabel(selectedImage.role), selectedImage.angle].filter(Boolean).join(" · ") || "主图"
    : "主图";
  const selectedImageDescription = selectedImage?.description || asset.desc || "暂无描述";
  const selectedImagePrompt = selectedImage?.prompt || asset.prompt || "暂无提示词";
  const selectedImageTags = selectedImage?.tags.length ? selectedImage.tags.join(", ") : asset.tags || "暂无标签";
  const canSwitchImages = images.length > 1;
  const selectedPosition = images.length ? Math.min(selectedImageIndex + 1, images.length) : 0;
  const selectPreviousImage = () => {
    if (!canSwitchImages) {
      return;
    }
    onImageSelect((selectedImageIndex - 1 + images.length) % images.length);
  };
  const selectNextImage = () => {
    if (!canSwitchImages) {
      return;
    }
    onImageSelect((selectedImageIndex + 1) % images.length);
  };

  return (
    <section className="public-asset-detail-dialog public-asset-detail-route">
      <div className="public-asset-detail-preview-pane">
        <div className="public-asset-detail-preview">
          {detailImageUrl ? (
            <img src={detailImageUrl} alt={selectedImage?.title || asset.name} />
          ) : (
            <div className="public-asset-detail-empty">{asset.name}</div>
          )}
          {canSwitchImages ? (
            <>
              <button
                type="button"
                className="public-asset-image-nav previous"
                onClick={selectPreviousImage}
                aria-label="查看上一张图片"
              >
                <ChevronLeft size={18} />
              </button>
              <button
                type="button"
                className="public-asset-image-nav next"
                onClick={selectNextImage}
                aria-label="查看下一张图片"
              >
                <ChevronRight size={18} />
              </button>
            </>
          ) : null}
        </div>
        <div className="public-asset-preview-bar">
          <div>
            <strong>{selectedImageTitle}</strong>
            <span>
              {selectedPosition ? `${selectedPosition} / ${images.length}` : "暂无图集图片"}
              {selectedImage?.source_type === "generated" ? " · AI 生成" : ""}
            </span>
          </div>
          <div className="public-asset-gallery-actions">
            <input
              ref={galleryFileInputRef}
              type="file"
              accept="image/*"
              multiple
              hidden
              onChange={(event) => onUploadImages(event.target.files)}
            />
            <button type="button" onClick={() => galleryFileInputRef.current?.click()} disabled={isUploadingImages}>
              <Upload size={14} />
              {isUploadingImages ? "上传中" : "上传"}
            </button>
            <button
              type="button"
              onClick={onDeleteImage}
              disabled={!canDeleteSelectedImage || isDeletingImage}
              title={canDeleteSelectedImage ? "删除当前图集图片" : "主图兜底项不能在这里删除"}
            >
              <Trash2 size={14} />
              删除
            </button>
          </div>
        </div>
        <div className="public-asset-gallery-rail" aria-label="图集快速切换">
          {isLoadingImages ? (
            <p>正在加载图集...</p>
          ) : images.length ? (
            images.map((image, index) => (
              <button
                className={index === selectedImageIndex ? "active" : ""}
                key={image.id}
                type="button"
                onClick={() => onImageSelect(index)}
                title={image.title || image.role}
              >
                {image.image_url ? <img src={tosCompressedImageUrl(image.image_url)} alt="" /> : null}
                <span>{image.title || roleLabel(image.role)}</span>
              </button>
            ))
          ) : (
            <p>暂无图集图片</p>
          )}
        </div>
      </div>
      <div className="public-asset-detail-info">
        <div className="public-asset-detail-scroll">
          <div className="public-asset-detail-topbar">
            <button type="button" className="public-asset-back" onClick={onBack}>
              <ChevronLeft size={15} />
              返回公共库
            </button>
            <span className="style-mode-pill">{asset.type}</span>
          </div>
          <h2>{asset.name}</h2>
          {selectedImage ? (
            <div className="public-asset-detail-section">
              <strong>当前图片</strong>
              <p>{selectedImageTitle}</p>
              {selectedImage.created_by_name ? <p>制作人：{selectedImage.created_by_name}</p> : null}
            </div>
          ) : null}
          <div className="public-asset-detail-section">
            <strong>资产描述</strong>
            <p>{selectedImageDescription}</p>
          </div>
          <div className="public-asset-detail-section">
            <strong>默认提示词</strong>
            <p>{selectedImagePrompt}</p>
          </div>
          {selectedImage?.scene_prompt ? (
            <div className="public-asset-detail-section">
              <strong>场景提示词</strong>
              <p>{selectedImage.scene_prompt}</p>
            </div>
          ) : null}
          <div className="public-asset-detail-section">
            <strong>标签</strong>
            <p>{selectedImageTags}</p>
          </div>
          <div className="public-asset-detail-section">
            <div className="public-asset-section-head">
              <strong>生成任务</strong>
              <button className="public-asset-refresh-button" type="button" onClick={onRefreshGenerationState} disabled={isLoadingTasks}>
                {isLoadingTasks ? "刷新中" : "刷新"}
              </button>
            </div>
            <div className="public-asset-task-list">
              {generationTasks.length ? (
                generationTasks.map((task) => (
                  <div className="public-asset-task-item" key={task.task_id}>
                    <span>{generationTaskStatusLabel(task.status)}</span>
                    <strong>{task.target_payload?.title ? String(task.target_payload.title) : task.prompt}</strong>
                    {task.error_message ? <small>{task.error_message}</small> : null}
                  </div>
                ))
              ) : (
                <p>暂无生成任务</p>
              )}
            </div>
          </div>
        </div>
        <div className="public-asset-generate-box">
          <div className="public-asset-generate-meta">
            <strong>使用这个角色画图</strong>
            <span>{selectedImageTitle}</span>
          </div>
          <textarea
            placeholder="输入动作、角度、场景或画面要求，例如：雨夜公路上警戒前进，低机位电影光影"
            value={generationPrompt}
            onChange={(event) => onGenerationPromptChange(event.target.value)}
          />
          <button
            className="public-asset-generate-submit"
            type="button"
            disabled={!generationPrompt.trim() || isSubmittingGeneration}
            onClick={onSubmitGeneration}
          >
            <Sparkles size={15} />
            {isSubmittingGeneration ? "提交中" : "提交生成任务"}
          </button>
        </div>
      </div>
    </section>
  );
}

function AuthScreen({
  authDraft,
  authError,
  authMode,
  authSubmitting,
  onCheckBackend,
  onDraftChange,
  onModeChange,
  onSubmit,
  statusText,
}: {
  authDraft: AuthDraft;
  authError: string;
  authMode: AuthMode;
  authSubmitting: boolean;
  onCheckBackend: () => void;
  onDraftChange: (key: keyof AuthDraft, value: string) => void;
  onModeChange: (mode: AuthMode) => void;
  onSubmit: (event: FormEvent<HTMLFormElement>) => void;
  statusText: string;
}) {
  const isRegister = authMode === "register";

  return (
    <div className="app auth-app">
      <main className="auth-page">
        <section className="auth-card">
          <div className="auth-brand">
            <BrandMark />
            <div>
              <strong>图片关键帧生成工作台</strong>
              <span>{statusText}</span>
            </div>
          </div>

          <div className="auth-head">
            <h1>{isRegister ? "创建账号" : "登录账号"}</h1>
            <p>{isRegister ? "注册后即可保存项目、资产和关键帧版本。" : "登录后继续管理你的项目、剧本和关键帧。"}</p>
          </div>

          <div className="auth-switch" role="tablist" aria-label="账号操作">
            <button
              className={!isRegister ? "active" : ""}
              type="button"
              onClick={() => onModeChange("login")}
            >
              <KeyRound size={15} />
              登录
            </button>
            <button
              className={isRegister ? "active" : ""}
              type="button"
              onClick={() => onModeChange("register")}
            >
              <UserPlus size={15} />
              注册
            </button>
          </div>

          <form className="auth-form" onSubmit={onSubmit}>
            {isRegister ? (
              <>
                <Field label="邮箱">
                  <input
                    autoComplete="email"
                    placeholder="name@example.com"
                    type="email"
                    value={authDraft.email}
                    onChange={(event) => onDraftChange("email", event.target.value)}
                  />
                </Field>
                <Field label="用户名">
                  <input
                    autoComplete="username"
                    placeholder="letters, numbers, dots, dashes"
                    value={authDraft.username}
                    onChange={(event) => onDraftChange("username", event.target.value)}
                  />
                </Field>
                <Field label="显示名">
                  <input
                    autoComplete="name"
                    placeholder="可选"
                    value={authDraft.displayName}
                    onChange={(event) => onDraftChange("displayName", event.target.value)}
                  />
                </Field>
              </>
            ) : (
              <Field label="邮箱或用户名">
                <input
                  autoComplete="username"
                  placeholder="name@example.com"
                  value={authDraft.login}
                  onChange={(event) => onDraftChange("login", event.target.value)}
                />
              </Field>
            )}
            <Field label="密码">
              <input
                autoComplete={isRegister ? "new-password" : "current-password"}
                placeholder={isRegister ? "至少 8 位" : "输入密码"}
                type="password"
                value={authDraft.password}
                onChange={(event) => onDraftChange("password", event.target.value)}
              />
            </Field>

            {authError ? <div className="auth-error">{authError}</div> : null}

            <button className="auth-submit" type="submit" disabled={authSubmitting}>
              {isRegister ? <UserPlus size={16} /> : <KeyRound size={16} />}
              {authSubmitting ? "处理中..." : isRegister ? "注册并进入" : "登录并进入"}
            </button>
          </form>

          <button className="auth-health" type="button" onClick={onCheckBackend}>
            <Wifi size={15} />
            检查后端连接
          </button>
        </section>
      </main>
    </div>
  );
}

function PanelHead({ children, subtitle, title }: { children: React.ReactNode; subtitle: string; title: string }) {
  return (
    <div className="asset-panel-head">
      <div>
        <h2>{title}</h2>
        <span>{subtitle}</span>
      </div>
      {children}
    </div>
  );
}

function Field({ children, label, meta }: { children: React.ReactNode; label: string; meta?: React.ReactNode }) {
  return (
    <label className="editor-field">
      <span className="field-head">
        <span>{label}</span>
        {meta ? <span>{meta}</span> : null}
      </span>
      {children}
    </label>
  );
}

function FrameCard({
  active,
  frame,
  index,
  onDelete,
  onDetail,
  onInsert,
  onSelect,
  onVersion,
}: {
  active: boolean;
  frame: UiFrame;
  index: number;
  onDelete: (index: number) => void;
  onDetail: () => void;
  onInsert: (index: number) => void;
  onSelect: (index: number) => void;
  onVersion: (versionIndex: number) => void;
}) {
  const version = currentVersion(frame);
  const generated = Boolean(version);
  const text = generated ? version?.note : "点我，然后在下方生成";
  const desc = generated ? version?.prompt : "还没有画面描述。选中这一帧后，在下方输入框写这一帧要发生什么。";

  return (
    <>
      <article className={active ? "frame-card active" : "frame-card"} onClick={() => onSelect(index)}>
        <div className="frame-top">
          <span className="frame-no">{index + 1}</span>
          <div className="frame-meta">
            <span className="frame-duration">{frame.story.duration || "3 秒"}</span>
            <span className="frame-state">{generated ? `v${frame.currentVersion + 1}/${frame.versions.length}` : "空"}</span>
            <button
              className="delete-frame"
              title="删除这一帧"
              type="button"
              onClick={(event) => {
                event.stopPropagation();
                onDelete(index);
              }}
            >
              <Trash2 size={13} />
            </button>
          </div>
        </div>
        <div className={generated ? "thumb generated" : "thumb"} style={frameStyle(frame)}>
          {version?.image ? <img src={version.image} alt={`第 ${index + 1} 帧`} /> : <span>{text}</span>}
        </div>
        <div className="frame-title">
          <div className="frame-desc">{desc}</div>
          <button
            className="detail-toggle"
            type="button"
            onClick={(event) => {
              event.stopPropagation();
              onDetail();
            }}
          >
            详情
          </button>
          <div className="version-strip">
            {frame.versions.length ? (
              <>
                <button
                  className="version-step"
                  disabled={frame.currentVersion <= 0}
                  title="上一版"
                  type="button"
                  onClick={(event) => {
                    event.stopPropagation();
                    onVersion(Math.max(0, frame.currentVersion - 1));
                  }}
                >
                  <ChevronLeft size={13} />
                </button>
                {frame.versions.map((item, versionIndex) => (
                  <button
                    className={versionIndex === frame.currentVersion ? "version-btn active" : "version-btn"}
                    key={`${item.note}-${versionIndex}`}
                    type="button"
                    onClick={(event) => {
                      event.stopPropagation();
                      onVersion(versionIndex);
                    }}
                  >
                    v{versionIndex + 1}
                  </button>
                ))}
                <button
                  className="version-step"
                  disabled={frame.currentVersion >= frame.versions.length - 1}
                  title="下一版"
                  type="button"
                  onClick={(event) => {
                    event.stopPropagation();
                    onVersion(Math.min(frame.versions.length - 1, frame.currentVersion + 1));
                  }}
                >
                  <ChevronRight size={13} />
                </button>
              </>
            ) : (
              <span className="frame-state">暂无版本</span>
            )}
          </div>
        </div>
      </article>
      <div className="insert-slot">
        <button
          className="insert-btn"
          title="在这里插入一帧"
          type="button"
          onClick={(event) => {
            event.stopPropagation();
            onInsert(index);
          }}
        >
          <Plus size={15} />
        </button>
        <div className="insert-line" />
      </div>
    </>
  );
}

function AssetPopover({
  activePanel,
  frames,
  onCreateAsset,
  onToggleChip,
  onToggleFrame,
  selectedChips,
  selectedFrameRefs,
}: {
  activePanel: AssetPanel;
  frames: UiFrame[];
  onCreateAsset: () => void;
  onToggleChip: (group: keyof typeof QUICK_CHIPS | "style", value: string, label?: string) => void;
  onToggleFrame: (index: number) => void;
  selectedChips: Record<string, string[]>;
  selectedFrameRefs: number[];
}) {
  if (!activePanel) {
    return null;
  }
  const visibleGroups =
    activePanel === "mention"
      ? (["role", "scene", "prop", "shot", "movement", "projectFrames", "other"] as const)
      : ([activePanel] as const);

  return (
    <div className="asset-popover">
      {visibleGroups.includes("role") ? (
        <ChipRow group="role" label="角色" onToggleChip={onToggleChip} selectedChips={selectedChips} />
      ) : null}
      {visibleGroups.includes("scene") ? (
        <ChipRow group="scene" label="场景" onToggleChip={onToggleChip} selectedChips={selectedChips} />
      ) : null}
      {visibleGroups.includes("prop") ? (
        <ChipRow group="prop" label="道具" onToggleChip={onToggleChip} selectedChips={selectedChips} />
      ) : null}
      {visibleGroups.includes("projectFrames") ? (
        <div className="asset-row">
          <label>帧</label>
          <div className="frame-pick-list">
            {frames.map((frame, index) => {
              const version = currentVersion(frame);
              return (
                <button
                  className={selectedFrameRefs.includes(index) ? "frame-pick active" : "frame-pick"}
                  key={frame.id}
                  type="button"
                  onClick={() => onToggleFrame(index)}
                >
                  <div className="frame-pick-thumb" style={frameStyle(frame)} />
                  <strong>第 {index + 1} 帧</strong>
                  <small>{version ? version.note : "空白帧"}</small>
                </button>
              );
            })}
          </div>
        </div>
      ) : null}
      {visibleGroups.includes("shot") ? (
        <ChipRow group="shot" label="镜头" onToggleChip={onToggleChip} selectedChips={selectedChips} />
      ) : null}
      {visibleGroups.includes("movement") ? (
        <ChipRow group="movement" label="运动" onToggleChip={onToggleChip} selectedChips={selectedChips} />
      ) : null}
      {visibleGroups.includes("other") ? (
        <div className="asset-row">
          <label>其他</label>
          <div className="chips">
            {QUICK_CHIPS.other.map(([label, text]) => (
              <button
                className={(selectedChips.other ?? []).includes(text) ? "chip active" : "chip"}
                key={text}
                type="button"
                onClick={() => onToggleChip("other", text, label)}
              >
                {label}
              </button>
            ))}
            <button className="chip upload-chip" type="button" onClick={onCreateAsset}>
              + 新建资产
            </button>
          </div>
        </div>
      ) : null}
    </div>
  );
}

function ChipRow({
  group,
  label,
  onToggleChip,
  selectedChips,
}: {
  group: keyof typeof QUICK_CHIPS;
  label: string;
  onToggleChip: (group: keyof typeof QUICK_CHIPS, value: string, label?: string) => void;
  selectedChips: Record<string, string[]>;
}) {
  return (
    <div className="asset-row">
      <label>{label}</label>
      <div className="chips">
        {QUICK_CHIPS[group].map(([chipLabel, text]) => (
          <button
            className={(selectedChips[group] ?? []).includes(text) ? "chip active" : "chip"}
            key={text}
            type="button"
            onClick={() => onToggleChip(group, text, chipLabel)}
          >
            {chipLabel}
          </button>
        ))}
      </div>
    </div>
  );
}

function DetailModal({
  frame,
  index,
  onClose,
  onStoryChange,
}: {
  frame: UiFrame;
  index: number;
  onClose: () => void;
  onStoryChange: (index: number, key: keyof FrameStory, value: string) => void;
}) {
  const version = currentVersion(frame);
  const artText = version ? version.note : "还没有生成图片";

  return (
    <div className="detail-overlay" onClick={(event) => event.target === event.currentTarget && onClose()}>
      <section className="detail-modal">
        <div className="detail-head">
          <strong>第 {index + 1} 帧详情</strong>
          <button type="button" onClick={onClose}>
            <X size={15} />
            关闭
          </button>
        </div>
        <div className="detail-body">
          <div className="detail-preview">
            <div className="detail-art" style={frameStyle(frame)}>
              {version?.image ? <img src={version.image} alt={`第 ${index + 1} 帧详情`} /> : <span>{artText}</span>}
            </div>
          </div>
          <div className="detail-form">
            <Field label="概要描述">
              <textarea
                className="detail-editor"
                value={frame.story.summary}
                onChange={(event) => onStoryChange(index, "summary", event.target.value)}
              />
            </Field>
            <div className="detail-grid">
              {[
                ["duration", "时长", "3 秒"],
                ["people", "人物", "未记录"],
                ["dialogue", "对白", "无对白"],
                ["action", "动作", version ? version.prompt : "未记录"],
                ["emotion", "情绪", "未记录"],
                ["note", "备注", "无"],
              ].map(([key, label, fallback]) => (
                <Field key={key} label={label}>
                  <textarea
                    className="detail-value"
                    value={frame.story[key as keyof FrameStory] || fallback}
                    onChange={(event) => onStoryChange(index, key as keyof FrameStory, event.target.value)}
                  />
                </Field>
              ))}
            </div>
            <div className="detail-prompt">
              <b>生成提示词记录</b>
              <br />
              {version ? version.prompt : frame.prompt || "未生成"}
            </div>
          </div>
        </div>
      </section>
    </div>
  );
}

function AssetThumb({ asset, onImageRatioLoad }: { asset: AssetItem; onImageRatioLoad?: (ratio: number) => void }) {
  const imageUrl = asset.image ? tosCompressedImageUrl(asset.image) : undefined;
  return (
    <div
      className={asset.image ? "asset-thumb has-image" : "asset-thumb"}
      data-label={asset.name}
      style={assetThumbStyle(asset)}
    >
      {asset.image ? (
        <img
          alt=""
          className="asset-thumb-image"
          loading="lazy"
          src={imageUrl}
          onLoad={(event) => {
            const image = event.currentTarget;
            if (image.naturalWidth && image.naturalHeight) {
              onImageRatioLoad?.(image.naturalHeight / image.naturalWidth);
            }
          }}
        />
      ) : null}
    </div>
  );
}

function tosCompressedImageUrl(url: string, options: { width?: number; quality?: number } = {}) {
  if (!/^https?:\/\//i.test(url) || url.includes("x-tos-process=")) {
    return url;
  }
  const width = options.width ?? 520;
  const quality = options.quality ?? 72;
  const separator = url.includes("?") ? "&" : "?";
  return `${url}${separator}x-tos-process=image/resize,w_${width}/quality,q_${quality}/format,webp`;
}

function roleLabel(role: string) {
  const labels: Record<string, string> = {
    primary: "主图",
    front: "正面",
    left_45: "左 45 度",
    right_45: "右 45 度",
    side: "侧面",
    back: "背面",
    expression: "表情",
    pose: "动作",
    scene: "场景",
    reference: "参考",
    other: "其他",
  };
  return labels[role] ?? role;
}

function generationTaskStatusLabel(status: GenerationTaskResult["status"]) {
  const labels: Record<GenerationTaskResult["status"], string> = {
    queued: "排队中",
    running: "生成中",
    succeeded: "已完成",
    failed: "失败",
    canceled: "已取消",
  };
  return labels[status];
}

function buildAssetMasonryColumns<T extends { asset: AssetItem }>(
  items: T[],
  columnCount: number,
  imageRatioMap: Record<string, number>,
) {
  const columns = Array.from({ length: Math.min(Math.max(1, columnCount), Math.max(1, items.length)) }, () => [] as T[]);
  const columnHeights = columns.map(() => 0);

  items.forEach((item) => {
    const targetColumn = columnHeights.indexOf(Math.min(...columnHeights));
    columns[targetColumn].push(item);
    columnHeights[targetColumn] += estimatedAssetCardHeight(item.asset, imageRatioMap);
  });

  return columns;
}

function estimatedAssetCardHeight(asset: AssetItem, imageRatioMap: Record<string, number>) {
  const knownRatio = imageRatioMap[assetRatioKey(asset)];
  if (knownRatio) {
    return 220 * knownRatio;
  }
  const [width, height] = assetImageRatio(asset).split(":").map((value) => Number(value));
  return width && height ? 220 * (height / width) : 220;
}

function assetRatioKey(asset: AssetItem) {
  return asset.id ?? `${asset.name}-${asset.image ?? ""}`;
}

function createEmptyAsset(): AssetItem {
  return {
    name: "未命名资产",
    type: "角色",
    desc: "",
    prompt: "",
    tags: "",
    colors: ["#bfdbfe", "#fde68a", "#fecaca"],
  };
}

function createStory(prompt = ""): FrameStory {
  return {
    summary: "",
    duration: "3 秒",
    people: "",
    dialogue: "",
    action: prompt,
    emotion: "",
    note: "",
  };
}

function createEmptyFrame(): UiFrame {
  return {
    id: `frame-${Date.now()}-${Math.random().toString(16).slice(2)}`,
    prompt: "",
    story: createStory(),
    versions: [],
    currentVersion: 0,
  };
}

function createInitialFrames(): UiFrame[] {
  return [createEmptyFrame(), createEmptyFrame(), createEmptyFrame()];
}

function mapBackendAsset(asset: BackendAsset, image?: string): AssetItem {
  return {
    id: asset.id,
    imageFileId: asset.image_file_id,
    sortOrder: asset.sort_order,
    name: asset.name,
    type: normalizeAssetType(asset.type),
    desc: asset.description,
    prompt: asset.default_prompt,
    tags: asset.tags.join(","),
    colors: PALETTES[Math.abs(hashString(asset.id)) % PALETTES.length],
    image: image ?? asset.image_url ?? undefined,
  };
}

function mapPublicAsset(asset: PublicAsset): AssetItem {
  return {
    id: asset.id,
    imageFileId: asset.image_file_id,
    sortOrder: asset.sort_order,
    name: asset.name,
    type: normalizeAssetType(asset.type),
    desc: asset.description,
    prompt: asset.default_prompt,
    tags: asset.tags.join(","),
    colors: PALETTES[Math.abs(hashString(asset.id)) % PALETTES.length],
    image: asset.image_url ?? undefined,
  };
}

function isBackendAsset(value: unknown): value is BackendAsset {
  if (!value || typeof value !== "object") {
    return false;
  }
  const asset = value as Partial<BackendAsset>;
  return (
    typeof asset.id === "string" &&
    typeof asset.project_id === "string" &&
    typeof asset.name === "string" &&
    typeof asset.description === "string" &&
    typeof asset.default_prompt === "string" &&
    Array.isArray(asset.tags)
  );
}

function assetItemToPayload(asset: AssetItem) {
  return {
    name: asset.name.trim(),
    type: asset.type,
    description: asset.desc,
    default_prompt: asset.prompt,
    tags: asset.tags
      .split(",")
      .map((tag) => tag.trim())
      .filter(Boolean),
    image_file_id: asset.imageFileId ?? null,
    sort_order: asset.sortOrder ?? 0,
  };
}

function buildAssetGenerationPrompt(asset: AssetItem) {
  const prompt = asset.prompt.trim();
  if (prompt) {
    return prompt;
  }

  const name = asset.name.trim();
  if (!name) {
    return "";
  }

  return `${asset.type}，${name}`;
}

function assetImageType(asset: AssetItem): "character" | "scene" | "prop" | undefined {
  if (asset.type === "角色") {
    return "character";
  }
  if (asset.type === "场景") {
    return "scene";
  }
  if (asset.type === "道具") {
    return "prop";
  }
  return undefined;
}

function fileToDataUrl(file: File) {
  return new Promise<string>((resolve, reject) => {
    const reader = new FileReader();
    reader.onload = () => resolve(String(reader.result));
    reader.onerror = () => reject(new Error("读取图片失败"));
    reader.readAsDataURL(file);
  });
}

function normalizeAssetType(type: string): AssetItem["type"] {
  const typeMap: Record<string, AssetItem["type"]> = {
    role: "角色",
    character: "角色",
    scene: "场景",
    prop: "道具",
    other: "其他",
  };
  if (ASSET_TYPES.includes(type as AssetType) && type !== "全部") {
    return type as AssetItem["type"];
  }
  return typeMap[type] ?? "其他";
}

function hashString(value: string) {
  return [...value].reduce((hash, char) => (hash * 31 + char.charCodeAt(0)) | 0, 0);
}

function projectCoverStyle(id: string): CSSProperties {
  const theme = COVER_THEMES[Math.abs(hashString(id)) % COVER_THEMES.length];
  return {
    backgroundImage: theme.background,
    "--project-cover-accent": theme.accent,
  } as CSSProperties;
}

function mapBackendFrames(items: Frame[]): UiFrame[] {
  return items.map((item) => {
    const versions = (item.versions || []).map((version, index) => ({
      id: version.id,
      imageFileId: version.image_file_id,
      generationTaskId: version.generation_task_id,
      prompt: version.prompt,
      note: version.note || version.prompt.slice(0, 18),
      colors: PALETTES[(item.order_index + index) % PALETTES.length],
      image: version.image_url || undefined,
    }));
    const selectedVersionIndex = versions.findIndex((version) => version.id === item.selected_version_id);
    const fallbackVersions =
      versions.length || !item.current_prompt
        ? versions
        : [
            {
              prompt: item.current_prompt,
              note: item.summary || item.current_prompt.slice(0, 18),
              colors: PALETTES[item.order_index % PALETTES.length],
            },
          ];

    return {
      id: item.id,
      prompt: item.current_prompt || "",
      story: {
        summary: item.summary || "",
        duration: item.duration_ms ? `${Math.round(item.duration_ms / 1000)} 秒` : "3 秒",
        people: item.people || "",
        dialogue: item.dialogue || "",
        action: item.action || "",
        emotion: item.emotion || "",
        note: item.note || "",
      },
      versions: fallbackVersions,
      currentVersion: selectedVersionIndex >= 0 ? selectedVersionIndex : Math.max(0, fallbackVersions.length - 1),
    };
  });
}

function currentVersion(frame?: UiFrame) {
  if (!frame) {
    return null;
  }
  return frame.versions[frame.currentVersion] ?? null;
}

function frameStyle(frame: UiFrame): React.CSSProperties {
  const colors = currentVersion(frame)?.colors ?? ["#bfdbfe", "#fde68a", "#fecaca"];
  return {
    "--c1": colors[0],
    "--c2": colors[1],
    "--c3": colors[2],
  } as React.CSSProperties;
}

function assetVisualStyle(asset: AssetItem, aspectRatio?: string): React.CSSProperties {
  return {
    "--c1": asset.colors[0],
    "--c2": asset.colors[1],
    "--c3": asset.colors[2],
    "--asset-image-padding": assetImagePadding(asset),
    aspectRatio: aspectRatio ?? assetImageCssAspectRatio(asset),
    backgroundImage: asset.image ? `url(${asset.image})` : undefined,
  } as React.CSSProperties;
}

function assetThumbStyle(asset: AssetItem): React.CSSProperties {
  return {
    "--c1": asset.colors[0],
    "--c2": asset.colors[1],
    "--c3": asset.colors[2],
    "--asset-aspect-ratio": assetImageCssAspectRatio(asset),
    "--asset-image-padding": assetImagePadding(asset),
  } as React.CSSProperties;
}

function formatDate(value: string) {
  const date = new Date(value);
  if (Number.isNaN(date.getTime())) {
    return value;
  }
  return date.toLocaleString("zh-CN", { hour12: false });
}

function displayUserName(user: User) {
  return user.display_name || user.username || user.email;
}

async function loadOrCreateProjectScript(projectId: string) {
  try {
    return await loadProjectScript(projectId);
  } catch (error) {
    if (error instanceof Error && error.message.includes("Project script not found")) {
      return updateProjectScript(projectId, "");
    }
    throw error;
  }
}

function parseHashRoute(hash: string): AppRoute {
  const path = hash.replace(/^#/, "") || "/projects";
  const [, root, projectId, child, detailId] = path.split("/");
  if (root === "public-assets") {
    return {
      page: "public-assets",
      projectId: null,
      assetId: null,
      publicAssetId: projectId ? decodeURIComponent(projectId) : null,
    };
  }
  if (root !== "projects") {
    return { page: "projects", projectId: null, assetId: null, publicAssetId: null };
  }
  if (!projectId) {
    return { page: "projects", projectId: null, assetId: null, publicAssetId: null };
  }

  const pageBySegment: Record<string, ProjectPage> = {
    settings: "project-settings",
    script: "script",
    style: "style",
    assets: "assets",
    keyframes: "workbench",
  };

  return {
    page: pageBySegment[child || "settings"] ?? "project-settings",
    projectId,
    assetId: child === "assets" && detailId ? decodeURIComponent(detailId) : null,
    publicAssetId: null,
  };
}

function assetDetailHash(projectId: string, assetId: string) {
  return `/projects/${encodeURIComponent(projectId)}/assets/${encodeURIComponent(assetId)}`;
}

function assetDetailUrl(projectId: string, assetId: string) {
  return `${window.location.origin}${window.location.pathname}#${assetDetailHash(projectId, assetId)}`;
}

async function waitForGenerationTask(
  taskId: string,
  options: {
    intervalMs?: number;
    onPoll?: (task: GenerationTaskResult, elapsedSeconds: number) => void;
  } = {},
) {
  const intervalMs = options.intervalMs ?? 1000;
  const startedAt = Date.now();

  while (true) {
    const task = await loadGenerationTask(taskId);
    options.onPoll?.(task, Math.round((Date.now() - startedAt) / 1000));
    if (["succeeded", "failed", "canceled"].includes(task.status)) {
      return task;
    }
    await new Promise((resolve) => window.setTimeout(resolve, intervalMs));
  }
}
