# AT+NL 測試報告

## 測試日期: 2025-11-11

## 問題發現與修正

### 問題描述
AT+NL 命令執行後，收到 `NL-MSG` 回應但顯示 "Unrouted message: NL"，訊息無法被 AsyncMessageListener 正確處理。

### 根本原因
`AsyncSerialInterface` 的 `_notification_patterns` 中缺少 `NL-MSG` 模式，導致 NL 訊息被視為命令回應而非異步通知。

### 修正內容

#### async_serial_interface.py (Line 87-91)
```python
# 修正前
self._notification_patterns = [
    re.compile(
        r'^(MDTG-MSG|MDTS-MSG|MDTPG-MSG|DIS-MSG|PROV-MSG|NR-MSG)'),
]

# 修正後
self._notification_patterns = [
    re.compile(
        r'^(MDTG-MSG|MDTS-MSG|MDTPG-MSG|DIS-MSG|PROV-MSG|NR-MSG|NL-MSG)'),
]
```

**說明**: 添加 `NL-MSG` 到通知模式列表，使其被正確路由到通知隊列。

## 測試結果

### 測試環境
- COM Port: COM17
- Baudrate: 115200
- 已配置節點數: 2

### 測試執行
```bash
python test_nl.py
```

### 測試輸出
```
✅ 找到 2 個已配置的節點

┌──────────┬────────────┬────────────┬────────────┐
│ 索引     │ 地址       │ 元素數     │ 狀態       │
├──────────┼────────────┼────────────┼────────────┤
│ 0        │ 0x0100     │ 1          │ 🟢 在線    │
│ 1        │ 0x0101     │ 1          │ 🟢 在線    │
└──────────┴────────────┴────────────┴────────────┘
```

### 驗證項目
- ✅ AT+NL 命令正確發送
- ✅ NL-MSG 通知正確接收
- ✅ 訊息被路由到通知隊列
- ✅ AsyncMessageListener 正確處理
- ✅ 節點資訊正確解析（索引、地址、元素數、在線狀態）
- ✅ 多個節點訊息正確收集

## AT+NL 命令詳解

### 命令格式
```
AT+NL
```

### 回應格式
```
NL-MSG <index> <unicast_addr> <element_num> <state_online>
```

**參數說明**:
- `index`: 節點索引 (0-based)
- `unicast_addr`: 節點的單播地址 (0x0100, 0x0101, ...)
- `element_num`: 節點包含的元素數量
- `state_online`: 在線狀態 (1=在線, 0=離線)

### 多節點回應範例
```
<< AT+NL
>> NL-MSG 0 0x0100 1 1
>> NL-MSG 1 0x0101 1 1
>> NL-MSG 2 0x0102 1 0
```

## 實作細節

### async_provisioner_manager.py - list_nodes()

#### 實作邏輯
1. 註冊 `NL-MSG` 訊息處理器
2. 啟動 AsyncMessageListener
3. 發送 `AT+NL` 命令（不等待回應，因為是異步通知）
4. 等待 0.5 秒收集所有 NL-MSG 通知
5. 解析並返回節點列表
6. 清理：移除訊息處理器

#### 關鍵代碼
```python
async def nl_handler(msg: Dict[str, Any]) -> None:
    """Handle NL-MSG messages."""
    params = msg.get('params', [])
    if len(params) >= 4:
        node = {
            'index': int(params[0]),
            'address': params[1],
            'element_num': int(params[2]),
            'online': int(params[3])
        }
        nodes.append(node)

self.listener.add_handler('NL', nl_handler)
await async_cmd_list_nodes().execute(self.serial, expect_response=False)
await asyncio.sleep(0.5)  # 等待收集所有訊息
```

#### 為什麼需要延遲？
- AT+NL 可能回傳多個 NL-MSG（每個節點一個）
- 訊息是異步到達的
- 0.5 秒延遲確保收集所有訊息

## 與其他命令的對比

### 命令回應型 vs 異步通知型

#### 命令回應型（單次回應）
```
AT+VER
VER-MSG SUCCESS 1.0.6  ← 單一回應，可以用 Future 等待
```

#### 異步通知型（多次回應）
```
AT+NL
NL-MSG 0 0x0100 1 1    ← 第一個節點
NL-MSG 1 0x0101 1 1    ← 第二個節點
NL-MSG 2 0x0102 1 0    ← 第三個節點
...                     ← 可能有更多節點
```

**AT+NL 的特性**:
- 不返回 SUCCESS/ERROR 狀態
- 回應數量不固定（取決於已配置節點數）
- 需要使用訊息監聽器收集所有回應
- 必須加入 `_notification_patterns` 才能正確路由

## 測試檔案

### test_nl.py
獨立的 AT+NL 測試程式：
- 簡潔的命令列介面
- Rich 表格顯示節點資訊
- 顏色標示在線/離線狀態

### test_provisioning_flow.py - 步驟 8
完整 Provisioning 流程中的驗證步驟：
- 綁定完成後驗證配置結果
- 確認新綁定的節點出現在列表中
- 檢查節點在線狀態

## 使用範例

### 獨立測試
```bash
python test_nl.py
```

### 整合流程測試
```bash
python test_provisioning_flow.py
# 選擇選項 1: 完整 Provisioning 流程測試
# 步驟 8 會自動執行 AT+NL 驗證
```

## 總結

✅ **問題已解決**: NL-MSG 現在被正確路由和處理  
✅ **測試通過**: 成功列出 2 個已配置節點  
✅ **功能完整**: 支援多節點查詢和狀態顯示  
✅ **文件完備**: 提供獨立測試程式和使用說明  

## 下一步建議

1. ✅ AT+NL 基本功能測試完成
2. ⏳ 測試節點離線情況（state_online = 0）
3. ⏳ 測試多元素節點（element_num > 1）
4. ⏳ 整合到 CLI 介面
5. ⏳ 添加節點管理功能（刪除節點、重置等）
