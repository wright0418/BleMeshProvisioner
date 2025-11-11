from __future__ import annotations
from ble_mesh_provisioner.utils.logger import setup_logger
from ble_mesh_provisioner.cli.ui_helpers import print_nodes, print_scan
from ble_mesh_provisioner.network.message_listener import MessageListener
from ble_mesh_provisioner.network.provisioner_manager import ProvisionerManager
from ble_mesh_provisioner.core.serial_interface import SerialInterface
from rich.console import Console
from typing import Optional
import typer
import time
logger = setup_logger(
    "ble_mesh_provisioner",
    level=20,
    log_file="logs/provisioner.log",
    console=True
)


# Optional mock for testing
try:
    from tests.mocks.mock_serial import MockSerialInterface  # type: ignore
except Exception:  # pragma: no cover
    MockSerialInterface = None  # type: ignore


app = typer.Typer(help="RL62M BLE Mesh Provisioner CLI")
console = Console()


def get_serial(port: str, mock: bool = False):
    if mock and MockSerialInterface is not None:
        return MockSerialInterface()
    return SerialInterface(port)


@app.command()
def info(port: str = typer.Option(..., "--port", "-p", help="Serial port"), mock: bool = False):
    """查詢韌體版本與模組角色"""
    serial = get_serial(port, mock)
    with serial:
        mgr = ProvisionerManager(serial)
        version = mgr.get_version()
        role = mgr.get_role()
        console.print(f"Firmware Version: [bold]{version}[/]")
        console.print(f"Module Role:     [bold]{role}[/]")
        console.print(f"Provisioner OK:  [bold]{mgr.verify_provisioner()}[/]")


@app.command()
def scan(
    port: str = typer.Option(..., "--port", "-p"),
    duration: int = typer.Option(3, "--duration", "-d"),
    mock: bool = False,
):
    """掃描未綁定設備 (3 秒後自動停止)"""
    serial = get_serial(port, mock)
    with serial:
        mgr = ProvisionerManager(serial)
        devices = mgr.start_scan(duration=duration)
        print_scan(devices)
        console.print(f"Found {len(devices)} unprovisioned devices")


@app.command()
def provision(
    port: str = typer.Option(..., "--port", "-p"),
    uuid: Optional[str] = typer.Option(None, "--uuid"),
    index: Optional[int] = typer.Option(None, "--index", "-i"),
    mock: bool = False,
):
    """綁定設備: 指定 UUID 或使用掃描列表編號"""
    serial = get_serial(port, mock)
    with serial:
        mgr = ProvisionerManager(serial)
        target_uuid: Optional[str] = uuid

        if not target_uuid and index is not None:
            devices = mgr.start_scan(duration=3)
            if 0 <= index < len(devices):
                target_uuid = devices[index]["uuid"]
        if not target_uuid:
            raise typer.Exit(code=2)
        result = mgr.provision_device(target_uuid)
        console.print(f"Provisioned address: [bold]{result['address']}[/]")


@app.command("list")
def list_nodes(
    port: str = typer.Option(..., "--port", "-p"),
    mock: bool = False,
):
    """列出已綁定設備"""
    serial = get_serial(port, mock)
    with serial:
        mgr = ProvisionerManager(serial)
        nodes = mgr.list_nodes()
        print_nodes(nodes)


@app.command()
def unprovision(
    port: str = typer.Option(..., "--port", "-p"),
    index: int = typer.Option(..., "--index", "-i"),
    mock: bool = False,
):
    """解除綁定設備 (依列表編號)"""
    serial = get_serial(port, mock)
    with serial:
        mgr = ProvisionerManager(serial)
        ok = mgr.unprovision_by_index(index)
        console.print(f"Removed: [bold]{ok}[/]")


pub_app = typer.Typer(help="Publish settings")


@pub_app.command("set")
def publish_set(
    port: str = typer.Option(..., "--port", "-p"),
    address: str = typer.Option(..., "--address", "-a"),
    element: int = typer.Option(0, "--element", "-e"),
    model: str = typer.Option("0x1000ffff", "--model", "-m"),
    publish_addr: str = typer.Option(..., "--publish-addr"),
    app_key_idx: int = typer.Option(0, "--app-key-idx"),
    mock: bool = False,
):
    serial = get_serial(port, mock)
    with serial:
        mgr = ProvisionerManager(serial)
        ok = mgr.set_publish(address, element, model,
                             publish_addr, app_key_idx)
        console.print(f"Publish set: [bold]{ok}[/]")


@pub_app.command("clear")
def publish_clear(
    port: str = typer.Option(..., "--port", "-p"),
    address: str = typer.Option(..., "--address", "-a"),
    element: int = typer.Option(0, "--element", "-e"),
    model: str = typer.Option("0x1000ffff", "--model", "-m"),
    app_key_idx: int = typer.Option(0, "--app-key-idx"),
    mock: bool = False,
):
    serial = get_serial(port, mock)
    with serial:
        mgr = ProvisionerManager(serial)
        ok = mgr.clear_publish(address, element, model, app_key_idx)
        console.print(f"Publish cleared: [bold]{ok}[/]")


app.add_typer(pub_app, name="publish")


sub_app = typer.Typer(help="Subscription settings")


@sub_app.command("add")
def subscribe_add(
    port: str = typer.Option(..., "--port", "-p"),
    address: str = typer.Option(..., "--address", "-a"),
    element: int = typer.Option(0, "--element", "-e"),
    model: str = typer.Option("0x1000ffff", "--model", "-m"),
    group_addr: str = typer.Option(..., "--group-addr"),
    mock: bool = False,
):
    serial = get_serial(port, mock)
    with serial:
        mgr = ProvisionerManager(serial)
        ok = mgr.add_subscription(address, element, model, group_addr)
        console.print(f"Subscription added: [bold]{ok}[/]")


@sub_app.command("remove")
def subscribe_remove(
    port: str = typer.Option(..., "--port", "-p"),
    address: str = typer.Option(..., "--address", "-a"),
    element: int = typer.Option(0, "--element", "-e"),
    model: str = typer.Option("0x1000ffff", "--model", "-m"),
    group_addr: str = typer.Option(..., "--group-addr"),
    mock: bool = False,
):
    serial = get_serial(port, mock)
    with serial:
        mgr = ProvisionerManager(serial)
        ok = mgr.remove_subscription(address, element, model, group_addr)
        console.print(f"Subscription removed: [bold]{ok}[/]")


app.add_typer(sub_app, name="subscribe")


@app.command()
def config(
    port: str = typer.Option(..., "--port", "-p"),
    address: str = typer.Option(..., "--address", "-a"),
    mock: bool = False,
):
    """查詢裝置的推播與訂閱設定 (本地記錄)"""
    serial = get_serial(port, mock)
    with serial:
        mgr = ProvisionerManager(serial)
        cfg = mgr.get_node_config(address)
        console.print(cfg)


@app.command()
def monitor(
    port: str = typer.Option(..., "--port", "-p"),
    mock: bool = False,
):
    """持續監聽網路訊息，按 Ctrl+C 停止"""
    serial = get_serial(port, mock)
    with serial:
        listener = MessageListener(serial)

        def show(line: str) -> None:
            console.print(f"[bold green]{line}[/]")

        listener.add_callback(show)
        listener.start()
        console.print("Monitoring... Press Ctrl+C to stop")
        try:
            while True:
                time.sleep(0.2)
        except KeyboardInterrupt:
            listener.stop()


if __name__ == "__main__":
    app()
