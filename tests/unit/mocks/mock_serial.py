"""
Mock Serial Interface for testing without hardware.

Simulates RL62M02 module behavior using pre-recorded responses.
"""

import time
import threading
from typing import Optional, Callable, List
from queue import Queue
from tests.mocks.mock_responses import get_mock_response, get_scan_devices_response


class MockSerialInterface:
    """
    Mock serial interface that simulates RL62M02 hardware responses.

    Compatible with SerialInterface API for drop-in replacement in tests.
    """

    def __init__(
        self,
        port: str = "MOCK_PORT",
        baudrate: int = 115200,
        timeout: float = 5.0,
        simulate_delay: bool = True
    ):
        """
        Initialize mock serial interface.

        Args:
            port: Port name (for compatibility, not used)
            baudrate: Baudrate (for compatibility, not used)
            timeout: Response timeout
            simulate_delay: Whether to simulate communication delays
        """
        self.port = port
        self.baudrate = baudrate
        self.timeout = timeout
        self.simulate_delay = simulate_delay

        self._is_open = False
        self._listening = False
        self._listen_thread: Optional[threading.Thread] = None
        self._message_queue: Queue = Queue()
        self._callbacks: List[Callable[[str], None]] = []

        # Track scan state
        self._scanning = False
        self._scan_count = 0

    def open(self) -> bool:
        """Open mock serial connection."""
        if self.simulate_delay:
            time.sleep(0.1)  # Simulate connection delay
        self._is_open = True
        return True

    def close(self) -> None:
        """Close mock serial connection."""
        self.stop_listening()
        self._is_open = False

    def is_open(self) -> bool:
        """Check if mock port is open."""
        return self._is_open

    def send_command(self, command: str, wait_response: bool = True) -> Optional[str]:
        """
        Send mock command and get response.

        Args:
            command: AT command string
            wait_response: Whether to wait for response

        Returns:
            Mock response string
        """
        if not self._is_open:
            raise RuntimeError("Serial port is not open")

        # Simulate transmission delay
        if self.simulate_delay:
            time.sleep(0.05)

        if not wait_response:
            return None

        # Normalize command
        cmd = command.strip()

        # Handle scan commands specially
        if cmd.startswith("AT+DIS 1"):
            self._scanning = True
            self._scan_count = 0
            return "DIS-MSG SUCCESS\r\n"
        elif cmd.startswith("AT+DIS 0"):
            self._scanning = False
            return "DIS-MSG SUCCESS\r\n"

        # Get mock response
        try:
            response = get_mock_response(cmd)

            # Simulate response delay
            if self.simulate_delay:
                time.sleep(0.1)

            return response

        except KeyError:
            # Unknown command - return error
            return f"ERROR-MSG Unknown command: {cmd}\r\n"

    def start_listening(self, callback: Optional[Callable[[str], None]] = None) -> None:
        """Start mock listening thread."""
        if self._listening:
            return

        if not self._is_open:
            raise RuntimeError("Serial port is not open")

        if callback:
            self._callbacks.append(callback)

        self._listening = True
        self._listen_thread = threading.Thread(
            target=self._listen_worker,
            daemon=True
        )
        self._listen_thread.start()

    def stop_listening(self) -> None:
        """Stop mock listening thread."""
        if not self._listening:
            return

        self._listening = False

        if self._listen_thread:
            self._listen_thread.join(timeout=2.0)
            self._listen_thread = None

    def _listen_worker(self) -> None:
        """Mock listener worker - generates scan results if scanning."""
        while self._listening:
            if self._scanning and self._scan_count < 3:
                # Generate mock scan results
                time.sleep(0.5)

                devices = [
                    "DIS-MSG 655600000152 -48 123E4567E89B12D3A456655600000152",
                    "DIS-MSG 655600000153 -52 123E4567E89B12D3A456655600000153",
                    "DIS-MSG 655600000151 -45 123E4567E89B12D3A456655600000151",
                ]

                if self._scan_count < len(devices):
                    message = devices[self._scan_count]
                    self._message_queue.put(message)

                    for callback in self._callbacks:
                        try:
                            callback(message)
                        except Exception:
                            pass

                    self._scan_count += 1
            else:
                time.sleep(0.1)

    def get_message(self, timeout: float = 1.0) -> Optional[str]:
        """Get message from mock queue."""
        try:
            return self._message_queue.get(timeout=timeout)
        except:
            return None

    def add_callback(self, callback: Callable[[str], None]) -> None:
        """Add callback for messages."""
        if callback not in self._callbacks:
            self._callbacks.append(callback)

    def remove_callback(self, callback: Callable[[str], None]) -> None:
        """Remove callback."""
        if callback in self._callbacks:
            self._callbacks.remove(callback)

    def inject_message(self, message: str) -> None:
        """
        Inject a message into the mock serial (for testing).

        Args:
            message: Message to inject
        """
        self._message_queue.put(message)
        for callback in self._callbacks:
            try:
                callback(message)
            except Exception:
                pass

    def __enter__(self):
        """Context manager entry."""
        self.open()
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        """Context manager exit."""
        self.close()
        return False
