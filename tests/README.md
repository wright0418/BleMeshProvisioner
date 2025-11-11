# 測試指南

## 測試結構

```
tests/
├── conftest.py              # Pytest 配置和共用 fixtures
├── unit/                    # 單元測試 (不需要硬體)
│   ├── test_async_at_command.py
│   ├── test_async_simple.py
│   ├── test_command_validation.py
│   └── mocks/              # Mock 物件
└── integration/            # 整合測試 (需要硬體)
    ├── test_basic_commands.py      # 基本 AT 指令測試
    ├── test_provisioning_flow.py   # 完整綁定流程
    ├── test_node_list.py           # 節點列表查詢
    ├── test_subscription.py        # 訂閱管理
    ├── test_publish.py             # 發布管理
    └── test_hardware.py            # 硬體基礎測試
```

## 執行測試

### 執行所有測試
```bash
pytest
```

### 只執行單元測試 (不需要硬體)
```bash
pytest tests/unit/
```

### 只執行整合測試 (需要硬體)
```bash
pytest tests/integration/
```

### 執行特定測試檔案
```bash
# 測試完整綁定流程
python tests/integration/test_provisioning_flow.py

# 測試節點列表
python tests/integration/test_node_list.py

# 測試基本命令
python tests/integration/test_basic_commands.py
```

### 使用 marker 篩選測試
```bash
# 只執行標記為 unit 的測試
pytest -m unit

# 只執行標記為 integration 的測試
pytest -m integration

# 排除需要硬體的測試
pytest -m "not hardware"
```

## 硬體測試要求

整合測試需要以下硬體環境：

- **硬體**: RichLink RL62M02 Provisioner Module
- **�韌體**: v1.0.6 或更高
- **連接**: UART COM17, 115200 baud, 8N1
- **裝置**: 至少一個已綁定的 BLE Mesh 節點 (用於部分測試)

### 設定 COM 埠

如果你的硬體不是使用 COM17，請修改 `tests/conftest.py`:

```python
DEFAULT_TEST_PORT = "COM17"  # 改成你的 COM 埠
```

## 測試分類

### Unit Tests (單元測試)
- ✅ **test_command_validation.py**: AT 指令格式驗證
- ✅ **test_async_at_command.py**: AsyncIO AT 指令測試
- ✅ **test_async_simple.py**: 簡單的 AsyncIO 測試

### Integration Tests (整合測試)
- 🔧 **test_basic_commands.py**: 基本 AT 指令 (VER, MRG, DIS)
- 🔧 **test_provisioning_flow.py**: 完整綁定流程 (DIS→PROV→AKA→MAKB)
- 🔧 **test_node_list.py**: AT+NL 節點列表查詢
- 🔧 **test_subscription.py**: AT+MSAA/MSAD 訂閱管理
- 🔧 **test_publish.py**: AT+MPAS/MPAD 發布管理
- 🔧 **test_hardware.py**: 硬體基礎功能測試

圖示說明:
- ✅ = 不需要硬體
- 🔧 = 需要硬體

## 測試覆蓋率

```bash
# 產生覆蓋率報告
pytest --cov=ble_mesh_provisioner --cov-report=html

# 查看報告
open htmlcov/index.html  # macOS/Linux
start htmlcov/index.html # Windows
```

## 開發新測試

### 單元測試模板
```python
"""測試描述"""
import pytest

def test_something():
    """測試某功能"""
    # Arrange
    expected = "result"
    
    # Act
    actual = do_something()
    
    # Assert
    assert actual == expected
```

### 整合測試模板
```python
"""測試描述"""
import pytest
import asyncio

@pytest.mark.integration
@pytest.mark.hardware
async def test_hardware_feature(provisioner_manager):
    """測試硬體功能"""
    # Arrange
    expected_response = "SUCCESS"
    
    # Act
    result = await provisioner_manager.some_command()
    
    # Assert
    assert result['status'] == expected_response
```

## 故障排除

### COM 埠錯誤
```
serial.serialutil.SerialException: could not open port 'COM17'
```
解決: 檢查硬體連接，或修改 `conftest.py` 的 `DEFAULT_TEST_PORT`

### 硬體無回應
```
TimeoutError: Command execution timeout
```
解決: 
1. 檢查硬體電源
2. 確認韌體版本 (需要 1.0.6+)
3. 嘗試重啟模組 (AT+RST)

### 綁定失敗
```
Failed to provision device
```
解決:
1. 確認裝置已進入配對模式
2. 檢查訊號強度 (RSSI > -80)
3. 嘗試清除網路 (AT+MCLR) 後重試
