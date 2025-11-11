"""
Basic usage example for BLE Mesh Provisioner SDK (AsyncIO version).

Demonstrates:
- Opening async serial connection
- Querying firmware version
- Querying module role
- Proper async/await patterns
- Error handling
"""

from ble_mesh_provisioner.network.async_provisioner_manager import AsyncProvisionerManager
from ble_mesh_provisioner.core.async_serial_interface import AsyncSerialInterface
import asyncio
import sys
from pathlib import Path

# 添加專案根目錄到路徑
sys.path.insert(0, str(Path(__file__).parent.parent))


async def main():
    """Main async example function."""

    # Configure your serial port here
    PORT = 'COM17'  # Windows: 'COM17', Linux: '/dev/ttyUSB0'
    BAUDRATE = 115200

    print("=" * 50)
    print("BLE Mesh Provisioner SDK - AsyncIO Example")
    print("=" * 50)
    print()

    try:
        # Create serial interface
        print(f"Connecting to {PORT}...")
        serial = AsyncSerialInterface(PORT, BAUDRATE, timeout=5.0)
        await serial.open()
        print("✓ Connected successfully\n")

        # Create provisioner manager
        manager = AsyncProvisionerManager(serial)

        try:
            # Query firmware version
            print("Querying firmware version...")
            version = await manager.get_version()
            print(f"✓ Firmware Version: {version}\n")

            # Query module role
            print("Querying module role...")
            role = await manager.get_role()
            print(f"✓ Module Role: {role}\n")

            if role != "PROVISIONER":
                print("⚠ Warning: Module is not a PROVISIONER")
                print("This SDK is designed for Provisioner modules\n")

            # List provisioned nodes
            print("Querying provisioned nodes...")
            nodes = await manager.list_nodes()
            print(f"✓ Found {len(nodes)} provisioned nodes\n")

            if nodes:
                print("Provisioned nodes:")
                for node in nodes:
                    print(
                        f"  - Address: {node['address']}, Elements: {node['elements']}, Online: {node['online']}")
            else:
                print("  (No nodes provisioned yet)")

            print("\n" + "=" * 50)
            print("✓ All queries completed successfully")
            print("=" * 50)

        finally:
            # Always close serial connection
            await serial.close()

    except Exception as e:
        print(f"\n✗ Error: {e}")
        print(f"Please check:")
        print(f"  - Port name is correct ({PORT})")
        print(f"  - Module is connected")
        print(f"  - No other program is using the port")


if __name__ == "__main__":
    # Run async main function
    asyncio.run(main())
