# FrameLab 图片生成要求

本文档定义 FrameLab 在通过 CLI、SDK、MCP 或 Agent 生成图片前必须读取和遵守的图片规范。

核心原则：

- 先判断图片类型，再写 prompt。
- 不同图片类型不能混用要求。
- 风格图不承担叙事，不表现具体主角。
- 角色、场景、道具先做资产设定图，再用于关键帧。
- 角色资产图和道具资产图默认使用纯色或低纹理背景，便于后续一致性引用。
- 关键帧图才表现剧情动作和镜头。

## 1. 风格参考图

用途：建立全项目统一视觉语言，用于色彩、材质、光线、摄影、世界观气质参考。

必须包含：

- 世界观环境气质，例如城市、室内、建筑、天气、光线。
- 色彩体系，例如霓虹青、品红、冷白、低饱和黑灰。
- 材质体系，例如湿沥青、玻璃幕墙、金属、全息投影、雾气。
- 摄影语言，例如电影感、宽银幕、体积光、浅雾、高反差。
- 2 到 4 个能代表世界观的视觉锚点，例如无人机、全息广告、AI 神像符号、数据塔。

禁止包含：

- 不要出现主角正脸或明确角色肖像。
- 不要出现多人群像作为主体。
- 不要做角色海报、人物立绘、战斗场面。
- 不要有文字排版、标题、logo、水印。
- 不要把风格图做成故事关键帧。

推荐构图：

- 16:9 横构图。
- 环境占 80% 以上。
- 可以有很小的人类剪影用于尺度参考，但不能识别为具体角色。
- 画面中心应是世界观空间、光线和材质，不是人物。

Prompt 模板：

```text
style reference image, no main character, no portrait, cinematic [题材] world, [时代/地点],
environment-focused composition, [核心空间], [天气/光线], [色彩体系],
[材质体系], [视觉锚点1], [视觉锚点2], [摄影语言],
wide establishing shot, production design reference, high detail, realistic film still,
no text, no logo, no poster layout, no character close-up
```

赛博朋克示例：

```text
style reference image, no main character, no portrait, cinematic cyberpunk sci-fi world,
2147 megacity under AI control, environment-focused composition, rainy elevated streets,
brutalist arcologies, wet asphalt, cyan and magenta neon reflections, holographic surveillance,
drone traffic, algorithmic temple-like data towers, volumetric fog, anamorphic wide shot,
production design reference, realistic film still, no text, no logo, no poster layout,
no character close-up
```

## 2. 角色设定图

用途：确定角色的脸、发型、服装、身体特征、气质和可复用视觉锚点。

角色图分两种，Agent 必须先判断用途：

- 角色资产图：用于资产库、后续一致性参考、图生图参考。默认使用纯色或低纹理背景。
- 角色氛围图：用于展示角色在世界观中的气质。可以使用低干扰场景背景。

FrameLab 默认生成“角色资产图”，除非用户明确要求角色氛围图。

必须包含：

- 单一角色为主体。
- 年龄段、体型、发型、五官气质。
- 服装层次、材质、颜色。
- 1 到 3 个不可变特征，例如义眼、神经接口、伤疤、徽章。
- 中性或轻微情绪，便于后续复用。

禁止包含：

- 不要表现复杂剧情动作。
- 不要被强烈阴影遮住脸。
- 不要和其他角色互动。
- 不要让背景抢主体。
- 不要多版本拼图，除非明确要求角色设计表。

角色资产图推荐构图：

- 半身或 3/4 身，角色占画面 55% 到 75%。
- 镜头略低或平视。
- 背景使用纯色、低纹理渐变或非常轻微的材质底。
- 背景颜色应服务角色轮廓识别，例如深灰、冷蓝灰、低饱和青黑，不建议刺眼纯白。
- 不要出现复杂场景、明显剧情、其他人物或抢主体的强光物件。
- 角色面部、服装和关键特征必须清晰。

角色资产图 Prompt 模板：

```text
character asset reference image, single character, [角色名], [身份/职业], [年龄/体型],
[发型/面部特征], [不可变特征], [服装材质和颜色], [性格气质],
three-quarter body or half body, clear face, clear costume details,
plain low-texture background, neutral studio lighting with cinematic color,
no extra characters, no action scene, no text, no logo
```

角色氛围图 Prompt 模板：

```text
character mood image, single character, [角色名], [身份/职业],
[不可变特征], [服装材质和颜色], standing in [低干扰世界观环境],
clear face and costume details, cinematic lighting, realistic film still,
environment supports character identity but does not dominate,
no extra characters, no complex action, no text, no logo
```

## 3. 场景设定图

用途：确定固定空间的结构、材质、光线、尺度和可重复使用的场景锚点。

必须包含：

- 空间名称和功能，例如地下记忆机房、城市中枢天井、第七码头。
- 空间结构，例如纵深、楼层、通道、桥、服务器阵列。
- 材质和光源。
- 2 到 5 个场景标志物，方便后续关键帧保持一致。
- 尺度参考，可以使用小人物剪影，但不要具体角色。

禁止包含：

- 不要做角色主导画面。
- 不要表现剧情高潮。
- 不要出现过多不可控杂物。
- 不要让空间结构模糊。

推荐构图：

- 16:9 横构图。
- 广角或中广角。
- 空间结构清楚，纵深明确。
- 角色只可作为尺度参考，占比不超过 10%。

Prompt 模板：

```text
environment design image, [场景名称], [空间功能], no main character,
wide establishing shot, clear spatial layout, [建筑/空间结构],
[材质], [光源], [天气/气氛], [标志物1], [标志物2], [标志物3],
scale reference silhouettes only, cinematic production design, high detail,
no character close-up, no text, no logo
```

## 4. 道具设定图

用途：确定可反复出现的关键物件外形、材质、比例、功能和细节。

必须包含：

- 单一道具为主体。
- 清晰轮廓和关键结构。
- 材质、颜色、发光部位、磨损程度。
- 尺度参考，例如手掌、桌面、影子，但不要抢主体。
- 功能暗示，例如接口、按钮、投影、数据槽。

禁止包含：

- 不要复杂背景或场景背景。
- 不要把道具做成角色或场景主图。
- 不要出现多种互相冲突的形态。
- 不要文字说明、UI 标注、爆炸图，除非明确要求设计板。

推荐构图：

- 3/4 视角产品图。
- 背景使用纯色、低纹理渐变或非常轻微的材质底。
- 背景颜色应帮助识别道具轮廓，例如深灰、冷蓝灰、低饱和青黑。
- 不要出现桌面杂物、场景道具堆、复杂灯牌或其他抢主体元素。
- 道具占画面 60% 到 80%。
- 细节清晰，边缘干净。

Prompt 模板：

```text
prop design image, single object, [道具名称], [用途],
three-quarter view, clear silhouette, [材质], [颜色], [发光/接口细节],
plain low-texture background, clean object reference,
high detail realistic product concept, no extra objects, no text, no logo
```

## 5. 关键帧图

用途：表现剧本中的具体镜头、动作、情绪和叙事节点。

必须包含：

- 镜头编号或剧情节点。
- 出现哪些角色，角色在画面中的位置关系。
- 具体动作和情绪。
- 场景位置。
- 镜头语言，例如远景、中景、特写、俯拍、低角度、推轨感。
- 与项目风格一致的光线、色彩和材质。

禁止包含：

- 不要做角色设定图。
- 不要做纯风格氛围图。
- 不要将多个时间点拼在同一张图。
- 不要出现多余主角或错误角色。
- 不要文字、字幕、logo、水印。

推荐构图：

- 16:9 横构图，除非项目设定为竖屏。
- 每张只表达一个清晰叙事瞬间。
- 主体、动作、环境三者都要可读。
- 保持电影截图感，不要海报感。

Prompt 模板：

```text
keyframe image, [镜头编号/剧情节点], [镜头类型],
[角色A] [动作/位置/情绪], [角色B/道具如有],
set in [场景], [环境细节], [光线和色彩],
cinematic film still, coherent single moment, high detail, realistic,
no text, no logo, no poster layout, no multiple panels
```

## 6. Agent 生成前检查清单

Agent 在调用图片生成前必须先完成：

1. 确认图片类型：风格、角色、场景、道具、关键帧。
2. 读取对应类型的要求和模板。
3. 检查禁止项，特别是风格图不能出现主角肖像。
4. 如果是关键帧，优先引用已生成的风格图、角色图、场景图或道具图。
5. 输出最终 prompt 前，确保它只服务于当前图片类型。

## 7. 质量通用负面约束

除非用户明确要求，否则所有图片都应追加：

```text
no low quality, no blurry subject, no bad anatomy, no extra limbs,
no distorted face, no unreadable clutter, no text, no watermark, no logo,
no cartoon, no anime, no poster typography
```
