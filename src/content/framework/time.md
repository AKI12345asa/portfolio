---
title: 时间系统与基础层
summary: 把"时间"做成可插拔的容器：世界 × 局部两级缩放，顿帧和子弹时间不需要改任何业务代码。配套还有 MonoSystem 与音频层。
highlight: 时间缩放做成"容器 + 回调"，业务只认 GetDeltaTime
order: 10
diagram: /framework/time.svg
diagramCaption: 注册 → 每帧读取 → 修改与顿帧
stack: ['Unity', 'C#', 'Cinemachine']
files: 5
lines: 756
---

## 时间容器与 `Time.deltaTime`

动作游戏里，不同对象对时间的感受不一样：主角被顿帧时，UI 动画和背景音乐不能跟着停；Boss 放技能时，敌人的思考频率要降下来。这些用全局的 `Time.deltaTime` 都做不到，所以每个对象拿到的是自己的一份时间容器：

```csharp
_playTotalTime += _owner.timeScaleContainer.GetDeltaTime();
```

技能推进、动画播放都读这个值。想让谁变慢，改它的容器就行。

## 两级缩放

`GetTimeScale = 局部 × 全局`，是否乘全局由 `ImpactByWorldScale` 决定。全局管整个游戏的节奏，比如暂停、慢动作演出；局部管单个对象自己的节奏，比如受击顿帧。

这里没有多套独立时钟。全局只有一个 `WorldTimeScale`，两级系数挂在同一套时钟上，场景名只是把容器分桶存放。

## 顿帧的实现

`SetShutter(时长)` 起一个协程，把局部缩放临时压到很低，计时结束后恢复原值。因为所有表现都读 `GetDeltaTime`，顿一下的效果自动覆盖动画、技能、位移，不需要每个模块各写一遍。

## `MonoSystem` 与音频层

`MonoSystem` 用三个静态事件把全框架的 `Update` / `FixedUpdate` / `LateUpdate` 收拢到一个 `MonoBehaviour` 上，另外配一张按对象 key 管理的协程表。状态机、行为节点、技能因此不需要继承 MonoBehaviour，切换状态也不产生 GC。

`AudioSystem` 是纯门面，`AudioModule` 用乘法音量组（全局 × 分类）。BGM 独占一个 `AudioSource` 并配淡入淡出协程，音效走对象池里的播放器，播完自动回池。

## 读图要点

初始化时建立全局缩放，并给每个宿主创建容器，容器按场景分桶存放。业务每帧只做一件事，读 `GetDeltaTime()`，是否受全局影响由 `ImpactByWorldScale` 决定。改缩放（`SetTimeScale` / `SetShutter`）会触发 `WhenUpdateTimeScale` 回调，由业务自己决定哪些表现跟着变，属于推送模式。
