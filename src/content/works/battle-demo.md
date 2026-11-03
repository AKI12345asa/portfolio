---
title: 战斗 Demo · 优先级抢占与帧事件技能
summary: 基于自研框架 MyFrame 重写的 ARPG 战斗原型。两套可插拔动作模块、9 个技能行为、锁定相机与 GOAP 敌人，重点解决「加一个新武器要改多少代码」。
year: '2025'
role: 独立开发
category: 玩法与战斗
stack: ['Unity', 'C#', 'MyFrame', 'Odin Inspector']
tags: ['3D', '战斗系统', 'GOAP']
cover: /covers/cover-01.svg
featured: true
order: 1
# ↓ 演示视频：首页入口在 src/site.config.ts 的 projects 里（地址来自 .env 的 VIDEO_BATTLE_URL）
# works 集合目前没有对应的详情页路由，下面这块配置暂不生效，先注释保留
# demo:
#   type: local
#   src: '见 .env 的 VIDEO_BATTLE_URL'
#   label: '战斗系统演示 · 04:39'
links:
  - label: GitHub · MyFrame
    url: https://github.com/AKI12345asa/MyFrame
---

## 项目背景

这是把早期 ARPG 原型里踩过的坑重写一遍的结果：同一套战斗玩法，换成基于 MyFrame 框架重新实现。

目标不是「再做一个战斗 Demo」，而是回答一个问题：**加一个新武器、新技能、新敌人，要改多少行代码？**

## 我做了什么

- 两套可插拔的动作模块（自由移动 / 剑盾），各自带状态机与优先级表
- 9 个技能行为：轻攻击、重攻击、跳劈、空中连段、盾反、闪避、冲撞…
- 锁定目标的选择与锁定相机
- GOAP 驱动的敌人 AI：4 个动作 + 4 个检查器
- 表现层处理器注册：6 个相机处理器 + 5 个检测处理器

## 关键实现

### 切状态其实是一次「优先级抢占申请」

大多数项目的状态切换是「先判断能不能切，再切」。这里换了个方向：**切状态本身就是一次抢占**——先向行为仲裁器申请，抢到了才真的切。

```csharp
public virtual bool TryChangeState(DemoPlayerState newState, float priority = -1f)
{
    priority = priority < 0 ? StatePriorityDic[newState] : priority;
    var handler = Owner.ExecuteBehaviour(priority: priority, behaviourID: newState.ToString());

    // 抢到了才算切换成功，抢不到就什么都不发生
    if (handler.State != PlayerBehaviourState.Working) return false;
    handler.SetBehaviourEnd();
    ChangeState(newState);
    return true;
}
```

优先级表写在动作模块里：`Dead 100 / BeHit 20 / OnAir 10 / Land 5 / Move 0.5 / Idle 0`。死亡能打断一切，受击能打断移动——这些都是数据，不是散落各处的 if。

仲裁本身用 `struct` 描述一次申请（动作 / 优先级 / 检查函数 / ID），handler 走对象池，所以这个高频操作几乎不产生 GC。

### 状态要能「夺回」自己的槽位

一个容易被忽略的问题：外部可以用不同的 behaviour 借进当前状态，如果它一直不结束，槽位就被占着了。所以状态每帧都在重新表达「我要占住这个位置」——当被低优先级行为占用时，凭自己的优先级把槽位抢回来，避免优先级反转。

这件事要做对，关键是让「同 ID 重入」直接命中快速通道（一次引用比较），而不是每次都走完整仲裁。

### 技能与输入解耦

按键只做一件事：`ReleaseSkill(KeyData)`。具体放出哪个技能，由配置决定。

```csharp
private void BindAttackKey(KeyData keyData)
{
    Owner.SkillBrain.ReleaseSkill(keyData);   // 键位 → 技能，映射在配置里
}
```

所以同一套输入代码能适配不同武器——换武器就是换一份配置。

### 表现层是注册制的

玩家和敌人在初始化时各自注册自己需要的处理器：

```csharp
SkillPlayer.RegisterDetectionEventProcessor(new AttackEventProcessor(this));
SkillPlayer.RegisterDetectionEventProcessor(new ImpulseEventProcessor(this));
SkillPlayer.RegisterDetectionEventProcessor(new StutterFrameProcessor(this));
```

同一份技能配置，在不同角色身上表现可以不同，因为「谁来响应这个事件」是注册进去的，不是写死在技能数据里的。

## 设计取舍

- **不做严格的 A\* 式规划**：战斗决策频率高、计划生命周期短，可解释性比全局最优更重要。
- **节点树不内置执行器**：框架只提供链路和编辑器，怎么执行由挂载方决定——在 ARPG 项目里，它被用来跑 NPC 对话。
- **动画不走 Animator Controller**：转场逻辑写在脚本里，方便打断点；片段和混合数据独立成配置资产，方便跨角色复用。
