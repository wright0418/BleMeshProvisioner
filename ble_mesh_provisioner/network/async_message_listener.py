"""
AsyncIO Message Router and Listener for Mesh messages.

處理來自 BLE Mesh 網路的各類訊息：
1. 命令回應 (已在 AsyncSerialInterface 處理)
2. 異步通知 (MDTG-MSG, SCAN-MSG 等)
3. 自訂訊息過濾與路由
"""

import asyncio
from typing import Any, Callable, Dict, List, Optional, Pattern
import re

from ble_mesh_provisioner.core.async_serial_interface import AsyncSerialInterface
from ble_mesh_provisioner.utils.logger import setup_logger

logger = setup_logger(
    "ble_mesh_provisioner",
    level=20,
    log_file="logs/provisioner.log",
    console=True
)


class AsyncMessageListener:
    """
    AsyncIO-based background listener for mesh messages.

    監聽並分發各類 Mesh 訊息：
    - MDTG-MSG: Mesh data from device to gateway
    - SCAN-MSG: Device scan results
    - PROV-MSG: Provisioning status
    - 其他自訂訊息
    """

    def __init__(self, serial: AsyncSerialInterface) -> None:
        """
        Initialize message listener.

        Args:
            serial: AsyncSerialInterface instance
        """
        self.serial = serial
        self._running = False
        self._listen_task: Optional[asyncio.Task] = None

        # 訊息處理器：pattern -> List[callback]
        self._handlers: Dict[str, List[Callable[[Dict[str, Any]], None]]] = {}

        # 預定義的訊息類型
        self.MESSAGE_TYPES = {
            'MESH_DATA': 'MDTG-MSG',      # Mesh data messages
            'SCAN': 'SCAN-MSG',            # Scan results
            'PROVISION': 'PROV-MSG',       # Provisioning events
            'NODE_RESET': 'NR-MSG',        # Node reset notifications
            'VENDOR': 'MDTS-MSG',          # Vendor model messages
        }

    def add_handler(
        self,
        message_type: str,
        callback: Callable[[Dict[str, Any]], Any]
    ) -> None:
        """
        Add message handler for specific message type.

        Args:
            message_type: Message type to listen for (e.g., 'MDTG-MSG', 'SCAN-MSG')
            callback: Async callback function to handle message

        Example:
            >>> async def handle_mesh_data(msg: Dict[str, Any]):
            ...     print(f"Received mesh data: {msg}")
            >>> listener.add_handler('MDTG-MSG', handle_mesh_data)
        """
        if message_type not in self._handlers:
            self._handlers[message_type] = []

        if callback not in self._handlers[message_type]:
            self._handlers[message_type].append(callback)
            logger.debug(f"Added handler for {message_type}")

    def remove_handler(
        self,
        message_type: str,
        callback: Callable[[Dict[str, Any]], Any]
    ) -> None:
        """
        Remove message handler.

        Args:
            message_type: Message type
            callback: Callback function to remove
        """
        if message_type in self._handlers:
            if callback in self._handlers[message_type]:
                self._handlers[message_type].remove(callback)
                logger.debug(f"Removed handler for {message_type}")

    async def start(self) -> None:
        """
        Start listening for messages.

        Raises:
            RuntimeError: If already running or serial not open
        """
        if self._running:
            logger.warning("Message listener already running")
            return

        if not self.serial.is_open():
            raise RuntimeError(
                "Serial port must be open before starting listener")

        self._running = True
        self._listen_task = asyncio.create_task(self._listen_loop())
        logger.info("AsyncMessageListener started")

    async def stop(self) -> None:
        """
        Stop listening for messages.
        """
        if not self._running:
            return

        self._running = False

        if self._listen_task:
            self._listen_task.cancel()
            try:
                await self._listen_task
            except asyncio.CancelledError:
                pass
            self._listen_task = None

        logger.info("AsyncMessageListener stopped")

    async def _listen_loop(self) -> None:
        """
        Background loop to continuously process notifications.
        """
        logger.debug("AsyncMessageListener loop started")

        while self._running:
            try:
                # Get next notification from serial interface
                notification = await self.serial.get_notification(timeout=0.5)

                if notification:
                    await self._dispatch_message(notification)

            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"Listen loop error: {e}")
                await asyncio.sleep(0.1)

        logger.debug("AsyncMessageListener loop stopped")

    async def _dispatch_message(self, message: Dict[str, Any]) -> None:
        """
        Dispatch message to registered handlers.

        Args:
            message: Parsed message dict
        """
        msg_type = message.get('type')

        if not msg_type:
            logger.warning(f"Message without type: {message}")
            return

        # 查找對應的處理器
        handlers = self._handlers.get(msg_type, [])

        if not handlers:
            logger.warning(f"Unrouted message: {msg_type}")
            return

        # 執行所有處理器
        for handler in handlers:
            try:
                # 檢查是否為 async 函數
                if asyncio.iscoroutinefunction(handler):
                    await handler(message)
                else:
                    handler(message)
            except Exception as e:
                logger.error(f"Handler error for {msg_type}: {e}")

    async def wait_for_message(
        self,
        message_type: str,
        timeout: Optional[float] = None,
        filter_func: Optional[Callable[[Dict[str, Any]], bool]] = None
    ) -> Optional[Dict[str, Any]]:
        """
        Wait for specific message type with optional filtering.

        Args:
            message_type: Message type to wait for
            timeout: Maximum wait time in seconds
            filter_func: Optional function to filter messages

        Returns:
            Matched message dict or None if timeout

        Example:
            >>> # Wait for scan message with specific UUID
            >>> msg = await listener.wait_for_message(
            ...     'SCAN-MSG',
            ...     timeout=10.0,
            ...     filter_func=lambda m: '655600000152' in m.get('raw', '')
            ... )
        """
        result_future = asyncio.get_event_loop().create_future()

        def handler(msg: Dict[str, Any]) -> None:
            # 檢查是否符合過濾條件
            if filter_func and not filter_func(msg):
                return

            # 設置結果
            if not result_future.done():
                result_future.set_result(msg)

        # 臨時註冊處理器
        self.add_handler(message_type, handler)

        try:
            if timeout:
                result = await asyncio.wait_for(result_future, timeout=timeout)
            else:
                result = await result_future
            return result
        except asyncio.TimeoutError:
            logger.debug(f"Timeout waiting for {message_type}")
            return None
        finally:
            # 移除臨時處理器
            self.remove_handler(message_type, handler)


class AsyncMessageRouter:
    """
    Advanced message router with pattern matching and filtering.

    提供更靈活的訊息路由功能，支援：
    - 正則表達式匹配
    - 優先級路由
    - 訊息轉換
    """

    def __init__(self, serial: AsyncSerialInterface) -> None:
        """
        Initialize message router.

        Args:
            serial: AsyncSerialInterface instance
        """
        self.serial = serial
        self._routes: List[Dict[str, Any]] = []
        self._running = False
        self._router_task: Optional[asyncio.Task] = None

    def add_route(
        self,
        pattern: str,
        callback: Callable[[Dict[str, Any]], None],
        priority: int = 0
    ) -> None:
        """
        Add routing rule.

        Args:
            pattern: Regex pattern to match message type or raw content
            callback: Callback function for matched messages
            priority: Route priority (higher = earlier execution)

        Example:
            >>> router.add_route(r'MDTG-MSG.*0x0100', handle_device_100)
            >>> router.add_route(r'SCAN-MSG', handle_scan_results, priority=10)
        """
        route = {
            'pattern': re.compile(pattern),
            'callback': callback,
            'priority': priority
        }

        self._routes.append(route)
        # 按優先級排序
        self._routes.sort(key=lambda r: r['priority'], reverse=True)
        logger.debug(f"Added route: {pattern} (priority={priority})")

    async def start(self) -> None:
        """Start message router."""
        if self._running:
            return

        if not self.serial.is_open():
            raise RuntimeError("Serial port must be open")

        self._running = True
        self._router_task = asyncio.create_task(self._route_loop())
        logger.info("AsyncMessageRouter started")

    async def stop(self) -> None:
        """Stop message router."""
        if not self._running:
            return

        self._running = False

        if self._router_task:
            self._router_task.cancel()
            try:
                await self._router_task
            except asyncio.CancelledError:
                pass
            self._router_task = None

        logger.info("AsyncMessageRouter stopped")

    async def _route_loop(self) -> None:
        """Background routing loop."""
        logger.debug("AsyncMessageRouter loop started")

        while self._running:
            try:
                notification = await self.serial.get_notification(timeout=0.5)

                if notification:
                    await self._route_message(notification)

            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"Router loop error: {e}")
                await asyncio.sleep(0.1)

        logger.debug("AsyncMessageRouter loop stopped")

    async def _route_message(self, message: Dict[str, Any]) -> None:
        """
        Route message through registered patterns.

        Args:
            message: Parsed message dict
        """
        msg_type = message.get('type', '')
        raw_msg = message.get('raw', '')

        # 測試每個路由規則
        for route in self._routes:
            pattern = route['pattern']
            callback = route['callback']

            # 檢查類型或原始內容是否匹配
            if pattern.search(msg_type) or pattern.search(raw_msg):
                try:
                    if asyncio.iscoroutinefunction(callback):
                        await callback(message)
                    else:
                        callback(message)
                except Exception as e:
                    logger.error(f"Route callback error: {e}")
