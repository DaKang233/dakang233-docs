# 配置文件

配置文件在 **`config/appliedcraftedenergistics-common.toml`**，首次启动游戏时生成。
修改后保存并**重启游戏**生效；服务器与客户端各自读取自己的配置，但世界内的行为以服务端为准。

## 全部配置项

### 气体接口

| 键 | 默认 | 说明 |
|---|---|---|
| `gas_interface.bufferVolumeLiters` | 8000 | ME 气体接口缓冲罐体积（升） |
| `gas_interface.supplyPressureKpa` | 100 | 接口供给压力（kPa，初始值；GUI 内可再调整） |
| `gas_interface.transferRate` | 1000 | 每 tick 缓冲罐 ↔ 网络搬运上限（GU/t） |
| `gas_interface.energyPerKiloGasUnit` | 1.0 | 每 kGU 搬运消耗的 AE |
| `gas_interface.idlePower` | 8.0 | 接口待机耗电（AE/t） |

### 气体 P2P

| 键 | 默认 | 说明 |
|---|---|---|
| `gas_p2p.bufferVolumeLiters` | 4000 | 每个气体 P2P 隧道面呈现的压力容器体积（升，承压 16 atm） |

## 示例

```toml
[gas_interface]
    # 更大的缓冲罐：一次能吞吐更多气体（受 24 atm 承压上限约束）
    bufferVolumeLiters = 16000
    # 更快的网络搬运（服务器性能允许时）
    transferRate = 4000
    # 降低搬运耗电
    energyPerKiloGasUnit = 0.5

[gas_p2p]
    bufferVolumeLiters = 8000
```

::: tip 改动前先备份
配置值会直接影响气体管路的压力平衡。修改大数值前建议先备份存档，尤其是已经用 P2P / 接口
连成一片的气体网络。
:::

## 元件容量不在这里

元件的容量由 `1 byte = 1,000 GU` 和升级卡决定，**不是配置项**；
想改变某只元件的容量，请使用 [元件升级卡](/guide/upgrades)。
