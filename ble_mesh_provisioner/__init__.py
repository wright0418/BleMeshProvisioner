"""
BLE Mesh Provisioner SDK

Python AsyncIO SDK for RichLink RL62M BLE Mesh Provisioner modules using UART AT commands.
"""

__version__ = "0.2.0"
__author__ = "Your Name"

# AsyncIO 版本 (推薦使用)
from ble_mesh_provisioner.core.async_serial_interface import AsyncSerialInterface
from ble_mesh_provisioner.core.async_at_command import AsyncATCommand
from ble_mesh_provisioner.network.async_provisioner_manager import AsyncProvisionerManager
from ble_mesh_provisioner.network.async_message_listener import AsyncMessageListener

# 為了向後兼容，提供舊名稱的別名
SerialInterface = AsyncSerialInterface
ATCommand = AsyncATCommand
ProvisionerManager = AsyncProvisionerManager
MessageListener = AsyncMessageListener

__all__ = [
    # 新的 AsyncIO API (推薦)
    "AsyncSerialInterface",
    "AsyncATCommand",
    "AsyncProvisionerManager",
    "AsyncMessageListener",
    # 向後兼容的別名
    "SerialInterface",
    "ATCommand",
    "ProvisionerManager",
    "MessageListener",
]
