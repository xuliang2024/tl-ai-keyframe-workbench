# 云资源记录

本文档记录本项目当前使用的云资源，方便后续排查、续费、迁移和部署。

## 火山引擎账号

- 账号 ID：`2110780953`
- DNS 托管域名：`51sut.com`
- DNS Zone ID：`169699`
- DNS NS：`vip1.volcengine-dns.com`、`vip2.volcengine-dns.com`

## 后端 API 服务器

后端服务器部署在阿里云广州，域名解析在火山 DNS。

| 项 | 值 |
| --- | --- |
| 域名 | `api.51sut.com` |
| 公网 IP | `8.134.236.241` |
| ECS 实例 ID | `i-7xvhfkjfnpv9cvtdvcjz` |
| 实例名称 | `tl-keyframe-backend-gz-0530-g91y` |
| 主机名 | `tl-backend-0530-g91y` |
| 地域/可用区 | `cn-guangzhou` / `cn-guangzhou-b` |
| 规格 | `ecs.c7a.xlarge`，4C/8G |
| 系统 | Ubuntu 24.04 |
| 内网 IP | `172.16.0.215` |
| EIP ID | `eip-7xvb2pubngja5t3rh14vc` |
| EIP 计费 | 按量付费，按流量，峰值带宽 200 Mbps |
| 安全组 | `sg-7xv11uu6afh9xppqcmf3`，开放 22/80/443 |
| SSH Key | `~/.ssh/task-worker-gz.pem` |

### Nginx 与 SSL

- Nginx 配置：`/etc/nginx/sites-available/api.51sut.com`
- 当前健康检查：`https://api.51sut.com/health`
- HTTPS 证书：Let's Encrypt，CN 为 `api.51sut.com`
- 服务器证书目录：
  - `/etc/letsencrypt/live/api.51sut.com/fullchain.pem`
  - `/etc/letsencrypt/live/api.51sut.com/privkey.pem`
- 本地签发备份目录：
  - `/tmp/certbot-51sut/config/live/api.51sut.com/fullchain.pem`
  - `/tmp/certbot-51sut/config/live/api.51sut.com/privkey.pem`
- 当前证书过期时间：`2026-08-28 05:30:23 GMT`

### DNS 记录

| Host | 类型 | 值 |
| --- | --- | --- |
| `api` | A | `8.134.236.241` |

## 静态站点 TOS + CDN

`www.51sut.com` 指向火山 CDN，CDN 回源到火山 TOS 桶。

| 项 | 值 |
| --- | --- |
| 访问域名 | `www.51sut.com` |
| TOS 桶 | `sut-www-51sut-com` |
| TOS 地域 | `cn-guangzhou` |
| TOS Endpoint | `tos-cn-guangzhou.volces.com` |
| TOS 源站域名 | `sut-www-51sut-com.tos-cn-guangzhou.volces.com` |
| CDN CNAME | `www.51sut.com.volcgslb.com` |
| CDN ServiceRegion | `chinese_mainland` |
| CDN ServiceType | `web` |
| CDN 状态 | `online` / `FullDeployed` |
| CDN 证书 ID | `cert-ecd57838d59941799373e438b4e8a0be` |
| CDN 刷新任务 | `refresh_url_050e79d055bc431f944893f962ef6fdb6084c94730dc89b0` |

### TOS 配置

- 桶 ACL：`public-read`
- 桶策略：允许公开读取对象，`tos:GetObject`，资源 `trn:tos:::sut-www-51sut-com/*`
- 静态网站首页：`index.html`
- 静态网站错误页：`index.html`
- 已上传验证对象：
  - `index.html`
  - `health.txt`

### CDN 配置

- CDN 回源协议：HTTP
- CDN 回源 Host：`sut-www-51sut-com.tos-cn-guangzhou.volces.com`
- CDN 回源改写：
  - `^/$` -> `/index.html`
- HTTPS：已开启
- HTTP2：当前未开启
- HTTP 强制跳转 HTTPS：当前未开启
- TLS：`tlsv1.1`、`tlsv1.2`、`tlsv1.3`

### SSL 证书

- HTTPS 证书：Let's Encrypt，CN 为 `www.51sut.com`
- 火山证书来源：`volc_cert_center`
- 本地签发目录：
  - `/tmp/certbot-51sut/config/live/www.51sut.com/fullchain.pem`
  - `/tmp/certbot-51sut/config/live/www.51sut.com/privkey.pem`
- 当前证书过期时间：`2026-08-28 05:54:52 GMT`

### DNS 记录

| Host | 类型 | 值 |
| --- | --- | --- |
| `www` | CNAME | `www.51sut.com.volcgslb.com` |
| `volccdnauth` | TXT | CDN 域名归属验证记录 |

## 生成资源 TOS + CDN

`cdn.51sut.com` 用于保存和访问生成图片、生成视频等媒体资源。业务上传时使用同一个 TOS 桶，通过不同对象前缀区分资源类型。

| 项 | 值 |
| --- | --- |
| 访问域名 | `cdn.51sut.com` |
| TOS 桶 | `sut-media-51sut-com` |
| TOS 地域 | `cn-guangzhou` |
| TOS Endpoint | `tos-cn-guangzhou.volces.com` |
| TOS 源站域名 | `sut-media-51sut-com.tos-cn-guangzhou.volces.com` |
| CDN CNAME | `cdn.51sut.com.volcgslb.com` |
| CDN ServiceRegion | `chinese_mainland` |
| CDN ServiceType | `download` |
| CDN 状态 | `online` / `FullDeployed` |
| CDN 证书 ID | `cert-ebb1ed4dc47e41acbcb6a854dfc6a1c9` |
| CDN 刷新任务 | `refresh_url_be403f67c93649548345298cf09ea6b3397abca0b1863875` |

### 资源桶配置

- 桶 ACL：`private`
- 桶策略：允许公开读取对象，`tos:GetObject`，资源 `trn:tos:::sut-media-51sut-com/*`
- 生成图片前缀：`generated/images/`
- 生成视频前缀：`generated/videos/`
- 已上传验证对象：
  - `health.txt`
  - `generated/images/.keep`
  - `generated/videos/.keep`
- 根路径访问：不列桶，返回 AccessDenied。

### 资源 CDN 配置

- CDN 回源协议：HTTP
- CDN 回源 Host：`sut-media-51sut-com.tos-cn-guangzhou.volces.com`

### 资源桶 CORS

浏览器使用后端签发的临时 `PUT` URL 直传 `sut-media-51sut-com`，媒体桶必须开启 CORS，否则前端上传会在预检请求阶段失败。

当前允许来源：

- `http://127.0.0.1:5174`
- `http://localhost:5174`
- `http://127.0.0.1:5173`
- `http://localhost:5173`
- `https://cdn.51sut.com`
- `https://www.51sut.com`

允许方法：`GET`、`PUT`、`POST`、`HEAD`；允许请求头：`*`；暴露响应头：`ETag`、`x-tos-request-id`、`x-tos-hash-crc64ecma`；`MaxAgeSeconds=3600`。
- HTTPS：已开启
- HTTP2：当前未开启
- HTTP 强制跳转 HTTPS：当前未开启
- TLS：`tlsv1.1`、`tlsv1.2`、`tlsv1.3`

### 资源 SSL 证书

- HTTPS 证书：Let's Encrypt，CN 为 `cdn.51sut.com`
- 火山证书来源：`volc_cert_center`
- 本地签发目录：
  - `/tmp/certbot-51sut/config/live/cdn.51sut.com/fullchain.pem`
  - `/tmp/certbot-51sut/config/live/cdn.51sut.com/privkey.pem`
- 当前证书过期时间：`2026-08-28 07:47:15 GMT`

### 资源 DNS 记录

| Host | 类型 | 值 |
| --- | --- | --- |
| `cdn` | CNAME | `cdn.51sut.com.volcgslb.com` |

## 当前验证地址

- `https://api.51sut.com/health`
- `https://www.51sut.com/`
- `https://www.51sut.com/health.txt`
- `https://cdn.51sut.com/health.txt`

## 环境变量

运行时域名和存储桶信息应放在 `.env` 中。示例见 `backend/.env.example` 和 `desktop/.env.example`。

```text
PUBLIC_API_BASE_URL=https://api.51sut.com
SITE_PUBLIC_BASE_URL=https://www.51sut.com
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
VITE_API_BASE_URL=https://api.51sut.com/api/v1
VITE_SITE_PUBLIC_BASE_URL=https://www.51sut.com
VITE_CDN_BASE_URL=https://cdn.51sut.com
```
