---
title: 动画系统
summary: 用 Playable API 直接搭混合子图，绕开 Animator Controller 的连线与分层；过渡、混合参数、动画事件全部在脚本里完成。
highlight: 没有连线、没有参数面板，混合结构就是代码
order: 1
diagram: /framework/animation.svg
diagramCaption: 建图 → 过渡 → 每帧混合
stack: ['Playable API', 'AnimationMixerPlayable', 'AvatarMask', 'Odin']
files: 15
lines: 3789
---

## 用 Playable 手动编排

Animator Controller 做混合的方式是在可视化窗口里连线：每个状态、每条过渡、每组参数都手工连出来。混合维度一多（速度 × 方向 × 上下半身），连线与分层就会失控，改一个参数要排查它影响了哪几条过渡，加一种动作要重连一片。我把这部分工作从窗口搬进了代码，改用 Playable API 直接搭子图。

混合结构现在是代码里的子图，一个节点就是一段混合逻辑。想知道某个角色此刻怎么混的，读节点实现就够了，不用在窗口里顺藤摸瓜。

过渡也放在脚本内部实现和运行：主混合器两个端口权重互换、协程插值，都是普通 C# 代码，可以打断点、打日志、单独测。调试起来比在 Animator 里拖过渡省事得多。

动画片段与混合配置抽成了独立的 Config 资产。每个方向配哪个 clip、每个速度段配哪个混合树，都记在 `CharacterAnimationConfig` 这类资产上，多个角色可以直接复用同一份。Animator 的配置绑死在某个 `.controller` 上，换角色就得复制一份。

参数这条链路也省掉了。参数由脚本自己写、片段由脚本自己播，不存在"这个 float 谁在改、什么时候改"的排查成本。

代价是要写代码，换来的是可维护性和复用性。

## 两个配套能力

除了混合本身，控制器还承担两件事：把动画里打的事件统一分发出去，以及把多段播放串成一条链。

### 动画事件的统一分发

动画里打的事件（命中帧、脚步帧、特效帧）不需要每个角色挂一个 `OnAnimationEvent` 的 MonoBehaviour。控制器按名字统一分发：

```csharp
controller.AddAnimationEvent("Hit", (int hitIndex) => { /* 命中判定 */ });
controller.AddAnimationEvent("FootStep", (string surface) => { /* 音效 */ });
controller.RemoveAnimationEvent("Hit", handler);
```

内部接到 Unity 的 `AnimationEvent` 回调后，按 `eventName` 查表，再按参数类型分派给 `Action<float>` / `Action<int>` / `Action<bool>` / `Action<string>` / `Action<Object>` 五种重载。订阅与退订成对出现，不会漏；同一段动画被多个对象复用也不会互相打架。

### 用 AnimationChain 串联片段

连招、落地接跑、技能多段，这类"播完这段马上接下一段"的需求，自己写会变成一堆协程加计时判断。`AnimationChain` 把它压成三行：

```csharp
var chain = controller.CreateAnimationChain();   // 从池里取，无 GC
chain.AddNode(...).AddNode(...).AddNode(...);     // 单片段 / 方向 / 二维 / 二维外一维内 都能混搭
controller.PlayAnimationChain(chain);
```

控制器每帧在 `UpdateChain()` 里检查当前段是否播完，播完自动接下一段。段与段之间仍然走双端口过渡，所以视觉上是平滑的，不会硬切。链本身从对象池取，播完即回收。

## 读图要点

1. 建图只做一次：`PlayableGraph.Create` → `Mixer(3)` → `Output` → `Play`，之后所有切换只是换子图。
2. 首次播放不做过渡，直接占用 `fromPort` 并置权重 1，避免开场淡入。
3. 节点自建子图：每个 `AnimationNodeBase` 在 `ConnectToPlayableGraph` 里创建自己的 clip/mixer playable，对外只暴露接哪根线。所以新增一种混合方式不用改控制器。
4. 相位同步挂在 `MonoSystem` 上：实现 `ICanSyncNode` 的节点会 `AddUpdate(SyncPhase)`，按权重 0.08、时间 0.15s 防抖往 master 节点对齐，走路时两只脚不会各走各的。

## 核心类型

| 类型 | 职责 |
| --- | --- |
| `Animation_Controller` | 建图、双端口过渡、播放链、动画事件、根运动、节点回收 |
| `AnimationNodeBase` | 节点抽象基类：端口、接线、速度、入池 |
| `BlendAnimationNodeBase` | 混合节点基类，暴露相位同步钩子 |
| `TwoDimensionalBlendTreeNode` | 二维混合：三角重心坐标算权重 |
| `DirectionalLinearBlendTreeNode` | 速度层 × 转向参数的线性混合 |
| `UpperLowerMixerAnimationNode` | 上下半身分层（`AnimationLayerMixerPlayable` + `AvatarMask`） |
| `AnimationChain` | 连续播放链，节点可混搭，池化 |
| `CharacterAnimationConfig` | 按名索引的动画配置资产 |

## 扩展一种混合方式

1. 继承 `BlendAnimationNodeBase`，需要相位同步就再实现 `ICanSyncNode`；
2. 在 `ConnectToPlayableGraph` 里建自己的 mixer、接 clip；
3. 实现一个入口方法，把参数换算成各输入端口的权重；
4. 在 `Animation_Controller` 加一个 `PlayXxx`，首播走 `fromPort`，过渡走 `toPort` + `RenewNextNode`；
5. 配置侧继承 `FrameConfigBase`，在 `CharacterAnimationConfig` 里加一个字典项。

走完这五步，已有的混合方式一行都不用改。
