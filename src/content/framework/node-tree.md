---
title: 节点树系统
summary: 它提供的是"链路"——谁接谁、什么条件下走哪条。执行不归框架管：挂载了对应接口的节点对象自己决定怎么跑。
highlight: 没有执行器，执行权在节点自己手里
order: 5
diagram: /framework/node-tree.svg
diagramCaption: 编辑期建模 → 运行期执行（由节点自己）→ 只读可视化
stack: ['UI Toolkit', 'GraphView', 'Odin']
files: 21
lines: 2775
---

## 框架提供的能力与边界

框架提供的是一条链路。节点图上有节点、有连线、有条件，但没有执行器：它不会遍历这张图，不会帮你调度，也不知道你什么时候该往下走。

框架负责的范围很窄。谁连着谁、每个节点有哪些参数、满足什么条件才能走，这些是数据，能序列化、能存进资产、能复制粘贴；给定参数表，`TryToGetConditions()` 能算出这个节点当前可不可以走下一跳；编辑器轮询节点的 `State`，执行到哪个节点就高亮哪个，只读，不写。

至于谁来走这棵树、什么时候走、走完做点什么，由挂载了对应接口的对象自己决定。框架只提供链路与编辑器，不内置执行器，执行语义由使用方实现。

## 树只认接口

大部分节点编辑器（包括 Shader Graph）把图和运行时打包在一起：节点类既描述数据、又负责执行，于是运行时要认识所有节点类型，加一种节点就要改运行时。

这套系统的做法相反，树只认接口，不认实现。

```csharp
public interface INodeViewer
{
    bool GetOutPutList(out List<INodeViewer> outputNodes);   // 我的后继是谁
    void Add(INodeViewer node);                              // 我接上了谁
    void Remove(INodeViewer node);
    bool TryToGetConditions(...);                            // 什么条件才能往下走
    NodeState State { get; set; }                            // 执行态，框架只读
}
```

`HierarchyInfo<T, O, H>` 里存的是 `List<T>`（泛型约束 `where T : INodeViewer<T, O>`），`NodeView` 也只持有 `INodeViewer`。整个树结构没有引用任何具体节点类型。

结果是加一种节点逻辑，不用改树、不用改编辑器、不用改序列化。

## 链路的建立

连线时编辑器只做一件事：把「加子节点」转发给节点自己。

```csharp
public static void ConnectNode(this Edge edge) {
    NodeView output = edge.output.node as NodeView;
    output?.AddChild(input as NodeView);      // → NodeData.Add(...)
}
```

所以树数据里没有边表，图长什么样完全由节点实现决定。复制粘贴也是同理：`SerializationUtility.SerializeValue<List<INodeViewer>>` 走 Odin 的多态二进制序列化，不关心具体类型。

## 条件与参数

节点可以带一串条件，条件是对参数表的判断。参数由宿主提供（`List<ParameterForTree>`），每个参数有唯一 `Guid`；条件只记参数的 `Guid`，不引用字段，所以改参数名不会让条件失效。

求值统一在 `RegisterCondition` 里按类型分派：`Bool / Float / Int / Trigger`。`Trigger` 是读一次即消费的语义，适合做本帧触发一次的事件节点。

## 编辑器

| 部分 | 作用 |
| --- | --- |
| `NodeTreeSystemWindow` | 主窗口：层级列表 + 画布 + 属性面板三栏 |
| `TreeView` / `NodeView` / `EdgeView` | 画布：建节点、连线、按 `State` 变色 |
| `Inspector` | 选中节点后，按 `[ShowNode(typeof(X))]` 反射出对应面板 |
| `NodeAutoLayouter` | 自动布局（non-layered tidy tree，两趟 walk 算位置） |

节点的创建菜单和属性面板都靠特性加反射扫描发现类型：`[NodeLabel]` 决定菜单里的位置，`[ShowNode]` 决定用哪个面板。两处都不用注册表。

## 新增一种节点

1. 写 `class XxxNode : INodeViewer<XxxNode, XxxOwner>`，实现位置、名字、`Add/Remove/GetOutPutList`、端口描述、条件、`Init/DeepCopy`；
2. 加 `[NodeLabel("分组/菜单名")]`；
3. 需要分支就返回 `Condition` 列表；
4. 需要属性面板就写 `InspectorItemBase<XxxNode>` 并标 `[ShowNode(typeof(XxxNode))]`。

树结构、编辑器、序列化都不需要改。

## 已知问题

数据层里的 `PortInfo` 用了 `UnityEditor.Experimental.GraphView.Port.Capacity`，`NodeTreeDataProcessor` 也 `using UnityEditor`，这会让数据层带进编辑器引用。目前靠 `#if` 和编辑器环境规避。如果要把它做成纯运行时资产，这处需要换成一个自定义枚举。
