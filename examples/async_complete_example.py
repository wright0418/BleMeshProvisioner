"""
Complete AsyncIO example for BLE Mesh Provisioner SDK.

This example demonstrates all major features:
1. Device discovery (scanning)
2. Device provisioning
3. Node configuration
4. Message listening
"""

import asyncio
from ble_mesh_provisioner import (
    AsyncSerialInterface,
    AsyncProvisionerManager,
)


async def scan_and_provision_example(manager: AsyncProvisionerManager):
    """Example: Scan for devices and provision one."""

    print("\n" + "=" * 70)
    print("  掃描並配置設備範例")
    print("=" * 70)

    # 1. Scan for unprovisioned devices
    print("\n▶ 掃描未配置的設備 (10秒)...")

    devices = await manager.scan_devices(
        duration=10,
        on_device_found=lambda d: print(
            f"  📡 發現設備: UUID={d['uuid']}, RSSI={d['rssi']}")
    )

    if not devices:
        print("  ℹ️  未發現任何設備")
        return

    print(f"\n✓ 發現 {len(devices)} 個設備")

    # 2. Select first device to provision
    device = devices[0]
    print(f"\n▶ 配置設備: {device['uuid']}")

    try:
        node_addr = await manager.provision_device(
            uuid=device['uuid'],
            unicast_addr="0x0100"
        )
        print(f"✓ 設備已配置，地址: {node_addr}")

        # Note: 進一步的節點配置（AppKey, Model binding等）
        # 可以使用 async_cmd_* 函數直接發送命令

    except Exception as e:
        print(f"✗ 配置失敗: {e}")


async def list_nodes_example(manager: AsyncProvisionerManager):
    """Example: List all provisioned nodes."""

    print("\n" + "=" * 70)
    print("  列出所有已配置節點")
    print("=" * 70)

    nodes = await manager.list_nodes()

    if not nodes:
        print("\n  ℹ️  目前沒有已配置的節點")
        return

    print(f"\n✓ 找到 {len(nodes)} 個節點:\n")

    for i, node in enumerate(nodes, 1):
        print(f"  {i}. 地址: {node['address']}")
        print(f"     元素數: {node['elements']}")
        print(f"     在線狀態: {'在線' if node['online'] else '離線'}")
        print()


async def message_listener_example(manager: AsyncProvisionerManager):
    """Example: Listen for mesh messages."""

    print("\n" + "=" * 70)
    print("  監聽 Mesh 訊息")
    print("=" * 70)

    print("\n▶ 啟動訊息監聽器...")
    print("  監聽 10 秒，按 Ctrl+C 提前結束\n")

    # Define message handler
    async def handle_mesh_data(msg):
        print(f"  📨 收到 Mesh 數據: {msg}")

    # Register handler
    manager.listener.add_handler('MDTG', handle_mesh_data)

    try:
        # Start listener
        await manager.listener.start()

        # Wait for messages
        await asyncio.sleep(10)

    except KeyboardInterrupt:
        print("\n  ⚠️  監聽中斷")
    finally:
        manager.listener.remove_handler('MDTG', handle_mesh_data)
        print("\n✓ 監聽器已停止")


async def main():
    """Main async function."""

    # Configuration
    PORT = "COM17"  # 修改為你的串口
    BAUDRATE = 115200

    print("=" * 70)
    print("  BLE Mesh Provisioner - 完整 AsyncIO 範例")
    print("=" * 70)
    print(f"\n串口: {PORT}, 波特率: {BAUDRATE}\n")

    # Create serial interface
    serial = AsyncSerialInterface(PORT, BAUDRATE, timeout=5.0)

    try:
        # Open connection
        await serial.open()
        print("✓ 串口連接成功\n")

        # Create manager
        manager = AsyncProvisionerManager(serial)

        # Get basic info
        version = await manager.get_version()
        role = await manager.get_role()

        print(f"韌體版本: {version}")
        print(f"設備角色: {role}")

        # Run examples (uncomment the ones you want to try)

        # Example 1: List nodes
        await list_nodes_example(manager)

        # Example 2: Scan and provision
        # await scan_and_provision_example(manager)

        # Example 3: Message listener
        # await message_listener_example(manager)

        print("\n" + "=" * 70)
        print("  ✓ 範例執行完成")
        print("=" * 70)

    except Exception as e:
        print(f"\n✗ 錯誤: {e}")
        import traceback
        traceback.print_exc()

    finally:
        await serial.close()
        print("\n✓ 串口已關閉")


if __name__ == "__main__":
    # Run async main
    asyncio.run(main())
