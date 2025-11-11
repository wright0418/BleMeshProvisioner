"""
測試訂閱 (Subscription) 設定
驗證 AT+MSAA 和 AT+MSAD 命令
"""

import asyncio
from rich.console import Console
from rich.panel import Panel
from rich.prompt import Prompt, Confirm
from ble_mesh_provisioner.core.async_serial_interface import AsyncSerialInterface
from ble_mesh_provisioner.network.async_provisioner_manager import AsyncProvisionerManager
from ble_mesh_provisioner.utils.logger import setup_logger

console = Console()
logger = setup_logger("subscription_test", level=20, console=True)


async def test_add_subscription(
    manager: AsyncProvisionerManager,
    node_addr: str,
    element_idx: str,
    model_id: str,
    group_addr: str
):
    """測試添加訂閱"""
    console.print("\n" + "="*70)
    console.print("[bold cyan]測試 AT+MSAA - 添加訂閱地址[/bold cyan]")
    console.print("="*70)
    console.print(f"  節點地址: {node_addr}")
    console.print(f"  元素索引: {element_idx}")
    console.print(f"  Model ID: {model_id}")
    console.print(f"  Group 地址: {group_addr}")
    console.print(
        f"  命令: AT+MSAA {node_addr} {element_idx} {model_id} {group_addr}")

    try:
        success = await manager.add_subscription(
            node_addr=node_addr,
            element_addr=element_idx,
            subscription_addr=group_addr,
            model_id=model_id
        )

        if success:
            console.print("\n✅ [green]訂閱地址添加成功[/green]")
            console.print(
                f"   節點 {node_addr} 的 Model {model_id} 現在訂閱 Group {group_addr}")
            return True
        else:
            console.print("\n❌ [red]訂閱地址添加失敗[/red]")
            return False
    except Exception as e:
        console.print(f"\n❌ [red]錯誤: {e}[/red]")
        import traceback
        traceback.print_exc()
        return False


async def test_remove_subscription(
    manager: AsyncProvisionerManager,
    node_addr: str,
    element_idx: str,
    model_id: str,
    group_addr: str
):
    """測試刪除訂閱"""
    console.print("\n" + "="*70)
    console.print("[bold cyan]測試 AT+MSAD - 刪除訂閱地址[/bold cyan]")
    console.print("="*70)
    console.print(f"  節點地址: {node_addr}")
    console.print(f"  元素索引: {element_idx}")
    console.print(f"  Model ID: {model_id}")
    console.print(f"  Group 地址: {group_addr}")
    console.print(
        f"  命令: AT+MSAD {node_addr} {element_idx} {model_id} {group_addr}")

    try:
        from ble_mesh_provisioner.core.async_at_command import async_cmd_remove_subscription

        cmd = async_cmd_remove_subscription(
            node_addr,
            int(element_idx) if element_idx.isdigit() else 0,
            model_id,
            group_addr
        )
        result = await cmd.execute(manager.serial, timeout=10.0)

        if result.get('success'):
            console.print("\n✅ [green]訂閱地址刪除成功[/green]")
            console.print(
                f"   節點 {node_addr} 的 Model {model_id} 不再訂閱 Group {group_addr}")
            return True
        else:
            console.print(
                f"\n❌ [red]訂閱地址刪除失敗: {result.get('error', 'Unknown error')}[/red]")
            return False
    except Exception as e:
        console.print(f"\n❌ [red]錯誤: {e}[/red]")
        import traceback
        traceback.print_exc()
        return False


async def main():
    """主程式"""
    console.print(Panel.fit(
        "[bold cyan]BLE Mesh 訂閱設定測試[/bold cyan]\n"
        "測試 AT+MSAA (添加訂閱) 和 AT+MSAD (刪除訂閱)",
        border_style="cyan"
    ))

    # 輸入參數
    port = Prompt.ask("\n請輸入 COM 埠", default="COM17")
    node_addr = Prompt.ask("請輸入節點地址", default="0x0100")
    element_idx = Prompt.ask("請輸入元素索引", default="0")
    model_id = Prompt.ask("請輸入 Model ID", default="0x4005D")
    group_addr = Prompt.ask("請輸入 Group 地址 (0xC000-0xFFFF)", default="0xC000")

    serial = AsyncSerialInterface(port, baudrate=115200)

    try:
        # 開啟串口
        console.print(f"\n[yellow]➤ 開啟串口 {port}...[/yellow]")
        await serial.open()
        console.print("  ✅ 串口已開啟")

        manager = AsyncProvisionerManager(serial)

        # 測試 1: 添加訂閱
        success_add = await test_add_subscription(
            manager, node_addr, element_idx, model_id, group_addr
        )

        if success_add:
            await asyncio.sleep(1)

            # 詢問是否測試刪除
            if Confirm.ask("\n是否測試刪除訂閱?", default=True):
                await test_remove_subscription(
                    manager, node_addr, element_idx, model_id, group_addr
                )

        # 總結
        console.print("\n" + "="*70)
        console.print("[bold green]測試完成[/bold green]")
        console.print("="*70)
        console.print(f"\n[bold]測試參數:[/bold]")
        console.print(f"  節點地址: {node_addr}")
        console.print(f"  元素索引: {element_idx}")
        console.print(f"  Model ID: {model_id}")
        console.print(f"  Group 地址: {group_addr}")

        console.print("\n[bold]重要提示:[/bold]")
        console.print("  • Model 必須先用 AT+MAKB 綁定 AppKey")
        console.print("  • Model ID 必須與綁定時使用的 ID 一致")
        console.print("  • Group 地址範圍: 0xC000 ~ 0xFFFF")
        console.print("  • 一個 Model 可以訂閱多個 Group 地址")

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
