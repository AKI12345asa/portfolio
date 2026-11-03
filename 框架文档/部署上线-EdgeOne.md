# 部署上线：腾讯 EdgeOne Pages

> 目标：把本地 `http://localhost:4321` 变成一个别人能打开的网址。
> 为什么选 EdgeOne Pages：默认域名**免备案**、走国内边缘节点、和你已有的腾讯云账号同一套。
> 备选：Netlify（2026-10 实测国内 5/5 可达）。GitHub Pages 实测 16 次只成功 8 次，不推荐给国内观众。

---

## 前置状态（已完成）

- ✅ 项目已是 git 仓库，`main` 分支有初始提交，**已推送到 <https://github.com/AKI12345asa/portfolio>**
- ✅ `.env`（含密钥 + 视频签名链接）已被 `.gitignore` 忽略，**没有**推送上去
- ✅ `node_modules/` `dist/` `.tools/` `Demo录制/` 均未进仓库，仓库仅 3.68MB
- ✅ GitHub Pages 工作流已移出 `.github/workflows/`，模板留在 `框架文档/参考-github-pages-workflow.yml.txt`
- ✅ `npm run build` 通过，14 个页面
- ✅ 支持 `SITE_URL`、`VIDEO_BATTLE_URL`、`VIDEO_ARPG_URL` 三个环境变量

> **踩过的两个坑，记录下来避免以后重复：**
> 1. 第一版把 COS 签名链接写死在 `site.config.ts` 里，GitHub **密钥扫描直接拒绝推送**
>    （它把 URL 里的 `q-ak=AKID...` 识别成腾讯云 SecretId）。现已改为从环境变量读取。
> 2. 仓库 token 没有 `workflow` 权限时，GitHub 会拒绝推送 `.github/workflows/` 下的任何文件，
>    所以工作流模板挪到了 `框架文档/`。

---

## 第 1 步：在 GitHub 建仓库

1. 打开 <https://github.com/new>
2. **Repository name** 填 `portfolio`
   - 别用 `<用户名>.github.io`，那个名字是给 GitHub Pages 用的，我们不用了
3. **可见性**选一个：
   - `Public` —— 面试官能直接看代码和提交记录，求职更有利
   - `Private` —— 只给自己看，EdgeOne 也支持私有仓库
4. 下面三个选项 **全部不要勾**（Add README / .gitignore / license）——仓库必须是空的，否则第一次推送会冲突
5. 点 Create repository

---

## 第 2 步：推送本地代码

在项目根目录打开 PowerShell：

```powershell
git remote add origin https://github.com/你的用户名/portfolio.git
git push -u origin main
```

首次推送会弹出浏览器登录窗口，按提示完成即可。

**如果认证失败**，改用个人访问令牌（PAT）：

1. GitHub → 右上头像 → Settings → Developer settings → Personal access tokens → **Tokens (classic)** → Generate new token
2. 勾选 `repo` 权限，生成后复制
3. 改远程地址：
   ```powershell
   git remote set-url origin https://<把token粘这里>@github.com/你的用户名/portfolio.git
   git push -u origin main
   ```

> ⚠️ 带 token 的远程地址会明文存在 `.git/config` 里，不要把这个文件发给别人。用完可以改回普通地址。

---

## 第 3 步：EdgeOne Pages 建项目

1. 打开 <https://console.cloud.tencent.com/edgeone/pages>
2. **创建项目** → 连接 **GitHub** → 授权（第一次会跳 GitHub 授权页）
3. 选中刚才的 `portfolio` 仓库
4. 构建配置按这个填：

   | 配置项 | 填什么 |
   |---|---|
   | 框架预设 | `Astro`（没有就选 Other / 自定义） |
   | 构建命令 | `npm run build` |
   | 输出目录 | `dist` |
   | 安装命令 | 留空或 `npm ci`（`package-lock.json` 已提交） |
   | Node 版本 | 20 或更高 |

5. **环境变量**：先把两个视频变量填上（域名那个等部署完再说）

   | 名称 | 值从哪里来 |
   |---|---|
   | `VIDEO_BATTLE_URL` | 本地 `.env` 里 `VIDEO_BATTLE_URL=` 后面那一整行 |
   | `VIDEO_ARPG_URL` | 本地 `.env` 里 `VIDEO_ARPG_URL=` 后面那一整行 |

   > ⚠️ **这两项不填，线上首页会显示「视频待上传」**。因为签名链接含 SecretId，
   > 被 GitHub 密钥扫描拦截，只能放环境变量，不能写进代码。
   > 在本地执行下面这条命令可以直接打印出来复制：
   > ```powershell
   > Get-Content .env | Select-String '^VIDEO_'
   > ```

6. 点**部署**，等 1~3 分钟

---

## 第 4 步：拿到域名后回填

1. 复制部署成功后的域名，形如 `https://xxxxx.edgeone.site`
2. 回到 EdgeOne 项目 → 设置 → **环境变量**，再新增一项：

   | 名称 | 值 |
   |---|---|
   | `SITE_URL` | `https://xxxxx.edgeone.site` |

   > 这一步是让页面的 canonical、og:url、og:image 指向真实域名，而不是占位的 example.com。SEO 和分享卡片都靠它。

3. **重新部署**一次，让新变量生效
4. 把网址发我，我可以顺手确认 canonical 是否正确

---

## 验证清单

上线后按顺序过一遍，勾完就算完成：

- [ ] 首页能打开，样式和本地一致
- [ ] 「项目」区块两个**演示视频**点开能正常播放
- [ ] **用手机流量**（断开 Wi-Fi）打开，确认国内速度可接受
- [ ] 自研框架 10 个模块页都能点进去
- [ ] `/about/` 里简历按钮能下载 PDF
- [ ] 手机竖屏浏览首页不串版
- [ ] 分享到微信/QQ，链接卡片有标题和缩略图（依赖 `SITE_URL` 已设置）

---

## 常见问题

**构建失败，提示 `npm ci` 相关错误**
→ 检查 `package-lock.json` 是否在仓库里：`git ls-files package-lock.json`。已提交就没问题。

**构建成功但打开是白屏 / 404**
→ 输出目录填错了，必须是 `dist`。

**首页出现「视频待上传」而不是「演示视频」**
→ EdgeOne 没配 `VIDEO_BATTLE_URL` / `VIDEO_ARPG_URL`。值是空字符串时 `site.config.ts` 会退化成占位文案。
   去项目设置补上两个环境变量后重新部署。

**视频打不开，控制台报 403**
→ 签名链接过期了。重新生成，然后**同时**更新本地 `.env` 和 EdgeOne 的环境变量：
```powershell
.\视频工具.cmd sign --key works/arpg-demo.mp4   --days 365
.\视频工具.cmd sign --key works/battle-demo.mp4 --days 365
```

**推送被 GitHub 拒绝，提示 GH013 / secret scanning**
→ 有人又把 COS 签名链接写进代码了。签名 URL 里的 `q-ak=AKID...` 会被识别为腾讯云 SecretId。
   正确做法是放环境变量，永远不要提交进仓库。

**样式全丢，只有裸 HTML**
→ 我们部署在根路径，**不需要**设 `base`。如果有人建议加 `base`，那是 GitHub Pages 项目页的做法。

**想换域名**
→ 设 `SITE_URL` 环境变量即可，不用改代码。

---

## 成本

| 项目 | 费用 |
|---|---|
| EdgeOne Pages 静态托管 | 免费（含构建、HTTPS） |
| 免费流量 | 50GB/月 |
| 你的站点体积 | 0.9MB / 页均 < 700KB |
| 折算可承载访问 | 约 5 万次/月 |

视频不占用这里的流量——视频走腾讯云 COS，单独计费（见 [视频托管-COS配置.md](视频托管-COS配置.md)）。
