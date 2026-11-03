---
title: ARPG 原型 · 完整游戏流程
summary: 从主菜单到存档返回的一整条流程：建角、场景加载、战斗、对话任务、背包商店、存档。重点是把每个系统都做成「加内容不用改代码」。
year: '2024'
role: 独立开发
category: 系统与流程
stack: ['Unity', 'C#', 'MyFrame']
tags: ['完整流程', '存档', '任务与对话']
cover: /covers/cover-02.svg
featured: true
order: 2
# ↓ 演示视频：首页入口在 src/site.config.ts 的 projects 里（地址来自 .env 的 VIDEO_ARPG_URL）
# works 集合目前没有对应的详情页路由，下面这块配置暂不生效，先注释保留
# demo:
#   type: local
#   src: '见 .env 的 VIDEO_ARPG_URL'
#   label: '完整流程演示 · 07:56'
---

## 项目背景

这是我第一个把所有系统串起来跑通的项目。难点不在某个单点技术，而在**怎么让它们彼此不打架**：存档要能存下所有系统、任务要知道物品有没有拿到、切场景不能让 NPC 记错状态。

## 跑通的流程

```
主菜单 → 建角（外观装配）→ 场景异步加载
   → 战斗 / 探索 → 与 NPC 对话接任务 → 完成任务领奖励
   → 背包 / 装备 / 商店 → 存档 → 返回主菜单
```

8 个场景之间用返回点衔接，切场景前自动存档。

## 关键实现

### 存档是「聚合」出来的，不是一个大类

存档系统只负责序列化，具体存什么由各模块自己决定：

```csharp
// 存档系统提供三个事件点，各业务模块自己挂上去
dataManager.OnGameDataCreated += () => { /* 新档初始化 */ };
dataManager.OnGameDataLoaded  += (data) => { /* 读档恢复自己那段 */ };
dataManager.OnGameDataSave    += (data) => { /* 保存自己那段 */ };
```

好处很直接：**新增一个需要存档的系统，不用改存档代码**。玩家、任务、NPC、商店各自管自己那份数据。

### 存档数据与运行时数据用两套模型

存档里只放 id 化的引用（`itemId / type / count / position`），运行时再映射回真正的资产引用。

```csharp
// 存档模型：只存能序列化的东西
class InventoryData_Save { int itemId; ItemType type; int count; Vector2 position; }
// 运行模型：持有资产引用
class InventoryData_Play { InventoryItemBase item; int count; Vector2 position; }
```

原因很实际：如果把 `ScriptableObject` 引用直接写进存档，资产改名或重新导入一次，所有存档就全废了。

### 任务参数是可以扩展的

任务不是写死的类型，而是「一组参数 + 比较符号 + 子任务链」：

| 参数类型 | 用在哪 |
| --- | --- |
| 数值 | 击杀数量、收集数量 |
| 敌人 | 击杀指定敌人 |
| 物品 | 收集指定物品 |

物品类参数每帧从背包同步进度，完成时扣除物品。任务分为「自动完成」和「回去交任务完成」两种，对话树里直接挂接取、完成、条件判断节点。

### UI 不主动问业务，而是业务告诉 UI

快捷栏每一格的内容、CD 遮罩、可用状态，都由技能自己在回调里决定：

```csharp
// UI 只是把格子交出去，技能决定显示成什么样
skillBehaviour.UpdateSkillSlot(slot);
```

这样 UI 层完全不需要认识技能系统，加一个新技能也不用动 UI 代码。

## 复盘

这套代码后来被拆开了：能复用的部分（动画、技能、资源、存档、UI 窗口、节点树）抽成了 MyFrame，业务部分重写成新的战斗 Demo。

写下这一句的时候才意识到，**当时觉得「写得挺乱」的部分，恰恰是最有价值的部分**——它逼我想清楚哪些属于框架、哪些属于业务。
