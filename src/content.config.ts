import { defineCollection, z } from 'astro:content';
import { glob } from 'astro/loaders';

/** 视频：B站 / YouTube / 本地 mp4 三选一 */
const videoSchema = z.object({
  type: z.enum(['bilibili', 'youtube', 'local']),
  /** B站填 BV 号，例如 BV1xx411c7mD */
  id: z.string().optional(),
  /** 本地视频填路径，例如 /videos/demo.mp4（文件放 public/videos/） */
  src: z.string().optional(),
  /** 视频封面图，不填就用作品封面 */
  poster: z.string().optional(),
  /** 视频上方的小标题，例如「战斗系统演示 01:32」 */
  label: z.string().optional(),
  /** 竖屏视频（手机游戏录屏）填 portrait */
  aspect: z.enum(['landscape', 'portrait']).optional(),
});

const works = defineCollection({
  loader: glob({ pattern: '**/*.md', base: './src/content/works' }),
  schema: z.object({
    /** 作品标题 */
    title: z.string(),
    /** 一句话简介，列表卡片上显示 */
    summary: z.string(),
    /** 年份或时间段，记得加引号写成 "2024" */
    year: z.coerce.string(),
    /** 你在项目里的角色 */
    role: z.string(),
    /** 作品大类，作品列表按它分组，例如「玩法与战斗」 */
    category: z.string(),
    /** 技术栈标签 */
    stack: z.array(z.string()).default([]),
    /** 更细的标签，用于筛选 */
    tags: z.array(z.string()).default([]),
    /** 封面图，放 public/covers/ 下，写 /covers/xxx.svg */
    cover: z.string().optional(),
    /** 是否在首页主推 */
    featured: z.boolean().default(false),
    /** 排序，数字越小越靠前 */
    order: z.number().default(99),
    /** 主演示视频 */
    demo: videoSchema.optional(),
    /** 更多视频片段 */
    clips: z.array(videoSchema).default([]),
    /** 图片画廊 */
    gallery: z
      .array(z.object({ src: z.string(), caption: z.string().optional() }))
      .default([]),
    /** 相关链接：GitHub 仓库、在线试玩、文章 … */
    links: z
      .array(z.object({ label: z.string(), url: z.string() }))
      .default([]),
    /** 隐藏草稿 */
    draft: z.boolean().default(false),
  }),
});

/** 框架模块：每个 .md 一个模块页 */
const framework = defineCollection({
  loader: glob({ pattern: '**/*.md', base: './src/content/framework' }),
  schema: z.object({
    /** 模块名 */
    title: z.string(),
    /** 一句话简介 */
    summary: z.string(),
    /** 卡片上的亮点短语 */
    highlight: z.string().optional(),
    /** 排序 */
    order: z.number().default(99),
    /** 工作流程图，放 public/framework/ 下 */
    diagram: z.string().optional(),
    /** 图注 */
    diagramCaption: z.string().optional(),
    /** 依赖 / 用到的技术 */
    stack: z.array(z.string()).default([]),
    /** 代码规模 */
    files: z.number().optional(),
    lines: z.number().optional(),
  }),
});

export const collections = { works, framework };
