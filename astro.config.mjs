import { defineConfig } from 'astro/config';

// 部署到 Vercel / Netlify / EdgeOne Pages：不需要改代码
//   域名通过环境变量 SITE_URL 提供，例如 https://xxx.edgeone.site
//   不设置时会退化成占位域名，canonical 和 og:image 会指向 example.com
// 部署到 GitHub Pages 项目页（https://用户名.github.io/仓库名/）：
//   site 改成 'https://用户名.github.io'，并加 base: '/仓库名'
const SITE_URL = process.env.SITE_URL || 'https://example.com';

export default defineConfig({
  site: SITE_URL,
  // 本地预览时不显示 Astro 开发工具栏（截图和给别人看都干净）
  devToolbar: { enabled: false },
  build: {
    format: 'directory',
  },
  markdown: {
    shikiConfig: {
      theme: 'github-light',
      wrap: true,
    },
  },
});
