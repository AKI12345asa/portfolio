---
title: UI 系统
summary: 一个特性写清窗口的全部信息——key、层级、资源地址、是否缓存、是否预初始化，反射建表，按层自动挂载。
highlight: 新增一个窗口 = 写一个类 + 打一个特性
order: 7
diagram: /framework/ui.svg
diagramCaption: 注册 → 打开 → 关闭
stack: ['UGUI', 'Addressables', 'Odin']
files: 6
lines: 303
---

## 声明即注册

窗口的全部配置都写在特性里，包括 key、层级、资源地址、是否缓存、是否预初始化：

```csharp
[UIWindowData("main-menu", ifCache: true, assetPath: "Assets/UI/MainMenu.prefab", layerNum: 2)]
public class MainMenuWindow : UIWindowBase { }
```

启动时 `FrameUtility` 反射扫描全程序集，把所有带这个特性的类收进 `Dictionary<string, UIWindowData>`，再存进 `MyFrameSetting` 资产。之后 `ShowWindow("main-menu")` 就能直接用，中间不需要手工维护配置表。新增一个窗口的工作量因此只剩写一个类、打一个特性，以及重新保存一次资产。

## 层级与遮罩

没有开多个 Canvas。所有窗口挂在同一个 Canvas 下的 `UILayout` 上，`UILayout` 的数组下标就是层级号，窗口在第几层由它挂在数组的哪个位置决定。

遮罩用的是同一层里的一张 Image。每次打开窗口，`UILayout.Update` 把这张 Image 的 `sibling index` 设为倒数第二，于是它挡住下面所有窗口，又不挡最新打开的那个。一个 Image 就满足了「弹窗要遮住底下的按钮」这一条需求，不必给每个窗口单独配遮罩。

## 读图要点

`ifCache` 与 `ifPreInit` 是两个正交开关，能表达四种组合：常驻后台、启动预建、用完即毁、懒加载。打开时先查缓存，命中就只做一次 `SetActive(true)` 并置顶，不重新实例化。关闭时按 `ifCache` 分流：保留的仅隐藏，不保留的走 `UnloadInstance` 释放实例并移出缓存。

## 核心类型

| 类型 | 职责 |
| --- | --- |
| `UISystem` | 窗口的开、关、缓存、层级管理 |
| `UIWindowDataAttribute` | 声明窗口的 key / 层级 / 地址 / 缓存 / 预初始化 |
| `UIWindowBase` | 窗口基类，提供生命周期回调 |
| `UILayout` | 一层 UI，负责遮罩与排序 |

## 已知问题

- 运行时不会重新扫描特性，窗口表来自资产里已序列化的字典。新增窗口后必须在编辑器里保存一次资产，否则打包后 `ShowWindow` 会抛「没有注册过」。
- `ShowWindow<T>` 用 `typeof(T).Name` 查表，而特性注册时用的是 `FullName`，两者对不上，按类型开窗会失败。
- 关闭窗口时不会回对象池，`assetPath` 当作池名的那条分支实际很少命中。
