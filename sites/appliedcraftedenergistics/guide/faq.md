# 常见问题与已知限制

## 为什么元件存气体却不显示压力？

因为元件只保存**数量**。压力是"数量 ÷ 体积"的推导量，而 ME 网络里没有"体积"这个概念。
真实的压力交接发生在 [ME 气体接口](/guide/interface) 的槽位容器和 [气体 P2P 隧道](/guide/p2p) 的缓冲罐里。

## 1 byte 到底是多少气体？

**1 AE byte = 1,000 GU = 1,000 升 @ 100 kPa（1 atm）**。
所以 1k 元件（1,024 字节）= 1,024,000 GU = 1,024 m³ 常压气体。

## 装了升级卡后元件显示的容量为什么变大？

升级卡提高的是**该元件的字节上限**。`1 byte = 1,000 GU` 的全局规则不变，
只是这只元件现在有更多字节可用。详见 [元件升级卡](/guide/upgrades)。

## 为什么原版 ME 接口不再从 CCB 管道收气体？

0.2.0 移除了旧版给 `ae2:interface` 添加的气体缓存。气体请使用 **ME 气体接口**
（或输入/输出总线、存储总线、样板供应器）——它们仍然完整支持气体。
原版 ME 接口的物品/流体功能不受影响。

## 气体接口的槽位怎么设置？

- **右击**配置槽（手持气体样本或 CCB 气体容器）：标记气体；
- **滚轮**：目标数量 ±1,000 GU；
- **Shift + 滚轮**：目标压力 ±1 atm（到 0 恢复默认 1 atm）；
- **中键**：循环逐槽模式（需要安装逐槽控制卡）。

## 为什么接口在排气？

安装了**安全阀卡**且某个槽位压力达到 20 atm 时会自动泄压。这是真实排气：
气体通过 CCB 的释放机制排到环境中，会推动附近实体。正常目标压力（≤16 atm）不会触发；
如果频繁排气，请检查该槽位的目标压力与外部管网压力。

## 与 Applied Pneumatics / PneumaticCraft 冲突吗？

不冲突。已在同一 183 模组整合包中同时加载 `Applied Pneumatics 1.0.9`、`PneumaticCraft 8.2.24`
与本模组并启动验证；三者各自注册自己的 key type / 能力，互不覆盖。

## 游戏崩溃了，报告里出现 `GasBufferTank$1` 或类似的 `NoClassDefFoundError`

先确认是不是**在游戏运行中替换了 mod 的 jar**。在运行中的实例里覆盖 jar，会让 JVM 打开的文件
与磁盘内容错位，随后任何一次懒加载都会失败（常见表现：玩一段时间后崩在某个方块实体上）。
处理方式：完全退出游戏 → 重新启动即可；同时以后替换 jar 前先关游戏。

如果重启后仍然复现，请带上 `crash-reports/` 与 `logs/latest.log` 到
[GitHub Issues](https://github.com/DaKang233/AppliedCraftedEnergistics/issues) 反馈。

## 已知限制（0.2.x）

- 输入/输出总线的**逐部件目标压力**尚未实现（气体标记与数量已支持）；
- JEI 拖拽标记已在 0.2.1 支持（需安装 JEI）；
- 便携式气体元件尚未实现；
- 不支持"按气体族系过滤"的分区（模糊卡对气体无意义）；
- 气体的配方以简化配方为主，不追求数值平衡。

## 反馈

- 源码与问题追踪：[GitHub](https://github.com/DaKang233/AppliedCraftedEnergistics)
- 下载：[GitHub Releases](https://github.com/DaKang233/AppliedCraftedEnergistics/releases)
