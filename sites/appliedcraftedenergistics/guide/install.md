# 安装与版本

## 前置版本

| 组件 | 版本 |
|---|---|
| Minecraft | 1.21.1 |
| NeoForge | 21.1.251 或更高（21.1.x） |
| Applied Energistics 2 | 19.2.x |
| Create | 6.0.10.x |
| Create: Crafted Beginning | 0.1.x（0.1.1 已验证；0.1.2 源码改过气体网络调度，公开 API 未变，发布后需回归） |
| Applied Crafted Energistics | 0.1.x |

以上版本范围也写进了模组的 `neoforge.mods.toml`，版本不符时加载器会直接提示。

## 安装

1. 安装 **NeoForge 1.21.1**（≥ 21.1.251）；
2. 把以下四个 jar 放进整合包的 `mods/` 目录：
   - `appliedenergistics2-19.2.x.jar`
   - `create-1.21.1-6.0.10.x.jar`
   - `createcraftedbeginning-0.1.x.jar`
   - `appliedcraftedenergistics-1.21.1-neoforge-0.1.1.jar`
3. 启动游戏。

> 本模组是纯附属，不需要新建世界、不需要额外资源包，也没有客户端 / 服务端分离的额外要求；
> 服务端需要与客户端安装同样的四个模组。

## 版本与下载

- 发布页：[GitHub Releases](https://github.com/DaKang233/AppliedCraftedEnergistics/releases)
- 当前版本 `0.1.1` 的文件校验：
  - 大小 200,868 字节
  - SHA-256 `3AB56065547E77A5D739D3229EBED77981EA931D64897AC294D7CE868DAD43EA`

## 升级注意

- **先完全退出游戏，再替换 `mods/` 里的 jar**。
  在游戏运行中覆盖 jar 会导致打开的文件与磁盘内容错位，之后任何一次懒加载都会抛
  `NoClassDefFoundError`（表现为"玩一段时间后崩溃在某个方块实体上"）。
- 替换后重启游戏即可；世界存档不需要迁移。

## 验证安装是否成功

进入游戏后，如果模组加载正常：

- 创造模式物品栏里能看到"气体存储元件"等物品；
- 任意物品栏界面按 `G` 能打开 GuideME 教程；
- `logs/latest.log` 里会出现两行以 `Applied Crafted Energistics:` 开头的日志。
