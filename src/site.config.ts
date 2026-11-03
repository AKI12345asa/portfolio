/**
 * 全站基础信息 —— 想改名字、联系方式、技能标签，只改这个文件。
 */

export const site = {
  /** 站点标题（顶部 logo 与页脚） */
  name: 'Unity 作品集',
  /** 名字的英文/拼音，用作 logo 和页脚 */
  nameEn: 'UNITY PORTFOLIO',
  /** 职位标题 */
  role: 'Unity 客户端开发',
  /** 首页大标题下面的一句话，说清你做什么、擅长什么 */
  tagline:
    '在 Unity / C# 上做客户端。写过一套 10 个子系统的框架、两个 ARPG 原型，以及一套从零实现的碰撞检测系统。',
  /** 求职状态条：不要就设成 null */
  status: {
    available: true,
    text: '寻找 Unity 客户端开发实习机会',
  },
  /** 城市 / 可接受的工作方式 */
  location: '杭州',
  years: '2028 届 · 本科在读',

  /** 联系方式 */
  email: '2318460152@qq.com',
  /** 简历 PDF：把文件放进 public/ 目录，这里写文件名 */
  resume: '/resume.pdf',

  /** 社交链接，不要的删掉 */
  links: [
    { label: 'GitHub', url: 'https://github.com/AKI12345asa' },
    { label: 'MyFrame 仓库', url: 'https://github.com/AKI12345asa/MyFrame' },
    { label: 'ColliderSystem 仓库', url: 'https://github.com/AKI12345asa/ColliderSystem' },
  ],

  /** 自研框架仓库地址（首页框架卡片与框架页都会用它） */
  frameworkRepo: 'https://github.com/AKI12345asa/MyFrame',

  /**
   * 项目列表：只放名称与链接。url 留空则显示「视频待上传」
   *
   * 为什么视频地址不写死在这里：
   * 腾讯云 COS 的签名链接里带 SecretId（URL 里的 q-ak 参数），GitHub 的密钥扫描
   * 会把它判定为泄露并**直接拒绝推送**，所以地址改从环境变量读。
   *
   *   本地开发：写在项目根目录 .env（已被 .gitignore 忽略）
   *     VIDEO_BATTLE_URL=https://...battle-demo.mp4?q-signature=...
   *     VIDEO_ARPG_URL=https://...arpg-demo.mp4?q-signature=...
   *   线上部署：在 EdgeOne 项目设置 → 环境变量 里配同名两项
   *
   * 链接有有效期，过期后 403，重新生成：
   *   .\视频工具.cmd sign --key works/battle-demo.mp4 --days 365
   *   .\视频工具.cmd sign --key works/arpg-demo.mp4   --days 365
   */
  projects: [
    {
      name: '战斗 Demo',
      label: '演示视频',
      url: import.meta.env?.VIDEO_BATTLE_URL ?? '',
    },
    {
      name: 'ARPG 原型',
      label: '演示视频',
      url: import.meta.env?.VIDEO_ARPG_URL ?? '',
    },
    {
      name: 'ColliderSystem',
      label: 'GitHub',
      url: 'https://github.com/AKI12345asa/ColliderSystem',
    },
  ],

  /** 技能标签，分三组展示 */
  skills: [
    {
      group: '引擎与语言',
      items: ['Unity 2022 LTS', 'C#', 'C++', 'Odin Inspector', 'Addressables', 'Cinemachine', 'HybridCLR'],
    },
    {
      group: '玩法与系统',
      items: ['帧事件技能系统', '优先级抢占式行为仲裁', '状态机', 'GOAP', '节点树', '配置驱动'],
    },
    {
      group: '工程与优化',
      items: ['JobSystem / Burst', 'NativeContainer', '对象池', 'GC 与原生内存', '编辑器扩展', 'Git'],
    },
  ],

  /** 经历：教育背景 + 项目经历，时间从新到旧 */
  experience: [
    {
      period: '2024 — 2028',
      org: '杭州电子科技大学',
      role: '计算机科学与技术 · 本科',
      points: [
        '主修课程：数据结构与算法、软件工程、网页设计、线性代数',
        '英语 CET-6',
      ],
    },
    {
      period: '2024 — 至今',
      org: '个人项目',
      role: '独立开发',
      points: [
        'MyFrame：自研 Unity 游戏框架，10 个子系统，约 2.6 万行',
        'ARPG 原型与战斗 Demo：基于框架实现完整游戏流程与战斗玩法',
        'ColliderSystem：从零实现的凸体碰撞检测系统，跑在 JobSystem + Burst 上',
      ],
    },
  ],

  /** 首页「关于」段落，写成口语就行 */
  about: [
    '杭州电子科技大学计算机科学与技术专业，2028 届，英语 CET-6。',
    '方向是 Unity 客户端。上面那套框架是自己从零搭的，动画、技能、战斗、GOAP、节点树、对象池、UI、存档都在里面；为了搞清碰撞的底层，又用 JobSystem 和 Burst 写了一套凸体碰撞检测。',
  ],
} as const;

export type Site = typeof site;

/** 把关于段落里的 {{name}} 替换成真实名字 */
export const aboutParagraphs: readonly string[] = site.about.map((p) =>
  p.replaceAll('{{name}}', site.name)
);
