# ARPG 原型项目分析

> 工程：`E:\GameMake\ARPG制作_Copy`
> 分析范围：`Assets\Script`（194 个 .cs / 15,143 行，14 个一级模块）、`Assets\NPCSystem`（35 个 .cs / 2,796 行）、`Assets\MyFrame`（179 个 .cs / 21,551 行）
> 用途：简历项目描述、个人网站「项目详情」页素材

---

## 一、项目全貌

| 指标 | 数值 |
| --- | --- |
| 业务代码 | 194 个 .cs / 15,143 行（14 个一级模块） |
| 对话系统 | 35 个 .cs / 2,796 行 |
| 内嵌框架 | 179 个 .cs / 21,551 行（10 个子模块） |
| 自有配置资产 | 104 个 `.asset`（全部由 `[FrameConfig]` 注册） |
| 技能片段 | 24 个 `SkillClip`（30 FPS 帧事件） |
| 技能配置 | 11 个（4 职业：战士/坦克/刺客/弓手） |
| 技能行为类 | 10 个实现 + 5 个抽象基类（4 层继承） |
| 状态类 | 11 个（玩家 5 + 敌人 6） |
| GOAP | 2 套，各 3 目标 / 6 状态 / 5 行为 |
| UI 窗口 | 17 个，4 层 Layout |
| NPC 对话树 | 3 棵，10 种节点类型，约 44 个节点实例 |
| 场景 | 8 个，配置化 + 异步加载 |
| 敌人 | 2 种（Archer / Shield），各带 1 套 GOAP + 技能 |

---

## 二、模块清单

| 目录 | 文件 / 行数 | 系统 | 核心类 |
| --- | --- | --- | --- |
| `Battle` | 39 / 2,956 | 战斗内核：技能播放器、技能行为、Buff、子弹、顿帧击退、属性 | `ICharacter`、`IHitTarget`、`AttackData`、`Skill_Player`、`SkillCamera`、`SkillBrainBase`、`BuffController`、`StutterFrameAndImpulseManager` |
| `Player` | 16 / 2,114 | 玩家装配、相机根、技能大脑、状态机 | `Player_Controller`、`PlayerManager`、`PlayerRoot`、`Player_SkillBrainBase` |
| `Enemy` | 33 / 2,554 | 敌人控制（状态机 + GOAP 双层）、感知、技能、回收 | `Enemy_ControllerBase`、`Enemy_ControllerForGOAPBase`、`EnemySkillBrain`、`EnemyManager` |
| `UI` | 56 / 4,625 | 17 个窗口 + 槽位控件 + 世界空间 HUD | `UI_GameSceneMainWindow`、`UI_ItemSlotBase`、`EnemyHpBar`、`PopupText` |
| `Tasks` | 3 / 581 | 参数化任务、子任务链、奖励、进度持久化 | `GameTask`、`TaskManager` |
| `Item` | 11 / 456 | 物品/背包/装备/掉落 | `InventoryData_Save/Play`、`WeaponItem`、`EquipmentItem` |
| `Config` | 12 / 532 | 角色/职业/场景/经验/飘字/部位配置 | `CharacterConfig`、`EXPConfig`、`CharacterPartConfig` |
| `Selected` | 5 / 309 | 交互选中与描边（CommandBuffer 蒙版） | `SelectedManager`、`ISelectedItem`、`ISelector` |
| `Data` | 5 / 269 | 存档数据根与管理 | `GameData`、`GameDataManager`、`IGameDataComponent` |
| `GameScene` | 5 / 195 | 场景配置、异步加载、返回点 | `GameSceneManager`、`ReturnPoint` |
| `General` | 4 / 323 | 通用工具、屏幕控制 | `ProjectUtility`、`ScreenRuntimeTool` |
| `CreateCharacterScene` | 2 / 126 | 捏脸/建角流程 | `CharacterCreator` |
| `Store` | 2 / 91 | 商店存档双模型 | `StoreData_Save/Play` |
| `MenuScene` | 1 / 12 | 主菜单入口 | `MenuSceneManager` |

---

## 三、技术要点（每项：做法 / 为什么 / 体现什么能力）

### 1. 帧事件驱动的技能系统

**做法**

配置三级：`SkillConfig`（技能，持 `SkillClip[]` 连段）→ `SkillClip`（片段：`FrameCount` + 30 FPS）→ 六条事件轨道：
动画 / 音效 / 特效 / 攻击检测 / 自定义事件 / 相机。每条轨道是 `List<Event>`，事件带 `FrameIndex` 与 `DurationFrame`。

播放器 `Skill_Player` 不按渲染帧驱动，而是：

```
_playTotalTime += owner.GetLocalDeltaTime();
targetFrameIndex = (int)(_playTotalTime * FrameRate);
while (_currentFrameIndex < targetFrameIndex) TickSkill();   // 追帧
```

帧事件用**模板方法**：`SkillBehaviourBase` 对每条轨道给 `BeforeXxx / AfterXxx` 钩子，具体技能只重写关心的钩子。

打断/冻结用**帧上配置**：`SkillCustomEvent.EventType ∈ {FreezeSkillRelease, UnFreezeSkillRelease, CanRotate, CantRotate, AddBuff}`。

CD 与消耗：`PlayerSkillConfig.ReleaseCosDic : Dictionary<SkillCostType,float>` + 等级成长 `base * (1 + (lv-1)*perLv)`。

连段：`_attackIndex` 在 `Clips[]` 中推进，**只有最后一段进 CD**；中途停手 `StandingTime` 秒后进入 CD（连段窗口）。

**为什么**：策划在编辑器里配出连招节奏，程序只维护"轨道解析 + 钩子"，新增技能几乎零代码；追帧保证低帧率下逻辑帧不丢。

**体现**：配置与逻辑分离、模板方法 + 钩子扩展、帧同步思维、编辑器与运行时共用一套数据结构。

### 2. 四种形态攻击检测与统一命中管线

**做法**

`Weapon`（武器碰撞体开关）/ `Box` / `Sphere` / `Fan` 四种形态，统一走 `SkillAttackDetectionTool`，全部 `Physics.Overlap*NonAlloc` 到静态 `Collider[20]`，命中过滤用**交换删除**压缩结果；扇形先用 Box 粗筛再按 `ClosestPoint` 计算内外半径与夹角精筛。

命中防重：`HashSet<IHitTarget>` + `ComboCount / ComboCheckDeltaTime` 定时清空，实现"一次挥砍多段命中"。

**体现**：物理查询零分配、缓存友好、用几何粗筛 + 精筛做两级过滤。

### 3. 局部时间缩放的顿帧 + Cinemachine 震屏

**做法**

`ImpulseConfig` 含冲量形状 / 力度 / 顿帧系数 / 自定义曲线 / 方向。受击者与攻击者各由 `ICharacter.LocalTimeScale` 缩放**自身**时间：技能帧推进用 `GetLocalDeltaTime()`、状态计时、`AnimationController.Speed` 全部吃这个系数；同时 `CinemachineImpulseSource.GenerateImpulseWithForce` 出震屏。统一由 `StutterFrameAndImpulseManager` 用协程字典管理，重复命中先 `StopCoroutine` 再重开。

受击动画过渡时间**按击退力度分档**：≤1.5 → 0.05s，≤3 → 0.08s，其余 0.03s。

**为什么**：局部时间缩放不波及 UI 与其他角色，避免全局 `Time.timeScale` 的副作用。

**体现**：数据驱动手感、接口隔离（`IImpulse` 让玩家/敌人各自实现差异）。

### 4. 泛型状态机 + GOAP 双层 AI

**做法**

自研 `StateMachine<TOwner,TStateBase,TStateEnum>`：枚举做 key、状态实例复用、`ChangeState` 返回 `bool`（进入失败可回退）、`CheckCanEnterState / BeforeEnter / BeforeExit` 三钩子；`Update/LateUpdate/FixedUpdate` 用**委托注册**到统一驱动而非每帧遍历所有状态；状态字典本身也从对象池取。

**双层**：状态机负责表现/动作（走、绕、攻击、受击），GOAP 负责决策。受击/死亡时 `goapAgent.Stop()`，恢复时 `Start()`，把"被打断"与"重新规划"解耦。

GOAP：`Goals`（目标 + 比较器 + 优先级 + `CanInterrupt/CanBeInterrupted`）→ 反向链式规划 `TryBuiltPlanPath` → **池化的 `SortedSet<GOAPPlanNode>`** 优先队列 → `GOAPPlan` 执行；支持 `GOAPGlobal` 全局状态覆盖局部。

**Expression Tree 优化**：`[FieldForGOAPBind]` 标记字段 → `GOAPUtility.GetBinderGetter<T>` 用 `Expression.Lambda<Func<...>>.Compile()` 生成 getter，避免 `FieldInfo.GetValue` 反射；`GoapValueContainer<T>` 池化避免装箱。

**敌人"贴脸绕圈"AI**：`Vector3.Cross(targetDir, up) * dir` 求切向绕行；用 `[Flags] ColliderDirection` 记录障碍在左/右/前/后，据此决定绕行方向（两侧都有障碍就直走）；用 `NavMeshAgent.Move` 做局部位移不打断寻路。

**体现**：泛型 + 委托驱动的状态机、GOAP 反向规划、Expression Tree 性能优化、AI 手感细节（绕行、防抖）。

### 5. 打击感数据链与受击流程

一次命中触发：受击音效 + 特效（在 `HitPoint` 生成并 `LookAt(Camera.main)`，定期回池）→ `IImpulse` → `BeHit` → 伤害飘字 + 血条 → 状态切 `Hurt` → 受击角超过视野半角则**转向攻击者** → `StopNavMesh`。

伤害公式：`最终 = AttackValue * AttackMultiply - defence.Total`；数值模型 `FloatProperties`：`Total = base + fixed + base * percent/100`，最大生命变化时**按比例保留当前血量**。

打断：`CanBeInterruptedByHurt(attackData)` 三层委派 —— 状态机 → `SkillBrain` → 当前 `SkillBehaviour`，实现"某些技能霸体、某些可被打断"。

> ⚠️ 暴击 / 闪避 / 抗性 / 格挡：全仓检索确认**没有实现**，不要写进简历。

### 6. 三机位相机体系

`CinemachineFreeLook`（常态）+ `aimCamera`（瞄准）+ `lockCamera`（锁定），通过 `SetActive` + `Priority` 切换。

锁定选目标：`OverlapSphereNonAlloc` + 距离/角度粗筛 → 屏幕中心射线与目标 `Bounds` 求交（`bounds.IntersectRay`）取最近者。

锁定相机每帧用"玩家→敌人"方向重算机位；`WorldToViewportPoint` 检测边距，敌人快出画时 `_cameraPositionMods += 0.01f` **自适应后拉**。

技能运镜 `SkillCamera`：支持 Linear/Bezier/Direction/Point 位移 + 旋转 + FOV + Impulse 事件；轨迹定义在"技能开始时的模型局部空间"，因此跟随角色朝向；贝塞尔用控制点 + 三次求值，按 `(playbackTime - startTime)/duration` 归一化插值。

> ⚠️ 相机系统运行时完整，但现有 24 个 `SkillClip` **未配置相机轨道**（`_skillCameraDic` 为空）。表述为"实现了技能运镜系统"，不要写"每个技能都有运镜"。

### 7. 背包 / 装备 / 商店的「存档-运行态」双模型

`InventoryData_Save`（只存 `itemId/itemType/count/position`，可序列化）↔ `InventoryData_Play`（运行时持资产引用），互为构造器。商店同理（`StoreData_Save/Play`），任务参数同理。

**三份索引**：`items(List)` + `ItemTypeDic`（分页/tab）+ `ItemConfigDic`（按配置反查，任务用）。8×8 网格 + 扫空位。

装备穿戴按子类分派：`WeaponItem → attack.FixedBonus`、`EquipmentItem → defence.FixedBonus`，再叠加 `AdditionalProperties` 到 `PercentBonus`。

**为什么**：避免 ScriptableObject 引用写进存档后资产改名就崩。

### 8. 存档系统

`persistentDataPath/SaveData/<saveID>/<FileName>`，二进制或 JSON 二选一；索引文件存槽位列表 + 时间；`SaveItem` 额外保留时间字符串规避 `JsonUtility` 不支持 `DateTime`。

`DataManager<G,S>` 提供三个事件点 `OnGameDataCreated / Loaded / Save`，业务模块各自注册回调保存自己那段（玩家 → 角色/技能/按键，任务 → 进度，NPC → 参数 + 商店）→ **存档是"聚合"而非"上帝类"**。

`Serialized_Dic<K,V> : ISerializationCallbackReceiver` 用 `[OnSerializing]/[OnDeserialized]` 同时兼容二进制与 `JsonUtility`。

自动存档：切场景前写入 `SceneGuid` 并 `AutoSaveData()`；`Application.quitting` 保存设置。10 个槽位 + 0 号自动存档。

**体现**：序列化限制的工程化处理、模块化持久化、新增系统零改码入档。

### 9. Addressables + 双层对象池

`ResSystem` 把 Addressables 与对象池**组合**：实例化先查池 → 未命中 `Addressables.InstantiateAsync`；`autoRelease` 时挂 `OnReleaseAddressableAsset` 组件，销毁即 `ReleaseInstance` —— "谁实例化谁释放"自动化。

`PoolSystem` 双层：GameObject 池（按 `<prefabName>Pool` 自动建池、预热、`maxCapacity` 校验）+ 普通 class 池（按 `Type.FullName`）。

池化"数据对象"：`EnemyHpBarData`、`PopupTextData`、`GoapValueContainer<T>`、`SkillShareData<T>`、`Buff` 都是 `ResSystem.GetOrNew` + 对象池，世界空间 UI 与 Buff 也做到零 GC。

### 10. 事件系统：按作用域分层

全局 `EventSystem`（静态门面）→ `EventModule`：string key + **16 个泛型重载**（源码注释写明：避免 `params` 数组 GC 与装箱）；`EventInfo` 从对象池取。

**用法分层**：
- **设置项广播** → 全局事件（`CameraSensitivityChange`、`MoneyChange`、`*VolumeChange`）
- **角色内部** → C# event（`ICharacter.UpdateEvent`、`OnAttackEvent`、`HurtEvent`）—— 强类型、无字典查找、随对象销毁自然解绑

多播表决：`DialogueManager.CheckWindowClose` 是 `Func<bool>` 多播，`GetInvocationList()` 逐个调用，**全部为真才关窗**。

### 11. 编辑器工具（含金量最高的一块）

| 工具 | 要点 |
| --- | --- |
| `SkillEditorWindow`（922 行） | IMGUI + `Handles.DrawLine` 画时间轴与播放头；鼠标位置→帧号；滚轮缩放帧宽（10→100px）；6 条轨道统一派生 `SkillTrackBase`；用 `DateTime` 差值 × `FrameRate` 做**帧级预览**；`[DidReloadScripts]` 清理预览态；`StripPreviewComponents` 剥离预览角色上多余组件，避免预览触发业务逻辑 |
| 配置系统 | `[FrameConfig(typeof(T), "菜单路径")]` 标注 → 工具反射收集，自动生成配置浏览/新建面板，新增配置类型零改工具 |
| `GOAPEditorWindow` | 双面板拖拽连线编辑 Goals / States / Actions |
| 节点树编辑器 | GraphView + UXML；多 Hierarchy、`NodeAutoLayouter` 自动布局、节点配色、画布位置缩放持久化 |
| 自定义 Inspector | `EXPInspector`（曲线/区间可视化与重叠校验）、NPC 节点 Inspector 10 个、`Skill*EventInspector` 7 个 |
| Scene 视图调参 | `Handles.ScaleHandle/RadiusHandle` 直接拖拽编辑扇形检测范围与追踪距离并 `SetDirty` |

**体现**：把"策划配表"的工作量从程序转移到工具；UI Toolkit / IMGUI / GraphView / Handles 四套编辑器 API 实战。

### 12. NPC 对话树

数据：`NPCConfig` 持 `SpeakNodeTree`（多 Hierarchy）+ `parameterList`；文本单独放 `TextData`（`Dictionary<string, List<DialogueData>>`）→ **内容与流程分离**。

节点：`SpeakNodeBase : INodeViewer<...>`，分 `EN_ActionNodeBase`（叶子）与 `EN_Executor`（有子节点），执行签名统一为 `async Task<NodeState> Execute()`。

**异步节点**：基类创建 `SemaphoreSlim(0,1)`，UI 类节点打开对话框后 `await SemaphoreSlim.WaitAsync()` 挂起；玩家点完最后一句 `Release()` 才继续。

组合：`En_SequenceEventExecutor`（顺序，遇 `Stop` 中断）、`EN_ShowChoice`（按 x 坐标定序，运行时过滤不满足条件的选项）、`EN_CheckConditionNode`、`EN_CompleteTask`。

参数：`ParameterForTree`（Int/Float/Bool/**Trigger**）；Trigger 是**一次性**的（读后置 false），天然支持"这段对话只出现一次"。

自定义事件节点：`EN_CustomEventNode` 用反射找带 `[SpeakNodeCustomEvent]` 的方法，参数签名 `(SemaphoreSlim, T)` 反推成下拉类型 —— 策划新加一个方法即可在树里调用，**无需改节点类**。

持久化：每棵树一个 `guid`，按 `sceneGuid → processorGuid → parameterList` 三级缓存 → **同名 NPC 跨场景参数互不污染**。

对话表现：`AdvancedText : TextMeshProUGUI` 实现 `ITextPreprocessor`，正则解析 `<0.5>`（逐字延迟）与 `<r=注音></r>`，按索引映射回字符；`Typing()` 协程逐字符改顶点 alpha 实现打字机。

**体现**：async/await + SemaphoreSlim 把"等待玩家操作"写成顺序代码（避免回调地狱）、Composite 模式、反射 + 特性做可扩展事件节点、TMP 顶点级文本动画。

### 13. UI 架构

**特性驱动注册**：窗口标 `[UIWindowData(key, ifCache, assetPath, layerNum, ifPreInit)]`（17 个），`MyFrameRoot` 反射收集自动注册 → 加窗口不用改注册表。

**4 层 Layout**：0=HUD / 1=常规 / 2=二级 / 3=设置，每层带 mask；`OnWindowShow/OnWindowClose` 计数，`Update()` 把 mask 插到 `root.childCount-2`，保证"遮罩挡交互不挡显示"。

**缓存策略**：`ifCache` 关窗只隐藏；`ifPreInit` 启动预实例化；非缓存关窗交还 Addressables。

**视图/数据分离**：`EnemyUGUIBase<T>` + 池化数据对象，视图只读数据。

**UI 被动刷新**：快捷栏每帧调 `skillBehaviour.UpdateSkillSlot(slot)`，**让技能自己决定** CD 填充、图标、遮罩颜色 —— 技能逻辑不反向依赖 UI 类。

### 14. 其他亮点

- **动画层（Playable Graph）**：自建 `PlayableGraph` + `AnimationMixerPlayable(3)` 做 A/B 过渡；封装一维/二维混合树；`UpperLowerMixer`（AvatarMask 上下半身分离，弓箭瞄准时下半身跑动 + 上半身射击）；节点池化；`EnsureAnyWeight` 防权重全零导致空输出。
- **选中描边**：不依赖 URP Renderer Feature —— 第二个相机 + `CommandBuffer.DrawRenderer` 画到 `RenderTexture` 蒙版，`OnRenderImage` 里 `Graphics.Blit` 叠加；只画当前选中项，支持每个物体自定义描边颜色。
- **成长曲线**：`EXPConfig` 用 `AnimationCurve` 分段，`GetLevelAmount` 累加前序区间末值 + 当前曲线采样；`CheckInterval` 做区间重叠校验。
- **初始化顺序**：`[DefaultExecutionOrder(-20)]` MyFrameRoot → `(-100)` SkillCamera → `(-10)` GameSceneManager。
- **敌人回收协议**：`IEnemyRecyclableComponent { Recycle(); ReStart(); }`，用 `Reverse()` 保证父级先于子级重置。
- **输入重绑定**：`ICanInputComponent.InitializeInput / RecoverInput` 区分"新建档默认键"与"读档自定义键"；`InputManager` 支持输入缓存、`keyResponseType`（Down/Hold/Up）、`InputChecker` 条件门（看窗口时不响应技能）。
- **NavMesh 用法**：追踪用 `SetDestination`；绕行/后撤用 `NavMeshAgent.Move()` 局部移动不打断路径；`CheckArriveDestination` 三段判定（`pathPending` → 距离 → 速度平方）确保"真停稳"。

---

## 四、与 MyFrame 的关系

### 形态
`Assets\MyFrame` 是框架的**内嵌副本**，与业务同处一个 `Assets` 目录、没有 asmdef 隔离。

子模块：`Script`(43) / `SkillEditor`(35) / `GOAP`(26) / `NodeSystemTree`(20) / `Animation`(16) / `SkillConfig`(17) / `GOAPEditor`(11) / `Input`(5) / `Editor`(6)。

### 四层衔接机制

| 方式 | 具体 | 用量 |
| --- | --- | --- |
| 静态门面 | `ResSystem` / `PoolSystem` / `EventSystem` / `UISystem` / `SaveSystem` | 业务 229 文件中 87 个显式 `using MyFrame` |
| 基类继承 | `FrameConfigBase`（全部配置 SO）、`UIWindowBase`（17 窗口）、`SingletonMono<T>`、`GameDataContainer`、`DataManager<G,S>` | 40 个文件 |
| 接口实现 | `IGameDataComponent`、`ICanInputComponent`、`IEnemyRecyclableComponent`、`IGOAPOwner`、`ISkillOwner` | — |
| 扩展点复用 | `SkillConfig` / `SkillClip` / `AttackDetectionEvent` / `NodeTreeData`；业务再派生 `PlayerSkillConfig`、`EnemySkillConfig`、`NPCConfig`、`SpeakNodeTree` | — |

### 耦合度
- **业务 → 框架为强依赖**（约 38% 文件显式引用）
- **框架 → 业务仅 6 个编辑器文件**（`SkillEditorWindow` / `SkillGizmosTool` / `AnimationTrack` / `GOAPInspector` 等引用 `Skill_Player` / `Enemy_ControllerBase`）
- **运行时框架零业务引用**

**结论表述**：这是一套"自研框架 + 业务层"分层的 ARPG 原型，业务 1.5 万行、框架 2.1 万行，通过静态门面 + 基类继承 + 接口实现 + 特性反射注册四层机制衔接；运行时保持单向依赖。

---

## 五、简历可用要点（6 条）

1. **设计帧事件驱动的技能系统**：技能拆为动画/音效/特效/攻击检测/自定义事件/相机六条时间轴轨道，按 30 FPS 逻辑帧追帧播放，支持连段窗口、CD 与等级成长、帧级打断与技能间共享数据。
2. **实现四种形态攻击检测与统一命中管线**：武器/盒/球/扇，`Overlap*NonAlloc` + 交换删除压缩结果 + `HashSet` 去重 + 多段命中窗口，全链路结构体传参避免 GC。
3. **基于 Cinemachine 搭建锁定/瞄准/技能运镜三机位相机体系**：屏幕中心射线与 Bounds 求交选目标、目标出画自适应后拉、Impulse 震屏、技能相机贝塞尔轨迹与 FOV 事件。
4. **实现局部时间缩放驱动的顿帧与受击反馈**：把 `LocalTimeScale` 注入技能帧推进、状态计时与动画速度，配合分档受击过渡、击退朝向、伤害飘字与双层血条。
5. **用自研泛型状态机 + GOAP 构建双层敌人 AI**：反向链式规划 + 池化优先队列，并用 Expression Tree 编译状态字段读取、对象池容器消除装箱。
6. **用 async/await + SemaphoreSlim 实现节点树对话系统**：顺序/分支/条件/任务/自定义事件节点自由组合，配合参数触发器与运行时深拷贝，支持多 NPC 跨场景参数独立持久化。

**附加项**：独立开发技能编辑器 / GOAP 编辑器 / 对话树编辑器 / 配置浏览器（UI Toolkit + IMGUI + GraphView + Handles）；特性驱动 + 四层 Layout 的 UI 框架。

---

## 六、写作红线（避免吹过头）

| 项 | 事实 |
| --- | --- |
| 暴击 / 闪避 / 抗性 / 格挡 | **未实现**，只有攻击倍率 + 防御减法 + 固定/百分比加成 |
| 击退位移 | 数据链完整，但实际位移未接入 |
| 技能相机 | 系统完整，但现有 `SkillClip` 未配置相机轨道 → 说"实现了运镜系统"，别说"每个技能都有运镜" |
| 玩家寻路 | 玩家用 `CharacterController`，不用 NavMesh；NavMesh 只用于敌人 |
