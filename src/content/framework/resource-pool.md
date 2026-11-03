---
title: 资源管理与对象池
summary: 两套池分工明确——Object 池管纯 C# 对象、GameObject 池管预制体实例；资源加载交给 Addressables，实例销毁即自动释放。
highlight: Object 池负责不产生 GC，GameObject 池负责不重复实例化
order: 6
diagram: /framework/resource-pool.svg
diagramCaption: 取用 → 回收 → 释放
stack: ['Addressables', 'C#']
files: 6
lines: 800
---

## 两套池的分工

这两套池解决的是两个不同的问题，经常被混为一谈。

| | `ObjectPoolModule` | `GameObjectPoolModule` |
| --- | --- | --- |
| 装什么 | 纯 C# 对象 | 预制体实例 |
| 解决什么 | **不产生 GC** | **不重复实例化** |
| 创建方式 | `new T()` 或自定义 `createFunc` | `Addressables.InstantiateAsync` |
| 销毁 | 归还后留在池里 | 回池时 `SetActive(false)` |
| 典型用途 | 状态实例、行为节点、事件条目、协程列表、动画链、GOAP 计划节点 | 子弹、特效、音效播放器、UI 窗口 |

## Object 池：避免托管分配

战斗里最高频的事情不是生成子弹，是生成一个对象来装这一次的数据：状态机切换时 new 一个状态实例，技能执行时 new 一个行为节点，事件派发时 new 一个条目，GOAP 规划时 new 一堆计划节点。这些东西每帧几百次，如果都 `new`，GC 很快就来了。

`ObjectPoolModule` 就是干这个的。用起来是两步：

```csharp
// 初始化（可以带创建函数，也可以要求 T : new()）
PoolSystem.InitObjectPool<List<Coroutine>>(
    "MonoSystem_Coroutines",
    defaultQuantity: 10,
    getAction: list => list.Clear(),
    pushAction: list => list.Clear());
```

```csharp
// 取 / 还
var list = ResSystem.GetOrNew<List<Coroutine>>("MonoSystem_Coroutines");
list.ObjectPushPool("MonoSystem_Coroutines");
```

`getAction` 与 `pushAction` 是做重置的钩子。上面那个协程列表在取出和归还时都 `Clear()`，因为列表里的残留数据比没有更危险。这类重置逻辑由池负责，业务方不用记得清。

`defaultQuantity` 让小池子在初始化时就备好对象，避免开局抖动；`maxCapacity` 限制池的膨胀，满了就直接丢弃。

池还可以重复初始化。同名池再次 `InitPoolData` 不会报错，而是更新配置并把数量补齐到 `defaultQuantity`，这样多个对象各自初始化自己会用到的池时不会互相覆盖。

这套池和资源毫无关系，不涉及加载、不涉及实例化、不涉及销毁，纯粹是别再 new 了。把它和 GameObject 池混在一起，反而会让职责变模糊。

## GameObject 池：复用预制体实例

预制体实例的创建成本高（实例化、挂组件、初始化），所以用完不销毁，`SetActive(false)` 收回池里，下次取出时重置 Transform 与组件状态。

取用逻辑是先查池、池空才加载：

```csharp
var go = ResSystem.InstantiateGameObject("Assets/Prefabs/Bullet.prefab");
```

池里有就出池，没有才走 `Addressables.InstantiateAsync`。

## 实例销毁时自动释放

Addressables 的实例如果忘记 `ReleaseInstance`，引用会一直挂着，资源永远卸不掉。传统写法要把 `AsyncOperationHandle` 一路传下去，很容易漏。

这里的做法是实例化之后给实例挂一个 `autoRelease` 监听，监听 `EventListener` 的 `OnDestroy`。对象被销毁的瞬间，引用自动释放。

```csharp
var go = ResSystem.InstantiateGameObject(path);
// 用完
Destroy(go);   // 引用自动释放，不需要记 handle
```

于是一个本来用于事件转发的组件被当成了生命周期钩子。这是整套框架里我最喜欢的一处借力。

## 读图要点

取用顺序是固定的：先查池，池空才走 Addressables，所以高频生成几乎没有加载开销。回池要重置 Transform、组件状态与 `SetActive(false)`，否则下次取出来是脏的；池满直接销毁，不无限增长。

释放有两条路径：显式 `UnloadInstance`，或实例被 Destroy 时的自动回调。
