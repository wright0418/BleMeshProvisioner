"""
實體硬體測試腳本

用於測試 AsyncIO 架構與實際 RL62M Provisioner 模組的通訊。

使用前請：
1. 確認 RL62M Provisioner 模組已連接
2. 修改下方的 SERIAL_PORT 設定為實際串口
3. 確認串口參數：115200, 8N1, No flow control
"""

from mocks.async_mock_serial import HardwareInteractionRecorder
from ble_mesh_provisioner.utils.logger import setup_logger
from ble_mesh_provisioner.network.async_provisioner_manager import AsyncProvisionerManager
from ble_mesh_provisioner.core.async_serial_interface import AsyncSerialInterface
import asyncio
import sys
import os
from datetime import datetime

# 添加專案路徑
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))


logger = setup_logger(
    "hardware_test",
    level=20,
    log_file="logs/hardware_test.log",
    console=True
)

# ============================================================================
# 配置區：請根據實際情況修改
# ============================================================================
SERIAL_PORT = "COM17"  # Windows: COM3, COM4 等 | Linux: /dev/ttyUSB0 等
BAUDRATE = 115200
TIMEOUT = 5.0

# 是否記錄硬體互動（用於建立測試資料庫）
RECORD_INTERACTIONS = True
INTERACTION_DB = "tests/hardware_interactions.json"

# ============================================================================


async def test_serial_connection():
    """測試串口連接"""
    print("\n" + "="*60)
    print("測試 1: 串口連接")
    print("="*60)

    try:
        serial = AsyncSerialInterface(SERIAL_PORT, BAUDRATE, TIMEOUT)
        await serial.open()

        print(f"✅ 串口 {SERIAL_PORT} 已成功開啟")
        print(f"   設定: {BAUDRATE} 8N1, Timeout={TIMEOUT}s")

        # 保持連接一下
        await asyncio.sleep(0.5)

        await serial.close()
        print("✅ 串口已正常關閉")
        return True

    except Exception as e:
        print(f"❌ 串口連接失敗: {e}")
        return False


async def test_basic_commands():
    """測試基本 AT 命令"""
    print("\n" + "="*60)
    print("測試 2: 基本 AT 命令")
    print("="*60)

    recorder = HardwareInteractionRecorder(
        INTERACTION_DB) if RECORD_INTERACTIONS else None

    try:
        serial = AsyncSerialInterface(SERIAL_PORT, BAUDRATE, TIMEOUT)
        await serial.open()
        manager = AsyncProvisionerManager(serial)

        # 測試 1: 獲取韌體版本
        print("\n▶ 測試命令: AT+VER (獲取韌體版本)")
        start = datetime.now()

        try:
            version = await manager.get_version()
            duration = (datetime.now() - start).total_seconds()

            print(f"  ✅ 韌體版本: {version}")
            print(f"  ⏱ 耗時: {duration:.3f}s")

            if recorder:
                recorder.record(
                    command="AT+VER\r\n",
                    response=f"VER-MSG SUCCESS {version}\r\n",
                    duration=duration
                )

        except Exception as e:
            print(f"  ❌ 失敗: {e}")
            return False

        # 測試 2: 獲取角色
        print("\n▶ 測試命令: AT+MRG (獲取設備角色)")
        start = datetime.now()

        try:
            role = await manager.get_role()
            duration = (datetime.now() - start).total_seconds()

            role_name = "Provisioner" if role == '1' else "Device" if role == '0' else "Unknown"
            print(f"  ✅ 設備角色: {role_name} ({role})")
            print(f"  ⏱ 耗時: {duration:.3f}s")

            if recorder:
                recorder.record(
                    command="AT+MRG\r\n",
                    response=f"MRG-MSG SUCCESS {role}\r\n",
                    duration=duration
                )

            if role != '1':
                print("  ⚠️  警告: 設備不是 Provisioner 角色!")

        except Exception as e:
            print(f"  ❌ 失敗: {e}")
            return False

        # 測試 3: 驗證 Provisioner
        print("\n▶ 驗證 Provisioner 角色")
        is_provisioner = await manager.verify_provisioner()

        if is_provisioner:
            print("  ✅ Provisioner 驗證通過")
        else:
            print("  ❌ Provisioner 驗證失敗")
            await serial.close()  # 確保關閉
            return False

        # 確保關閉串口
        await serial.close()
        logger.info("Serial port closed after basic commands test")

        # 儲存記錄
        if recorder:
            recorder.save()
            print(f"\n📝 硬體互動已記錄到: {INTERACTION_DB}")

        print("\n✅ 基本命令測試完成")
        return True

    except Exception as e:
        print(f"\n❌ 測試失敗: {e}")
        import traceback
        traceback.print_exc()
        return False


async def test_list_nodes():
    """測試列出已配置節點"""
    print("\n" + "="*60)
    print("測試 3: 列出已配置節點")
    print("="*60)

    try:
        serial = AsyncSerialInterface(SERIAL_PORT, BAUDRATE, TIMEOUT)
        await serial.open()
        manager = AsyncProvisionerManager(serial)

        print("\n▶ 執行命令: AT+NL (列出節點)")
        nodes = await manager.list_nodes()

        print(f"  ✅ 找到 {len(nodes)} 個已配置節點")

        if nodes:
            for i, node in enumerate(nodes, 1):
                print(f"     {i}. {node}")
        else:
            print("     (目前沒有已配置的節點)")

        await serial.close()
        return True

    except Exception as e:
        print(f"  ❌ 失敗: {e}")
        return False


async def test_concurrent_commands():
    """測試並發命令執行"""
    print("\n" + "="*60)
    print("測試 4: 並發命令執行")
    print("="*60)

    try:
        serial = AsyncSerialInterface(SERIAL_PORT, BAUDRATE, TIMEOUT)
        await serial.open()
        manager = AsyncProvisionerManager(serial)

        print("\n▶ 同時執行多個命令...")
        start = datetime.now()

        # 並發執行三個命令
        results = await asyncio.gather(
            manager.get_version(),
            manager.get_role(),
            manager.list_nodes(),
            return_exceptions=True
        )

        duration = (datetime.now() - start).total_seconds()

        version, role, nodes = results

        print(f"  ✅ 並發執行完成")
        print(f"  ⏱ 總耗時: {duration:.3f}s")
        print(f"     - 韌體版本: {version}")
        print(f"     - 設備角色: {role}")
        print(
            f"     - 節點數量: {len(nodes) if isinstance(nodes, list) else 'N/A'}")

        await serial.close()
        return True

    except Exception as e:
        print(f"  ❌ 失敗: {e}")
        return False


async def test_message_listener():
    """測試訊息監聽功能"""
    print("\n" + "="*60)
    print("測試 5: 訊息監聽")
    print("="*60)

    try:
        serial = AsyncSerialInterface(SERIAL_PORT, BAUDRATE, TIMEOUT)
        await serial.open()
        manager = AsyncProvisionerManager(serial)

        # 設定訊息處理器
        received_count = [0]  # 使用 list 讓內部函數可修改

        async def message_handler(msg):
            received_count[0] += 1
            print(
                f"  📨 收到訊息 #{received_count[0]}: {msg.get('type')} - {msg.get('raw', '')[:50]}")

        manager.listener.add_handler('MDTG-MSG', message_handler)
        manager.listener.add_handler('SCAN-MSG', message_handler)

        # 啟動 listener
        await manager.listener.start()
        print("\n▶ 訊息監聽器已啟動")
        print("  監聽 5 秒鐘...")
        print("  (如果有設備發送訊息，將會顯示在這裡)")

        # 監聽 5 秒
        try:
            await asyncio.sleep(5.0)
        except KeyboardInterrupt:
            print("\n  ⏹ 用戶中斷")

        await manager.listener.stop()

        if received_count[0] > 0:
            print(f"\n  ✅ 總共收到 {received_count[0]} 個訊息")
        else:
            print(f"\n  ℹ️  未收到任何訊息（這是正常的，如果網路中沒有活動設備）")

        await serial.close()
        return True

    except Exception as e:
        print(f"  ❌ 失敗: {e}")
        return False


async def run_all_tests():
    """執行所有測試"""
    print("\n" + "="*70)
    print("  AsyncIO 架構 - 實體硬體測試")
    print("="*70)
    print(f"\n串口設定:")
    print(f"  - 端口: {SERIAL_PORT}")
    print(f"  - 波特率: {BAUDRATE}")
    print(f"  - 超時: {TIMEOUT}s")
    print(f"  - 記錄互動: {'是' if RECORD_INTERACTIONS else '否'}")

    input("\n▶ 請確認 RL62M Provisioner 已連接，按 Enter 開始測試...")

    results = []

    # 執行測試
    results.append(("串口連接", await test_serial_connection()))

    if results[-1][1]:  # 只有串口連接成功才繼續
        results.append(("基本命令", await test_basic_commands()))
        results.append(("列出節點", await test_list_nodes()))
        results.append(("並發命令", await test_concurrent_commands()))

        print("\n⚠️  接下來將測試訊息監聽（需要 5 秒）")
        results.append(("訊息監聽", await test_message_listener()))

    # 總結
    print("\n" + "="*70)
    print("測試結果總結")
    print("="*70)

    for name, success in results:
        status = "✅ 通過" if success else "❌ 失敗"
        print(f"  {name:20s} {status}")

    passed = sum(1 for _, s in results if s)
    total = len(results)

    print("\n" + "="*70)
    if passed == total:
        print(f"🎉 恭喜！所有測試通過 ({passed}/{total})")
        print("="*70)
        print("\n✅ AsyncIO 架構可以投入使用！")
        return 0
    else:
        print(f"⚠️  部分測試失敗 ({passed}/{total} 通過)")
        print("="*70)
        return 1


if __name__ == "__main__":
    try:
        exit_code = asyncio.run(run_all_tests())
        sys.exit(exit_code)
    except KeyboardInterrupt:
        print("\n\n⏹️  測試已中斷")
        sys.exit(1)
    except Exception as e:
        print(f"\n\n❌ 未預期的錯誤: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
