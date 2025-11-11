"""
測試基本 AT 命令執行 (不包含需要綁定的命令)
驗證命令能正確發送並接收回應
"""

import asyncio
from ble_mesh_provisioner.core.async_serial_interface import AsyncSerialInterface
from ble_mesh_provisioner.core.async_at_command import (
    async_cmd_get_version,
    async_cmd_get_role,
    async_cmd_mesh_clear,
    async_cmd_start_scan,
    async_cmd_stop_scan,
)
from ble_mesh_provisioner.utils.logger import setup_logger

logger = setup_logger(
    "ble_mesh_provisioner",
    level=20,
    log_file="logs/basic_commands_test.log",
    console=True
)


async def test_basic_commands():
    """測試基本 AT 命令"""
    serial = AsyncSerialInterface(port="COM17", baudrate=115200, timeout=5.0)

    try:
        # 開啟串口
        await serial.open()
        print("✅ 串口已開啟\n")

        # 測試 1: AT+VER
        print("="*60)
        print("測試 AT+VER (查詢韌體版本)")
        print("="*60)
        cmd = async_cmd_get_version()
        print(f"發送命令: {cmd.raw.strip()}")
        result = await cmd.execute(serial)
        print(f"回應: {result}")
        print()

        # 測試 2: AT+MRG
        print("="*60)
        print("測試 AT+MRG (查詢角色)")
        print("="*60)
        cmd = async_cmd_get_role()
        print(f"發送命令: {cmd.raw.strip()}")
        result = await cmd.execute(serial)
        print(f"回應: {result}")
        print()

        # 測試 3: AT+DIS (掃描)
        print("="*60)
        print("測試 AT+DIS (掃描設備)")
        print("="*60)

        # 開始掃描
        cmd = async_cmd_start_scan()
        print(f"發送命令: {cmd.raw.strip()}")
        result = await cmd.execute(serial)
        print(f"回應: {result}")

        # 等待掃描
        print("掃描中... (3秒)")
        await asyncio.sleep(3)

        # 停止掃描
        cmd = async_cmd_stop_scan()
        print(f"發送命令: {cmd.raw.strip()}")
        result = await cmd.execute(serial)
        print(f"回應: {result}")
        print()

        # 測試 4: AT+NR (選擇性測試，會清除網路)
        # print("="*60)
        # print("測試 AT+NR (清除 Mesh 網路) - 已跳過")
        # print("="*60)
        # print("⚠️ 此命令會清除所有已配對的設備，跳過測試")
        # print()

        print("="*60)
        print("基本命令測試完成")
        print("="*60)

    except Exception as e:
        print(f"❌ 錯誤: {e}")
        import traceback
        traceback.print_exc()

    finally:
        await serial.close()
        print("✅ 串口已關閉")


if __name__ == "__main__":
    asyncio.run(test_basic_commands())
