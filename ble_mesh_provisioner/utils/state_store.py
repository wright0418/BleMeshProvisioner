"""
StateStore: Persist and retrieve node configuration state locally.

Used to track publish and subscription settings because the module
does not expose explicit query commands for them.
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Dict, List, Optional


class StateStore:
    """
    Simple JSON-backed state store for node configuration.

    Schema:
    {
        "nodes": {
            "0x0100": {
                "publish": {
                    "element_idx": 0,
                    "model_id": "0x1000ffff",
                    "publish_addr": "0xC000",
                    "app_key_idx": 0
                },
                "subscriptions": [
                    {
                        "element_idx": 0,
                        "model_id": "0x1000ffff",
                        "group_addr": "0xC000"
                    }
                ]
            }
        }
    }
    """

    def __init__(self, path: Optional[str] = None) -> None:
        self.path = Path(path) if path else Path(".mesh_state.json")
        self.data: Dict = {"nodes": {}}
        self._loaded = False

    def load(self) -> None:
        if self._loaded:
            return
        if self.path.exists():
            try:
                self.data = json.loads(self.path.read_text(encoding="utf-8"))
            except Exception:
                # Corrupted file; start fresh
                self.data = {"nodes": {}}
        else:
            self.data = {"nodes": {}}
        self._loaded = True

    def save(self) -> None:
        self.path.write_text(json.dumps(
            self.data, ensure_ascii=False, indent=2), encoding="utf-8")

    # Publish state
    def set_publish(
        self,
        addr: str,
        element_idx: int,
        model_id: str,
        publish_addr: str,
        app_key_idx: int = 0,
    ) -> None:
        self.load()
        node = self.data["nodes"].setdefault(addr, {"subscriptions": []})
        node["publish"] = {
            "element_idx": element_idx,
            "model_id": model_id,
            "publish_addr": publish_addr,
            "app_key_idx": app_key_idx,
        }
        self.save()

    def clear_publish(self, addr: str) -> None:
        self.load()
        node = self.data["nodes"].setdefault(addr, {"subscriptions": []})
        node.pop("publish", None)
        self.save()

    # Subscriptions
    def add_subscription(
        self,
        addr: str,
        element_idx: int,
        model_id: str,
        group_addr: str,
    ) -> None:
        self.load()
        node = self.data["nodes"].setdefault(addr, {"subscriptions": []})
        subs: List[Dict] = node.setdefault("subscriptions", [])
        rec = {
            "element_idx": element_idx,
            "model_id": model_id,
            "group_addr": group_addr,
        }
        # Avoid duplicates
        if rec not in subs:
            subs.append(rec)
        self.save()

    def remove_subscription(
        self,
        addr: str,
        element_idx: int,
        model_id: str,
        group_addr: str,
    ) -> None:
        self.load()
        node = self.data["nodes"].setdefault(addr, {"subscriptions": []})
        subs: List[Dict] = node.setdefault("subscriptions", [])
        subs = [s for s in subs if not (
            s.get("element_idx") == element_idx and
            s.get("model_id") == model_id and
            s.get("group_addr") == group_addr
        )]
        node["subscriptions"] = subs
        self.save()

    # Read
    def get_node(self, addr: str) -> Dict:
        self.load()
        return self.data["nodes"].get(addr, {"subscriptions": []})

    def clear_node(self, addr: str) -> None:
        self.load()
        self.data["nodes"].pop(addr, None)
        self.save()
