"""
Pytest Configuration and Fixtures

提供測試所需的共用配置和 fixtures
"""

import pytest
import asyncio
from typing import AsyncGenerator
from ble_mesh_provisioner.core.async_serial_interface import AsyncSerialInterface
from ble_mesh_provisioner.network.async_provisioner_manager import AsyncProvisionerManager
from ble_mesh_provisioner.utils.logger import setup_logger

# 測試用預設 COM 埠
DEFAULT_TEST_PORT = "COM17"
DEFAULT_BAUDRATE = 115200


@pytest.fixture(scope="session")
def event_loop():
    """建立事件迴圈"""
    loop = asyncio.get_event_loop_policy().new_event_loop()
    yield loop
    loop.close()


@pytest.fixture
def test_logger():
    """測試用 logger"""
    return setup_logger("pytest", level=20, console=True)


@pytest.fixture
async def serial_interface() -> AsyncGenerator[AsyncSerialInterface, None]:
    """
    提供已開啟的串口介面 (需要硬體)

    使用方式:
        async def test_something(serial_interface):
            result = await some_command.execute(serial_interface)
    """
    serial = AsyncSerialInterface(DEFAULT_TEST_PORT, baudrate=DEFAULT_BAUDRATE)
    await serial.open()
    yield serial
    await serial.close()


@pytest.fixture
async def provisioner_manager(
    serial_interface: AsyncSerialInterface,
) -> AsyncProvisionerManager:
    """
    提供 Provisioner Manager 實例 (需要硬體)

    使用方式:
        async def test_something(provisioner_manager):
            result = await provisioner_manager.some_method()
    """
    return AsyncProvisionerManager(serial_interface)


# Pytest 配置
def pytest_configure(config):
    """Pytest 配置"""
    config.addinivalue_line(
        "markers", "hardware: 標記需要實際硬體的測試"
    )
    config.addinivalue_line(
        "markers", "unit: 標記不需要硬體的單元測試"
    )
    config.addinivalue_line(
        "markers", "integration: 標記需要硬體的整合測試"
    )
    config.addinivalue_line(
        "markers", "slow: 標記執行時間較長的測試"
    )
