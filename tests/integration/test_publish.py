"""
測試發佈 (Publish) 設定
驗證 AT+MPAS 和 AT+MPAD 命令
"""

import asyncio
from rich.console import Console
from rich.panel import Panel
from rich.prompt import Prompt, Confirm
from ble_mesh_provisioner.core.async_serial_interface import AsyncSerialInterface
from ble_mesh_provisioner.network.async_provisioner_manager import AsyncProvisionerManager
from ble_mesh_provisioner.utils.logger import setup_logger

console = Console()
logger = setup_logger("publish_test", level=20, console=True)


async def test_set_publish(
    manager: AsyncProvisionerManager,
    node_addr: str,
    element_idx: str,
    model_id: str,
    publish_addr: str,
    app_key_idx: int
):
    """測試設置發佈地址"""
    console.print("\n" + "="*70)
    console.print("[bold cyan]測試 AT+MPAS - 設置發佈地址[/bold cyan]")
    console.print("="*70)
    console.print(f"  節點地址: {node_addr}")
    console.print(f"  元素索引: {element_idx}")
    console.print(f"  Model ID: {model_id}")
    console.print(f"  Publish 地址: {publish_addr}")
    console.print(f"  AppKey 索引: {app_key_idx}")
    console.print(
        f"  命令: AT+MPAS {node_addr} {element_idx} {model_id} {publish_addr} {app_key_idx}")

    try:
        success = await manager.set_publish(
            node_addr=node_addr,
            element_addr=element_idx,
            publish_addr=publish_addr,
            model_id=model_id
        )

        if success:
            console.print("\n✅ [green]發佈地址設置成功[/green]")
            console.print(
                f"   節點 {node_addr} 的 Model {model_id} 將發佈到 {publish_addr}")
            console.print(f"   當 Model 狀態改變時，會自動發送到此地址")
            return True
        else:
            console.print("\n❌ [red]發佈地址設置失敗[/red]")
            return False
    except Exception as e:
        console.print(f"\n❌ [red]錯誤: {e}[/red]")
        import traceback
        traceback.print_exc()
        return False


async def test_clear_publish(
    manager: AsyncProvisionerManager,
    node_addr: str,
    element_idx: str,
    model_id: str,
    app_key_idx: int
):
    """測試清除發佈地址"""
    console.print("\n" + "="*70)
    console.print("[bold cyan]測試 AT+MPAD - 清除發佈地址[/bold cyan]")
    console.print("="*70)
    console.print(f"  節點地址: {node_addr}")
    console.print(f"  元素索引: {element_idx}")
    console.print(f"  Model ID: {model_id}")
    console.print(f"  AppKey 索引: {app_key_idx}")
    console.print(
        f"  命令: AT+MPAD {node_addr} {element_idx} {model_id} {app_key_idx}")

    try:
        from ble_mesh_provisioner.core.async_at_command import async_cmd_clear_publish

        cmd = async_cmd_clear_publish(
            node_addr,
            int(element_idx) if element_idx.isdigit() else 0,
            model_id,
            app_key_idx
        )
        result = await cmd.execute(manager.serial, timeout=10.0)

        if result.get('success'):
            console.print("\n✅ [green]發佈地址清除成功[/green]")
            console.print(f"   節點 {node_addr} 的 Model {model_id} 不再自動發佈")
            return True
        else:
            console.print(
                f"\n❌ [red]發佈地址清除失敗: {result.get('error', 'Unknown error')}[/red]")
            return False
    except Exception as e:
        console.print(f"\n❌ [red]錯誤: {e}[/red]")
        import traceback
        traceback.print_exc()
        return False


async def main():
    """主程式"""
    console.print(Panel.fit(
        "[bold cyan]BLE Mesh 發佈設定測試[/bold cyan]\n"
        "測試 AT+MPAS (設置發佈) 和 AT+MPAD (清除發佈)",
        border_style="cyan"
    ))

    # 輸入參數
    port = Prompt.ask("\n請輸入 COM 埠", default="COM17")
    node_addr = Prompt.ask("請輸入節點地址", default="0x0100")
    element_idx = Prompt.ask("請輸入元素索引", default="0")
    model_id = Prompt.ask("請輸入 Model ID", default="0x4005D")

    console.print("\n[bold]發佈地址類型:[/bold]")
    console.print("  1. Group 地址 (0xC000-0xFFFF)")
    console.print("  2. Unicast 地址 (其他節點)")

    publish_type = Prompt.ask("請選擇類型", choices=["1", "2"], default="1")

    if publish_type == "1":
        publish_addr = Prompt.ask("請輸入 Group 地址", default="0xC000")
    else:
        publish_addr = Prompt.ask("請輸入目標節點地址", default="0x0101")

    app_key_idx = int(Prompt.ask("請輸入 AppKey 索引", default="0"))

    serial = AsyncSerialInterface(port, baudrate=115200)

    try:
        # 開啟串口
        console.print(f"\n[yellow]➤ 開啟串口 {port}...[/yellow]")
        await serial.open()
        console.print("  ✅ 串口已開啟")

        manager = AsyncProvisionerManager(serial)

        # 測試 1: 設置發佈
        success_set = await test_set_publish(
            manager, node_addr, element_idx, model_id, publish_addr, app_key_idx
        )

        if success_set:
            await asyncio.sleep(1)

            # 詢問是否測試清除
            if Confirm.ask("\n是否測試清除發佈?", default=True):
                await test_clear_publish(
                    manager, node_addr, element_idx, model_id, app_key_idx
                )

        # 總結
        console.print("\n" + "="*70)
        console.print("[bold green]測試完成[/bold green]")
        console.print("="*70)
        console.print(f"\n[bold]測試參數:[/bold]")
        console.print(f"  節點地址: {node_addr}")
        console.print(f"  元素索引: {element_idx}")
        console.print(f"  Model ID: {model_id}")
        console.print(f"  Publish 地址: {publish_addr}")
        console.print(f"  AppKey 索引: {app_key_idx}")

        console.print("\n[bold]重要提示:[/bold]")
        console.print("  • Model 必須先用 AT+MAKB 綁定 AppKey")
        console.print("  • Model ID 必須與綁定時使用的 ID 一致")
        console.print("  • Publish 地址可以是 Group 地址或其他節點的 Unicast 地址")
        console.print("  • 設置後，Model 狀態改變時會自動發送到 Publish 地址")
        console.print("  • Group 地址範圍: 0xC000 ~ 0xFFFF")

    except KeyboardInterrupt:
        console.print("\n[yellow]⚠️  測試被使用者中斷[/yellow]")
    except Exception as e:
        console.print(f"\n[red]❌ 錯誤: {e}[/red]")
        import traceback
        traceback.print_exc()
    finally:
        console.print("\n[yellow]➤ 關閉串口...[/yellow]")
        await serial.close()
        console.print("  ✅ 串口已關閉")


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        console.print("\n\n[yellow]⚠️  程式被中斷[/yellow]")
    except Exception as e:
        console.print(f"\n[red]❌ 錯誤: {e}[/red]")
        import traceback
        traceback.print_exc()
