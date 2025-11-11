# Provisioner Manager CLI 工具設計文檔

## 概述
這是一個基於 Python 的 BLE Mesh Provisioner 管理工具，使用 UART AT 指令與 RL62M02 模組通訊，提供完整的設備綁定、網路管理和訊息監聽功能。

## 系統架構

### 專案目錄結構
```
BleMeshProvisioner/
├── ble_mesh_provisioner/
│   ├── __init__.py
│   ├── core/                      # 核心通訊層
│   │   ├── __init__.py
│   │   ├── serial_interface.py   # UART 串口通訊
│   │   ├── at_command.py          # AT 指令封裝
│   │   └── response_parser.py    # 回應解析器
│   ├── network/                   # 網路管理層
│   │   ├── __init__.py
│   │   ├── provisioner_manager.py # Provisioner 管理器
│   │   ├── node_manager.py        # 節點管理
│   │   └── message_listener.py    # 網路訊息監聽器
│   ├── devices/                   # 設備層
│   │   ├── __init__.py
│   │   ├── base_device.py         # 設備基類
│   │   ├── rgb_led.py             # RGB LED 設備
│   │   ├── plug.py                # 插座設備
│   │   └── alarm.py               # 警報設備
│   ├── cli/                       # CLI 介面層
│   │   ├── __init__.py
│   │   ├── main.py                # CLI 主程式
│   │   ├── commands.py            # CLI 命令實作
│   │   └── ui_helpers.py          # UI 輔助函數 (Rich)
│   └── utils/                     # 工具模組
│       ├── __init__.py
│       ├── logger.py              # 日誌系統
│       └── validators.py          # 驗證器
├── tests/                         # 測試目錄
│   ├── __init__.py
│   ├── mocks/                     # Mock 類別
│   │   ├── __init__.py
│   │   ├── mock_serial.py         # 模擬串口
│   │   └── mock_responses.py      # 模擬回應資料
│   ├── test_at_command.py
│   ├── test_provisioner_manager.py
│   └── test_cli.py
├── examples/                      # 範例程式
│   ├── basic_usage.py
│   ├── auto_provision.py
│   └── device_control.py
├── docs/                          # 文檔
│   └── API.md
├── requirements.txt               # 依賴套件
├── setup.py                       # 安裝設定
└── README.md                      # 專案說明
```

## 核心模組設計

### 1. Serial Interface (core/serial_interface.py)
```python
class SerialInterface:
    """
    UART 串口通訊介面
    - 115200 baud, 8N1, no flow control
    - 處理 AT 指令發送與回應接收
    - 支援背景執行緒持續監聽訊息
    """
    
    def __init__(self, port: str, baudrate: int = 115200)
    def open(self) -> bool
    def close(self) -> None
    def send_command(self, command: str) -> str
    def start_listening(self, callback: Callable) -> None
    def stop_listening(self) -> None
```

### 2. AT Command (core/at_command.py)
```python
class ATCommand:
    """
    AT 指令封裝與執行
    - 建構符合格式的 AT 指令
    - 執行指令並解析回應
    - 支援重試機制 (最多1次)
    """
    
    @staticmethod
    def build_command(cmd: str, params: List[str] = None) -> str
    
    def execute(self, serial: SerialInterface, timeout: float = 5.0) -> dict
    def execute_with_retry(self, serial: SerialInterface) -> dict
```

### 3. Response Parser (core/response_parser.py)
```python
class ResponseParser:
    """
    解析 AT 指令回應
    - 解析 INDICATION 訊息
    - 提取 SUCCESS/ERROR 狀態
    - 解析參數列表
    """
    
    @staticmethod
    def parse_response(response: str) -> dict
    
    @staticmethod
    def parse_indication(indication: str) -> dict
```

### 4. Provisioner Manager (network/provisioner_manager.py)
```python
class ProvisionerManager:
    """
    Provisioner 管理器 - 實作所有核心功能
    """
    
    # 功能 1: 查詢韌體版本與角色
    def get_version(self) -> str
    def get_role(self) -> str
    def verify_provisioner(self) -> bool
    
    # 功能 2: 掃描未綁定設備
    def start_scan(self, duration: int = 3) -> List[dict]
    def stop_scan(self) -> None
    
    # 功能 3: 綁定設備
    def provision_device(self, uuid: str) -> dict
    def complete_binding(self, unicast_addr: str) -> bool
    
    # 功能 4: 移除未完成綁定的設備
    def remove_node(self, unicast_addr: str) -> bool
    
    # 功能 5: 列出已綁定設備
    def list_nodes(self) -> List[dict]
    
    # 功能 6: 解除綁定設備
    def unprovision_device(self, index: int) -> bool
    
    # 功能 7: 設定推播
    def set_publish(self, unicast_addr: str, element_idx: int, 
                    model_id: str, publish_addr: str, app_key_idx: int = 0) -> bool
    def clear_publish(self, unicast_addr: str, element_idx: int,
                      model_id: str, app_key_idx: int = 0) -> bool
    
    # 功能 8: 設定訂閱
    def add_subscription(self, unicast_addr: str, element_idx: int,
                        model_id: str, group_addr: str) -> bool
    def remove_subscription(self, unicast_addr: str, element_idx: int,
                           model_id: str, group_addr: str) -> bool
    
    # 功能 9: 查詢設備設定狀態
    def get_node_config(self, unicast_addr: str) -> dict
```

### 5. Message Listener (network/message_listener.py)
```python
class MessageListener:
    """
    網路訊息監聽器
    - 持續接收 MDTG, MDTPG 等網路訊息
    - 背景執行緒運行
    - 即時顯示在終端機
    """
    
    def __init__(self, serial: SerialInterface)
    def start(self) -> None
    def stop(self) -> None
    def on_message_received(self, message: dict) -> None
```

## CLI 命令設計

### 主命令結構 (使用 typer)
```
provisioner-cli [OPTIONS] COMMAND [ARGS]...

Commands:
  info           查詢模組資訊
  scan           掃描未綁定設備
  provision      綁定設備
  list           列出已綁定設備
  unprovision    解除綁定設備
  publish        設定推播
  subscribe      設定訂閱
  config         查詢設備設定
  monitor        啟動訊息監聽
```

### 詳細命令規格

#### 1. info - 查詢模組資訊
```bash
provisioner-cli info [OPTIONS]

Options:
  --port, -p TEXT  串口名稱 [required]

功能:
  - 查詢韌體版本 (AT+VER)
  - 查詢模組角色 (AT+MRG)
  - 驗證是否為 PROVISIONER

顯示範例:
┌─────────────────────────────────┐
│  Provisioner Module Information │
├─────────────────────────────────┤
│ Firmware Version: 1.0.0         │
│ Module Role:      PROVISIONER   │
│ Status:           ✓ Ready       │
└─────────────────────────────────┘
```

#### 2. scan - 掃描未綁定設備
```bash
provisioner-cli scan [OPTIONS]

Options:
  --port, -p TEXT      串口名稱 [required]
  --duration, -d INT   掃描時間(秒) [default: 3]

功能:
  - 開啟掃描 (AT+DIS 1)
  - 等待指定時間
  - 關閉掃描 (AT+DIS 0)
  - 顯示編號列表

顯示範例:
┌────┬──────────────┬──────┬──────────────────────────────────────┐
│ No │     MAC      │ RSSI │                UUID                  │
├────┼──────────────┼──────┼──────────────────────────────────────┤
│ 1  │ 655600000152 │ -48  │ 123E4567E89B12D3A456655600000152     │
│ 2  │ 655600000153 │ -52  │ 123E4567E89B12D3A456655600000153     │
│ 3  │ 655600000151 │ -45  │ 123E4567E89B12D3A456655600000151     │
└────┴──────────────┴──────┴──────────────────────────────────────┘
Found 3 unprovisioned devices
```

#### 3. provision - 綁定設備
```bash
provisioner-cli provision [OPTIONS]

Options:
  --port, -p TEXT     串口名稱 [required]
  --uuid TEXT         設備 UUID (如不提供則進入互動模式)
  --index, -i INT     掃描列表編號 (互動模式)

功能流程:
  1. 執行掃描 (如未提供 UUID)
  2. 選擇設備 (互動模式)
  3. 執行 AT+PBADVCON <UUID>
  4. 執行 AT+PROV
  5. 執行 AT+AKA <addr> 0 0
  6. 執行 AT+MAKB <addr> 0 0x1000ffff 0
  7. 如果 MAKB 失敗,執行 AT+NR <addr>

顯示範例:
Provisioning device...
[1/4] Opening PB-ADV channel... ✓
[2/4] Provisioning device...    ✓ (Address: 0x0100)
[3/4] Adding AppKey...          ✓
[4/4] Binding Model...          ✓

✓ Device successfully provisioned!
  Unicast Address: 0x0100
  Elements:        1
```

#### 4. list - 列出已綁定設備
```bash
provisioner-cli list [OPTIONS]

Options:
  --port, -p TEXT  串口名稱 [required]

功能:
  - 查詢節點列表 (AT+NL)
  - 顯示設備資訊

顯示範例:
┌────┬──────────┬──────────┬────────┐
│ No │ Address  │ Elements │ Status │
├────┼──────────┼──────────┼────────┤
│ 0  │ 0x0100   │    1     │ ●ON    │
│ 1  │ 0x0101   │    1     │ ○OFF   │
│ 2  │ 0x0102   │    1     │ ●ON    │
└────┴──────────┴──────────┴────────┘
Total: 3 nodes (2 online, 1 offline)
```

#### 5. unprovision - 解除綁定設備
```bash
provisioner-cli unprovision [OPTIONS]

Options:
  --port, -p TEXT    串口名稱 [required]
  --index, -i INT    設備列表編號 [required]

功能:
  - 列出設備列表
  - 確認要解除的設備
  - 執行 AT+NR <addr>

顯示範例:
Current nodes:
┌────┬──────────┬──────────┬────────┐
│ No │ Address  │ Elements │ Status │
├────┼──────────┼──────────┼────────┤
│ 0  │ 0x0100   │    1     │ ●ON    │
│ 1  │ 0x0101   │    1     │ ○OFF   │
└────┴──────────┴──────────┴────────┘

Remove node #1 (0x0101)? [y/N]: y
Removing node... ✓
Node 0x0101 has been removed.
```

#### 6. publish - 設定推播
```bash
provisioner-cli publish [OPTIONS] COMMAND

Commands:
  set     設定推播位址
  clear   清除推播位址

set options:
  --port, -p TEXT         串口名稱 [required]
  --address, -a TEXT      設備位址 [required]
  --element, -e INT       元素索引 [default: 0]
  --model, -m TEXT        Model ID [default: 0x1000ffff]
  --publish-addr TEXT     推播位址 [required]
  --app-key-idx INT       AppKey 索引 [default: 0]

clear options:
  --port, -p TEXT         串口名稱 [required]
  --address, -a TEXT      設備位址 [required]
  --element, -e INT       元素索引 [default: 0]
  --model, -m TEXT        Model ID [default: 0x1000ffff]
  --app-key-idx INT       AppKey 索引 [default: 0]

功能:
  - 設定: AT+MPAS <dst> <elem> <model> <pub_addr> <key_idx>
  - 清除: AT+MPAD <dst> <elem> <model> <key_idx>

顯示範例:
Setting publish address...
✓ Publish address set successfully
  Device:  0x0100
  Publish: 0xC000 (Group)
```

#### 7. subscribe - 設定訂閱
```bash
provisioner-cli subscribe [OPTIONS] COMMAND

Commands:
  add     新增訂閱
  remove  移除訂閱

add options:
  --port, -p TEXT         串口名稱 [required]
  --address, -a TEXT      設備位址 [required]
  --element, -e INT       元素索引 [default: 0]
  --model, -m TEXT        Model ID [default: 0x1000ffff]
  --group-addr TEXT       群組位址 [required]

remove options:
  (同 add)

功能:
  - 新增: AT+MSAA <dst> <elem> <model> <group>
  - 移除: AT+MSAD <dst> <elem> <model> <group>

顯示範例:
Adding subscription...
✓ Subscription added successfully
  Device: 0x0100
  Group:  0xC000
```

#### 8. config - 查詢設備設定
```bash
provisioner-cli config [OPTIONS]

Options:
  --port, -p TEXT      串口名稱 [required]
  --address, -a TEXT   設備位址 [required]

功能:
  - 查詢設備的推播與訂閱設定
  - 顯示完整配置資訊

注意: 此功能需要查詢 Mesh 配置資料庫或通過特定指令取得

顯示範例:
┌─────────────────────────────────────┐
│  Device Configuration (0x0100)      │
├─────────────────────────────────────┤
│ Publish Address:                    │
│   0xC000 (Group)                    │
│                                     │
│ Subscriptions:                      │
│   0xC000 (Group)                    │
│   0xC001 (Group)                    │
│                                     │
│ Models:                             │
│   0x1000FFFF (Vendor DataTrans)    │
└─────────────────────────────────────┘
```

#### 9. monitor - 啟動訊息監聽
```bash
provisioner-cli monitor [OPTIONS]

Options:
  --port, -p TEXT  串口名稱 [required]

功能:
  - 持續接收並顯示網路訊息
  - 監聽 MDTG-MSG, MDTPG-MSG 等
  - 按 Ctrl+C 停止

顯示範例:
┌─────────────────────────────────────────────────────┐
│  Network Message Monitor (Press Ctrl+C to stop)    │
└─────────────────────────────────────────────────────┘

[2025-11-09 10:30:15] MDTG-MSG
  From:    0x0100
  Element: 0
  Data:    112233445566

[2025-11-09 10:30:18] MDTPG-MSG
  From:    0x0101
  Element: 0
  Publish: 0xC000

[2025-11-09 10:30:20] MDTG-MSG
  From:    0x5151 (Alarm Device)
  Status:  ALARM ON
```

## 技術細節

### AT 指令對應表

| 功能 | AT 指令 | 回應格式 |
|------|---------|----------|
| 查詢版本 | `AT+VER` | `VER-MSG SUCCESS <version>` |
| 查詢角色 | `AT+MRG` | `MRG-MSG SUCCESS {PROVISIONER/DEVICE}` |
| 開啟掃描 | `AT+DIS 1` | `DIS-MSG SUCCESS`<br>`DIS-MSG <mac> <rssi> <uuid>` |
| 關閉掃描 | `AT+DIS 0` | `DIS-MSG SUCCESS` |
| 開啟 PB-ADV | `AT+PBADVCON <uuid>` | `PBADVCON-MSG SUCCESS` |
| 開始綁定 | `AT+PROV` | `PROV-MSG SUCCESS <addr>` |
| 新增 AppKey | `AT+AKA <addr> 0 0` | `AKA-MSG SUCCESS` |
| 綁定 Model | `AT+MAKB <addr> 0 0x1000ffff 0` | `MAKB-MSG SUCCESS` |
| 移除節點 | `AT+NR <addr>` | `NR-MSG SUCCESS <addr>` |
| 查詢節點 | `AT+NL` | `NL-MSG <idx> <addr> <elem> <state>` |
| 設定推播 | `AT+MPAS <dst> <e> <m> <pub> <k>` | `MPAS-MSG SUCCESS` |
| 清除推播 | `AT+MPAD <dst> <e> <m> <k>` | `MPAD-MSG SUCCESS` |
| 新增訂閱 | `AT+MSAA <dst> <e> <m> <grp>` | `MSAA-MSG SUCCESS` |
| 移除訂閱 | `AT+MSAD <dst> <e> <m> <grp>` | `MSAD-MSG SUCCESS` |

### 錯誤處理策略

1. **串口通訊錯誤**
   - 檢查串口是否存在
   - 檢查串口權限
   - 提供明確的錯誤訊息

2. **AT 指令失敗**
   - 自動重試一次
   - 記錄錯誤日誌 (指令、時間、原因)
   - 顯示友善的錯誤訊息

3. **綁定流程失敗**
   - 在 MAKB 失敗時自動執行 AT+NR
   - 清理殘留配置
   - 提供重試選項

4. **超時處理**
   - 預設超時 5 秒
   - 特殊操作 (如掃描) 可調整
   - 顯示進度指示器

### 日誌系統

```python
# 日誌等級
DEBUG:   詳細的除錯資訊
INFO:    一般操作訊息
WARNING: 警告訊息
ERROR:   錯誤訊息

# 日誌格式
[2025-11-09 10:30:15] [INFO] Command sent: AT+VER
[2025-11-09 10:30:15] [INFO] Response: VER-MSG SUCCESS 1.0.0
[2025-11-09 10:30:16] [ERROR] Command failed: AT+PROV, Timeout after 5s
```

### 設定檔支援

```yaml
# config.yaml
serial:
  port: COM3
  baudrate: 115200
  timeout: 5

provisioner:
  default_app_key_index: 0
  default_net_key_index: 0
  default_model_id: "0x1000ffff"
  scan_duration: 3

logging:
  level: INFO
  file: provisioner.log
  console: true
```

## 依賴套件

```
# requirements.txt
pyserial>=3.5
typer>=0.9.0
rich>=13.0.0
pyyaml>=6.0
pytest>=7.4.0
pytest-mock>=3.11.0
```

## 實作優先順序

### Phase 1: 核心通訊層
1. SerialInterface - 串口通訊
2. ATCommand - 指令封裝
3. ResponseParser - 回應解析
4. 單元測試 + Mock

### Phase 2: 基本管理功能
1. ProvisionerManager (功能 1-6)
   - info (查詢資訊)
   - scan (掃描)
   - provision (綁定)
   - list (列表)
   - unprovision (解除綁定)
2. CLI 基本命令
3. 整合測試

### Phase 3: 進階配置功能
1. ProvisionerManager (功能 7-9)
   - publish (推播設定)
   - subscribe (訂閱設定)
   - config (查詢配置)
2. CLI 進階命令
3. 整合測試

### Phase 4: 訊息監聽
1. MessageListener
2. monitor 命令
3. 背景執行緒處理
4. 整合測試

### Phase 5: 完善與優化
1. 設定檔支援
2. 完整錯誤處理
3. 日誌系統
4. 使用文檔
5. 範例程式

## 測試策略

### Mock 資料結構
```python
# tests/mocks/mock_responses.py
MOCK_RESPONSES = {
    "AT+VER": "VER-MSG SUCCESS 1.0.0\r\n",
    "AT+MRG": "MRG-MSG SUCCESS PROVISIONER\r\n",
    "AT+DIS 1": [
        "DIS-MSG SUCCESS\r\n",
        "DIS-MSG 655600000152 -48 123E4567E89B12D3A456655600000152\r\n",
        "DIS-MSG 655600000153 -52 123E4567E89B12D3A456655600000153\r\n",
    ],
    # ... 更多模擬回應
}
```

### 測試涵蓋範圍
- 單元測試: 每個模組獨立測試
- 整合測試: 多模組協作測試
- CLI 測試: 命令列介面測試
- Mock 測試: 無需硬體測試

## 使用範例

### 完整綁定流程
```bash
# 1. 查詢模組資訊
provisioner-cli info -p COM3

# 2. 掃描設備
provisioner-cli scan -p COM3 -d 5

# 3. 綁定設備 (使用編號)
provisioner-cli provision -p COM3 -i 1

# 4. 列出已綁定設備
provisioner-cli list -p COM3

# 5. 設定推播
provisioner-cli publish set -p COM3 -a 0x0100 --publish-addr 0xC000

# 6. 設定訂閱
provisioner-cli subscribe add -p COM3 -a 0x0100 --group-addr 0xC000

# 7. 查詢配置
provisioner-cli config -p COM3 -a 0x0100

# 8. 啟動監聽
provisioner-cli monitor -p COM3
```

## 後續擴展計劃

1. **圖形化介面 (GUI)**
   - 使用 PyQt 或 Tkinter
   - 視覺化網路拓樸
   - 即時狀態監控

2. **網路拓樸視覺化**
   - 節點關係圖
   - 推播/訂閱路徑顯示
   - 互動式配置

3. **批次操作**
   - 批次綁定
   - 批次配置
   - 腳本自動化

4. **進階診斷**
   - 網路健康檢查
   - 通訊品質分析
   - 問題診斷工具

5. **設備模板**
   - 預設配置模板
   - 快速部署
   - 場景設定

## 總結

此 CLI 工具提供完整的 BLE Mesh Provisioner 管理功能，從基本的設備綁定到進階的網路配置，都能透過簡潔的命令列介面操作。採用模組化設計，易於擴展和維護，並提供完整的測試框架確保程式品質。
