# 常见问题与已知限制

## 为什么元件存气体却不显示压力？

因为元件只保存**数量**。压力是"数量 ÷ 体积"的推导量，而 ME 网络里没有"体积"这个概念。
真实的压力交接发生在 [ME 气体接口](/guide/interface) 和 [气体 P2P 隧道](/guide/p2p) 的缓冲罐里。

## 1 byte 到底是多少气体？

**1 AE byte = 1,000 GU = 1,000 升 @ 100 kPa（1 atm）**。
所以 1k 元件（1,024 字节）= 1,024,000 GU = 1,024 m³ 常压气体。

## 装了升级卡后元件显示的容量为什么变大？

升级卡提高的是**该元件的字节上限**。`1 byte = 1,000 GU` 的全局规则不变，
只是这只元件现在有更多字节可用。详见 [元件升级卡](/guide/upgrades)。

## 为什么 CCB 管道从 ME 接口抽不到气？

- 检查 ME 接口里是否真的有气体（接口的存储槽 / 网络里的气体）；
- 检查管道压力是否**严格高于**接口侧压力；
- 检查接口是否被 AE2 的"存储总线"之类占用？ME 接口本身只被动提供气体能力，
  它不会主动把气体推到相邻管道。

## 与 Applied Pneumatics / PneumaticCraft 冲突吗？

不冲突。已在同一 183 模组整合包中同时加载 `Applied Pneumatics 1.0.9`、`PneumaticCraft 8.2.24`
与本模组并启动验证；三者各自注册自己的 key type / 能力，互不覆盖。

## 游戏崩溃了，报告里出现 `GasBufferTank$1` 或类似的 `NoClassDefFoundError`

先确认是不是**在游戏运行中替换了 mod 的 jar**。在运行中的实例里覆盖 jar，会让 JVM 打开的文件
与磁盘内容错位，随后任何一次懒加载都会失败（常见表现：玩一段时间后崩在某个方块实体上）。
处理方式：完全退出游戏 → 重新启动即可；同时以后替换 jar 前先关游戏。

如果重启后仍然复现，请带上 `crash-reports/` 与 `logs/latest.log` 到
[GitHub Issues](https://github.com/DaKang233/AppliedCraftedEnergistics/issues) 反馈。

## 已知限制（0.1.x）

- 便携式气体元件尚未实现；
- ME 气体接口的"气罐槽"（把气体灌进 / 倒出 CCB 气罐物品）尚未实现；
- 不支持"按气体族系过滤"的分区（模糊卡对气体无意义）；
- 气体的配方以简化配方为主，不追求数值平衡。

## 反馈

- 源码与问题追踪：[GitHub](https://github.com/DaKang233/AppliedCraftedEnergistics)
- 下载：[GitHub Releases](https://github.com/DaKang233/AppliedCraftedEnergistics/releases)
