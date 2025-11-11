"""
完整的 Provisioning (配網綁定) 流程測試

正確的綁定流程:
1. AT+DIS 1 - 開始掃描設備
2. 找到設備 UUID
3. AT+DIS 0 - 停止掃描
4. AT+PBADVCON <UUID> - 開啟 PB-ADV 通道
5. AT+PROV - 執行 Provisioning
6. AT+AKA <dst> <app_key_index> <net_key_index> - 添加 AppKey
7. AT+MAKB <dst> <element_index> <model_id> <app_key_index> - 綁定 Model (model_id: 0x4005D)
8. AT+MSAA - 設置訂閱地址 (可選)
9. AT+MPAS - 設置發佈地址 (可選)
10. AT+NL - 驗證配置
"""

import asyncio
from rich.console import Console
from rich.table import Table
from rich.panel import Panel
from rich.progress import Progress, SpinnerColumn, TextColumn
from ble_mesh_provisioner.core.async_serial_interface import AsyncSerialInterface
from ble_mesh_provisioner.network.async_provisioner_manager import AsyncProvisionerManager
from ble_mesh_provisioner.utils.logger import setup_logger

console = Console()
logger = setup_logger("provisioning_test", level=20, console=True)


async def test_step_1_scan(manager: AsyncProvisionerManager, duration: int = 5):
    """步驟 1: 掃描未配置的設備 (包含開始和停止)"""
    console.print("\n" + "="*70)
    console.print("[bold cyan]步驟 1: 掃描未配置的設備[/bold cyan]")
    console.print("="*70)
    console.print("  [1] AT+DIS 1 - 開始掃描")

    devices = []

    def on_device(data):
        console.print(f"  📡 發現設備: UUID={data['uuid'][:32]}...")
        console.print(f"     MAC={data['mac']}, RSSI={data['rssi']}")
        devices.append(data)

    with Progress(
        SpinnerColumn(),
        TextColumn("[progress.description]{task.description}"),
        console=console
    ) as progress:
        task = progress.add_task(f"掃描中 ({duration} 秒)...", total=None)
        result = await manager.scan_devices(duration=duration, on_device_found=on_device)

    console.print("  [2] AT+DIS 0 - 停止掃描")

    if result:
        console.print(
            f"\n✅ [green]步驟 1 完成: 找到 {len(result)} 個設備，掃描已停止[/green]")

        table = Table(show_header=True, header_style="bold magenta")
        table.add_column("序號", style="cyan", width=6)
        table.add_column("UUID", style="yellow")
        table.add_column("MAC", style="green")
        table.add_column("RSSI", style="blue", width=8)

        for i, dev in enumerate(result, 1):
            table.add_row(
                str(i),
                dev['uuid'][:32] + "...",
                dev['mac'],
                str(dev['rssi'])
            )

        console.print(table)
        return result
    else:
        console.print("❌ [red]步驟 1 失敗: 沒有找到設備[/red]")
        return []


async def test_step_2_pbadvcon(manager: AsyncProvisionerManager, device_uuid: str):
    """步驟 2: 開啟 PB-ADV 通道"""
    console.print("\n" + "="*70)
    console.print("[bold cyan]步驟 2: 開啟 PB-ADV 通道 (AT+PBADVCON)[/bold cyan]")
    console.print("="*70)
    console.print(f"  目標設備 UUID: {device_uuid}")
    console.print(f"  命令: AT+PBADVCON {device_uuid}")

    try:
        from ble_mesh_provisioner.core.async_at_command import async_cmd_open_pbadv
        cmd = async_cmd_open_pbadv(device_uuid)
        result = await cmd.execute(manager.serial, timeout=10.0)

        if result.get('success'):
            console.print("✅ [green]步驟 2 完成: PB-ADV 通道已開啟[/green]")
            return True
        else:
            console.print(
                f"❌ [red]步驟 2 失敗: {result.get('error', 'Unknown error')}[/red]")
            return False
    except Exception as e:
        console.print(f"❌ [red]步驟 2 錯誤: {e}[/red]")
        import traceback
        traceback.print_exc()
        return False


async def test_step_3_prov(manager: AsyncProvisionerManager):
    """步驟 3: 執行 Provisioning，回傳實際分配的地址"""
    console.print("\n" + "="*70)
    console.print("[bold cyan]步驟 3: 執行 Provisioning (AT+PROV)[/bold cyan]")
    console.print("="*70)
    console.print(f"  命令: AT+PROV")
    console.print(f"  ⚠️  實際地址將由 Provisioner 自動分配")

    try:
        from ble_mesh_provisioner.core.async_at_command import async_cmd_provision
        # AT+PROV 不需要預先指定地址，Provisioner 會自動分配
        cmd = async_cmd_provision("0x0100", 0)
        result = await cmd.execute(manager.serial, timeout=15.0)

        if result.get('success'):
            # 從回應中取得實際分配的地址
            # PROV-MSG SUCCESS <unicast_address>
            allocated_addr = result.get('params', [])[
                0] if result.get('params') else None

            if allocated_addr:
                console.print(f"✅ [green]步驟 3 完成: Provisioning 成功[/green]")
                console.print(
                    f"   📍 Provisioner 分配的地址: [cyan]{allocated_addr}[/cyan]")
                return allocated_addr
            else:
                console.print(f"⚠️  [yellow]步驟 3 完成但未取得地址，使用預設值[/yellow]")
                return "0x0100"
        else:
            console.print(
                f"❌ [red]步驟 3 失敗: {result.get('error', 'Unknown error')}[/red]")
            return None
    except Exception as e:
        console.print(f"❌ [red]步驟 3 錯誤: {e}[/red]")
        import traceback
        traceback.print_exc()
        return None


async def test_step_4_aka(manager: AsyncProvisionerManager, unicast_addr: str, app_key_index: int = 0, net_key_index: int = 0):
    """步驟 4: 添加 AppKey"""
    console.print("\n" + "="*70)
    console.print("[bold cyan]步驟 4: 添加 AppKey (AT+AKA)[/bold cyan]")
    console.print("="*70)
    console.print(f"  目標節點: {unicast_addr}")
    console.print(f"  AppKey Index: {app_key_index}")
    console.print(f"  NetKey Index: {net_key_index}")
    console.print(
        f"  命令: AT+AKA {unicast_addr} {app_key_index} {net_key_index}")

    try:
        from ble_mesh_provisioner.core.async_at_command import async_cmd_add_appkey
        cmd = async_cmd_add_appkey(unicast_addr, app_key_index, net_key_index)
        result = await cmd.execute(manager.serial, timeout=10.0)

        if result.get('success'):
            console.print("✅ [green]步驟 4 完成: AppKey 已添加[/green]")
            return True
        else:
            console.print(
                f"❌ [red]步驟 4 失敗: {result.get('error', 'Unknown error')}[/red]")
            return False
    except Exception as e:
        console.print(f"❌ [red]步驟 4 錯誤: {e}[/red]")
        import traceback
        traceback.print_exc()
        return False


async def test_step_5_makb(manager: AsyncProvisionerManager, unicast_addr: str, model_id: str = "0x4005D", element_index: str = "0", app_key_index: str = "0"):
    """步驟 5: 綁定 Model AppKey"""
    console.print("\n" + "="*70)
    console.print("[bold cyan]步驟 5: 綁定 Model AppKey (AT+MAKB)[/bold cyan]")
    console.print("="*70)
    console.print(f"  目標節點: {unicast_addr}")
    console.print(f"  Element Index: {element_index}")
    console.print(f"  Model ID: {model_id}")
    console.print(f"  AppKey Index: {app_key_index}")
    console.print(
        f"  命令: AT+MAKB {unicast_addr} {element_index} {model_id} {app_key_index}")

    try:
        from ble_mesh_provisioner.core.async_at_command import async_cmd_bind_model
        cmd = async_cmd_bind_model(
            unicast_addr, element_index, model_id, app_key_index)
        result = await cmd.execute(manager.serial, timeout=10.0)

        if result.get('success'):
            console.print("✅ [green]步驟 5 完成: Model AppKey 已綁定[/green]")
            return True
        else:
            console.print(
                f"❌ [red]步驟 5 失敗: {result.get('error', 'Unknown error')}[/red]")
            return False
    except Exception as e:
        console.print(f"❌ [red]步驟 5 錯誤: {e}[/red]")
        import traceback
        traceback.print_exc()
        return False


async def test_step_6_set_subscription(manager: AsyncProvisionerManager, unicast_addr: str, group_addr: str = "0xC000", model_id: str = "0x1000"):
    """步驟 6: 設置訂閱地址"""
    console.print("\n" + "="*70)
    console.print("[bold cyan]步驟 6: 設置訂閱地址 (AT+MSAA)[/bold cyan]")
    console.print("="*70)
    console.print(f"  節點地址: {unicast_addr}")
    console.print(f"  元素索引: 0")
    console.print(f"  Model ID: {model_id}")
    console.print(f"  Group Address: {group_addr}")
    console.print(f"  命令: AT+MSAA {unicast_addr} 0 {model_id} {group_addr}")

    try:
        success = await manager.add_subscription(
            node_addr=unicast_addr,
            element_addr="0",  # Element index
            subscription_addr=group_addr,
            model_id=model_id
        )

        if success:
            console.print("✅ [green]步驟 6 完成: 訂閱地址已設置[/green]")
            return True
        else:
            console.print(f"❌ [red]步驟 6 失敗[/red]")
            return False
    except Exception as e:
        console.print(f"❌ [red]步驟 6 錯誤: {e}[/red]")
        return False


async def test_step_7_set_publish(manager: AsyncProvisionerManager, unicast_addr: str, publish_addr: str = "0xC000", model_id: str = "0x1000"):
    """步驟 7: 設置發佈地址"""
    console.print("\n" + "="*70)
    console.print("[bold cyan]步驟 7: 設置發佈地址 (AT+MPAS)[/bold cyan]")
    console.print("="*70)
    console.print(f"  節點地址: {unicast_addr}")
    console.print(f"  元素索引: 0")
    console.print(f"  Model ID: {model_id}")
    console.print(f"  Publish Address: {publish_addr}")
    console.print(f"  AppKey Index: 0")
    console.print(
        f"  命令: AT+MPAS {unicast_addr} 0 {model_id} {publish_addr} 0")

    try:
        success = await manager.set_publish(
            node_addr=unicast_addr,
            element_addr="0",  # Element index
            publish_addr=publish_addr,
            model_id=model_id
        )

        if success:
            console.print("✅ [green]步驟 7 完成: 發佈地址已設置[/green]")
            return True
        else:
            console.print(f"❌ [red]步驟 7 失敗[/red]")
            return False
    except Exception as e:
        console.print(f"❌ [red]步驟 7 錯誤: {e}[/red]")
        return False


async def test_step_8_verify(manager: AsyncProvisionerManager):
    """步驟 8: 驗證配置結果"""
    console.print("\n" + "="*70)
    console.print("[bold cyan]步驟 8: 驗證配置結果 (AT+NL)[/bold cyan]")
    console.print("="*70)

    try:
        nodes = await manager.list_nodes()

        if nodes:
            console.print(f"✅ [green]步驟 8 完成: 共有 {len(nodes)} 個已配置節點[/green]")

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
            return nodes
        else:
            console.print("⚠️  [yellow]步驟 8: 沒有找到已配置的節點[/yellow]")
            return []
    except Exception as e:
        console.print(f"❌ [red]步驟 8 錯誤: {e}[/red]")
        return []


async def run_complete_provisioning_flow(port: str = "COM17"):
    """執行完整的 Provisioning 流程"""

    console.print(Panel.fit(
        "[bold cyan]BLE Mesh Provisioning 完整流程測試[/bold cyan]\n"
        "測試從掃描到配置的所有步驟",
        border_style="cyan"
    ))

    serial = AsyncSerialInterface(port, baudrate=115200)

    try:
        # 開啟串口
        console.print(f"\n[yellow]➤ 開啟串口 {port}...[/yellow]")
        await serial.open()
        console.print("  ✅ 串口已開啟")

        manager = AsyncProvisionerManager(serial)

        # 步驟 1: 掃描設備
        devices = await test_step_1_scan(manager, duration=5)
        if not devices:
            console.print("\n[red]❌ 測試終止: 沒有找到可配置的設備[/red]")
            return

        # 選擇第一個設備進行配置
        target_device = devices[0]
        device_uuid = target_device['uuid']

        console.print(f"\n[yellow]➤ 選擇設備進行配置:[/yellow]")
        console.print(f"   UUID: {device_uuid}")
        console.print(f"   MAC: {target_device['mac']}")
        console.print(f"   RSSI: {target_device['rssi']}")

        # 等待用戶確認
        await asyncio.sleep(1)

        # 步驟 2: 開啟 PB-ADV 通道
        if not await test_step_2_pbadvcon(manager, device_uuid):
            console.print("\n[red]❌ 測試終止: PB-ADV 通道開啟失敗[/red]")
            return
        await asyncio.sleep(1)

        # 步驟 3: 執行 Provisioning (取得實際分配的地址)
        unicast_addr = await test_step_3_prov(manager)
        if not unicast_addr:
            console.print("\n[red]❌ 測試終止: Provisioning 失敗[/red]")
            return
        await asyncio.sleep(2)  # Provisioning 後需要較長延遲

        # 步驟 4: 添加 AppKey (使用 PROV 回傳的地址)
        if not await test_step_4_aka(manager, unicast_addr, 0, 0):
            console.print("\n[red]❌ 測試終止: AppKey 添加失敗[/red]")
            return
        await asyncio.sleep(1)

        # 步驟 5: 綁定 Model AppKey (使用 PROV 回傳的地址)
        model_id = "0x4005D"  # 實際設備的 Model ID
        if not await test_step_5_makb(manager, unicast_addr, model_id, "0", "0"):
            console.print("\n[red]❌ 警告: Model 綁定失敗，繼續後續步驟...[/red]")
        await asyncio.sleep(1)

        # 步驟 6: 設置訂閱地址 (使用 PROV 回傳的地址和相同的 Model ID)
        group_addr = "0xC000"
        if not await test_step_6_set_subscription(manager, unicast_addr, group_addr, model_id):
            console.print("\n[red]❌ 警告: 訂閱地址設置失敗,繼續後續步驟...[/red]")

        await asyncio.sleep(1)

        # 步驟 7: 設置發佈地址 (必須使用相同的 Model ID)
        if not await test_step_7_set_publish(manager, unicast_addr, group_addr, model_id):
            console.print("\n[red]❌ 警告: 發佈地址設置失敗,繼續後續步驟...[/red]")

        await asyncio.sleep(1)

        # 步驟 8: 驗證配置
        nodes = await test_step_8_verify(manager)

        # 總結
        console.print("\n" + "="*70)
        console.print("[bold green]🎉 Provisioning 流程測試完成![/bold green]")
        console.print("="*70)
        console.print(f"  已配置設備地址: {unicast_addr}")
        console.print(f"  Model ID: {model_id}")
        console.print(f"  Group 地址: {group_addr}")
        console.print(f"  已配置節點數: {len(nodes)}")
        console.print("\n  完整流程:")
        console.print("  1. ✅ AT+DIS 1 (開始掃描)")
        console.print("  2. ✅ AT+DIS 0 (停止掃描)")
        console.print("  3. ✅ AT+PBADVCON <UUID>")
        console.print("  4. ✅ AT+PROV")
        console.print("  5. ✅ AT+AKA (AppKey)")
        console.print(f"  6. ✅ AT+MAKB (Model {model_id})")
        console.print(f"  7. ⚠️  AT+MSAA (訂閱 Model {model_id})")
        console.print(f"  8. ⚠️  AT+MPAS (發佈 Model {model_id})")
        console.print("  9. ✅ AT+NL (驗證)")

    except KeyboardInterrupt:
        console.print("\n[yellow]⚠️  測試被使用者中斷[/yellow]")
    except Exception as e:
        console.print(f"\n[red]❌ 測試錯誤: {e}[/red]")
        import traceback
        traceback.print_exc()
    finally:
        console.print("\n[yellow]➤ 關閉串口...[/yellow]")
        await serial.close()
        console.print("  ✅ 串口已關閉")


async def run_individual_step_tests(port: str = "COM17"):
    """執行個別步驟測試"""

    console.print(Panel.fit(
        "[bold cyan]BLE Mesh Provisioning 個別步驟測試[/bold cyan]\n"
        "測試每個步驟的獨立功能",
        border_style="cyan"
    ))

    serial = AsyncSerialInterface(port, baudrate=115200)

    try:
        await serial.open()
        console.print(f"✅ 串口 {port} 已開啟\n")

        manager = AsyncProvisionerManager(serial)

        # 測試步驟 1: 掃描
        await test_step_1_scan(manager, duration=3)
        await asyncio.sleep(2)

        # 測試步驟 8: 列出已配置節點
        await test_step_8_verify(manager)

        console.print("\n[bold green]✅ 個別步驟測試完成[/bold green]")

    except Exception as e:
        console.print(f"\n[red]❌ 測試錯誤: {e}[/red]")
        import traceback
        traceback.print_exc()
    finally:
        await serial.close()


async def main():
    """主程式"""
    console.print("\n")
    console.print("[bold]選擇測試模式:[/bold]")
    console.print("  [1] 完整 Provisioning 流程測試")
    console.print("  [2] 個別步驟測試")
    console.print("  [q] 退出")

    from rich.prompt import Prompt
    choice = Prompt.ask("\n請選擇", choices=["1", "2", "q"], default="1")

    if choice == "q":
        console.print("👋 再見!")
        return

    # 輸入 COM 埠
    port = Prompt.ask("請輸入 COM 埠", default="COM17")

    if choice == "1":
        await run_complete_provisioning_flow(port)
    elif choice == "2":
        await run_individual_step_tests(port)


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        console.print("\n\n[yellow]⚠️  程式被中斷[/yellow]")
    except Exception as e:
        console.print(f"\n[red]❌ 錯誤: {e}[/red]")
        import traceback
        traceback.print_exc()
