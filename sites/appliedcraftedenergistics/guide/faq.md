# 常见问题与已知限制

## 为什么元件存气体却不显示压力？

因为元件只保存**数量**。压力是“数量 ÷ 体积”的推导量，而 ME 网络里没有“体积”这个概念。
真实的压力交接发生在 [ME 气体接口](/guide/interface) 的槽位容器和 [气体 P2P 隧道](/guide/p2p) 的缓冲罐里。

## 1 byte 到底是多少气体？

**1 AE byte = 1,000 GU = 1,000 升 @ 100 kPa（1 atm）**。
所以 1k 元件（1,024 字节）= 1,024,000 GU = 1,024 m³ 常压气体；
1M 元件（1,048,576 字节）= 1,048,576,000 GU。

## 装了升级卡后元件显示的容量为什么变大？

升级卡提高的是**该元件的字节上限**。`1 byte = 1,000 GU` 的全局规则不变，
只是这只元件现在有更多字节可用。详见 [元件升级卡](/guide/upgrades)。

## 为什么 1M–256M 元件没有配方？

这些元件的默认配方以 **MEGA Cells** 为前置，并且带 `neoforge:mod_loaded` 条件：
**只有安装 MEGA Cells 时，默认配方才会加载和显示**。

- 想用默认配方：安装 MEGA Cells 4.11.x；
- 不想装 MEGA：用数据包覆盖 `data/appliedcraftedenergistics/recipe/gas_cell_*.json`；
- 想移除默认配方：把 `recipes.enable_mega_cell_recipes` 设为 `false`。

元件本身始终注册，可由创造模式或命令获得。详见 [配置文件](/guide/config)。

## 原版 ME 接口能处理气体吗？

可以。0.2.2 通过 `AeInterfaceGasCompat` 为原版 `ae2:interface` 注册气体能力：
它的槽位以固定 100 kPa 容器暴露给 CCB 管道，管道可以从接口抽气。
ACE 自己的 ME 气体接口额外提供逐槽目标数量、目标压力和传输模式。

## 气体接口的槽位怎么设置？

- **点击配置槽上方的设置按钮**，或**中键点击**配置槽：打开逐槽设置界面；
- 设置界面可编辑**目标数量**、**目标压力**和（安装逐槽控制卡后）**传输模式**；
- 右键配置槽（手持气体样本 / CCB 气体容器）：标记气体；
- 安装 JEI 时也可以从 JEI 拖拽气体 ingredient 到配置槽。

## 为什么接口在排气？

安装了**安全卡**（`safety_valve_card`）且某个槽位压力达到 20 atm 时会自动泄压。这是真实排气：
气体通过 CCB 的释放机制排到环境中，会推动附近实体。正常目标压力（≤16 atm）不会触发；
如果频繁排气，请检查该槽位的目标压力与外部管网压力。

> 元件上的 `relief_valve_card` 中文名是 **泄压阀卡**，与本接口的 **安全卡** 不同。

## 输入/输出总线的目标压力怎么设置？

在总线里安装 **气体压力卡**（`gas_pressure_card`）：
输出总线只输出到目标压力，输入总线只在高于目标压力时抽取；右键循环预设，潜行右键回退。

## 气体自动合成在重载存档后失败？

0.2.2 已修复：`GasKey` 使用注册表里的规范 Gas 对象作为 AE2 主键，保存并重载世界后合成计划的 Key 查找仍然稳定。
如果仍遇到问题，请带上存档、`crash-reports/` 和 `logs/latest.log` 反馈。

## 与 Applied Pneumatics / PneumaticCraft 冲突吗？

不冲突。已在同一 183 模组整合包中同时加载 `Applied Pneumatics 1.0.9`、`PneumaticCraft 8.2.24`
与本模组并启动验证；三者各自注册自己的 key type / 能力，互不覆盖。

## 游戏崩溃了，报告里出现 `GasBufferTank$1` 或类似的 `NoClassDefFoundError`

先确认是不是**在游戏运行中替换了 mod 的 jar**。在运行中的实例里覆盖 jar，会让 JVM 打开的文件
与磁盘内容错位，随后任何一次懒加载都会失败（常见表现：玩一段时间后崩在某个方块实体上）。
处理方式：完全退出游戏 → 重新启动即可；同时以后替换 jar 前先关游戏。

如果重启后仍然复现，请带上 `crash-reports/` 与 `logs/latest.log` 到
[GitHub Issues](https://github.com/DaKang233/AppliedCraftedEnergistics/issues) 反馈。

## 已知限制（0.2.2）

- 便携式气体元件尚未实现；
- 不支持“按气体族系过滤”的分区（模糊卡对气体无意义）；
- 标准 AE2 处理样板不携带目标压力，压力仍由机器/容器决定；
- 1M–256M 的默认配方需要 MEGA Cells；不装 MEGA 时需要自定义数据包；
- 气体的配方以简化配方为主，不追求数值平衡。

## 反馈

- 源码与问题追踪：[GitHub](https://github.com/DaKang233/AppliedCraftedEnergistics)
- 下载：[GitHub Releases](https://github.com/DaKang233/AppliedCraftedEnergistics/releases)
- 许可证：**LGPL v3.0**（SPDX: `LGPL-3.0-only`），详见 [许可与第三方声明](/guide/license)。
