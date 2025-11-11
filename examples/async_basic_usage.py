"""
AsyncIO usage example for RL62M BLE Mesh Provisioner.

展示如何使用新的 AsyncIO 架構進行設備管理。
"""

import asyncio
from ble_mesh_provisioner.core.async_serial_interface import AsyncSerialInterface
from ble_mesh_provisioner.network.async_provisioner_manager import AsyncProvisionerManager
from ble_mesh_provisioner.utils.logger import setup_logger

logger = setup_logger(
    "example",
    level=20,
    log_file="logs/example.log",
    console=True
)


async def example_basic_commands():
    """基本命令使用範例。"""
    # 設定串口 (根據實際情況修改)
    port = "COM3"  # Windows
    # port = "/dev/ttyUSB0"  # Linux

    # 創建 serial interface
    serial = AsyncSerialInterface(port, baudrate=115200)

    try:
        # 開啟連接
        await serial.open()
        logger.info("✅ Serial port opened")

        # 創建 provisioner manager
        manager = AsyncProvisionerManager(serial)

        # 1. 獲取韌體版本
        logger.info("Getting firmware version...")
        version = await manager.get_version()
        logger.info(f"📌 Firmware version: {version}")

        # 2. 驗證是 Provisioner
        logger.info("Verifying provisioner role...")
        is_provisioner = await manager.verify_provisioner()
        if not is_provisioner:
            logger.error("❌ Device is not a provisioner!")
            return

        logger.info("✅ Device is provisioner")

        # 3. 列出已配置節點
        logger.info("Listing provisioned nodes...")
        nodes = await manager.list_nodes()
        logger.info(f"📋 Found {len(nodes)} nodes")
        for i, node in enumerate(nodes):
            logger.info(f"  Node {i}: {node}")

    except Exception as e:
        logger.error(f"❌ Error: {e}")
    finally:
        # 關閉連接
        await serial.close()
        logger.info("✅ Serial port closed")


async def example_device_scan():
    """設備掃描範例。"""
    port = "COM3"
    serial = AsyncSerialInterface(port)

    try:
        await serial.open()
        manager = AsyncProvisionerManager(serial)

        # 驗證 provisioner
        if not await manager.verify_provisioner():
            logger.error("Not a provisioner!")
            return

        # 掃描設備 (10 秒)
        logger.info("🔍 Starting device scan for 10 seconds...")

        def on_device_found(device):
            """設備發現回調。"""
            logger.info(
                f"  📱 Found: UUID={device['uuid']}, RSSI={device['rssi']}")

        devices = await manager.scan_devices(
            duration=10,
            on_device_found=on_device_found
        )

        logger.info(f"✅ Scan complete. Total devices: {len(devices)}")

        # 顯示所有設備
        for i, device in enumerate(devices, 1):
            logger.info(f"{i}. UUID: {device['uuid']}")
            logger.info(f"   MAC: {device['mac']}")
            logger.info(f"   RSSI: {device['rssi']}")

    except Exception as e:
        logger.error(f"❌ Error: {e}")
    finally:
        await serial.close()


async def example_provision_device():
    """設備配置範例。"""
    port = "COM3"
    serial = AsyncSerialInterface(port)

    try:
        await serial.open()
        manager = AsyncProvisionerManager(serial)

        # 驗證 provisioner
        if not await manager.verify_provisioner():
            return

        # 1. 掃描設備
        logger.info("🔍 Scanning for devices...")
        devices = await manager.scan_devices(duration=5)

        if not devices:
            logger.warning("⚠️ No devices found!")
            return

        # 2. 選擇第一個設備進行配置
        device = devices[0]
        logger.info(f"📱 Provisioning device: {device['uuid']}")

        # 3. 配置設備
        success = await manager.provision_device(
            uuid=device['uuid'],
            unicast_addr="0x0100",  # 可以根據需要分配地址
            attention_duration=0
        )

        if success:
            logger.info("✅ Device provisioned successfully!")
        else:
            logger.error("❌ Provisioning failed!")

    except Exception as e:
        logger.error(f"❌ Error: {e}")
    finally:
        await serial.close()


async def example_concurrent_operations():
    """並發操作範例 - 展示 AsyncIO 的優勢。"""
    port = "COM3"
    serial = AsyncSerialInterface(port)

    try:
        await serial.open()
        manager = AsyncProvisionerManager(serial)

        # 並發執行多個操作
        logger.info("🚀 Running concurrent operations...")

        # 同時執行：獲取版本、角色、列出節點
        results = await asyncio.gather(
            manager.get_version(),
            manager.get_role(),
            manager.list_nodes(),
            return_exceptions=True
        )

        version, role, nodes = results

        logger.info(f"📌 Version: {version}")
        logger.info(f"📌 Role: {role}")
        logger.info(f"📌 Nodes: {len(nodes) if isinstance(nodes, list) else 0}")

    except Exception as e:
        logger.error(f"❌ Error: {e}")
    finally:
        await serial.close()


async def example_message_listener():
    """訊息監聽範例。"""
    port = "COM3"
    serial = AsyncSerialInterface(port)
    manager = None

    try:
        await serial.open()
        manager = AsyncProvisionerManager(serial)

        # 設定訊息處理器
        async def handle_mesh_data(msg):
            """處理 Mesh 數據訊息。"""
            logger.info(f"📨 Received mesh data: {msg}")

        # 註冊處理器
        manager.listener.add_handler('MDTG-MSG', handle_mesh_data)

        # 啟動 listener
        await manager.listener.start()

        logger.info("👂 Listening for mesh messages... (Press Ctrl+C to stop)")

        # 持續監聽
        try:
            while True:
                await asyncio.sleep(1)
        except KeyboardInterrupt:
            logger.info("⏹️ Stopping listener...")

    except Exception as e:
        logger.error(f"❌ Error: {e}")
    finally:
        if manager and manager.listener._running:
            await manager.listener.stop()
        await serial.close()


def main():
    """主程式。"""
    import sys

    examples = {
        '1': ('Basic Commands', example_basic_commands),
        '2': ('Device Scan', example_device_scan),
        '3': ('Provision Device', example_provision_device),
        '4': ('Concurrent Operations', example_concurrent_operations),
        '5': ('Message Listener', example_message_listener),
    }

    print("\n" + "="*50)
    print("AsyncIO BLE Mesh Provisioner Examples")
    print("="*50)
    print("\nAvailable examples:")
    for key, (name, _) in examples.items():
        print(f"  {key}. {name}")
    print("\n")

    choice = input("Select example (1-5) or 'q' to quit: ").strip()

    if choice.lower() == 'q':
        return

    if choice in examples:
        name, func = examples[choice]
        print(f"\n▶️ Running: {name}\n")
        try:
            asyncio.run(func())
        except KeyboardInterrupt:
            print("\n\n⏹️ Interrupted by user")
    else:
        print("❌ Invalid choice!")


if __name__ == "__main__":
    main()
