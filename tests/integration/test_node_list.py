"""
測試 AT+NL 命令 - 列出已配置的節點
"""

import asyncio
from rich.console import Console
from rich.table import Table
from ble_mesh_provisioner.core.async_serial_interface import AsyncSerialInterface
from ble_mesh_provisioner.network.async_provisioner_manager import AsyncProvisionerManager
from ble_mesh_provisioner.utils.logger import setup_logger

console = Console()
logger = setup_logger("nl_test", level=20, console=True)


async def test_list_nodes(port: str = "COM17"):
    """測試列出已配置的節點"""

    console.print("\n" + "="*70)
    console.print("[bold cyan]測試 AT+NL - 列出已配置節點[/bold cyan]")
    console.print("="*70)

    serial = AsyncSerialInterface(port, baudrate=115200)

    try:
        # 開啟串口
        await serial.open()
        console.print(f"✅ 串口 {port} 已開啟\n")

        manager = AsyncProvisionerManager(serial)

        # 執行 AT+NL
        console.print("[yellow]執行 AT+NL 命令...[/yellow]")
        nodes = await manager.list_nodes()

        if nodes:
            console.print(f"\n✅ [green]找到 {len(nodes)} 個已配置的節點[/green]\n")

            # 建立表格顯示節點資訊
            table = Table(show_header=True, header_style="bold magenta")
            table.add_column("索引", style="cyan", width=8)
            table.add_column("地址", style="yellow", width=10)
            table.add_column("元素數", style="green", width=10)
            table.add_column("狀態", style="blue", width=10)

            for node in nodes:
                status = "🟢 在線" if node.get('online', 0) == 1 else "🔴 離線"
                table.add_row(
                    str(node.get('index', 'N/A')),
                    node.get('address', 'N/A'),
                    str(node.get('element_num', 'N/A')),
                    status
                )

            console.print(table)

            # 顯示詳細資訊
            console.print("\n[bold]節點詳細資訊:[/bold]")
            for node in nodes:
                console.print(f"\n  節點 #{node.get('index')}:")
                console.print(f"    地址: {node.get('address')}")
                console.print(f"    元素數: {node.get('element_num')}")
                console.print(
                    f"    在線狀態: {'在線' if node.get('online') == 1 else '離線'}")
        else:
            console.print("\n⚠️  [yellow]沒有找到已配置的節點[/yellow]")
            console.print("   提示: 請先執行 Provisioning 流程綁定設備")

        console.print("\n" + "="*70)
        console.print("[bold green]測試完成[/bold green]")
        console.print("="*70)

    except Exception as e:
        console.print(f"\n❌ [red]錯誤: {e}[/red]")
        import traceback
        traceback.print_exc()

    finally:
        await serial.close()
        console.print("\n✅ 串口已關閉")


async def main():
    """主程式"""
    from rich.prompt import Prompt

    console.print("\n[bold cyan]AT+NL 測試程式[/bold cyan]")
    console.print("用於查詢已配置的 BLE Mesh 節點\n")

    # 輸入 COM 埠
    port = Prompt.ask("請輸入 COM 埠", default="COM17")

    await test_list_nodes(port)


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        console.print("\n\n[yellow]⚠️  程式被中斷[/yellow]")
    except Exception as e:
        console.print(f"\n[red]❌ 錯誤: {e}[/red]")
        import traceback
        traceback.print_exc()
