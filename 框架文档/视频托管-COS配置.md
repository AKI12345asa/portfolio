# 视频托管配置：腾讯云 COS 私有桶 + 签名链接

> 目标：视频上传后**没有公开地址**，只有你生成的、带有效期的链接才能播放。
> 到期自动失效，桶权限一改就能全网切断。

---

## 原理先说清楚（30 秒）

普通网盘/公开桶是「有地址就能看」。私有桶是「没签名就看不了」：

```
你的站点 ──播放请求──▶ https://桶.cos.地域.myqcloud.com/works/arpg-demo.mp4?q-signature=...
                              ↑ 不带签名 → 403 Forbidden
                              ↑ 带有效签名 → 200 正常播放
```

签名由 SecretKey 算出来，**只有你能生成**，且带过期时间。所以：
- 链接泄露 → 最多泄漏到过期
- 想立刻切断 → 桶策略改成禁止，或换密钥

---

## 步骤 1：开通对象存储

登录 [腾讯云控制台](https://console.cloud.tencent.com/) → 搜索「对象存储」→ 点**开通**（免费，不预付费）。

> 账户需要实名认证。刚注册的话先在右上角「账号信息」完成个人实名。

---

## 步骤 2：创建存储桶

对象存储 → **存储桶列表** → **创建存储桶**，按下面填：

| 配置项 | 填什么 | 说明 |
|---|---|---|
| 名称 | `portfolio-video` + 你自己的后缀 | 全平台唯一，系统会自动加 `-125xxxxxxx` 的 APPID 后缀 |
| 所属地域 | **广州**（ap-guangzhou） | 离大陆观众近；已选就别改，改了要重传 |
| 访问权限 | **私有读写** ✅ | **这一步最关键，别选错** |
| 版本控制 | 关闭 | 省钱 |
| 服务端加密 | 不开启 | 否则播放要额外处理 |
| 日志存储 | 关闭 | 省钱 |

创建完，记下**完整桶名**（含 APPID），形如 `portfolio-video-1250000000`。

---

## 步骤 3：拿密钥

右上角头像 → **访问管理** → 左侧 **API 密钥管理** → **新建密钥**。

复制 **SecretId** 和 **SecretKey**（SecretKey 只显示一次）。

> ⚠️ 主账号密钥权限极大，能操作你名下所有云资源。
> 先跑通用主账号密钥没问题，但**别提交到 git**、别贴聊天里。
> 长期用建议建子账号，只授权 COS 权限（CAM → 用户 → 新建 → 关联策略 `QcloudCOSFullAccess`）。

---

## 步骤 4：填配置

把项目根目录的 `.env.example` 复制成 `.env`（`.gitignore` 已忽略 `.env`），填四项：

```ini
COS_SECRET_ID=（复制控制台里的 SecretId）
COS_SECRET_KEY=（复制控制台里的 SecretKey）
COS_REGION=ap-guangzhou
COS_BUCKET=portfolio-video-1250000000
```

---

## 步骤 5：验证配置

在项目根目录打开 PowerShell，运行：

```powershell
.\视频工具.cmd check
```

> `视频工具.cmd` 已经帮你配好 Python 路径和依赖目录，不用管环境变量。
> 想直接看所有命令：`.\视频工具.cmd --help`

期望输出：

```
✓ 配置正常
  存储桶 : portfolio-video-1250000000
  地域   : ap-guangzhou
  对象数 : 0（以下最多列 5 个）
  ✓ 私有性检查通过（匿名访问被拒绝 403）
```

**如果看到 `⚠ 警告：匿名访问似乎成功了`** → 回步骤 2 把桶权限改成「私有读写」，否则任何人都能直接访问。

---

## 步骤 6：上传视频

压缩好的文件在 `Demo录制/发布版/`：

```powershell
.\视频工具.cmd upload "Demo录制/发布版/arpg-web.mp4"   --key works/arpg-demo.mp4
.\视频工具.cmd upload "Demo录制/发布版/battle-web.mp4" --key works/battle-demo.mp4
```

对象键用小写英文（如 `works/arpg-demo.mp4`），避免 URL 编码问题。

---

## 步骤 7：生成链接，接到首页

```powershell
.\视频工具.cmd sign --key works/arpg-demo.mp4   --days 365
.\视频工具.cmd sign --key works/battle-demo.mp4 --days 365
```

把生成的两条 URL 填进 **`src/site.config.ts`** 的 `projects`：

```ts
projects: [
  { name: '战斗 Demo', label: '演示视频', url: 'https://...战斗视频的签名链接' },
  { name: 'ARPG 原型', label: '演示视频', url: 'https://...ARPG视频的签名链接' },
  { name: 'ColliderSystem', label: 'GitHub', url: 'https://github.com/...' },
],
```

`url` 留空会显示「视频待上传」。填上后首页变成可点的「演示视频」，点开在新标签页直接播放。

> ⚠️ 这个站点的视频入口在 `site.config.ts`，**不在** `src/content/works/` 的 markdown 里。
> works 那三个 md 目前没有被任何页面引用（没有 `/works/` 路由），改 frontmatter 是不生效的。

**验证链接是否真的可用：**

```powershell
.\视频工具.cmd verify --key works/arpg-demo.mp4 --days 365
```

期望 `✓ 链接有效 HTTP 206`。

> 别用 `--url` 传完整链接：签名 URL 里有 `&`，经 `cmd` 传参会当成命令分隔符把 URL 截断，必然 403。
> 用 `--key` 让脚本现签，绕开这个坑。

---

## 步骤 8：到期怎么办

当前签名是 **365 天**。到期后首页点开会 403，重新生成并替换 `src/site.config.ts` 里的两条 URL 即可：

```powershell
.\视频工具.cmd sign --key works/arpg-demo.mp4   --days 365
.\视频工具.cmd sign --key works/battle-demo.mp4 --days 365
```

嫌麻烦有三个选择：

1. **同一批链接刷新一次就行** —— 用同一个 `--days` 批量重跑
2. **改成长有效期**（如 `--days 365`）—— 省事但泄露窗口变长，作品集场景可以接受
3. **上自动续签** —— 加一个 Vercel 接口，前端播放前现签，链接不落盘。要的话告诉我

---

## 费用参考（按你这两个视频）

| 项目 | 单价 | 你的量 | 每月 |
|---|---|---|---|
| 标准存储 | 0.118 元/GB/月 | ≈0.35 GB | 0.04 元 |
| 外网下行流量 | 0.5 元/GB | 每次完整看完 ≈0.18 元 | 20 次观看 ≈3.5 元 |

存储费可以忽略，全部成本在流量。**账户余额留几块钱就能跑**，别欠费（欠费会停服）。

---

## 安全清单

- [ ] 桶权限是「私有读写」
- [ ] `.env` 没有被提交（`git status` 里看不到）
- [ ] 密钥没有出现在任何 markdown / 代码里
- [ ] 匿名访问返回 403（`check` 命令会自动验证）
- [ ] 签名链接有效期符合你的接受范围
