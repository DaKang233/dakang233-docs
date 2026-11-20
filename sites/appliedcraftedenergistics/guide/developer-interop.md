::: warning 0.2.0 文档说明
0.2.0 已**移除**给原版 `ae2:interface` 添加气体缓存的 `AeInterfaceGasCompat`：
现在只有 ACE 的 ME 气体接口暴露 CCB 气体能力（`GasInterfaceStorageView`，9 个逐槽
`GasPressureCompartment`，体积 = 目标数量 / 目标压力）。下文中关于 `ae2:interface` 兼容的
小节保留作历史记录；其余端点契约、CCB 求解器要求与 0.1.2 兼容性分析仍然有效。
:::
# 开发者：与 CCB 气体管网的交互

本页写给想看代码的人：**本模组不实现自己的气体网络，而是"扮演一个符合 CCB 契约的真实容器"**，
让 CCB 的管道求解器自己完成压力、流量与回滚。下面按契约 → 接触点 → AE 侧策略 → 0.1.2 兼容性展开。

## 1. CCB 端点契约（0.1.1 与 0.1.2 均成立）

CCB 的管网只接受满足以下条件的端点（`GasEndpointDiscovery`，0.1.1 与 0.1.2 的判定一致）：

```java
GasHandler handler = level.getCapability(GasCapabilities.BLOCK, pos, face);
if (handler instanceof GasStorageHandler tanks) {
    for (int tank = 0; tank < tanks.getTanks(); tank++) {
        GasPressureCompartment compartment = tanks.getPressureCompartment(tank);
        if (compartment.getVolume() <= 0) continue;   // 没有体积 = 不是容器 = 不产生流量
        ...
    }
}
```

因此集成点必须同时满足：

| 契约 | 方法 | 我们的实现 |
|---|---|---|
| 方块能力 | `GasCapabilities.BLOCK` | 方块 / part 上注册 |
| 存储端点 | `GasStorageHandler` | `GasBufferTank`、`InterfaceGasHandler`、`TankView` |
| 有体积 | `getVolume() > 0` | 接口缓冲罐、P2P 缓冲罐、AE 接口每槽虚拟体积 |
| 压力模型 | `getPressureModel()` 返回 `VARIABLE` 或 `FIXED` | 真实罐用 `VARIABLE`（默认），AE 接口槽位用 `FIXED` |
| 可回滚 | `captureTransferSnapshot()` / `restoreDrainedGas()` | `GasBufferTank` 快照、AE 槽位写回 |
| 预测 | `predictTransferLimits(gas, amount)` | 按承压/存量给出可抽/可注上限 |
| 分组 | `getCompartmentIdentity()` | AE 接口每个槽位一个 identity；P2P 每个 part 一个 |

## 2. 四个接触点

### 2.1 ME 气体接口方块：把缓冲罐直接交给 CCB

```java
// init/ACECapabilities.java
event.registerBlockEntity(
        GasCapabilities.BLOCK,
        ACEBlockEntities.ME_GAS_INTERFACE.get(),
        (be, side) -> be.getTank());     // 每个面都是同一只 GasBufferTank
```

缓冲罐实现 CCB 的两个接口（`core/GasBufferTank.java`）：

```java
public class GasBufferTank implements GasStorageHandler, GasPressureCompartment {
    @Override public long getVolume()       { return volumeLiters; }
    @Override public long getPressurePa()   { return GasPressure.pressure(gas.getAmount(), volumeLiters); }
    @Override public long getMaxAmount()    { return GasPressure.amount(volumeLiters, maxPressurePa); }

    @Override
    public GasTransferSnapshot captureTransferSnapshot() { ... }   // 求解器回滚用
}
```

AE 网络与这只罐之间的搬运完全在 `GasInterfaceBlockEntity.serverTick()` 里，用 AE2 的
`StorageHelper.poweredInsert/poweredExtraction` 做"模拟 → 提交"，细节见
[ME 气体接口](/guide/interface)。

### 2.2 气体 P2P 隧道：输入端只收、输出端只放

```java
// device/p2p/GasP2PTunnelPart.java
private GasBufferTank storage() {
    if (!isOutput()) return buffer;                 // 输入端：自己的罐
    GasP2PTunnelPart input = getInput();
    return input != null ? input.buffer : null;     // 输出端：读输入端同一只罐
}

// TankView.fill：输出端永远返回 0，气体只能从输入端进
// TankView.drain：输入端永远返回 EMPTY，输出端从输入罐抽并 deductTransportCost()
```

每个面的 `GasPressureCompartment` 都由 `TankView` 提供，所以 CCB 管道在两端都看到"一只真实的罐"。

### 2.3 AE2 的 ME 接口：只抽不灌的固定压力源

AE2 的 ME 接口本来就能把气体放进 9 个槽，但 CCB 管道不会主动来抽。所以给 `ae2:interface`
补一个 `GasCapabilities.BLOCK`（`integration/AeInterfaceGasCompat.java`），并且每个槽位是一个
**FIXED 压力**的虚拟容器：

```java
@Override public long getPressurePa()            { return SUPPLY_PRESSURE_PA; } // 100 kPa
@Override public PressureModel getPressureModel() { return PressureModel.FIXED; }
@Override public long fill(GasStack resource, GasAction action) { return 0; }   // 只抽不灌

@Override
public GasStack drain(long maxDrain, GasAction action) {
    long extracted = inventory.extract(slot, key, Math.min(maxDrain, storedAmount()),
            action.execute() ? Actionable.MODULATE : Actionable.SIMULATE);
    return extracted <= 0 ? GasStack.EMPTY : key.toGasStack(extracted);
}
```

只抽不灌是刻意的：AE2 拥有这些槽位并会按请求补货、把放不下的推回网络；如果 CCB 管道也能写入，
两边每个 tick 会互相打架（复制 / 吞气）。样板供应器同理不纳入这条路径（其返回库存禁止外部抽取），
气体推送走下一节的导出策略。

### 2.4 AE2 原生总线 / 样板供应器：策略层

```java
// integration/ACEGasIntegration.java
ExternalStorageStrategy.register(GasKeyType.TYPE, GasExternalStorageStrategy::new);   // 存储总线
StackImportStrategy.register(GasKeyType.TYPE, ACEGasIntegration::createImportStrategy); // 输入总线
StackExportStrategy.register(GasKeyType.TYPE, ACEGasIntegration::createExportStrategy); // 输出总线 + 样板供应器
GenericSlotCapacities.register(GasKeyType.TYPE, INTERFACE_SLOT_CAPACITY);              // 接口/样板槽容量
```

`GasHandlerStrategy` 把 AE2 的 "AEKey + 数量" 翻译成相邻 CCB handler 的 `fill`/`drain`；
`GasMachineExternalStorageFacade` 把每个 CCB 罐映射成 ME 的一个槽位。
这条路径由 **AE2 设备主动 pull/push**，不参与 CCB 的压力求解。

## 3. 与 CCB 0.1.2 的兼容性

CCB 0.1.2（源码已提交到 `CreateCraftedBeginning` 仓库，尚未发布）的主要变更是
**"Rework gas network flow and pressure scheduling"**：用 Zone / Branch 调度替换了原来的
图求解器（移除 `GasPressureGraphSolver` 等，新增 `GasZonePressure`、`GasZoneRoute`、
`GasBranchRound`、`GasFixedManifold` 等），传输执行改为 pair 级执行。

对现有逻辑的影响评估：

| 检查项 | 结论 |
|---|---|
| 公开 API（`api.gas.*`、`api.canister.*`） | **逐字节比较：无改动**（0.1.2 只改了 `api.gasreleasehandlers.*`，本模组未使用）→ 可直接编译 |
| 端点契约（`GasStorageHandler` + `volume > 0`） | 新 `GasEndpointDiscovery` 仍是同一判定 → 我们的容器仍被识别 |
| `PressureModel.FIXED` | 新 `GasEndpointPlanner` 仍区分 FIXED/VARIABLE，FIXED 直接使用 handler 报出的压力 → AE 接口槽位行为保持 |
| 快照 / 回滚 | `GasTransferExecutor.executePooledTransfer` 仍调用 `captureTransferSnapshot`/`restoreDrainedGas` → 我们的实现继续生效 |
| `predictTransferLimits` | 新 `GasNetworkPressureEndpoint` 仍使用 → 我们给出的抽/注上限继续生效 |
| 槽位分组（`getCompartmentIdentity`） | 新 `GasEndpointPlanner` 仍按 identity 分组 → ME 接口"每槽一个组"的假设仍成立 |
| 流量/时序 | 求解器调度方式改变，**同一网络的传输量、每 tick 顺序可能不同**；我们的代码不依赖顺序，但需要回归测试 |

**结论：不会破坏现有逻辑，也不需要改代码；但 0.1.2 发布后需要跑一次运行时回归。**
重点验证：

1. ME 气体接口：空罐导入、满罐停止、双向模式在供给压力上下切换；
2. AE2 ME 接口：单槽/多槽、不同气体、两个方向的管道同时抽取；
3. 气体 P2P：输入只收、输出只放、断开输出后缓冲不丢气、扣费正常；
4. 与 0.1.2 新增/调整的"气体释放、进气范围"相邻时的表现（例如接口旁边有开放管口）。

本模组声明的 CCB 版本范围是 `[0.1.1, 0.2)`，0.1.2 在范围内，发布后替换 jar 即可测试。
