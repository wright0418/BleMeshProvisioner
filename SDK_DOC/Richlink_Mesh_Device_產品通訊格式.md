# RL Mesh 設備通訊協議文檔

## 1. RL Mesh Device 命令格式 (不需要檢查回傳訊息) @Provisioner

| 欄位 | 大小 | 值 |
|------|------|-----|
| Start Header | 1 byte | 0x87 |
| Opcode | 2 bytes | 詳見各設備類型 |
| Payload Length | 1 byte | Payload 長度 |
| Payload | 1~16 bytes | 依設備類型而定 |

### 1.1 RGB LED Device

| 欄位 | 值 |
|------|-----|
| Opcode | 0x0100 |
| Payload Length | 0x05 |
| Payload | CWRGB |

**參數說明:**
- C = 0~255 (冷光)
- W = 0~255 (暖光)
- R = 0~255 (紅色)
- G = 0~255 (綠色)
- B = 0~255 (藍色)

### 1.2 Plug Device

| 欄位 | 值 |
|------|-----|
| Opcode | 0x0200 |
| Payload Length | 0x01 |
| Payload | ON/OFF |

**參數說明:**
- ON = 0x01
- OFF = 0x00

### 1.3 Alarm Device (接收警報狀態) @ Provisioner
- 當 警報 ON 時，Provisioner 會收到以下命令格式:
- MDTG-MSG <unicast_addr> 0x875151


### 1.4 RL Mesh Device AT 命令格式 @Provisioner

```
AT+MDTS <device uid> 0 <RL Mesh Device command format hex string>
```

**參數說明:**
- `device uid`: 設備唯一識別碼
- `0`: 固定參數
- `hex string`: RL Mesh Device 命令的十六進制字串

