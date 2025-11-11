# AT+PROV 地址分配機制說明

## 關鍵發現

AT+PROV 命令會由 Provisioner **自動分配** unicast address 給新設備，而不是使用預先指定的地址。

## AT+PROV 回應格式

```
命令: AT+PROV
回應: PROV-MSG SUCCESS <unicast_address>
```

### 範例
```
<< AT+PROV
>> PROV-MSG SUCCESS 0x0100
```

回應中的 `0x0100` 是 Provisioner 實際分配的地址。

## 正確的使用流程

### ❌ 錯誤做法
```python
# 錯誤: 預先假設地址
unicast_addr = "0x0100"

# 步驟 3: Provisioning
await async_cmd_provision(unicast_addr, 0).execute(serial)

# 步驟 4-7: 使用假設的地址 (可能不正確!)
await async_cmd_add_appkey(unicast_addr, 0, 0).execute(serial)  # ❌
await async_cmd_bind_model(unicast_addr, "0", "0x4005D", "0").execute(serial)  # ❌
```

### ✅ 正確做法
```python
# 步驟 3: Provisioning，取得實際分配的地址
cmd = async_cmd_provision("0x0100", 0)
result = await cmd.execute(serial, timeout=15.0)

if result.get('success'):
    # 從回應中取得實際分配的地址
    allocated_addr = result.get('params', [])[0]
    print(f"實際分配的地址: {allocated_addr}")
    
    # 步驟 4-7: 使用實際分配的地址
    await async_cmd_add_appkey(allocated_addr, 0, 0).execute(serial)  # ✅
    await async_cmd_bind_model(allocated_addr, "0", "0x4005D", "0").execute(serial)  # ✅
    await async_cmd_add_subscription(allocated_addr, 0, "0x4005D", "0xC000").execute(serial)  # ✅
    await async_cmd_set_publish(allocated_addr, 0, "0x4005D", "0xC000", 0).execute(serial)  # ✅
```

## 為什麼這很重要？

1. **地址唯一性**: Provisioner 維護已分配地址的列表，確保不重複
2. **自動管理**: Provisioner 會自動選擇下一個可用地址
3. **多設備配置**: 連續配置多個設備時，每個設備會得到不同的地址
4. **命令失敗**: 如果使用錯誤的地址，後續的 AKA/MAKB/MSAA/MPAS 都會失敗

## 實際範例

配置兩個設備：

```python
# 第一個設備
result1 = await async_cmd_provision(...).execute(serial)
addr1 = result1['params'][0]  # 得到 0x0100

# 第二個設備
result2 = await async_cmd_provision(...).execute(serial)
addr2 = result2['params'][0]  # 得到 0x0101 (自動遞增)

# 兩個設備使用各自的地址進行後續配置
await async_cmd_add_appkey(addr1, 0, 0).execute(serial)  # 設備 1
await async_cmd_add_appkey(addr2, 0, 0).execute(serial)  # 設備 2
```

## test_provisioning_flow.py 修正

已更新測試程式：

### test_step_3_prov 函數
- 回傳實際分配的 unicast address
- 不再接受預設地址參數
- 從 PROV-MSG 回應中解析地址

### 主流程
```python
# 步驟 3: 執行 Provisioning (取得實際分配的地址)
unicast_addr = await test_step_3_prov(manager)
if not unicast_addr:
    return

# 步驟 4-7: 使用實際分配的地址
await test_step_4_aka(manager, unicast_addr, 0, 0)
await test_step_5_makb(manager, unicast_addr, "0x4005D", "0", "0")
await test_step_6_set_subscription(manager, unicast_addr, "0xC000", "0x4005D")
await test_step_7_set_publish(manager, unicast_addr, "0xC000", "0x4005D")
```

## 總結

✅ AT+PROV 自動分配地址  
✅ 必須從回應中取得實際地址  
✅ 後續所有命令 (AKA/MAKB/MSAA/MPAS) 使用實際地址  
✅ 支援多設備自動地址管理  

這是 BLE Mesh Provisioning 協議的標準行為，確保網路中每個節點都有唯一的地址。
