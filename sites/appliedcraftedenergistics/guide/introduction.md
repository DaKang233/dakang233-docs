# 这是什么

**Applied Crafted Energistics（应用机巧能源，简称 ACE）** 是一个 **非官方**的
[应用能源 2（AE2）](https://modrinth.com/mod/ae2) 附属模组，把
**Create: Crafted Beginning（机械动力：机巧新生，CCB）** 的气体接入 ME 网络。

| | |
|---|---|
| 支持的 MC 版本 | 1.21.1 |
| 加载器 | NeoForge 21.1.251+ |
| 前置 | AE2 19.2.x、Create 6.0.10.x、Create: Crafted Beginning 0.1.x |
| 当前版本 | 0.1.1 |
| 源码 | [GitHub](https://github.com/DaKang233/AppliedCraftedEnergistics) |

## 能做什么

- **气体存储元件**：把 CCB 的气体存进 ME 网络，按 `1 AE byte = 1,000 GU` 计量；
- **ME 气体接口**：让 ME 网络与相邻的气体储罐 / 管路交换气体，背后是一只真实的 CCB 压力容器；
- **气体 P2P 隧道**：把一段气体管路"瞬移"到网络的另一头；
- **原生设备互通**：AE2 的输入 / 输出 / 存储总线、ME 接口、样板供应器无需改装即可处理气体；
- **元件升级卡**：AE2 原生卡 + 四张气体专属卡（高压 / 扩容 / 多类型 / 安全阀）；
- **GuideME 游戏内教程**：中英双语，游戏里按 `G` 打开。

## 一句话理解"气体与 ME"的关系

AE2 网络只认"**数量**"，而 CCB 的气体由"**数量 + 体积 + 气压**"共同描述。
本模组的做法是：

1. 元件里只保存气体数量（GU），不保存压力；
2. 任何一次"网络 ↔ 真实世界"的交换，都经过一只**真实的气体容器**（接口的缓冲罐、P2P 的缓冲罐），
   由 CCB 自己的管路求解器负责压力；
3. 于是 ME 网络永远不会"凭空产生压力"，也不会把玩家的储罐压爆。

具体换算见 [气压与容量换算](/guide/pressure)。

## 从哪里开始

- 第一次使用：阅读 [安装与版本](/guide/install)；
- 想快速存气：阅读 [气体存储元件](/guide/cells)；
- 想接入工厂：阅读 [ME 气体接口](/guide/interface) 与 [与 AE2 原生设备互通](/guide/interop)。

::: tip 非官方附属
本项目与 Applied Energistics 2、Create、Create: Crafted Beginning 的官方团队无隶属关系；
发布遵循各前置模组的许可证要求，详见 [许可与第三方声明](/guide/license)。
:::
