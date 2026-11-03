# 03 GOAP 系统

## 一句话定位

GOAP 是 MyFrame 的 AI 决策层：`GOAPAgent` 按优先级选目标，用状态比较器**逆向递归**出满足目标效果的动作树，交 `GOAPPlan` 以先子后父的顺序执行；配置存于 `GOAPConfig`，运行时深拷贝隔离。

## 目录与文件清单

行数为非空行统计，合计约 3.8k 行。

| 文件 | 行数 | 作用 |
| --- | --- | --- |
| Script/GOAP/GOAPAgent.cs | 461 | 决策主循环：目标排序、规划入口、执行/抢占、全局状态判定、配置深拷贝与校验 |
| Script/GOAP/GOAPConfig.cs | 24 | `Config/GOAPConfig` 配置资产（继承 `FrameConfigBase`），装 Goals/States/Actions/Plan 模板 |
| Script/GOAP/GOAPAttribute.cs | 19 | `GOAPActionAttribute`、`GOAPCheckerAttribute`，编辑器中显示名 |
| Script/GOAP/GOAPEditorUtility.cs | 37 | 编辑器静态桥：缓存当前 Agent/Global、`SaveData()` SetDirty |
| Script/GOAP/GOAPObjectPool.cs | 38 | 按类型栈池，复用计划节点与 SortedSet |
| Script/GOAP/IDeepCopy.cs | 4 | `IDeepCopy<T>` 深拷贝接口 |
| Script/GOAP/Test_Action.cs | 4 | 空动作，仅一个 `float Test` 字段 |
| Script/GOAP/Action/GOAPActionBase.cs | 171 | 动作基类 + `GOAPTypeAndComparer` + `GOAPActionUpdateType` 事件枚举 |
| Script/GOAP/Action/GOAPActions.cs | 68 | 动作列表容器，构建 `ActionEffectDic` 反查索引 |
| Script/GOAP/BaseActions/TimerAction.cs | 24 | 内置「计时」动作，计满后 `ApplyEffect()` |
| Script/GOAP/Goals/Goals.cs | 122 | `GOAPGoals` 容器与嵌套 `Goal` 定义、优先级排序 |
| Script/GOAP/Goals/GOAPGlobal.cs | 24 | 全局状态单例 `GOAPGlobal.Instance` |
| Script/GOAP/Goals/IGOAPGoalChecker.cs | 4 | 目标每帧回调接口 |
| Script/GOAP/Goals/IGOAPOwner.cs | 8 | AI 本体协议：`UpdateGoapStates` + `Binders` |
| Script/GOAP/GOAPBinder/BinderData.cs | 94 | 绑定数据结构：`StateAndPropertyBinder`、`IFieldBinder`、池化取值容器 |
| Script/GOAP/GOAPBinder/GOAPUtility.cs | 98 | 用 Expression 编译字段 getter 与 `UpdateGoapStates` 调用委托 |
| Script/GOAP/Plan/GOAPPlan.cs | 99 | 计划执行状态机：定位起点、后序推进、整树回收 |
| Script/GOAP/Plan/GOAPPlanNode.cs | 41 | 计划树节点：Action / Parent / Preconditions / IndexAtParent |
| Script/GOAP/Plan/GOAPRunState.cs | 6 | Running / Success / Failed 三态 |
| Script/GOAP/State/GOAPStateBase.cs | 89 | 状态抽象基类 + 泛型实现 + `GOAPStateBaseType` 枚举 |
| Script/GOAP/State/GOAPStateComparer.cs | 29 | 比较器抽象（条件、期望值、效果描述共用） |
| Script/GOAP/State/GOAPStates.cs | 81 | `Dictionary<string, GOAPStateBase>` 世界状态容器 |
| Script/GOAP/State/GOAPStateType.cs | 37 | 状态名 struct，与 string 双向隐式转换 + 编辑器下拉 |
| Script/GOAP/State/BoolState.cs | 69 | 布尔状态与比较器（是/否） |
| Script/GOAP/State/IntState.cs | 104 | 整数状态与比较器（大小/增减/等于） |
| Script/GOAP/State/FloatState.cs | 113 | 浮点状态与比较器，含「提升即可/下降即可」 |
| Script/GOAP/State/UnityObjectState.cs | 77 | Unity 对象状态与比较器（是/否/为空/不为空） |
| GOAPEditor/Editor/GOAPEditorWindow.cs | 821 | 主窗口：五条轨道、Add 表单、拖拽排序、运行时面板 |
| GOAPEditor/Editor/GOAPWindowTool.cs | 102 | 用 GlobalObjectId+SessionState 记住选中 Agent；类型扫描工具 |
| GOAPEditor/Editor/TwoSpanView.cs | 16 | `TwoPaneSplitView` 薄封装，供 UXML 使用 |
| GOAPEditor/Editor/GOAPInspector/GOAPInspector.cs | 641 | 被选条目的属性面板（手绘 UIElements）+ Checker 搜索树 |
| GOAPEditor/Editor/GOAPInspector/GOAPActionInspector.cs | 83 | 动作自定义面板基类与注册特性 |
| GOAPEditor/Editor/ItemScript/GOAPItemBase.cs | 41 | 条目基类：加载 .uxml、删除按钮、按 index 定位 |
| GOAPEditor/Editor/ItemScript/GoalItem.cs | 39 | 目标条目视图 |
| GOAPEditor/Editor/ItemScript/StateItem.cs | 35 | 状态条目视图 |
| GOAPEditor/Editor/ItemScript/ActionItems/GOAPActionItem.cs | 39 | 动作条目视图 |
| GOAPEditor/Editor/ItemScript/ActionItems/PreConditionItem.cs | 38 | 前提条目视图 |
| GOAPEditor/Editor/ItemScript/ActionItems/EffectItem.cs | 38 | 效果条目视图 |

## 核心类型

| 类型 | 基类/接口 | 职责 | 关键方法 |
| --- | --- | --- | --- |
| `GOAPAgent` | `SerializedMonoBehaviour` | 单个 AI 的运行时宿主，持有深拷贝后的 States/Goals/Actions 与当前 Plan | `Init` `OnUpdate` `GeneratePlan` `TryBuiltPlanPath` `CheckStateForPreCondition/Effect` |
| `GOAPConfig` | `FrameConfigBase` | 可配置资产，只做模板，运行时被深拷贝 | `OnValidate`（反调窗口刷新） |
| `GOAPStateBase` / `GOAPStateBase<T,V,C>` | `IDeepCopy` | 状态值容器，泛型版提供 `V Value` | `CompareWithPreCondition/Effect` `ApplyEffect` `Copy` `GetComparer` |
| `BoolState` / `IntState` / `FloatState` / `UnityObjectState` | `GOAPStateBase<...>` | 四种值类型状态 | 同上 |
| `GOAPStateComparer` / `GOAPStateComparer<S,C>` | `IDeepCopy` | 条件/期望值描述（符号 + 值） | `MatchWithComparer` `Copy` |
| `Bool/Int/Float/UnityObjectStateComparer` | `GOAPStateComparer<S,C>` | 各状态的具体符号集 | `MatchWithComparer` |
| `GOAPStateType` | struct | 状态名包装，字典 key | 隐式转 string；`GetAllState`（编辑器下拉） |
| `GOAPStates` | `IDeepCopy` | 世界状态容器 | `TryGetState` `CheckStateForPreCondition/Effect` `ApplyEffect` `DeepCopy` |
| `GOAPActions` | `IDeepCopy` | 动作注册表 | `Init`（建 `ActionEffectDic`）`DeepCopy` |
| `GOAPActionBase` | `IDeepCopy` | 动作基类：前提/效果/代价/排序值/事件钩子 | `Init` `StartRun` `OnStart` `OnUpdate` `OnStop` `ApplyEffect` |
| `GOAPTypeAndComparer` | `IDeepCopy` | 一条「状态名 + 比较器」 | `CheckState`（编辑器自动 new 比较器） |
| `GOAPPlan` | — | 计划执行状态机 | `StartRun` `OnUpdate` `Stop` `OnDestroy` |
| `GOAPPlanNode` | `IComparable` | 计划树节点 | `Start` `Update` `Stop` `OnDestroy` |
| `GOAPRunState` | enum | Running/Success/Failed | — |
| `GOAPGoals` / `GOAPGoals.Goal` | `IDeepCopy` | 目标表与单条目标 | `Init` `UpdateGoals` `DeepCopy` |
| `IGOAPGoalChecker` | 接口 | 每帧改目标实时优先级 | `Update(goal, agent, owner)` |
| `IGOAPOwner` | 接口 | AI 本体协议 | `UpdateGoapStates` `Binders` |
| `GOAPGlobal` | `SerializedMonoBehaviour` | 全局状态单例 | `TryGetGlobalState` |
| `GOAPObjectPool` | 静态类 | 类型栈池 | `Get` `GetOrNew` `RecycleObject` |
| `GOAPUtility` / `StateAndPropertyBinder` | 静态类 / 普通类 | 字段→状态绑定 | `InitCurrentGoapStateBindList` `GetBinderGetter` |
| `GOAPEditorWindow` / `GOAPInspector` | `EditorWindow` / `Editor` | 配置窗口与条目属性面板 | `RefreshItems` `DrawGoalItem/DrawAction` |

## 运行流程

1. **感知在框架外**：`IGOAPOwner` 每帧先（按 Demo 的写法）遍历绑定缓存调 `IFieldBinder.Invoke`，经池化 `GoapValueContainer<T>` 把字段值写进 `agent.States`，再调 `agent.OnUpdate()`；GOAP 自身无 Sensor。
2. **目标排序**：`UpdateGoals()` 先跑每个 `Checker.Update`（可改 `RuntimePriority`），再按 `Priority = PriorityMultiply × RuntimePriority` 降序放进 `SortedList`。
3. **规划**：`Plan` 为空或未运行时按序试 `Priority > 0` 的目标；先 `CheckStateForEffect` 判目标已达成（达成则不规划），成功即 `RunPlan` 并 `break`。
4. **反查候选**：从 `ActionEffectDic` 取效果与目标比较器 `MatchWithComparer` 的动作，节点按 `Priority = EffectValue - CostValue` 降序进 `SortedSet`，并触发 `BeforePlanningUpdateEvent`。
5. **成树**：`TryBuiltPlanPath` 逐条比对前提，不满足则反向查「谁能产生该效果」，按优先级递归、失败回溯；成功者设 `Parent`/`IndexAtParent` 挂为子节点，首个成功根节点触发 `BeIntoPlanUpdateEvent`。
6. **起跑**：`StartRun` 沿 `Preconditions.First()` 找最深节点为 `RunningNode`，`Action.StartRun()`（效果已满足→Success；前提满足→`OnStart`+Running；否则 Failed），此后每帧 `OnUpdate`。
7. **推进/失败**：Success 则 `Stop`+`AfterActionEndUpdateEvent`，根节点完成即整树回收；否则先跑下一个兄弟再跑父节点（后序）。Failed 则回收整树，下一帧重新规划。
8. **抢占与帧末**：当前目标可被打断且存在更高优先级、可打断、能规划成功的目标时 `StopPlan`+`RunPlan`；最后执行 `Always` 动作的 `AlwaysUpdateEvent`。

## 关键机制详解

### 状态建模：比较器既是条件也是效果

`GOAPStateBase<T,V,C>` 用 `Value` 存值，四种实现对应 bool/int/float/`UnityEngine.Object`。比较器不是等值判断而是「符号 + 值」，同一对象承担三种语义：`CompareWithPreCondition`（满足前提）、`CompareWithEffect`（效果已达成）、`ApplyEffect`（写回，除「等于」外均 `+=`）；`MatchWithComparer` 反向判断「动作效果能否满足目标期望值」，规划靠它筛候选。`GOAPStates` 以 `Dictionary<string, GOAPStateBase>` 存（key 由 `GOAPStateType` 隐式转 string），状态缺失判不满足；`GOAPAgent` 与 `ApplyEffect` 都先查 `GOAPGlobal.Instance`，同名状态全局优先。

### 规划算法：逆向链 + AND/OR 树 + 优先级贪心，不是 A*

从代码可确认：**既不是 A\* 也不是状态空间搜索**。没有 open/closed 表、没有 `f = g + h` 累计代价，也不模拟推进——前提判定打的是真实世界状态。做法是逆向链：从目标效果反查 `ActionEffectDic`，对每条未满足前提再反查「谁能产生该效果」，递归成 AND/OR 树（节点=动作，子节点=未满足前提）。唯一策略是贪心：候选入 `SortedSet`，比较器只比 `Action.Priority` 降序，取第一个能递归成功的分支，失败才回溯。`CostValue` 只影响排序、不累计，故无「总代价最优」。

### 动作执行：GOAPRunState 与生命周期

`GOAPRunState` 只有 Running/Success/Failed，Running 为 0，故 `OnUpdate` 返回 `default` 即「继续跑」。`GOAPPlan` 持有 `StartNode`（根=最终动作）、`RunningNode`、`GoalName`、`Running`，每帧只推进一个节点，Running 期间不重校验前提，世界突变只能靠动作返回 Failed。生命周期：`Init` → `Initialize`（编辑器新增）→ `BeforePlanningUpdateEvent`（被当候选，可重算 `EffectValue`）→ `BeIntoPlanUpdateEvent` → `StartRun/OnStart` → 每帧 `OnUpdate` → `OnStop` → `AfterActionEndUpdateEvent`；`Always` 另有 `AlwaysUpdateEvent`。**效果不会自动写入**，由动作自己调 `ApplyEffect()`。

### 目标选择

`Goals.Dic` 的 key 即目标名，`Goal` 含 `TargetState`+`TargetValue`（比较器描述期望值）、`PriorityMultiply`、`RuntimePriority`、`CanInterrupt`（能否抢别人）、`CanBeInterrupted`（能否被抢）、`Checker`。每帧 `UpdateGoals` 先跑 `Checker.Update`，实时优先级与启用逻辑都在 `IGOAPGoalChecker` 里；选中规则是按 `Priority` 降序取第一个 `Priority > 0` 且能出计划的目标，无多目标效用比较。

### 绑定：Expression 编译委托，不是每帧反射

三层：① `StateAndPropertyBinder`（`FieldName`/`StateName`/`StateType`）列「字段→状态名」，字段须标 `[FieldForGOAPBind]`，编辑器在选中变化时反射扫描刷新候选；② `GOAPUtility.InitCurrentGoapStateBindList` 用 Expression 把字段编译成 `Func<IGOAPOwner,T>`（int/float/bool/Object 四分支），并把 `UpdateGoapStates` 编译成静态委托；③ `ActionSetForGOAPBinder<T>.Invoke` 取值 → 放进 `ResSystem` 池化的 `GoapValueContainer<T>` → 调编译委托 → owner 强转容器 `SetValue` → 归还池。反射只在初始化一次，每帧只是一次委托调用；方向是 owner 主动推数据。可选 `ownerID` 缓存，Demo 未传即每次重编译。

### 编辑器：五条轨道 + 条目级 Inspector，不是节点图

`GOAPEditorWindow` 是 UIElements 窗口（菜单 `GOAP/GOAPEditorWindow`），布局来自 `GOAPEditorWindow.uxml`，固定五条轨道 Goals/States/Actions/PreCondition/Effect，条目实例化 `.uxml` 后按 `y = index × 50` 绝对定位。**没有 GraphView/Port/Edge**，`UnityEditor.Experimental.GraphView` 只用于开 `SearchWindow`；「图」靠轨道对齐加颜色区分，真正树形在运行时面板。选中条目后 `Selection.activeObject = 窗口`，由 `GOAPInspector`（`[CustomEditor(typeof(GOAPEditorWindow))]`，检视窗口而非数据）手绘符号/数值/优先级/Flags；动作可用 `[GOAPActionInspector]`+`GOAPActionInspectorItem<T>` 加专属面板。Play 下每帧重建状态列表与缩进计划树（`RunningNode` 高亮）。保存走 `SaveData()`。

### 对象池：为什么需要

规划是「每次重规划重建整棵树」，直接 `new` 就是几十个短命对象，对每帧跑 AI 的场景是持续 GC 压力。`GOAPObjectPool` 用 `Dictionary<Type, Stack<object>>` 做类型栈池，`GetOrNew` 取不到才 new、`RecycleObject` 归还；节点、候选 `SortedSet`、整树回收都走它。代价是静态池无上限、不清池、不防重复归还。

## 对外 API 与扩展点

**新增 Action**：继承 `GOAPActionBase`（或子类）并标 `[GOAPAction("名")]`，重写 `OnStart`/`OnUpdate`/`OnStop`，落状态时显式调 `ApplyEffect()`，需要 owner 数据则重写 `Init` 缓存；窗口 Action 轨 Add 后填前提/效果/`CostValue`/`EffectValue`/`GoapActionUpdateType`；动态代价写 `BeforePlanningUpdateEvent`；专属面板用 `[GOAPActionInspector]`+`GOAPActionInspectorItem<MyAction>`。

**新增 Goal**：在 `Goals.Dic` 加一条（key 即名），配 `TargetState`+`TargetValue`、两个优先级字段与抢占开关；动态优先级写 `IGOAPGoalChecker`（`[GOAPChecker]`，必须有无参构造，深拷贝按其类型重建），在 `Update` 里改 `RuntimePriority`。

**新增 State**：值类型仍是 int/float/bool/Object 时，继承 `GOAPStateBase<TState,TValue,TComparer>` 实现比较与应用方法，再写配套 `GOAPStateComparer<S,C>`，加入 States 后规划与下拉自动生效；若是全新值类型，还须改 `GOAPStateBaseType` 枚举与绑定层四分支（按该枚举硬编码）。

**驱动**：`Init/OnUpdate/Stop/Start/ReStart` 全由宿主调用；`UpdateGoapStates`+`Binders` 是绑定协议。

## 与其他模块的耦合

- **Odin**：`SerializedMonoBehaviour`、`FrameConfigBase`（`SerializedScriptableObject`）、`[OdinSerialize]` 序列化泛型字典与接口字段，及 `ValueDropdown`/`Button` 等特性。
- **MyFrame**：`FrameConfigBase`、`ResSystem.GetOrNew` + `FrameExtension.ObjectPushPool`。
- **Demo**：`DemoEnemyController` 实现 `IGOAPOwner`，`Init` 里 `goapAgent.Init(this)`，`Update` 里先刷绑定再 `OnUpdate()`；MyFrame 内无调用方，驱动权在业务侧。
- **与 StateMachine 并行**，两者无代码互调。
- **编辑器**：`GOAPEditorUtility.Agent/Global` 静态桥、`GOAPWindowTool` 用 `GlobalObjectId`+`SessionState`、`GOAPConfig.OnValidate` 反调窗口刷新。
- ⚠ **编译期**：`GOAPEditorUtility.cs` 与 `BinderData.cs` 在 `#if` 外 `using UnityEditor;`，出包有 CS0246 风险。

## 设计亮点与可改进点

**亮点**：① 逆向链+实时校验，配错立刻表现为执行期失败→重规划；② 比较器一物三用，「提升即可」让加减量动作匹配阈值目标；③ 配置与运行时全链深拷贝隔离；④ 绑定用 Expression 编译委托，反射只在初始化；⑤ 编辑器闭环，可一站改完并预览运行中计划。

**可改进**

- ✅ **已修**：同优先级节点被 `SortedSet` 静默丢弃 → 节点加自增 `Id` 作为 tie-break；
- ✅ **已修**：`GOAPPlanNode.OnDestroy` 沿 `Parent` 上行清理的语义问题 → 改为只向下清理；
- ✅ **已修**：`GetActionMinCost` 的空引用（前置无解时返回 `float.MaxValue`）；
- ✅ **已修**：规划失败时已建子树的泄漏与"脏节点回池"；
- ⚠ **仍存在**：无环检测（目前靠 `MaxDepth` 兜底）；规划失败每帧打 Log 易刷屏；`GOAPConfig.Plan` 疑似未使用；`IntState` 与 `FloatState` 对「提升即可」的判定不一致；
- ⚠ **编译期**：`GOAPEditorUtility.cs` 与 `BinderData.cs` 在 `#if` 外 `using UnityEditor;`，出包有 CS0246 风险；
- 🔸 **设计取舍**：不做全局代价累计、不保证最优解 —— 见下方附录。

---

## 附录：规划器设计（2026-11 讨论结论）

> 这一节记录的是"为什么是现在这个形态"，比具体代码更重要，改规划器之前先读这里。

### 1. 搜索空间是 AND/OR 树，不是普通图

GOAP 的计划结构有两层语义：

```
条件（OR）      —— 只要【任意一个】动作能产生这个效果就行
  └── 动作（AND）—— 必须【同时满足】它的所有前置条件
        ├── 前置 1（OR）→ 再为它选一个动作
        └── 前置 2（OR）→ 再为它选一个动作
```

关键在于：**"给前置 1 找解"和"给前置 2 找解"不是备选关系，而是并列任务**。它们必须都成立，因此无法放进同一个 open 集按 `f` 比较。

### 2. 为什么不做严格 A*

A\* 的适用前提是"每个节点只选一个后继"（OR 图）。要在 GOAP 上用 A\*，必须先把 AND/OR 树展平成**世界状态图**：

- 节点 = 状态快照，边 = 动作，`f = g + h`
- 需要状态拷贝 + 状态哈希（浮点必须量化，否则 closed 集形同虚设）

换来的收益是"总代价最优"。但在动作游戏里这个收益很低：

| 因素 | 结论 |
| --- | --- |
| 计划寿命 | 世界状态每帧在变，最优解往往执行不完就失效 |
| 决策频率 | 目标是一帧内出结果，而不是"想得再久一点" |
| 可解释性 | 设计师要看得懂 AI 为什么这么做；回归分解天然能解释，`f` 值讲不清 |
| 实现成本 | 状态拷贝 + 哈希，且启发式弱时状态数会爆 |

### 3. 现行算法：递归分解 + 启发式排序 + 失败回溯

```
Solve(条件 c, 深度 depth):
    if depth > MaxDepth: return null
    候选 = 所有「有某个效果能匹配 c」的动作
    候选按 f 排序：f = 动作代价 + h(动作)
    for 候选 in 候选:
        node = 新节点(候选)
        for 前置 p in 候选.未满足前置:
            child = Solve(p, depth + 1)
            if child == null: 回滚 node 的子树; 换下一个候选   ← 回溯
            node.children.add(child)
        return node                ← 所有前置都有解，节点"完整"
    return null                    ← 该条件无解
```

**节点的"完整"是递归返回时才成立的**——被 Effect 选中的只是候选动作，它的前置还没解决，不能提前挂到父节点上。

### 4. 启发式 h 的定义

```
h(动作) = Σ_{未满足的前置 p}  最便宜的能产生 p 的动作的代价
```

注意三点：

- **不含动作自身代价**——那部分在 `g` 里（`G` 由子树自底向上累加：`G = 自身代价 + Σ 子节点 G`）；
- **只递归一层**，不是精确下界，属于乐观估计；
- 前置无解时返回 `float.MaxValue`，让该候选自然排到最后。

### 5. 乐观效果匹配

AI 的动作效果大多是**模糊**的（加血、加速、拉近距离），很少产生"精确等于某值"的结果。所以匹配语义是"**有可能让条件成立**"：

```csharp
// FloatState.MatchWithComparer
case 大于:      return Value > other.Value || Symbol == 提升即可;
case 小于:      return Value < other.Value || Symbol == 下降即可;
```

- 绝对值型效果（`Symbol == 等于`）→ 直接比数值；
- 增量型效果（`提升即可 / 下降即可`）→ 只看符号方向。

代价：可能选到"方向对但幅度不够"的动作，执行期 `CheckForEffect` 失败 → 重规划。这是**刻意**的：AI 规划的是"当下有哪些合理手段"，不是"数学上保证达成"。

> 注意：`提升即可 / 下降即可` 作为**前置条件**时，`CompareWithPreCondition` 恒返回 true，永远不会进 `Pending`。这类符号只该用在目标与效果上。

### 6. 与"经典 A\* 版 GOAP"的对照

| 维度 | 本文实现 | 经典 A\* 版（如 F.E.A.R. 常被引用的做法） |
| --- | --- | --- |
| 搜索对象 | AND/OR 树（动作分解） | 部分计划序列 / 状态图 |
| 排序依据 | `f = 动作代价 + h(前置最便宜代价)` | `f = 已累计代价 + 未满足目标数` |
| 全局 open 集 | 无（每个条件独立递归） | 有 |
| 去重 | 靠 `MaxDepth` 与回溯 | closed 集 + 状态哈希 |
| 最优性 | 不保证 | 有（h 可采纳时） |
| 规划耗时 | 可预估，与动作数线性相关 | 依赖分支因子，需上限 |

### 7. 节点池与失败回滚

一次规划会创建几十个候选节点，全部走 `ResSystem.GetOrNew<GOAPPlanNode>()`。三条纪律：

1. 失败的候选必须**连同它已建立的子树一起回滚**（先 `OnDestroy` 递归断链，再入池）；
2. 入池前必须清空 `Preconditions`，否则复用时会带着旧子树进入新计划；
3. 同一个节点**绝不能入池两次**——否则两个计划会拿到同一个对象，一方 `OnDestroy` 就把另一方的计划打断。

### 8. 可选的后续增强

不需要换算法，这三件事能显著提升稳定性，按性价比排序：

- **条件级 memo**：`条件签名 → 已知最优解代价`，同一条件在不同分支被反复求解时直接剪枝（解决指数级重复）；
- **代价上界（branch & bound）**：递归时把剩余预算往下传，超支即放弃；
- **效果幅度次级排序**：同样能满足时，增量大的优先，减少"方向对但量不够"的重规划；
- **失败拉黑**：某 `(目标, 动作)` 连续失败后短期拉黑，避免原地打转。

