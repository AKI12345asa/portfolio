---
title: ColliderSystem · 从零实现的凸体碰撞检测
summary: 不依赖 Unity 内置物理，自己写粗筛、精算、求解与事件四段管线：GJK / EPA + Morton 码 LBVH，全流程跑在 JobSystem + Burst 上。
year: '2025'
role: 独立开发
category: 底层与性能
stack: ['Unity', 'C#', 'JobSystem', 'Burst', 'NativeContainer']
tags: ['3D', '物理', '性能优化']
cover: /covers/cover-03.svg
featured: true
order: 3
# ↓ 演示视频：做好后把下面几行的注释去掉
# demo:
#   type: bilibili
#   id: BV1xx411c7mD
#   label: 碰撞系统演示 · 02:30
links:
  - label: GitHub · ColliderSystem
    url: https://github.com/AKI12345asa/ColliderSystem
---

## 项目背景

用 Unity 内置物理做碰撞是最省事的选择。想做这个，是因为一直没搞明白「两个物体碰上了」这句话底下到底发生了什么。

所以从零写了一遍：从「怎么快速排除不可能相撞的物体」到「怎么算出把它们分开需要推多远」。

## 管线四段

```
① 实体收集   ColliderDic → 按类型拆到 4 个 NativeArray（Box / Sphere / Capsule / Mesh）
       │
② 粗筛       Mesh 本地 BVH（引用计数缓存）+ 顶层 Morton 码 LBVH
       │         → 候选碰撞对（NativeStream）
       │
③ 精算       GJK 判交 → EPA 求穿透深度
       │
④ 求解/事件   MTV 按逆质量加权 → 并行回写 Transform
              双缓冲 HashSet 对比前后两帧 → Trigger 的 Enter / Stay / Exit
```

## 关键实现

### 粗筛用 Morton 码排序建树

朴素做法是每次按轴对半分裂，递归建树。这里换了个思路：把物体的世界坐标映射到格子、算 Morton 编码，**排一次序**，然后自底向上合并成树。

好处是整个过程天然适合并行，而且相邻的物体在数组里也相邻，缓存友好。

### 精算不需要解方程

GJK 只做一件事：用**支撑函数**（往某个方向找最远的点）在 Minkowski 差上迭代，看能不能把原点包进单纯形里。

```csharp
// 不用求交、不用解方程，只要"往这个方向最远的点在哪"
private static float3 SupportAgainstShape(float3* pointSet, int count, GJKType type, ...)
```

判交出结果之后，EPA 再从单纯形往外扩展，找到最近的那个面，就是最小穿透深度。

### 把并行结果收回来

`IJobParallelFor` 里不能让多个线程写同一个数组。解法是用 `NativeStream`：每个线程写自己那一段，主线程顺序读。

```csharp
resultReader.BeginForEachIndex(i);
while (resultReader.RemainingItemCount > 0)
{
    var couple = resultReader.Read<ColliderCouple>();
    ...
}
resultReader.EndForEachIndex();
```

### Enter / Stay / Exit 零分配实现

两个 `HashSet<ColliderCouple>` 轮流用：本帧集合和上一帧比较，天然得出「新碰上的」「一直在碰的」「刚分开的」，不需要额外分配。

### 容量池：别把「容量」当成「物体数量」

这是我在这上面踩得最狠的一次：为了消除每帧分配，把数组改成预分配。结果 Job 里 `buffer.Length` 从「物体数」变成了「容量」，BVH 直接塞进几千个退化包围盒，整个系统看起来「什么都没碰到」。

修法是把容量关在内部，Job 只接收有效区间：

```csharp
var boundsSlice = ColliderBoundsEntities.GetSubArray(0, colliderCount);
handle = bvtTree.ScheduleBuild(boundsSlice, handle);
```

同时补齐了 `Dispose` 和生命周期钩子，退出时不再报 `Leak Detected`。

## 已知限制

- **还没有性能基准数据**：没做和 Unity 内置物理、暴力 O(n²) 的对比测试，这是下一步要补的；
- 顶层 BVH 每帧重建，没做增量更新；
- `TransformAccessArray`、`NativeStream` 仍是每帧新建；
- 只支持凸体，凹体需要拆成凸包组合。

写在这里是想提醒自己：**没有数据的「优化」是不能下结论的**。
