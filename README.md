# BLE Mesh Provisioner SDK

[![Tests](https://img.shields.io/badge/tests-passing-green)](tests/)
[![Python](https://img.shields.io/badge/python-3.8+-blue.svg)](https://www.python.org/downloads/)
[![License](https://img.shields.io/badge/license-MIT-blue.svg)](LICENSE)
[![Version](https://img.shields.io/badge/version-0.2.0-blue)](CHANGELOG.md)

Python SDK for RichLink RL62M BLE Mesh Provisioner modules using UART AT commands with AsyncIO architecture.

## 特色功能

- ⚡ **AsyncIO 架構**: 完整非同步 UART 通訊支援
- 🔌 **UART 通訊**: 透過串口與 RL62M02 模組通訊 (115200 baud, 8N1)
- 📡 **完整 AT 指令**: 支援所有 14 種 AT 指令 (DIS/PROV/AKA/MAKB/NL/MSAA/MPAS 等)
- 🎯 **完整綁定流程**: DIS → PBADVCON → PROV → AKA → MAKB → MSAA/MPAS
- 🧪 **硬體驗證**: 所有 AT 指令經過實際硬體測試
-  **詳細日誌**: 完整的操作日誌與錯誤追蹤
- 🏗️ **模組化設計**: OOP 設計，易於擴展和維護

## 系統需求

- Python 3.8 或更高版本
- pySerial 3.5+
- RichLink RL62M02 Provisioner Module (Firmware 1.0.6+)

## 安裝

### 使用 uv (推薦)

```bash
# 安裝 uv
pip install uv

# 建立虛擬環境
uv venv venv

# 激活虛擬環境 (Windows)
.\venv\Scripts\Activate.ps1

# 安裝依賴
uv pip install -r requirements.txt
```

## 快速開始

### AsyncIO 基本使用

```python
import asyncio
from ble_mesh_provisioner.core.async_serial_interface import AsyncSerialInterface
from ble_mesh_provisioner.core.async_at_command import cmd_get_version

async def main():
    # 開啟串口連接
    async with AsyncSerialInterface('COM17') as serial:
        # 查詢韌體版本
        cmd = cmd_get_version()
        result = await cmd.execute_async(serial)
        
        if result['success']:
            version = result['response']['params'][0]
            print(f"Firmware Version: {version}")

asyncio.run(main())
```

### 完整綁定流程範例

```python
import asyncio
from ble_mesh_provisioner.core.async_serial_interface import AsyncSerialInterface
from ble_mesh_provisioner.core.async_at_command import (
    cmd_device_scan, cmd_provision_with_address,
    cmd_add_appkey, cmd_bind_model_appkey
)

async def provision_device():
    async with AsyncSerialInterface('COM17') as serial:
        # 1. 啟動掃描
        await cmd_device_scan(1).execute_async(serial)
        
        # 2. 等待 DIS-MSG 通知
        msg = await serial.get_notification(timeout=10.0)
        uuid = msg['params'][1]
        
        # 3. 停止掃描並開始綁定
        await cmd_device_scan(0).execute_async(serial)
        await cmd_provision_address_connect(uuid).execute_async(serial)
        
        # 4. 分配地址
        result = await cmd_provision_with_address(0).execute_async(serial)
        unicast_addr = result['response']['params'][0]
        
        # 5. 綁定 AppKey 和 Model
        await cmd_add_appkey(unicast_addr, 0, 0).execute_async(serial)
        await cmd_bind_model_appkey(unicast_addr, 0x4005D, 0).execute_async(serial)

asyncio.run(provision_device())
```

## 測試

### 測試結構

```
tests/
├── unit/              # 單元測試 (不需硬體)
├── integration/       # 整合測試 (需要硬體)
└── conftest.py        # Pytest 配置
```

### 執行測試

```bash
# 執行所有測試
pytest

# 只執行單元測試 (不需要硬體)
pytest tests/unit/

# 只執行整合測試 (需要硬體: RL62M02 on COM17)
pytest tests/integration/

# 執行特定測試
python tests/integration/test_provisioning_flow.py  # 完整綁定流程
python tests/integration/test_node_list.py          # 節點列表查詢
python tests/integration/test_subscription.py       # 訂閱管理
python tests/integration/test_publish.py            # 發布管理
python tests/integration/test_basic_commands.py     # 基本 AT 指令
```

詳細測試說明請參考 [tests/README.md](tests/README.md)

## 專案結構

```
BleMeshProvisioner/
├── ble_mesh_provisioner/               # 主要套件
│   ├── core/                           # ✅ 核心通訊層 (AsyncIO)
│   │   ├── async_serial_interface.py  # 非同步串口介面
│   │   ├── async_at_command.py        # 非同步 AT 指令
│   │   └── response_parser.py         # 回應解析器
│   ├── network/                        # ⏳ 網路管理層 (開發中)
│   ├── devices/                        # ⏳ 裝置層 (規劃中)
│   └── utils/                          # ✅ 工具模組
├── tests/                              # ✅ 測試程式
│   ├── unit/                           # 單元測試 (不需硬體)
│   ├── integration/                    # 整合測試 (需要硬體)
│   ├── conftest.py                     # Pytest 配置
│   └── README.md                       # 測試指南
├── docs/                               # 📚 開發文件
├── SDK_DOC/                            # 📚 SDK 參考文件
└── examples/                           # 📘 範例程式
```

## AT 指令支援狀態

| 指令 | 功能 | 狀態 |
|------|------|------|
| AT+VER | 查詢韌體版本 | ✅ |
| AT+RST | 重啟模組 | ✅ |
| AT+MCLR | 清除 Mesh 網路 | ✅ |
| AT+DIS | 掃描未綁定裝置 | ✅ |
| AT+PBADVCON | 開始綁定連線 | ✅ |
| AT+PROV | 分配節點地址 | ✅ |
| AT+AKA | 新增 AppKey | ✅ |
| AT+MAKB | 綁定 Model AppKey | ✅ |
| AT+NL | 查詢節點列表 | ✅ |
| AT+MSAA | 新增訂閱 | ✅ |
| AT+MSAD | 刪除訂閱 | ✅ |
| AT+MPAS | 設定發布 | ✅ |
| AT+MPAD | 清除發布 | ✅ |
| AT+MDTS | 傳送資料 | ✅ |

## 開發狀態

### v0.2.0 (Current)
- ✅ 完整 AsyncIO 架構遷移
- ✅ 所有 14 種 AT 指令實作與驗證
- ✅ 完整綁定流程測試通過
- ✅ 訂閱/發布管理功能驗證
- ✅ 硬體測試完成 (RL62M02 Firmware 1.0.6)

### 下一步 (v0.3.0)
- ⏳ Provisioner Manager 實作
- ⏳ CLI 工具開發
- ⏳ 裝置層抽象化

詳細資訊請參考：
- [PROVISIONING_FLOW.md](PROVISIONING_FLOW.md) - 綁定流程說明
- [PROV_ADDRESS_ALLOCATION.md](PROV_ADDRESS_ALLOCATION.md) - 地址分配機制
- [docs/PROVISIONER_CLI_DESIGN.md](docs/PROVISIONER_CLI_DESIGN.md) - CLI 設計文檔

## 授權

MIT License

---
**開發階段**: Alpha (v0.1.0) | **最後更新**: 2025-11-09
