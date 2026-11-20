# 配置文件

配置文件在 **`config/appliedcraftedenergistics-common.toml`**，首次启动游戏时生成。
修改后保存并**重启游戏**生效；服务器与客户端各自读取自己的配置，但世界内的行为以服务端为准。

## 全部配置项（0.2.0）

### ME 气体接口

| 键 | 默认 | 说明 |
|---|---|---|
| `gas_interface.idlePower` | 8.0 | 接口待机耗电（AE/t） |

接口的逐槽目标数量、目标压力与传输模式**不在配置文件中**，而是在 GUI 内逐槽设置并存档。

### 气体 P2P

| 键 | 默认 | 说明 |
|---|---|---|
| `gas_p2p.bufferVolumeLiters` | 4000 | 每个气体 P2P 隧道面呈现的压力容器体积（升，承压 16 atm） |

## 示例

```toml
[gas_interface]
    # 接口待机耗电（AE/t）
    idlePower = 8.0

[gas_p2p]
    bufferVolumeLiters = 4000
```

## 已废弃的 0.1.x 配置

以下键在 0.2.0 中不再使用（旧配置文件里的值会被忽略）：

- `gas_interface.bufferVolumeLiters`
- `gas_interface.supplyPressureKpa`
- `gas_interface.transferRate`
- `gas_interface.energyPerKiloGasUnit`

## 元件容量不在这里

元件的容量由 `1 byte = 1,000 GU` 和升级卡决定，**不是配置项**；
想改变某只元件的容量，请使用 [元件升级卡](/guide/upgrades)。
