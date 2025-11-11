"""
簡單的 AsyncIO 功能測試腳本
不依賴 pytest,直接運行驗證基本功能
"""

import pytest
from tests.mocks.async_mock_serial import AsyncMockSerial
from ble_mesh_provisioner.core.async_at_command import (
    AsyncATCommand,
    async_cmd_get_version,
    async_cmd_get_role,
)
import asyncio
import sys
import os

# 添加專案路徑
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))


def test_at_command_build():
    """測試 AT 命令建構"""
    print("✓ 測試 AT 命令建構...")

    # 簡單命令
    cmd = AsyncATCommand("VER")
    assert cmd.raw == "AT+VER\r\n", f"Expected 'AT+VER\\r\\n', got '{cmd.raw}'"
    print("  ✓ 簡單命令: AT+VER")

    # 帶參數的命令
    cmd = AsyncATCommand("MDTS", ["0x0100", "0", "0", "1", "0x11223344"])
    expected = "AT+MDTS 0x0100 0 0 1 0x11223344\r\n"
    assert cmd.raw == expected, f"Expected '{expected}', got '{cmd.raw}'"
    print("  ✓ 帶參數命令: AT+MDTS")

    # 便利函數
    cmd = async_cmd_get_version()
    assert cmd.command == "VER"
    assert cmd.raw == "AT+VER\r\n"
    print("  ✓ 便利函數: async_cmd_get_version()")

    cmd = async_cmd_get_role()
    assert cmd.command == "MRG"
    assert cmd.raw == "AT+MRG\r\n"
    print("  ✓ 便利函數: async_cmd_get_role()")

    print("✅ AT 命令建構測試通過\n")


@pytest.mark.asyncio
async def test_mock_serial_basic():
    """測試 Mock Serial 基本功能"""
    print("✓ 測試 Mock Serial 基本功能...")

    mock = AsyncMockSerial()

    # 測試 open/close
    assert not mock.is_open(), "Mock should be closed initially"
    mock.open()
    assert mock.is_open(), "Mock should be open after open()"
    print("  ✓ Open/Close 功能")

    # 測試 write
    mock.write(b"AT+VER\r\n")
    print("  ✓ Write 功能")

    # 等待回應生成
    await asyncio.sleep(0.2)

    # 檢查命令歷史
    history = mock.get_command_history()
    assert len(
        history) == 1, f"Expected 1 command in history, got {len(history)}"
    assert history[0]['command'] == 'AT+VER', f"Expected 'AT+VER', got '{history[0]['command']}'"
    print("  ✓ 命令歷史記錄")

    mock.close()
    print("✅ Mock Serial 基本測試通過\n")


@pytest.mark.asyncio
async def test_mock_serial_async():
    """測試 Mock Serial 非同步功能"""
    print("✓ 測試 Mock Serial 非同步功能...")

    mock = AsyncMockSerial(response_delay=0.1)
    mock.open()

    # 寫入命令
    mock.write(b"AT+VER\r\n")
    print("  ✓ 發送命令: AT+VER")

    # 等待回應生成
    await asyncio.sleep(0.2)

    # 讀取回應
    if mock.in_waiting > 0:
        data = mock.read(mock.in_waiting)
        response = data.decode('utf-8')
        print(f"  ✓ 收到回應: {response.strip()}")

        assert 'VER-MSG' in response, f"Expected 'VER-MSG' in response, got '{response}'"
        assert 'SUCCESS' in response, f"Expected 'SUCCESS' in response, got '{response}'"
        print("  ✓ 回應格式正確")
    else:
        raise AssertionError("No response received from mock")

    mock.close()
    print("✅ Mock Serial 非同步測試通過\n")


@pytest.mark.asyncio
async def test_mock_serial_custom_response():
    """測試自訂回應"""
    print("✓ 測試自訂回應...")

    mock = AsyncMockSerial(response_delay=0.1)
    mock.add_response('AT+TEST', 'TEST-MSG SUCCESS Custom response\r\n')
    mock.open()

    mock.write(b"AT+TEST\r\n")
    await asyncio.sleep(0.2)

    data = mock.read(mock.in_waiting)
    response = data.decode('utf-8')

    assert 'Custom response' in response, f"Expected 'Custom response', got '{response}'"
    print(f"  ✓ 自訂回應: {response.strip()}")

    mock.close()
    print("✅ 自訂回應測試通過\n")


@pytest.mark.asyncio
async def test_mock_serial_error():
    """測試錯誤模擬"""
    print("✓ 測試錯誤模擬...")

    mock = AsyncMockSerial(response_delay=0.1)
    mock.simulate_error('AT+VER')
    mock.open()

    mock.write(b"AT+VER\r\n")
    await asyncio.sleep(0.2)

    data = mock.read(mock.in_waiting)
    response = data.decode('utf-8')

    assert 'ERROR' in response, f"Expected 'ERROR' in response, got '{response}'"
    print(f"  ✓ 錯誤回應: {response.strip()}")

    mock.close()
    print("✅ 錯誤模擬測試通過\n")


@pytest.mark.asyncio
async def test_mock_notifications():
    """測試通知生成"""
    print("✓ 測試通知生成...")

    mock = AsyncMockSerial(response_delay=0.05)
    mock.open()

    # 啟用通知 (每 0.3 秒一次)
    mock.enable_notifications('MDTG', interval=0.3)
    print("  ✓ 已啟用通知生成")

    # 等待一些通知
    await asyncio.sleep(1.0)

    # 讀取通知
    if mock.in_waiting > 0:
        data = mock.read(mock.in_waiting)
        response = data.decode('utf-8')

        count = response.count('MDTG-MSG')
        print(f"  ✓ 收到 {count} 個 MDTG-MSG 通知")
        assert count >= 2, f"Expected at least 2 notifications, got {count}"
    else:
        raise AssertionError("No notifications received")

    mock.close()
    print("✅ 通知生成測試通過\n")


async def run_all_tests():
    """執行所有測試"""
    print("="*60)
    print("AsyncIO 架構功能測試")
    print("="*60)
    print()

    try:
        # 同步測試
        test_at_command_build()

        # 非同步測試
        await test_mock_serial_basic()
        await test_mock_serial_async()
        await test_mock_serial_custom_response()
        await test_mock_serial_error()
        await test_mock_notifications()

        print("="*60)
        print("✅ 所有測試通過!")
        print("="*60)
        return 0

    except AssertionError as e:
        print("\n" + "="*60)
        print(f"❌ 測試失敗: {e}")
        print("="*60)
        return 1
    except Exception as e:
        print("\n" + "="*60)
        print(f"❌ 測試錯誤: {e}")
        import traceback
        traceback.print_exc()
        print("="*60)
        return 1


if __name__ == "__main__":
    exit_code = asyncio.run(run_all_tests())
    sys.exit(exit_code)
