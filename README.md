# 个人作品集网站

游戏客户端开发方向的求职作品集。Astro 静态站点，内容用 Markdown 维护，构建产物是纯静态 HTML，可以部署到任何地方。

## 先跑起来

```bash
npm install          # 第一次
npm run dev          # 开发预览 http://localhost:4321
npm run build        # 构建到 dist/
npm run preview      # 预览构建结果
```

> 国内网络装依赖慢的话，用镜像：`npm install --registry=https://registry.npmmirror.com`

## 目录结构

```
.
├─ src/
│  ├─ site.config.ts        ← 名字、职位、邮箱、技能、经历，改这个文件
│  ├─ content/
│  │  ├─ works/             ← 每个作品一个 .md 文件，加作品就是加文件
│  │  └─ framework/         ← 框架模块，一个 .md 一个模块页
│  ├─ pages/
│  │  ├─ index.astro        首页
│  │  ├─ about.astro        关于
│  │  ├─ framework/         框架总览 + 模块详情
│  │  └─ works/
│  │     ├─ index.astro     作品列表
│  │     └─ [...slug].astro 作品详情模板
│  ├─ components/           顶栏、页脚、作品卡、视频播放器
│  ├─ layouts/BaseLayout    HTML 骨架、SEO、分享卡片
│  └─ styles/global.css     配色和全局样式（改这里整体换肤）
├─ public/
│  ├─ covers/               作品封面
│  ├─ videos/               本地视频（可选）
│  ├─ favicon.svg
│  ├─ og.png                微信/Twitter 分享卡片
│  └─ resume.pdf            ← 把简历放这里，顶栏会自动出现「简历」按钮
├─ scripts/                 封面生成、分享图生成
└─ 作品模板.md              ← 加新作品时复制这个文件
```

## 加一个作品（最常做的事）

1. 复制根目录的 `作品模板.md`，重命名成英文文件名，放进 `src/content/works/`
   - 例：`src/content/works/fps-controller.md`
   - **文件名就是网址**：`/works/fps-controller/`
2. 改 frontmatter（`---` 之间的部分）和正文
   - `category` 决定它归到哪个**大类**，作品列表页按大类分组显示
   - 建议大类保持稳定：玩法与战斗 / 系统与工具 / 性能优化 / 工程与工具链
3. 把封面图放进 `public/covers/`，frontmatter 里写 `/covers/你的图.jpg`
4. 存盘，页面自动刷新

### 视频有三种写法

**B 站（推荐，省流量）**

```yaml
demo:
  type: bilibili
  id: BV1xx411c7mD     # 视频地址里 BV 开头的那串
  label: 演示视频 · 02:14
```

**YouTube**

```yaml
demo:
  type: youtube
  id: dQw4w9WgXcQ       # watch?v= 后面那串
```

**本地视频**（放 `public/videos/`，建议 < 30MB，太大就用 B 站）

```yaml
demo:
  type: local
  src: /videos/demo.mp4
  label: 本地录屏
```

手机游戏竖屏录屏加一行 `aspect: portrait`，播放器会变成 9:16。

一个作品可以有多个视频：

```yaml
clips:
  - type: bilibili
    id: BV1xx411c7mD
    label: 技能编辑器
  - type: bilibili
    id: BV1yy411c7mE
    label: 战斗流程
```

## 改个人信息

全部在 `src/site.config.ts`：

- 名字、职位、一句话介绍、求职状态
- 邮箱、GitHub / B站 / 知乎链接
- 技能分组
- 工作经历
- 首页「关于」段落

改完重新 `npm run build`，分享卡片图也可以重新生成：

```bash
python scripts/make-og.py
```

（需要 Pillow；改了名字或职位才需要重新跑）

## 部署

> **当前线上地址**：<https://personalportfolioforcheck.netlify.app>
> Netlify 自动构建，`netlify.toml` 固定了构建命令（`npm run build`）和发布目录（`dist`）。
>
> ⚠️ `SITE_URL` 环境变量必须以 **`https://`** 开头且不带结尾斜杠，
> 否则 canonical、og:url、og:image 会写成 `http://`，微信分享卡片抓不到缩略图。

> **实测结论（2026-11）**：EdgeOne Pages 的平台默认域名 `xxx.edgeone.cool` 只提供 **3 小时限时预览**，
> 不带 `eo_token` 访问返回 401，**不能作为公网地址**。要长期访问必须绑自定义域名，
> 而本项目加速区域是「中国大陆可用区」（锁定不可改），绑域名必须 ICP 备案。
>
> **想当天上线 → 用 Netlify**（免费、有真正公网域名、免备案，实测国内 5/5 可达）。
> **想要国内节点速度 → 买域名 + 备案 + 绑 EdgeOne**（1~3 周）。
>
> 完整说明见 [框架文档/部署上线-EdgeOne.md](框架文档/部署上线-EdgeOne.md)。

### 方案 A：Netlify（推荐，最快拿到可用网址）

1. 推到 GitHub
2. netlify.com 用 GitHub 登录 → Add new site → Import an existing project → 选仓库
3. 构建命令 `npm run build`，发布目录 `dist`
4. 设置环境变量 `SITE_URL`、`VIDEO_BATTLE_URL`、`VIDEO_ARPG_URL`
5. 部署后拿到 `xxx.netlify.app`，可长期使用

### 方案 B：EdgeOne Pages（要备案域名才能真正公网访问）

1. 推到 GitHub
2. 到 <https://console.cloud.tencent.com/edgeone/pages> → 创建项目 → 连接仓库
3. 构建命令 `npm run build`，输出目录 `dist`
4. 部署后设置环境变量 `SITE_URL=https://你的域名`，再部署一次

### 方案 B：Netlify / Vercel

`*.netlify.app` / `*.vercel.app` 默认域名在国内不稳定（Vercel 的尤其受限），**建议绑定自己的域名**。Framework 会自动识别成 Astro。

### 方案 C：GitHub Pages

⚠️ 实测国内 16 次请求只成功 8 次，185.199 段链路被干扰，换 DNS 无解。只适合观众在海外的情况。

仓库名必须是 `<你的用户名>.github.io`，这样站点在根路径，不用改配置。

1. 推到 GitHub
2. Settings → Pages → Source 选 **GitHub Actions**
3. 工作流模板放在 `框架文档/参考-github-pages-workflow.yml.txt`，复制回 `.github/workflows/deploy.yml` 才会触发
   （为什么不放现成的：一是本项目改用 EdgeOne，二是仓库 token 没有 `workflow` 权限时 GitHub 会拒绝推送该目录下的文件）

如果仓库名不是 `用户名.github.io`（项目页），需要额外两步：

- `astro.config.mjs` 里 `site` 改成 `https://用户名.github.io`，`base` 改成 `'/仓库名'`
- 代码里写死的 `/works/`、`/covers/...` 这类绝对路径要加 `base` 前缀——这种情况告诉我，我批量改。

### 方案 D：自己的服务器

`npm run build` 之后把 `dist/` 整个丢到 nginx 的目录里就行。

## 加一个框架模块

框架区（`/framework/`）的内容在 `src/content/framework/` 下，一个 `.md` 一个模块页：

```yaml
---
title: 动画系统
summary: 一句话说清这个模块解决什么问题
highlight: 卡片上那句亮点
order: 1                    # 排序
diagram: /framework/animation.svg   # 工作流程图（可选）
diagramCaption: 建图 → 过渡 → 每帧混合
stack: ['Playable API', 'Odin']
files: 15
lines: 3789
---
```

- 工作流程图放 `public/framework/`，frontmatter 里写 `/framework/xxx.svg`
- 正文用普通 Markdown，站点会自动套用标题、表格、代码块样式
- 流程图是从 `框架文档/09-工作流程图.md` 渲染出来的，改完跑 `node scripts/render-flow.mjs` 重新导出，再把 SVG 复制到 `public/framework/`

## 换配色

整个站点是白底黑字，只用一个强调色。改 `src/styles/global.css` 顶部的 `:root`：

```css
--ink: #16161a;    /* 强调色：按钮、下划线、选中态。改成 #2f6feb 就是蓝色系 */
--fg:  #1b1b19;    /* 正文颜色 */
--line: #e7e7e4;   /* 分隔线 */
```

想整体变深色，把 `--bg` 改成深色、`--fg` 改成浅色即可，其余会自动跟着走。

## 辅助脚本

```bash
npm run covers     # 重新生成封面占位图（public/covers/*.svg）
npm run shots      # 跑一遍自检：桌面/手机整页截图 + 视频/菜单/横向溢出检查
```

`npm run shots` 需要先 `npm run preview` 或 `npm run dev` 起一个本地服务，截图会存到 `.shots/`。

## 注意

- `src/content/works/` 里的示例作品是**占位内容**，发布前记得替换或删掉
- 示例里的 B 站视频 ID 是假的，点了会报错，换成自己的 BV 号
- 简历 PDF 没放的时候，顶栏和页脚不会显示「简历」按钮（避免 404）
