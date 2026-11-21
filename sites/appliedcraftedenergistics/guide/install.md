# 安装与版本

## 前置版本

| 组件 | 版本 |
|---|---|
| Minecraft | 1.21.1 |
| NeoForge | 21.1.251 或更高（21.1.x） |
| Applied Energistics 2 | 19.2.x |
| Create | 6.0.10.x |
| Create: Crafted Beginning | 0.1.x（0.1.1 已验证；0.1.2 源码改过气体网络调度，公开 API 未变，发布后需回归） |
| MEGA Cells | 4.11.x，**可选**；仅 1M–256M 元件的默认配方需要 |
| Applied Crafted Energistics | 0.2.2 |

以上版本范围也写进了模组的 `neoforge.mods.toml`，版本不符时加载器会直接提示。
MEGA Cells 是可选的配方前置：不安装时基础 1k–256k 元件和其余功能照常工作。

## 安装

1. 安装 **NeoForge 1.21.1**（≥ 21.1.251）；
2. 把以下 jar 放进整合包的 `mods/` 目录：
   - `appliedenergistics2-19.2.x.jar`
   - `create-1.21.1-6.0.10.x.jar`
   - `createcraftedbeginning-0.1.x.jar`
   - `appliedcraftedenergistics-1.21.1-neoforge-0.2.2.jar`
3. 如需默认的 1M–256M 配方，再加入 `megacells-4.11.x.jar`；不安装 MEGA 也可启动和使用基础元件。
4. 启动游戏。

> 本模组是纯附属，不需要新建世界、不需要额外资源包，也没有客户端 / 服务端分离的额外要求；
> 服务端需要与客户端安装同样的模组。

## 版本与下载

- 发布页：[GitHub Releases](https://github.com/DaKang233/AppliedCraftedEnergistics/releases)
- 当前版本 `0.2.2` 的文件校验：
  - 大小 289,395 字节
  - SHA-256 `A05632AFBFF2BBB578F52629ACC29864F0D5F5996A514A0CEC9127E1A92B4044`

## 从 0.1.x 升级到 0.2.x

- 旧接口 8 kL 缓冲罐中的气体会自动转入新接口的第一个空槽；
- 旧的单设备模式与供给压力设置不再使用，改为逐槽设置；
- 原版 `ae2:interface` 的气体能力在 0.2.2 由新的适配器恢复；旧版本行为可能不同。

## 升级注意

- **先完全退出游戏，再替换 `mods/` 里的 jar**。
  在游戏运行中覆盖 jar 会导致打开的文件与磁盘内容错位，之后任何一次懒加载都会抛
  `NoClassDefFoundError`（表现为"玩一段时间后崩溃在某个方块实体上"）。
- 替换后重启游戏即可；世界存档不需要迁移。

## 验证安装是否成功

进入游戏后，如果模组加载正常：

- 创造模式物品栏里能看到“气体存储元件”等物品；
- 任意物品栏界面按 `G` 能打开 GuideME 教程；
- `logs/latest.log` 里会出现两行以 `Applied Crafted Energistics:` 开头的日志。
