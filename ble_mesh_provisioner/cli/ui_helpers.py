from __future__ import annotations

from typing import List, Dict
from rich.table import Table
from rich.console import Console


console = Console()


def print_nodes(nodes: List[Dict]) -> None:
    table = Table(title="Provisioned Nodes")
    table.add_column("No", justify="right")
    table.add_column("Address")
    table.add_column("Elements", justify="right")
    table.add_column("Status")
    for n in nodes:
        status = "●ON" if n.get("online") else "○OFF"
        table.add_row(str(n.get("index")), n.get("address", ""),
                      str(n.get("elements", 0)), status)
    console.print(table)


def print_scan(devices: List[Dict[str, str]]) -> None:
    table = Table(title="Unprovisioned Devices")
    table.add_column("No", justify="right")
    table.add_column("MAC")
    table.add_column("RSSI", justify="right")
    table.add_column("UUID")
    for i, d in enumerate(devices):
        table.add_row(str(i), d.get("mac", ""), d.get(
            "rssi", ""), d.get("uuid", ""))
    console.print(table)
