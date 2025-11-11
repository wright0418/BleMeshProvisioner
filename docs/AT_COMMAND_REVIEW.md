# AT 命令參數審查報告

## 審查日期: 2025-11-10

### 檢查的命令

根據 `SDK_DOC/RL62M02_Provisioner_ATCMD.md` 檢查所有 AT 命令的參數順序和類型。

---

## 1. ✅ AT+VER - 查詢韌體版本
**格式**: `AT+VER`
**實作**: `async_cmd_get_version()` 
**狀態**: ✅ 正確

---

## 2. ✅ AT+MRG - 查詢角色
**格式**: `AT+MRG`
**實作**: `async_cmd_get_role()`
**狀態**: ✅ 正確

---

## 3. ✅ AT+NR - 清除 Mesh 網路
**格式**: `AT+NR [param]`
**實作**: `async_cmd_mesh_clear()`
**狀態**: ✅ 正確

---

## 4. ✅ AT+DIS - 掃描設備
**格式**: `AT+DIS [param]` (1=開始, 0=停止)
**實作**: 
- `async_cmd_start_scan()` → `AT+DIS 1`
- `async_cmd_stop_scan()` → `AT+DIS 0`
**狀態**: ✅ 正確

---

## 5. ✅ AT+PBADVCON - 開啟 PB-ADV 通道
**格式**: `AT+PBADVCON [DEV_UUID]`
**實作**: `async_cmd_open_pbadv(uuid)` → `AT+PBADVCON {uuid}`
**狀態**: ✅ 正確

---

## 6. ✅ AT+PROV - Provisioning
**格式**: `AT+PROV`
**實作**: `async_cmd_provision(unicast_addr, attention_duration)` → `AT+PROV`
**狀態**: ✅ 正確 (參數未被使用，僅用於文檔目的)

---

## 7. ✅ AT+AKA - 添加 AppKey
**文檔格式**: `AT+AKA [dst] [app_key_index] [net_key_index]`
**實作**: `async_cmd_add_appkey(node_addr, app_key_index, net_key_index)`
```python
AsyncATCommand("AKA", [node_addr, str(app_key_index), str(net_key_index)])
```
**範例**: `AT+AKA 0x100 0 0`
**狀態**: ✅ 正確

---

## 8. ❌ AT+MAKB - 綁定 Model AppKey
**文檔格式**: `AT+MAKB [dst] [element_index] [model_id] [app_key_index]`
**實作**: `async_cmd_bind_model(node_addr, element_index, model_id, appkey_index)`
```python
AsyncATCommand("MAKB", [node_addr, element_index, model_id, appkey_index])
```
**範例**: `AT+MAKB 0x100 0 0x1000ffff 0`

### 🔴 問題: `provision_device` 方法中的調用錯誤
**錯誤代碼**:
```python
result = await async_cmd_bind_model(
    unicast_addr,
    unicast_addr,  # ❌ 錯誤: 應該是 element_index (0)
    "0x1000",
    "0"
)
```
生成命令: `AT+MAKB 0x0100 0x0100 0x1000 0` ❌

**正確代碼**:
```python
result = await async_cmd_bind_model(
    unicast_addr,
    "0",  # ✅ 正確: element_index
    "0x1000",
    "0"
)
```
生成命令: `AT+MAKB 0x0100 0 0x1000 0` ✅

---

## 9. ✅ AT+NL - 列出節點
**格式**: `AT+NL`
**實作**: `async_cmd_list_nodes()` → `AT+NL`
**回應**: `NL-MSG <index> <unicast_addr> <element_num> <state_online>`
**狀態**: ✅ 正確

---

## 10. ✅ AT+MSAA - 添加訂閱地址
**文檔格式**: `AT+MSAA [dst] [element_index] [model_id] [Group_addr]`
**實作**: `async_cmd_add_subscription(node_addr, element_idx, model_id, group_addr)`
```python
AsyncATCommand("MSAA", [node_addr, str(element_idx), model_id, group_addr])
```
**範例**: `AT+MSAA 0x100 0 0x1000ffff 0xc000`
**狀態**: ✅ 正確 (已修正)

---

## 11. ✅ AT+MSAD - 刪除訂閱地址
**文檔格式**: `AT+MSAD [dst] [element_index] [model_id] [Group_addr]`
**實作**: `async_cmd_remove_subscription(node_addr, element_idx, model_id, group_addr)`
```python
AsyncATCommand("MSAD", [node_addr, str(element_idx), model_id, group_addr])
```
**狀態**: ✅ 正確

---

## 12. ✅ AT+MPAS - 設置發佈地址
**文檔格式**: `AT+MPAS [dst] [element_idx] [model_id] [publish_addr] [publish_app_key_idx]`
**實作**: `async_cmd_set_publish(node_addr, element_idx, model_id, publish_addr, appkey_index)`
```python
AsyncATCommand("MPAS", [node_addr, str(element_idx), model_id, publish_addr, str(appkey_index)])
```
**範例**: `AT+MPAS 0x100 0 0x1000ffff 0x101 0`
**狀態**: ✅ 正確 (已修正)

---

## 13. ✅ AT+MPAD - 刪除發佈地址
**文檔格式**: `AT+MPAD [dst] [element_idx] [model_id] [publish_app_key_idx]`
**實作**: `async_cmd_clear_publish(node_addr, element_idx, model_id, appkey_index)`
```python
AsyncATCommand("MPAD", [node_addr, str(element_idx), model_id, str(appkey_index)])
```
**狀態**: ✅ 正確

---

## 14. ✅ AT+MDTS - 發送 Vendor 數據
**文檔格式**: `AT+MDTS [dst] [element_index] [app_key_idx] [ack] [data(1~20bytes)]`
**實作**: `async_cmd_send_vendor_data(dst_addr, appkey_index, opcode, payload_length, payload)`

### ⚠️ 注意: 參數不匹配文檔
**文檔參數**: `[dst] [element_index] [app_key_idx] [ack] [data]`
**實作參數**: `[dst_addr] [appkey_index] [opcode] [payload_length] [payload]`

這可能是舊版本或不同用途的實作，需要確認實際使用情境。

---

## 總結

### 需要修正的問題:

1. **async_provisioner_manager.py 中的 `provision_device` 方法**
   - 第 315 行: `async_cmd_bind_model` 的第二個參數應該從 `unicast_addr` 改為 `"0"`

### 已修正的問題:

1. ✅ `add_subscription` 參數順序 (已修正)
2. ✅ `set_publish` 參數順序 (已修正)

### 建議:

1. 檢查 `async_cmd_send_vendor_data` 的實作是否符合實際需求
2. 統一 element_index 的類型 (int vs str)
3. 添加參數驗證（如 Group 地址範圍檢查: 0xc000 ~ 0xffff）
