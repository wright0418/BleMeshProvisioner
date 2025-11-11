"""
AsyncIO-based Serial Interface for UART communication with RL62M02 module.

使用 asyncio 實現非阻塞 UART 通訊，支援：
1. 非阻塞讀寫
2. 事件驅動的訊息處理
3. 命令-回應關聯 (Future-based)
4. 異步通知路由 (Queue-based)
5. 並發命令處理
"""

import asyncio
import serial
from typing import Optional, Dict, Any, List, Callable, Pattern
from asyncio import Queue, Future, Task
from collections import defaultdict
import re
from datetime import datetime

from ble_mesh_provisioner.core.response_parser import ResponseParser
from ble_mesh_provisioner.utils.logger import setup_logger

logger = setup_logger(
    "ble_mesh_provisioner",
    level=20,
    log_file="logs/provisioner.log",
    console=True
)


class AsyncSerialInterface:
    """
    AsyncIO-based UART Serial Interface for RL62M02 Provisioner module.

    Communication settings:
    - Baud rate: 115200
    - Data bits: 8
    - Parity: None
    - Stop bits: 1
    - Flow control: None

    Features:
    - 非阻塞命令執行 (async execute_command)
    - 自動訊息路由 (命令回應 vs 異步通知)
    - Future-based 等待機制
    - 支援並發命令
    """

    def __init__(
        self,
        port: str,
        baudrate: int = 115200,
        timeout: float = 5.0
    ):
        """
        Initialize async serial interface.

        Args:
            port: Serial port name (e.g., 'COM3', '/dev/ttyUSB0')
            baudrate: Communication speed (default: 115200)
            timeout: Default command timeout in seconds (default: 5.0)
        """
        self.port = port
        self.baudrate = baudrate
        self.timeout = timeout
        self.serial: Optional[serial.Serial] = None

        # AsyncIO components
        self._reader_task: Optional[Task] = None
        self._running = False

        # 命令回應處理：msg_type -> Future
        # 當發送命令時，註冊 Future 等待對應的回應
        self._pending_responses: Dict[str, List[Future]] = defaultdict(list)

        # 異步通知處理：Queue for listeners
        self._notification_queue: Queue = Queue()

        # 自訂 callbacks (for advanced use)
        self._callbacks: List[Callable[[str], None]] = []

        # 訊息路由規則
        self._response_patterns = [
            # 命令回應 patterns (這些訊息應該被 Future 接收)
            re.compile(r'^(\w+)-MSG\s+(SUCCESS|ERROR)'),
        ]
        self._notification_patterns = [
            # 異步通知 patterns (這些訊息應該進入 Queue)
            re.compile(
                r'^(MDTG-MSG|MDTS-MSG|MDTPG-MSG|DIS-MSG|PROV-MSG|NR-MSG|NL-MSG)'),
        ]

        logger.info(
            f"AsyncSerialInterface initialized: port={port}, "
            f"baudrate={baudrate}, timeout={timeout}"
        )

    async def open(self) -> bool:
        """
        Open serial port and start reader task.

        Returns:
            True if successful

        Raises:
            serial.SerialException: If port cannot be opened
        """
        try:
            # Open serial port (still using pyserial for portability)
            self.serial = serial.Serial(
                port=self.port,
                baudrate=self.baudrate,
                bytesize=serial.EIGHTBITS,
                parity=serial.PARITY_NONE,
                stopbits=serial.STOPBITS_ONE,
                timeout=0,  # Non-blocking reads
                xonxoff=False,
                rtscts=False,
                dsrdtr=False
            )

            # Clear buffers
            self.serial.reset_input_buffer()
            self.serial.reset_output_buffer()

            logger.info(f"Serial port {self.port} opened successfully")

            # Start background reader task
            self._running = True
            self._reader_task = asyncio.create_task(self._read_loop())

            logger.info("AsyncIO reader task started")
            return True

        except serial.SerialException as e:
            logger.error(f"Failed to open serial port {self.port}: {e}")
            raise

    async def close(self) -> None:
        """
        Close serial port and stop reader task.
        """
        self._running = False

        # Cancel reader task
        if self._reader_task:
            self._reader_task.cancel()
            try:
                await self._reader_task
            except asyncio.CancelledError:
                pass
            self._reader_task = None

        # Close serial port
        if self.serial and self.serial.is_open:
            self.serial.close()
            logger.info(f"Serial port {self.port} closed")

        self.serial = None

        # Cancel all pending futures
        for futures in self._pending_responses.values():
            for future in futures:
                if not future.done():
                    future.cancel()
        self._pending_responses.clear()

    def is_open(self) -> bool:
        """
        Check if serial port is open.

        Returns:
            True if port is open and running
        """
        return self.serial is not None and self.serial.is_open and self._running

    async def send_command(
        self,
        command: str,
        expect_response: Optional[str] = None,
        timeout: Optional[float] = None
    ) -> Optional[Dict[str, Any]]:
        """
        Send AT command and wait for response.

        Args:
            command: AT command string (should end with \\r\\n)
            expect_response: Expected response message type (e.g., 'VER', 'DIS')
                           If None, returns immediately without waiting
            timeout: Command timeout (uses default if None)

        Returns:
            Parsed response dict if expect_response is set, None otherwise

        Raises:
            RuntimeError: If port is not open
            asyncio.TimeoutError: If response timeout
            serial.SerialException: If communication fails

        Example:
            >>> await serial.send_command("AT+VER\\r\\n", expect_response='VER')
            {'type': 'VER', 'status': 'SUCCESS', 'params': ['1.0.0'], ...}
        """
        if not self.is_open():
            raise RuntimeError("Serial port is not open")

        if self.serial is None:
            raise RuntimeError("Serial port is not initialized")

        if timeout is None:
            timeout = self.timeout

        try:
            # Ensure command ends with \r\n
            if not command.endswith('\r\n'):
                command += '\r\n'

            # Register future if expecting response
            response_future: Optional[Future] = None
            if expect_response:
                response_future = asyncio.get_event_loop().create_future()
                self._pending_responses[expect_response].append(
                    response_future)

            # Send command
            self.serial.write(command.encode('utf-8'))
            self.serial.flush()

            logger.debug(f"Sent command: {command.strip()}")

            # Wait for response if requested
            if response_future and expect_response is not None:
                try:
                    result = await asyncio.wait_for(response_future, timeout=timeout)
                    logger.debug(
                        f"Received response for {expect_response}: {result}")
                    return result
                except asyncio.TimeoutError:
                    logger.error(
                        f"Timeout waiting for {expect_response} response")
                    # Remove from pending
                    if response_future in self._pending_responses[expect_response]:
                        self._pending_responses[expect_response].remove(
                            response_future)
                    raise
                except asyncio.CancelledError:
                    logger.warning(f"Command {expect_response} cancelled")
                    raise

            return None

        except serial.SerialException as e:
            logger.error(f"Failed to send command: {e}")
            raise

    async def _read_loop(self) -> None:
        """
        Background task to continuously read from serial port.

        Reads lines, parses them, and routes to appropriate handlers:
        - Command responses -> resolve pending Future
        - Async notifications -> put in notification queue
        - Unknown messages -> invoke callbacks
        """
        logger.debug("AsyncIO read loop started")
        buffer = bytearray()

        while self._running:
            try:
                # Non-blocking read
                if self.serial and self.serial.in_waiting > 0:
                    chunk = self.serial.read(self.serial.in_waiting or 1)
                    if chunk:
                        buffer.extend(chunk)

                        # Process complete lines (ending with \r or \n)
                        while b'\r' in buffer or b'\n' in buffer:
                            # Find line ending
                            cr_pos = buffer.find(b'\r')
                            lf_pos = buffer.find(b'\n')

                            if cr_pos == -1:
                                split_pos = lf_pos
                            elif lf_pos == -1:
                                split_pos = cr_pos
                            else:
                                split_pos = min(cr_pos, lf_pos)

                            # Extract line
                            line_bytes = buffer[:split_pos]
                            buffer = buffer[split_pos + 1:]

                            if line_bytes:
                                try:
                                    line = line_bytes.decode(
                                        'utf-8', errors='ignore').strip()
                                    if line:
                                        await self._process_line(line)
                                except Exception as e:
                                    logger.error(f"Error processing line: {e}")

                # Yield control to event loop
                await asyncio.sleep(0.01)

            except Exception as e:
                logger.error(f"Read loop error: {e}")
                await asyncio.sleep(0.1)

        logger.debug("AsyncIO read loop stopped")

    async def _process_line(self, line: str) -> None:
        """
        Process received line and route to appropriate handler.

        Args:
            line: Received line from UART
        """
        logger.debug(f"RAW UART RX: {repr(line)}")

        # Parse response
        parsed = ResponseParser.parse_response(line)
        msg_type = parsed.get('type')

        # Route to appropriate handler
        routed = False

        # 1. Check if it's a command response
        if msg_type and msg_type in self._pending_responses:
            futures = self._pending_responses[msg_type]
            if futures:
                # Resolve first pending future
                future = futures.pop(0)
                if not future.done():
                    future.set_result(parsed)
                    routed = True
                    logger.debug(f"Resolved future for {msg_type}")

        # 2. Check if it's an async notification
        if not routed:
            for pattern in self._notification_patterns:
                if pattern.match(line):
                    await self._notification_queue.put(parsed)
                    routed = True
                    logger.debug(f"Routed notification: {msg_type}")
                    break

        # 3. Invoke custom callbacks
        for callback in self._callbacks:
            try:
                callback(line)
            except Exception as e:
                logger.error(f"Callback error: {e}")

        if not routed and msg_type:
            logger.warning(f"Unrouted message: {msg_type}")

    async def get_notification(self, timeout: Optional[float] = None) -> Optional[Dict[str, Any]]:
        """
        Get next notification from queue.

        Args:
            timeout: Maximum time to wait (None = wait forever)

        Returns:
            Parsed notification dict or None if timeout

        Example:
            >>> notification = await serial.get_notification(timeout=1.0)
            >>> if notification and notification['type'] == 'MDTG-MSG':
            ...     print(f"Received mesh data: {notification}")
        """
        try:
            if timeout:
                return await asyncio.wait_for(self._notification_queue.get(), timeout=timeout)
            else:
                return await self._notification_queue.get()
        except asyncio.TimeoutError:
            return None

    def add_callback(self, callback: Callable[[str], None]) -> None:
        """
        Add callback for all received messages.

        Args:
            callback: Function to call when message received
        """
        if callback not in self._callbacks:
            self._callbacks.append(callback)

    def remove_callback(self, callback: Callable[[str], None]) -> None:
        """
        Remove callback.

        Args:
            callback: Callback function to remove
        """
        if callback in self._callbacks:
            self._callbacks.remove(callback)

    async def __aenter__(self):
        """Async context manager entry."""
        await self.open()
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Async context manager exit."""
        await self.close()
        return False
