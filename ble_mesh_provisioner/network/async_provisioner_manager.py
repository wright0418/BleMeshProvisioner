"""
AsyncIO ProvisionerManager: High-level async manager for provisioning and node management.

實現功能：
1. 獲取韌體版本與角色
2. 掃描未配置設備
3. 配置設備 (Provision)
4. 列出已配置節點
5. 移除節點
6. Publish/Subscribe 管理
7. 查詢本地配置狀態
"""

import asyncio
from typing import Any, Dict, List, Optional, Callable

from ble_mesh_provisioner.core.async_serial_interface import AsyncSerialInterface
from ble_mesh_provisioner.core.async_at_command import (
    async_cmd_get_version,
    async_cmd_get_role,
    async_cmd_start_scan,
    async_cmd_stop_scan,
    async_cmd_open_pbadv,
    async_cmd_provision,
    async_cmd_add_appkey,
    async_cmd_bind_model,
    async_cmd_list_nodes,
    async_cmd_remove_node,
    async_cmd_set_publish,
    async_cmd_clear_publish,
    async_cmd_add_subscription,
    async_cmd_remove_subscription,
    async_cmd_mesh_clear,
)
from ble_mesh_provisioner.network.async_message_listener import AsyncMessageListener
from ble_mesh_provisioner.core.response_parser import ResponseParser
from ble_mesh_provisioner.utils.logger import setup_logger
from ble_mesh_provisioner.utils.state_store import StateStore

logger = setup_logger(
    "ble_mesh_provisioner",
    level=20,
    log_file="logs/provisioner.log",
    console=True
)


class AsyncProvisionerManager:
    """
    AsyncIO-based Provisioner manager for high-level operations.

    提供基於 asyncio 的高階管理功能，完全非阻塞。
    """

    def __init__(
        self,
        serial: AsyncSerialInterface,
        state_file: Optional[str] = None
    ) -> None:
        """
        Initialize async provisioner manager.

        Args:
            serial: AsyncSerialInterface instance
            state_file: Optional state file path for persistence
        """
        self.serial = serial
        self.listener = AsyncMessageListener(serial)
        self.store = StateStore(state_file)

        # 掃描結果暫存
        self._scan_results: List[Dict[str, Any]] = []
        self._scan_lock = asyncio.Lock()

    # ========================================================================
    # 1. Version and Role
    # ========================================================================

    async def get_version(self) -> str:
        """
        Get firmware version (async).

        Returns:
            Version string

        Raises:
            RuntimeError: If command fails

        Example:
            >>> version = await manager.get_version()
            >>> print(f"Firmware: {version}")
        """
        result = await async_cmd_get_version().execute_with_retry(self.serial)

        if not result['success']:
            raise RuntimeError(f"Failed to get version: {result.get('error')}")

        params = result.get('params', [])
        return params[0] if params else "Unknown"

    async def get_role(self) -> str:
        """
        Get device role (async).

        Returns:
            Role string ('0' = Device, '1' = Provisioner)

        Raises:
            RuntimeError: If command fails
        """
        result = await async_cmd_get_role().execute_with_retry(self.serial)

        if not result['success']:
            raise RuntimeError(f"Failed to get role: {result.get('error')}")

        params = result.get('params', [])
        return params[0] if params else "Unknown"

    async def verify_provisioner(self) -> bool:
        """
        Verify this device is a provisioner.

        Returns:
            True if device is provisioner
        """
        try:
            role = await self.get_role()
            # 支援多種格式：'1', 'PROVISIONER', 'Provisioner'
            is_provisioner = role in ('1', 'PROVISIONER', 'Provisioner')

            if is_provisioner:
                logger.info("Device verified as Provisioner")
            else:
                logger.warning(f"Device role is {role}, not Provisioner")

            return is_provisioner
        except Exception as e:
            logger.error(f"Failed to verify provisioner: {e}")
            return False

    # ========================================================================
    # 2. Device Scanning
    # ========================================================================

    async def scan_devices(
        self,
        duration: int = 10,
        on_device_found: Optional[Callable[[Dict[str, Any]], None]] = None
    ) -> List[Dict[str, Any]]:
        """
        Scan for unprovisioned devices (async).

        Args:
            duration: Scan duration in seconds
            on_device_found: Optional callback for each found device

        Returns:
            List of found devices with UUID, RSSI, etc.

        Example:
            >>> devices = await manager.scan_devices(duration=10)
            >>> for dev in devices:
            ...     print(f"UUID: {dev['uuid']}, RSSI: {dev['rssi']}")
        """
        # 清空之前的掃描結果
        async with self._scan_lock:
            self._scan_results = []

        # 設置 DIS-MSG 處理器 (掃描結果)
        async def scan_handler(msg: Dict[str, Any]) -> None:
            """Handle scan result messages."""
            params = msg.get('params', [])
            if len(params) >= 3:
                device = {
                    'mac': params[0],
                    'rssi': params[1],
                    'uuid': params[2],
                    'raw': msg.get('raw', '')
                }

                async with self._scan_lock:
                    # 避免重複
                    if not any(d['uuid'] == device['uuid'] for d in self._scan_results):
                        self._scan_results.append(device)
                        logger.info(
                            f"Found device: UUID={device['uuid']}, RSSI={device['rssi']}")

                        # 呼叫用戶回調
                        if on_device_found:
                            if asyncio.iscoroutinefunction(on_device_found):
                                await on_device_found(device)
                            else:
                                on_device_found(device)

        # 註冊處理器 (DIS 而非 SCAN)
        self.listener.add_handler('DIS', scan_handler)

        try:
            # 啟動 listener
            if not self.listener._running:
                await self.listener.start()

            # 開始掃描
            logger.info(f"Starting device scan for {duration} seconds...")
            result = await async_cmd_start_scan(duration).execute(self.serial)

            # 檢查是否成功開始掃描 (注意: DIS 命令可能不回傳 SUCCESS，只有 DIS-MSG)
            # 所以我們不檢查 success，直接等待掃描完成

            # 等待掃描完成
            await asyncio.sleep(duration)

            # 停止掃描
            logger.debug("Stopping device scan...")
            await async_cmd_stop_scan().execute(self.serial)

            # 額外等待一點時間以接收最後的訊息
            await asyncio.sleep(0.5)

            # 返回結果
            async with self._scan_lock:
                devices = self._scan_results.copy()

            logger.info(f"Scan complete. Found {len(devices)} devices")
            return devices

        finally:
            # 確保掃描已停止
            try:
                await async_cmd_stop_scan().execute(self.serial)
            except Exception as e:
                logger.debug(f"Error stopping scan: {e}")

            # 移除處理器 (DIS 而非 SCAN)
            self.listener.remove_handler('DIS', scan_handler)

    # ========================================================================
    # 3. Device Provisioning
    # ========================================================================

    async def provision_device(
        self,
        uuid: str,
        unicast_addr: str,
        attention_duration: int = 0
    ) -> bool:
        """
        Provision device by UUID (async).

        Args:
            uuid: Device UUID (32 hex characters)
            unicast_addr: Assigned unicast address (e.g., "0x0100")
            attention_duration: Attention timer duration

        Returns:
            True if provisioning successful

        Example:
            >>> success = await manager.provision_device(
            ...     uuid="123E4567E89B12D3A456655600000152",
            ...     unicast_addr="0x0100"
            ... )
        """
        logger.info(f"Starting provision: UUID={uuid}, Addr={unicast_addr}")

        try:
            # 1. Open PB-ADV bearer
            logger.info("Step 1: Opening PB-ADV bearer...")
            result = await async_cmd_open_pbadv(uuid).execute_with_retry(
                self.serial,
                timeout=10.0
            )

            if not result['success']:
                raise RuntimeError(
                    f"Failed to open PB-ADV: {result.get('error')}")

            logger.info("PB-ADV bearer opened")
            await asyncio.sleep(1)

            # 2. Provision device
            logger.info("Step 2: Provisioning device...")
            result = await async_cmd_provision(
                unicast_addr,
                attention_duration
            ).execute_with_retry(
                self.serial,
                timeout=15.0
            )

            if not result['success']:
                raise RuntimeError(
                    f"Provisioning failed: {result.get('error')}")

            logger.info(f"Device provisioned successfully: {unicast_addr}")

            # 3. Add AppKey
            logger.info("Step 3: Adding AppKey...")
            result = await async_cmd_add_appkey(unicast_addr).execute_with_retry(
                self.serial,
                timeout=10.0
            )

            if not result['success']:
                logger.warning(f"Failed to add AppKey: {result.get('error')}")
                # 繼續，因為可能已經添加過
            else:
                logger.info("AppKey added")

            # 4. Bind model (Generic OnOff Server)
            logger.info("Step 4: Binding model...")
            result = await async_cmd_bind_model(
                unicast_addr,
                "0",           # Element index (not address!)
                "0x1000",      # Generic OnOff Server
                "0"            # AppKey index
            ).execute_with_retry(
                self.serial,
                timeout=10.0
            )

            if not result['success']:
                logger.warning(f"Failed to bind model: {result.get('error')}")
                # 繼續，因為可能已經綁定過
            else:
                logger.info("Model bound")

            # 儲存到 state
            # self.store.add_node({
            #     'uuid': uuid,
            #     'address': unicast_addr,
            #     'provisioned': True
            # })

            logger.info(f"✅ Provisioning complete: {unicast_addr}")
            return True

        except Exception as e:
            logger.error(f"❌ Provisioning failed: {e}")
            return False

    # ========================================================================
    # 4. Node Management
    # ========================================================================

    async def list_nodes(self) -> List[Dict[str, Any]]:
        """
        List all provisioned nodes (async).

        Returns:
            List of node information dicts with keys:
            - index: Node index (int)
            - address: Unicast address (str)
            - element_num: Number of elements (int)
            - online: Online status (int, 1=online, 0=offline)

        Example:
            >>> nodes = await manager.list_nodes()
            >>> for node in nodes:
            ...     print(f"Node {node['index']}: {node['address']}")
        """
        nodes: List[Dict[str, Any]] = []

        # 設置 NL-MSG 處理器 (收集所有節點訊息)
        async def nl_handler(msg: Dict[str, Any]) -> None:
            """Handle NL-MSG messages."""
            params = msg.get('params', [])
            if len(params) >= 4:
                node = {
                    'index': int(params[0]),
                    'address': params[1],
                    'element_num': int(params[2]),
                    'online': int(params[3])
                }
                nodes.append(node)
                logger.debug(f"Found node: {node}")

        # 註冊處理器
        self.listener.add_handler('NL', nl_handler)

        try:
            # 啟動 listener
            if not self.listener._running:
                await self.listener.start()

            # 發送 AT+NL 命令
            logger.debug("Listing nodes...")
            await async_cmd_list_nodes().execute(self.serial, expect_response=False)

            # 等待接收所有 NL-MSG (短暫延遲)
            await asyncio.sleep(0.5)

            logger.info(f"Listed {len(nodes)} provisioned nodes")
            return nodes

        finally:
            # 移除處理器
            self.listener.remove_handler('NL', nl_handler)

    async def remove_node(self, node_index: int) -> bool:
        """
        Remove node from network (async).

        Args:
            node_index: Node index from list (0-based)

        Returns:
            True if removal successful

        Example:
            >>> success = await manager.remove_node(0)
        """
        logger.info(f"Removing node at index {node_index}")

        result = await async_cmd_remove_node(node_index).execute_with_retry(
            self.serial,
            timeout=15.0
        )

        if result['success']:
            logger.info(f"✅ Node {node_index} removed")
            return True
        else:
            logger.error(f"❌ Failed to remove node: {result.get('error')}")
            return False

    async def clear_mesh_network(self) -> bool:
        """
        Clear entire mesh network (async).

        Returns:
            True if successful

        Warning:
            This will remove all provisioned nodes!
        """
        logger.warning("Clearing mesh network - all nodes will be removed!")

        result = await async_cmd_mesh_clear().execute_with_retry(self.serial)

        if result['success']:
            # self.store.clear_nodes()
            logger.info("✅ Mesh network cleared")
            return True
        else:
            logger.error(f"❌ Failed to clear network: {result.get('error')}")
            return False

    # ========================================================================
    # 5. Publish/Subscribe Management
    # ========================================================================

    async def set_publish(
        self,
        node_addr: str,
        element_addr: str,
        publish_addr: str,
        model_id: str = "0x1000"
    ) -> bool:
        """
        Set model publication address (async).

        Args:
            node_addr: Node unicast address
            element_addr: Element address (通常為 element index，如 0)
            publish_addr: Publish address
            model_id: Model ID

        Returns:
            True if successful
        """
        logger.info(
            f"Setting publish: Node={node_addr}, Publish={publish_addr}")

        # 修正參數順序: AT+MPAS <dst> <element_idx> <model_id> <publish_addr> <publish_app_key_idx>
        result = await async_cmd_set_publish(
            node_addr,
            int(element_addr) if element_addr.isdigit() else 0,
            model_id,
            publish_addr,
            0
        ).execute_with_retry(self.serial)

        return result['success']

    async def add_subscription(
        self,
        node_addr: str,
        element_addr: str,
        subscription_addr: str,
        model_id: str = "0x1000"
    ) -> bool:
        """
        Add subscription address to model (async).

        Args:
            node_addr: Node unicast address
            element_addr: Element address (通常為 element index，如 0)
            subscription_addr: Subscription group address
            model_id: Model ID

        Returns:
            True if successful
        """
        logger.info(
            f"Adding subscription: Node={node_addr}, Group={subscription_addr}")

        # 修正參數順序: AT+MSAA <dst> <element_index> <model_id> <Group_addr>
        result = await async_cmd_add_subscription(
            node_addr,
            int(element_addr) if element_addr.isdigit() else 0,
            model_id,
            subscription_addr
        ).execute_with_retry(self.serial)

        return result['success']

    # ========================================================================
    # 6. Lifecycle Management
    # ========================================================================

    async def __aenter__(self):
        """Async context manager entry."""
        if not self.serial.is_open():
            await self.serial.open()
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Async context manager exit."""
        if self.listener._running:
            await self.listener.stop()
        if self.serial.is_open():
            await self.serial.close()
        return False
