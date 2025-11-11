# AT 命令修正完成報告

## 日期: 2025-11-10

## 背景

用戶在測試 Provisioning 流程時發現多個 AT 命令參數順序錯誤：
1. `AT+MSAA` - 添加訂閱地址
2. `AT+MPAS` - 設置發佈地址  
3. `AT+MAKB` - 綁定 Model AppKey
4. `AT+MDTS` - 發送 Vendor 數據

## 執行步驟

### 1. 全面審查所有 AT 命令
建立 `AT_COMMAND_REVIEW.md` 文件，對照 SDK 文件檢查所有 14 個 AT 命令的參數順序和格式。

### 2. 修正發現的問題

#### 2.1 修正 `async_provisioner_manager.py`

**問題 1: `provision_device` 方法中的 `async_cmd_bind_model` 調用錯誤**
- 位置: Line 315
- 錯誤: 第二個參數使用 `unicast_addr` (例如 0x0100)
- 修正: 改為 element_index `"0"`
```python
# 修正前
result = await async_cmd_bind_model(unicast_addr, unicast_addr, "0x1000", "0")
# 生成: AT+MAKB 0x0100 0x0100 0x1000 0 ❌

# 修正後
result = await async_cmd_bind_model(unicast_addr, "0", "0x1000", "0")
# 生成: AT+MAKB 0x0100 0 0x1000 0 ✅
```

**問題 2: `set_publish` 方法參數順序錯誤**
- 位置: Lines 464-472
- 錯誤: model_id 和 publish_addr 順序顛倒
- 修正: 
```python
# 修正後的參數順序
result = await async_cmd_set_publish(
    node_addr,
    int(element_addr) if element_addr.isdigit() else 0,
    model_id,      # 先 model_id
    publish_addr,  # 後 publish_addr
    0
)
# 生成: AT+MPAS 0x0100 0 0x1000 0xC000 0 ✅
```

**問題 3: `add_subscription` 方法參數順序錯誤**
- 位置: Lines 486-498
- 錯誤: model_id 和 subscription_addr 順序顛倒
- 修正:
```python
# 修正後的參數順序
result = await async_cmd_add_subscription(
    node_addr,
    int(element_addr) if element_addr.isdigit() else 0,
    model_id,           # 先 model_id
    subscription_addr   # 後 subscription_addr
)
# 生成: AT+MSAA 0x0100 0 0x1000 0xC000 ✅
```

#### 2.2 修正 `async_at_command.py`

**問題: `async_cmd_send_vendor_data` 參數完全不符合 SDK 文件**
- 錯誤簽名: `(dst_addr, appkey_index, opcode, payload_length, payload)`
- SDK 格式: `AT+MDTS [dst] [element_index] [app_key_idx] [ack] [data]`
- 修正後:
```python
def async_cmd_send_vendor_data(
    dst_addr: str,
    element_index: int = 0,
    app_key_idx: int = 0,
    ack: int = 0,
    data: str = ""
) -> AsyncATCommand:
    """Send vendor model data."""
    return AsyncATCommand(
        "MDTS",
        [dst_addr, str(element_index), str(app_key_idx), str(ack), data]
    )
```

### 3. 建立驗證測試

#### 3.1 命令格式驗證測試 (`test_commands_validation.py`)
測試所有 AT 命令生成的格式是否符合 SDK 文件規格。

**測試結果**: ✅ 所有 14 個命令格式正確

```
✅ AT+VER
✅ AT+MRG
✅ AT+NR
✅ AT+DIS 1 / AT+DIS 0
✅ AT+PBADVCON
✅ AT+PROV
✅ AT+AKA 0x0100 0 0
✅ AT+MAKB 0x0100 0 0x1000 0
✅ AT+NL
✅ AT+MSAA 0x0100 0 0x1000 0xC000
✅ AT+MSAD 0x0100 0 0x1000 0xC000
✅ AT+MPAS 0x0100 0 0x1000 0xC000 0
✅ AT+MPAD 0x0100 0 0x1000 0
✅ AT+MDTS 0x0100 0 0 0 870100050AFF00FF00
```

#### 3.2 基本命令硬體測試 (`test_basic_commands.py`)
測試基本命令能否正確執行（不需要 Provisioning 的命令）。

**測試結果**: ✅ 所有基本命令正常工作

```
✅ AT+VER → SUCCESS, Version: 1.0.6
✅ AT+MRG → SUCCESS, Role: PROVISIONER
✅ AT+DIS → SUCCESS (開始/停止掃描)
```

## 修正前後對比

### AT+MAKB (Model AppKey Binding)
```diff
- AT+MAKB 0x0100 0x0100 0x1000 0  ❌ (element_index 錯誤使用 address)
+ AT+MAKB 0x0100 0 0x1000 0       ✅ (element_index 正確)
```

### AT+MSAA (Add Subscription)
```diff
- AT+MSAA 0x0100 0x0100 0xC000 0x1000  ❌ (參數順序錯誤)
+ AT+MSAA 0x0100 0 0x1000 0xC000       ✅ (參數順序正確)
```

### AT+MPAS (Set Publish)
```diff
- AT+MPAS 0x0100 0x0100 0xC000 0x1000 0  ❌ (參數順序錯誤)
+ AT+MPAS 0x0100 0 0x1000 0xC000 0       ✅ (參數順序正確)
```

### AT+MDTS (Send Vendor Data)
```diff
- async_cmd_send_vendor_data(dst, appkey_idx, opcode, len, payload)  ❌
+ async_cmd_send_vendor_data(dst, element_idx, app_key_idx, ack, data)  ✅
```

## 關鍵發現

### Element Index vs Element Address
這是主要的混淆來源：
- **Element Index**: 相對於節點的元素索引，從 0 開始 (0, 1, 2, ...)
- **Element Address**: 絕對地址，unicast address + element index (0x0100, 0x0101, ...)

大多數 AT 命令需要的是 **Element Index**，不是 Element Address。

### 文件對照的重要性
所有參數必須嚴格對照 SDK 文件，不能憑記憶或假設。建議：
1. 每個命令實作時對照文件
2. 參數命名應該與文件一致
3. 添加參數驗證

## 未來改進建議

1. **參數型別統一**: 
   - 目前 element_index 有時是 str，有時是 int
   - 建議統一使用 int，在命令生成時轉為 str

2. **參數驗證**:
   - Group 地址範圍: 0xC000 ~ 0xFFFF
   - Unicast 地址範圍: 0x0001 ~ 0x7FFF
   - Element index 範圍: 0 ~ element_num-1

3. **增加文件註解**:
   - 每個函數添加 SDK 文件對應的命令格式
   - 說明每個參數的含義和有效範圍

4. **AT+NL 測試**:
   - 目前 list_nodes 需要在有已綁定節點時測試
   - 回應格式為 `NL-MSG` 而非 `NL`
   - 需要修正 message listener 的路由邏輯

## 結論

✅ 所有命令參數順序已修正
✅ 所有命令格式驗證通過
✅ 基本命令硬體測試通過
⏳ Provisioning 流程測試待進行（需要實際設備綁定）

下一步應該進行完整的 Provisioning 流程測試，驗證：
1. PBADVCON → PROV → AKA → MAKB 流程
2. MSAA 訂閱設置
3. MPAS 發佈設置
4. MDTS Vendor 數據發送
5. NL 節點列表查詢
