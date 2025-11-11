"""
AsyncIO Mock Serial for testing.

提供模擬 UART 通訊的 Mock 類別，用於單元測試。
"""

import asyncio
from typing import Dict, List, Optional, Callable, Any
from datetime import datetime

from ble_mesh_provisioner.utils.logger import setup_logger

logger = setup_logger(
    "ble_mesh_provisioner",
    level=20,
    log_file="logs/provisioner.log",
    console=True
)


class AsyncMockSerial:
    """
    Mock Serial interface for testing AsyncSerialInterface.

    模擬真實硬體的行為，包括：
    - 命令回應延遲
    - 異步訊息生成
    - 錯誤情境模擬
    """

    def __init__(
        self,
        port: str = "MOCK",
        response_delay: float = 0.1,
        responses: Optional[Dict[str, List[str]]] = None
    ):
        """
        Initialize mock serial.

        Args:
            port: Mock port name
            response_delay: Simulated response delay in seconds
            responses: Pre-configured responses dict {command_pattern: [responses]}
        """
        self.port = port
        self.response_delay = response_delay
        self.responses = responses or self._default_responses()

        # Mock state
        self.is_open_flag = False
        self.write_buffer: List[bytes] = []
        self.read_buffer: bytearray = bytearray()

        # 記錄所有命令
        self.command_history: List[Dict[str, Any]] = []

        # 異步訊息生成器
        self._notification_task: Optional[asyncio.Task] = None
        self._notifications_enabled = False

    @staticmethod
    def _default_responses() -> Dict[str, List[str]]:
        """Default mock responses for common commands."""
        return {
            'AT+VER': ['VER-MSG SUCCESS 1.0.0\r\n'],
            'AT+MRG': ['MRG-MSG SUCCESS PROVISIONER\r\n'],
            'AT+DIS 1': ['DIS-MSG SUCCESS\r\n', 'DIS-MSG 655600000152 -48 123E4567E89B12D3A456655600000152\r\n'],
            'AT+DIS 0': ['DIS-MSG SUCCESS\r\n'],
            'AT+PBADVCON': ['PBADVCON-MSG SUCCESS\r\n'],
            'AT+PROV': ['PROV-MSG SUCCESS 0x0100\r\n'],
            'AT+AKA': ['AKA-MSG SUCCESS\r\n'],
            'AT+MAKB': ['MAKB-MSG SUCCESS\r\n'],
            'AT+NL': ['NL-MSG 1 0x0100 1 1\r\n', 'NL-MSG SUCCESS\r\n'],
            'AT+NR': ['NR-MSG SUCCESS 0x0000\r\n'],
            'AT+MSAA': ['MSAA-MSG SUCCESS\r\n'],
            'AT+MSAD': ['MSAD-MSG SUCCESS\r\n'],
            'AT+MPAS': ['MPAS-MSG SUCCESS\r\n'],
            'AT+MPAD': ['MPAD-MSG SUCCESS\r\n'],
            'AT+MDTS': ['MDTS-MSG SUCCESS\r\n'],
            'AT+MDTG': ['MDTG-MSG SUCCESS\r\n'],
        }

    def open(self) -> bool:
        """Mock open."""
        self.is_open_flag = True
        logger.debug(f"Mock serial {self.port} opened")
        return True

    def close(self) -> None:
        """Mock close."""
        self.is_open_flag = False
        self._notifications_enabled = False
        if self._notification_task:
            self._notification_task.cancel()
        logger.debug(f"Mock serial {self.port} closed")

    def is_open(self) -> bool:
        """Check if mock serial is open."""
        return self.is_open_flag

    def write(self, data: bytes) -> int:
        """Mock write."""
        self.write_buffer.append(data)

        # 記錄命令
        command = data.decode('utf-8', errors='ignore').strip()
        self.command_history.append({
            'timestamp': datetime.now(),
            'command': command
        })

        logger.debug(f"Mock write: {command}")

        # 生成回應
        asyncio.create_task(self._generate_response(command))

        return len(data)

    def flush(self) -> None:
        """Mock flush."""
        pass

    @property
    def in_waiting(self) -> int:
        """Mock in_waiting."""
        return len(self.read_buffer)

    def read(self, size: int = 1) -> bytes:
        """Mock read."""
        if not self.read_buffer:
            return b''

        data = bytes(self.read_buffer[:size])
        self.read_buffer = self.read_buffer[size:]
        return data

    def reset_input_buffer(self) -> None:
        """Mock reset input buffer."""
        self.read_buffer = bytearray()

    def reset_output_buffer(self) -> None:
        """Mock reset output buffer."""
        self.write_buffer = []

    async def _generate_response(self, command: str) -> None:
        """
        Generate mock response for command.

        Args:
            command: Received command
        """
        # 延遲以模擬真實硬體
        await asyncio.sleep(self.response_delay)

        # 查找匹配的回應
        response_lines = []
        for pattern, responses in self.responses.items():
            if command.startswith(pattern):
                response_lines = responses
                break

        if not response_lines:
            # 預設錯誤回應
            cmd_name = command.split()[0].replace('AT+', '')
            response_lines = [f'{cmd_name}-MSG ERROR Unknown command\r\n']

        # 寫入回應到讀取緩衝區
        for line in response_lines:
            self.read_buffer.extend(line.encode('utf-8'))
            logger.debug(f"Mock response: {line.strip()}")

    def enable_notifications(self, message_type: str = 'MDTG', interval: float = 2.0):
        """
        Enable periodic notification generation for testing.

        Args:
            message_type: Type of notification to generate
            interval: Notification interval in seconds
        """
        if self._notifications_enabled:
            return

        self._notifications_enabled = True
        self._notification_task = asyncio.create_task(
            self._notification_generator(message_type, interval)
        )

    async def _notification_generator(self, message_type: str, interval: float):
        """Background task to generate notifications."""
        counter = 0
        while self._notifications_enabled:
            await asyncio.sleep(interval)

            if message_type == 'MDTG':
                # 模擬 Mesh data
                notification = f"MDTG-MSG 0x0100 87010005FF{counter:02X}FFFFFF\r\n"
            elif message_type == 'SCAN':
                # 模擬 Scan 結果
                notification = f"SCAN-MSG 65560000{counter:04X} -48 123E4567E89B12D3A456655600000{counter:03X}\r\n"
            else:
                notification = f"{message_type}-MSG Test notification {counter}\r\n"

            self.read_buffer.extend(notification.encode('utf-8'))
            logger.debug(f"Mock notification: {notification.strip()}")
            counter += 1

    def add_response(self, command: str, response: str):
        """
        Add custom response for specific command.

        Args:
            command: Command pattern
            response: Response string (with \r\n)
        """
        self.responses[command] = [response]

    def simulate_error(self, command: str):
        """
        Simulate error response for command.

        Args:
            command: Command pattern
        """
        cmd_name = command.replace('AT+', '')
        self.responses[command] = [f'{cmd_name}-MSG ERROR Simulated error\r\n']

    def simulate_timeout(self, command: str):
        """
        Simulate timeout by not responding to command.

        Args:
            command: Command pattern
        """
        self.responses[command] = []  # No response

    def get_command_history(self) -> List[Dict[str, Any]]:
        """Get history of all commands sent."""
        return self.command_history.copy()

    def clear_history(self):
        """Clear command history."""
        self.command_history = []


# 測試數據庫：記錄真實硬體互動
class HardwareInteractionRecorder:
    """
    Record real hardware interactions for test replay.

    記錄真實硬體互動，建立測試資料庫。
    """

    def __init__(self, db_file: str = "tests/hardware_interactions.json"):
        """
        Initialize recorder.

        Args:
            db_file: Path to database file
        """
        self.db_file = db_file
        self.interactions: List[Dict[str, Any]] = []

    def record(self, command: str, response: str, duration: float):
        """
        Record an interaction.

        Args:
            command: Sent command
            response: Received response
            duration: Response time in seconds
        """
        self.interactions.append({
            'timestamp': datetime.now().isoformat(),
            'command': command,
            'response': response,
            'duration': duration
        })

    def save(self):
        """Save interactions to file."""
        import json
        with open(self.db_file, 'w', encoding='utf-8') as f:
            json.dump(self.interactions, f, indent=2, ensure_ascii=False)

    def load(self) -> List[Dict[str, Any]]:
        """Load interactions from file."""
        import json
        try:
            with open(self.db_file, 'r', encoding='utf-8') as f:
                return json.load(f)
        except FileNotFoundError:
            return []

    def replay_as_mock(self) -> AsyncMockSerial:
        """
        Create mock serial from recorded interactions.

        Returns:
            AsyncMockSerial configured with recorded responses
        """
        interactions = self.load()

        responses = {}
        for interaction in interactions:
            cmd = interaction['command']
            resp = interaction['response']

            # 提取命令模式 (AT+XXX 部分)
            cmd_pattern = cmd.split()[0] if ' ' in cmd else cmd

            if cmd_pattern not in responses:
                responses[cmd_pattern] = []
            responses[cmd_pattern].append(resp)

        # 計算平均延遲
        avg_delay = sum(i['duration'] for i in interactions) / \
            len(interactions) if interactions else 0.1

        return AsyncMockSerial(
            port="RECORDED",
            response_delay=avg_delay,
            responses=responses
        )
