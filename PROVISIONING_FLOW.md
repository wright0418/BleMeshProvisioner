# 正確的 BLE Mesh Provisioning 綁定流程

## 日期: 2025-11-10

## 完整綁定流程 (已驗證)

**重要**: Provisioner 會自動分配 unicast address，後續所有命令必須使用實際分配的地址！

### 步驟 1: AT+DIS 1 - 開始掃描
```
命令: AT+DIS 1
回應: DIS-MSG SUCCESS
通知: DIS-MSG <UUID> <MAC> <RSSI> <OOB> <URI>
```

### 步驟 2: 記錄設備 UUID
從掃描通知中找到目標設備的 UUID。

### 步驟 3: AT+DIS 0 - 停止掃描
```
命令: AT+DIS 0
回應: DIS-MSG SUCCESS
```
⚠️ **重要**: 必須停止掃描才能進行配置！

### 步驟 4: AT+PBADVCON <UUID> - 開啟通道
```
命令: AT+PBADVCON <device_uuid>
回應: PBADVCON-MSG SUCCESS
超時: 10秒
```

### 步驟 5: AT+PROV - 執行 Provisioning
```
命令: AT+PROV
回應: PROV-MSG SUCCESS <unicast_address>
超時: 15秒
延遲: 完成後等待 2 秒
```

**重要**: 
- Provisioner 會自動分配 unicast address
- 回應中的 `<unicast_address>` 是實際分配的地址
- **後續所有命令 (AKA/MAKB/MSAA/MPAS) 必須使用這個實際分配的地址！**

範例回應：
```
>> PROV-MSG SUCCESS 0x0100
```
此時實際分配的地址是 `0x0100`，後續命令都要使用這個地址。

### 步驟 6: AT+AKA - 添加 AppKey
```
格式: AT+AKA [dst] [app_key_index] [net_key_index]
範例: AT+AKA 0x0100 0 0
回應: AKA-MSG SUCCESS
超時: 10秒
```

### 步驟 7: AT+MAKB - 綁定 Model
```
格式: AT+MAKB [dst] [element_index] [model_id] [app_key_index]
範例: AT+MAKB 0x0100 0 0x4005D 0
回應: MAKB-MSG SUCCESS
超時: 10秒
```

**重點**: 
- `element_index` 使用 **0** (相對索引)，不是 0x0100 (絕對地址)
- `model_id` 使用 **0x4005D** (實際 Model ID)

### 步驟 8: AT+MSAA - 訂閱 (可選)
```
格式: AT+MSAA [dst] [element_index] [model_id] [Group_addr]
範例: AT+MSAA 0x0100 0 0x4005D 0xC000
```

**重要**: `model_id` 必須與 AT+MAKB 綁定的 Model ID 相同！

### 步驟 9: AT+MPAS - 發佈 (可選)
```
格式: AT+MPAS [dst] [element_idx] [model_id] [publish_addr] [app_key_idx]
範例: AT+MPAS 0x0100 0 0x4005D 0xC000 0
```

**重要**: `model_id` 必須與 AT+MAKB 綁定的 Model ID 相同！

### 步驟 10: AT+NL - 驗證
```
命令: AT+NL
回應: NL-MSG <index> <addr> <element_num> <online>
```

## 關鍵參數說明

### Model ID 必須一致！
**最重要的規則**: AT+MAKB、AT+MSAA、AT+MPAS 必須使用**相同的 Model ID**！

- ✅ **正確流程**:
  ```
  AT+MAKB 0x0100 0 0x4005D 0  (綁定 Model 0x4005D)
  AT+MSAA 0x0100 0 0x4005D 0xC000  (訂閱 Model 0x4005D)
  AT+MPAS 0x0100 0 0x4005D 0xC000 0  (發佈 Model 0x4005D)
  ```

- ❌ **錯誤流程**:
  ```
  AT+MAKB 0x0100 0 0x4005D 0  (綁定 Model 0x4005D)
  AT+MSAA 0x0100 0 0x1000 0xC000  ❌ Model ID 不一致！
  AT+MPAS 0x0100 0 0x1000 0xC000 0  ❌ Model ID 不一致！
  ```

### Model ID: 0x4005D
這是實際設備支援的 Model ID，不是 Generic OnOff Server (0x1000)。

### Element Index vs Element Address
- ❌ **錯誤**: `AT+MAKB 0x0100 0x0100 ...` (用地址當索引)
- ✅ **正確**: `AT+MAKB 0x0100 0 ...` (用索引 0)

Element Index 是相對於節點的索引 (0, 1, 2...)，不是絕對地址。

## 程式碼已更新

### test_provisioning_flow.py
已將流程拆分為獨立步驟：
- `test_step_2_pbadvcon()` - PB-ADV 通道
- `test_step_3_prov()` - Provisioning
- `test_step_4_aka()` - AppKey
- `test_step_5_makb()` - Model 綁定 (使用 0x4005D)

每個步驟獨立執行，方便除錯和觀察結果。

## 執行測試

```powershell
python test_provisioning_flow.py
```

選擇選項 1 執行完整流程。
