---
title: 技能编辑器
summary: 时间轴式技能编辑器：在一条帧轴上摆放动画、音效、特效、检测、相机事件，并在场景里直接预览播放。
highlight: 预览不复用运行时播放器，是独立的一条采样管线
order: 3
stack: ['UI Toolkit', 'EditorWindow', 'Odin']
files: 35
lines: 4914
---

## 编辑器要解决的问题

技能数据是"第几帧发生什么"，这种数据必须看着画面调。每次改完都进游戏、跑到指定位置、放一遍技能，一天调不了几个技能。

我把帧轴、事件面板、场景预览三样东西做进一个窗口：拖时间轴就能看到动画、听到音效、看到特效和相机变化。

## 四层结构

| 层 | 类型 | 负责 |
| --- | --- | --- |
| 行为层 | `SkillTrackBase` | 轨道的时间轴逻辑、增删条目、播放/暂停 |
| 外观层 | `SkillTrackStyleBase` | 轨道的 DOM 结构（Menu / Content 双树），与逻辑分离 |
| 条目层 | `TrackItemBase<T>` | 单条事件在时间轴上的位置、宽度、拖拽 |
| 面板层 | `SkillEventDataInspectorBase` | 选中条目后右侧的属性编辑 |

## 三个实现细节

全编辑器只有 `FrameUnitWidth` 一处把帧号换算成像素（默认 10px/帧），滚轮缩放改的也是这一个值。缩放、拖拽、吸附都从它取值，不会出现两处算法不一致堆出来的偏移。

事件面板复用了 Inspector：点中条目时把 `Selection.activeObject` 指向窗口自身，再用 `[CustomEditor(typeof(SkillEditorWindow))]` 接管面板绘制。这样不必为每种事件写一个 Editor，面板切换只是换一个 switch 分支。

预览播放走一条独立的采样管线，不复用运行时播放器：

- 帧号由 `EditorWindow.Update` 用 `DateTime.Now` 推进，不依赖游戏循环；
- 动画用 `AnimationClip.SampleAnimation` 直接采样姿态，不经过 Animator 状态机；
- 根运动靠临时打开 `applyRootMotion` 采样累加位移；
- 相机直接抢 Cinemachine 的 `Priority = 10000`，退出时还原快照；
- 预览角色是把真实预制体 `Instantiate` 后按白名单剥掉业务组件得到的空壳，只保留 `Animator`、`Skill_Player`、碰撞体这些挂点。

所以编辑器里能跑，不代表运行时逻辑跑了。这里只是表现预览，不做逻辑模拟。

## 扩展一种新事件

1. 数据类 + 容器，挂到 `SkillClip`（`[NonSerialized, OdinSerialize]` 这对特性必须成对，否则 Odin 不序列化）；
2. `XxxTrack : SkillTrackBase`，在 `Init` 里建轨道外观；
3. `XxxTrackItem : TrackItemBase<XxxTrack>`，处理拖拽与显示；
4. `XxxTrackItemStyle : SkillTrackItemStyleBase`，实例化 uxml；
5. `XxxEventInspector : SkillEventDataInspectorBase`，右侧面板；
6. 在 `InitTrack()` 和 `SkillEditorInspector.Show()` 的 switch 里各注册一处。

## 已知问题

- 缩放时会全量重建所有条目，事件多的技能会有明显卡顿；
- 用反射调 `UnityEditor.AudioUtil` 来试听音效，Unity 版本升级时可能失效；
- 相机事件轨道在停止播放时不复位相机优先级与姿态。
