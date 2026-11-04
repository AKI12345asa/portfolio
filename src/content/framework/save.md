---
title: 存档系统
summary: 用「槽目录 + 数据块文件」的存档模型，二进制与 JSON 双通道，一套装饰器容器抹平两种序列化器的差异。
highlight: Serialized_Dic 一套代码同时喂给 Unity 和 BinaryFormatter
order: 9
diagram: /framework/save.svg
diagramCaption: 初始化 → 读取 → 保存
stack: ['BinaryFormatter', 'JsonUtility', 'FileStream']
files: 8
lines: 853
---

## 存储结构

```
persistentDataPath/
├─ SaveData/
│  ├─ index            ← 槽索引
│  ├─ slot_0/…
│  └─ slot_1/…
└─ Setting/            ← 全局设置，与玩家存档分开
```

玩家数据（`GameDataContainer`）和设置数据（`SettingDataContainer`）走两个不同的目录，「删档重来」因此不会把设置一起清掉。

## 双通道

`MyFrameSetting.SaveSystemType` 一个开关切换：

- **Binary**：`BinaryFormatter` 直接序列化对象图，写 `.bytes`；
- **Json**：`JsonUtility` 走 Unity 的序列化规则，写 `.json`。

二进制更小更快，JSON 方便调试，按开发阶段选就行。两种序列化器的规则并不一致，中间需要一层适配，下面那个容器就是为此存在的。

## `Serialized_Dic` 与序列化适配

Unity 的序列化器不序列化 `Dictionary`，`BinaryFormatter` 又要求字段本身可序列化，`Serialized_Dic<K,V>` 要同时满足这两条。

它的做法是：对外用 `[NonSerialized]` 的字典，序列化时把字典拆成两个 `List`，一份 key 列表、一份 value 列表；回调也备了两套，`ISerializationCallbackReceiver` 给 Unity 用，`[OnSerializing]` / `[OnDeserialized]` 给 BinaryFormatter 用。同一份代码，两种序列化器都能吃。

`Serialized_Vector` / `Serialized_Color` 是同样的思路，把值类型降级成纯 float 字段，再用隐式转换提供原类型的接口。

## 读图要点

初始化时读索引建立内存缓存，之后读取只需查缓存定位到块文件。保存是收集数据块、按通道序列化、更新索引三步。加载完成后会触发事件，UI 自己刷新，存档系统不需要认识任何界面。

