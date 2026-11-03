---
title: 事件系统
summary: 主表是"字符串 key + 泛型多播"的事件中心，另有一套组件级的 int 键转发器。两套都在 GC 上做过优化。
highlight: 0~16 参定长重载 + 条目池化，高频派发稳态零分配
order: 8
stack: ['C#', 'ObjectPool']
files: 4
lines: 1540
---

## 两套体系

| 体系 | 键 | 用法 |
| --- | --- | --- |
| `EventSystem` / `EventModule` | 字符串 key | 全局事件：血量变化、金币变化、场景加载 |
| `EventListener` | int 键（`EventType` 枚举） | 组件级：挂在某个对象上，`OnDestroy` 自动解绑 |

框架层两者没有绑定，耦合都留在业务层。UI 窗口在 `Init()` 里订阅全局事件，逻辑层用 `EventSystem.EventTrigger("UpdatePlayerHp", …)` 派发。

## 派发路径上的分配

事件派发是每帧都在跑的高频路径。用 `params object[]` 传参时，每次派发要分配一个数组，值类型还要装箱，一分钟几万次下来 GC 压力很直接。

这套系统在三处把分配压掉：0 到 16 个参数各写一个定长重载，绕开 `params` 的数组分配；形参走泛型，值类型不装箱；事件条目从对象池取用，订阅和退订都不产生垃圾。稳态下高频派发的分配为零。

## 核心类型

| 类型 | 职责 |
| --- | --- |
| `EventSystem` | 静态门面，对外的 Add/Remove/Trigger |
| `EventModule` | 实际存储：`Dictionary<string, IEventInfo>` |
| `EventListener` | 组件级转发器，按 int 键分发，自动回池 |
| `FrameEventExtend` | 把组件回调压成一行的扩展方法 |

## 在资源系统里的复用

事件系统在框架内部唯一的使用者是资源系统：

```csharp
// 借用 EventListener 的 OnDestroy 钩子，做 Addressables 的自动释放
```

一个本来只负责事件转发的组件被当成生命周期钩子用了。上一个模块里「实例销毁即自动释放」就是靠这条路径实现的。

## 已知问题

- `AddTypeEventListener<T>` / `TypeEventTrigger<T>` 用 `nameof(T)` 当 key。按 C# 规范，`nameof` 作用于类型参数返回的是字符串 `"T"`，所有类型事件会挤在同一个 key 上。这两个 API 目前不可用，正确写法是 `typeof(T).Name`。
- 同一个 key 换签名只能在运行期抛 `InvalidCastException`，没有编译期保护。
- `EventModule` 九参 `EventTrigger` 少了一个 `?.`，空委托时会 NRE。
- 退订只清委托不删 key，会残留空条目。
