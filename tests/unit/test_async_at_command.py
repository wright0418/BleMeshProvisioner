"""
AsyncIO unit tests for AT commands and serial interface.

測試 AsyncIO 架構的基本功能。
"""

import pytest
import asyncio
from ble_mesh_provisioner.core.async_serial_interface import AsyncSerialInterface
from ble_mesh_provisioner.core.async_at_command import (
    AsyncATCommand,
    async_cmd_get_version,
    async_cmd_get_role,
)
from tests.mocks.async_mock_serial import AsyncMockSerial


@pytest.mark.asyncio
async def test_async_serial_interface_open_close():
    """Test async serial interface open and close."""
    # 使用 mock serial
    mock_serial = AsyncMockSerial()

    # 創建 interface (需要修改 AsyncSerialInterface 支持 mock)
    # 這裡展示測試架構
    assert mock_serial.is_open() == False
    mock_serial.open()
    assert mock_serial.is_open() == True
    mock_serial.close()
    assert mock_serial.is_open() == False


@pytest.mark.asyncio
async def test_async_at_command_build():
    """Test AT command building."""
    # Test simple command
    cmd = AsyncATCommand("VER")
    assert cmd.raw == "AT+VER\r\n"

    # Test command with params
    cmd = AsyncATCommand("MDTS", ["0x0100", "0", "0", "1", "0x11223344"])
    assert cmd.raw == "AT+MDTS 0x0100 0 0 1 0x11223344\r\n"


@pytest.mark.asyncio
async def test_async_command_helpers():
    """Test command helper functions."""
    cmd = async_cmd_get_version()
    assert cmd.command == "VER"
    assert cmd.raw == "AT+VER\r\n"

    cmd = async_cmd_get_role()
    assert cmd.command == "MRG"
    assert cmd.raw == "AT+MRG\r\n"


@pytest.mark.asyncio
async def test_mock_serial_write_read():
    """Test mock serial write and read."""
    mock = AsyncMockSerial()
    mock.open()

    # Write command
    mock.write(b"AT+VER\r\n")

    # Wait for response generation
    await asyncio.sleep(0.2)

    # Read response
    assert mock.in_waiting > 0
    data = mock.read(mock.in_waiting)
    response = data.decode('utf-8')

    assert 'VER-MSG' in response
    assert 'SUCCESS' in response

    mock.close()


@pytest.mark.asyncio
async def test_mock_serial_custom_response():
    """Test mock serial with custom responses."""
    mock = AsyncMockSerial()
    mock.add_response('AT+TEST', 'TEST-MSG SUCCESS Custom response\r\n')
    mock.open()

    # Write custom command
    mock.write(b"AT+TEST\r\n")
    await asyncio.sleep(0.2)

    # Check response
    data = mock.read(mock.in_waiting)
    response = data.decode('utf-8')

    assert 'Custom response' in response

    mock.close()


@pytest.mark.asyncio
async def test_mock_serial_error_simulation():
    """Test error simulation."""
    mock = AsyncMockSerial()
    mock.simulate_error('AT+VER')
    mock.open()

    mock.write(b"AT+VER\r\n")
    await asyncio.sleep(0.2)

    data = mock.read(mock.in_waiting)
    response = data.decode('utf-8')

    assert 'ERROR' in response

    mock.close()


@pytest.mark.asyncio
async def test_mock_serial_command_history():
    """Test command history tracking."""
    mock = AsyncMockSerial()
    mock.open()

    # Send multiple commands
    commands = [b"AT+VER\r\n", b"AT+MRG\r\n", b"AT+MLN\r\n"]
    for cmd in commands:
        mock.write(cmd)

    # Check history
    history = mock.get_command_history()
    assert len(history) == 3
    assert history[0]['command'] == 'AT+VER'
    assert history[1]['command'] == 'AT+MRG'
    assert history[2]['command'] == 'AT+MLN'

    mock.close()


@pytest.mark.asyncio
async def test_mock_serial_notifications():
    """Test notification generation."""
    mock = AsyncMockSerial()
    mock.open()

    # Enable notifications
    mock.enable_notifications('MDTG', interval=0.5)

    # Wait for some notifications
    await asyncio.sleep(1.5)

    # Should have received 2-3 notifications
    data = mock.read(mock.in_waiting)
    response = data.decode('utf-8')

    # Count MDTG-MSG occurrences
    count = response.count('MDTG-MSG')
    assert count >= 2

    mock.close()


# 整合測試 (需要實際硬體時 skip)
@pytest.mark.skipif(True, reason="Requires actual RL62M hardware")
@pytest.mark.asyncio
async def test_real_hardware_version():
    """
    Integration test with real hardware.

    這個測試需要連接實際的 RL62M 模組。
    執行時會記錄互動數據到測試資料庫。
    """
    from tests.mocks.async_mock_serial import HardwareInteractionRecorder

    # 設定真實的串口
    port = "COM3"  # 根據實際情況修改

    # 創建 recorder
    recorder = HardwareInteractionRecorder()

    # 創建 serial interface
    serial = AsyncSerialInterface(port)

    try:
        await serial.open()

        # 執行命令並記錄
        import time
        start = time.time()

        result = await serial.send_command(
            "AT+VER\r\n",
            expect_response='VER',
            timeout=5.0
        )

        duration = time.time() - start

        # 記錄互動
        recorder.record(
            command="AT+VER\r\n",
            response=result.get('raw', '') if result else '',
            duration=duration
        )

        # 驗證結果
        assert result is not None
        assert result['type'] == 'VER'
        assert result['status'] == 'SUCCESS'

        print(f"Version: {result.get('params', [])}")

    finally:
        await serial.close()
        recorder.save()


if __name__ == "__main__":
    # 執行測試
    pytest.main([__file__, "-v", "-s"])
