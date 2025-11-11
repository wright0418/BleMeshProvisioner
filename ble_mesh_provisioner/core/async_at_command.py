"""
AsyncIO AT Command builder and executor for RL62M02 module.

提供高階 AT 命令介面，支援：
1. async/await 執行模式
2. 自動重試機制
3. 命令超時處理
4. 錯誤處理與日誌記錄
"""

import asyncio
from datetime import datetime
from typing import List, Optional, Dict, Any
from ble_mesh_provisioner.core.async_serial_interface import AsyncSerialInterface
from ble_mesh_provisioner.core.response_parser import ResponseParser

from ble_mesh_provisioner.utils.logger import setup_logger

logger = setup_logger(
    "ble_mesh_provisioner",
    level=20,
    log_file="logs/provisioner.log",
    console=True
)


class AsyncATCommand:
    """
    AsyncIO AT Command builder and executor.

    格式化並執行 AT 命令，支援自動重試。

    Command format: AT+COMMAND {<param>…}\\r\\n
    """

    def __init__(self, command: str, params: Optional[List[str]] = None):
        """
        Initialize AT command.

        Args:
            command: Command name (without AT+ prefix)
            params: Optional list of parameters

        Example:
            >>> cmd = AsyncATCommand("VER")
            >>> cmd = AsyncATCommand("MDTS", ["0x0100", "0", "0", "1", "0x11223344"])
        """
        self.command = command
        self.params = params or []
        self.raw = self._build_command()

    def _build_command(self) -> str:
        """
        Build raw AT command string.

        Returns:
            Formatted AT command with \\r\\n
        """
        cmd = f"AT+{self.command}"
        if self.params:
            cmd += " " + " ".join(str(p) for p in self.params)
        cmd += "\r\n"
        return cmd

    @staticmethod
    def build_command(cmd: str, params: Optional[List[str]] = None) -> str:
        """
        Static method to build AT command string.

        Args:
            cmd: Command name (without AT+ prefix)
            params: Optional list of parameters

        Returns:
            Formatted AT command string

        Example:
            >>> AsyncATCommand.build_command("VER")
            'AT+VER\\r\\n'
            >>> AsyncATCommand.build_command("DIS", ["1"])
            'AT+DIS 1\\r\\n'
        """
        command = AsyncATCommand(cmd, params)
        return command.raw

    async def execute(
        self,
        serial: AsyncSerialInterface,
        timeout: float = 5.0,
        expect_response: bool = True,
    ) -> Dict[str, Any]:
        """
        Execute AT command and get response (async).

        Args:
            serial: AsyncSerialInterface instance
            timeout: Command timeout in seconds
            expect_response: Whether to wait for response

        Returns:
            Dictionary with execution result:
            {
                'success': bool,
                'status': str,  # 'SUCCESS' or 'ERROR'
                'type': str,    # Message type
                'params': list,
                'raw': str,
                'error': str (optional)
            }

        Example:
            >>> cmd = AsyncATCommand("VER")
            >>> result = await cmd.execute(serial)
            >>> if result['success']:
            ...     print(f"Version: {result['params'][0]}")
        """
        try:
            # Determine expected response type
            # VER -> VER-MSG, MDTS -> MDTS-MSG, etc.
            response_type = self.command if expect_response else None

            # Send command and wait for response
            response = await serial.send_command(
                self.raw,
                expect_response=response_type,
                timeout=timeout
            )

            if not response:
                return {
                    'success': True,
                    'status': None,
                    'type': None,
                    'params': [],
                    'raw': self.raw
                }

            # Check status
            success = response.get('status') == 'SUCCESS'

            return {
                'success': success,
                'status': response.get('status'),
                'type': response.get('type'),
                'params': response.get('params', []),
                'raw': response.get('raw', ''),
                'error': None if success else response.get('raw', 'Unknown error')
            }

        except asyncio.TimeoutError:
            logger.error(f"Command timeout: {self.raw.strip()}")
            return {
                'success': False,
                'status': 'ERROR',
                'type': self.command,
                'params': [],
                'raw': self.raw,
                'error': f"Timeout after {timeout}s"
            }
        except Exception as e:
            logger.error(
                f"Command execution error: {self.raw.strip()}, Error: {e}")
            return {
                'success': False,
                'status': 'ERROR',
                'type': self.command,
                'params': [],
                'raw': self.raw,
                'error': str(e)
            }

    async def execute_with_retry(
        self,
        serial: AsyncSerialInterface,
        timeout: float = 5.0,
        max_retries: int = 1,
        expect_response: bool = True,
    ) -> Dict[str, Any]:
        """
        Execute command with retry on failure.

        Args:
            serial: AsyncSerialInterface instance
            timeout: Command timeout in seconds
            max_retries: Maximum retry attempts (0 = no retry, 1 = one retry)
            expect_response: Whether to wait for response

        Returns:
            Dictionary with execution result

        Example:
            >>> cmd = AsyncATCommand("VER")
            >>> result = await cmd.execute_with_retry(serial, max_retries=1)
        """
        last_result = None

        for attempt in range(max_retries + 1):
            if attempt > 0:
                logger.info(
                    f"Retrying command: {self.raw.strip()} (attempt {attempt + 1}/{max_retries + 1})")
                await asyncio.sleep(0.5)  # Brief delay before retry

            result = await self.execute(serial, timeout, expect_response)
            last_result = result

            if result['success']:
                return result

            # Log failure
            logger.warning(
                f"Command failed: {self.raw.strip()}, "
                f"Status: {result.get('status')}, "
                f"Error: {result.get('error')}, "
                f"Attempt: {attempt + 1}/{max_retries + 1}"
            )

        # All attempts failed
        logger.error(
            f"Command failed after {max_retries + 1} attempts: {self.raw.strip()}, "
            f"Time: {datetime.now()}"
        )
        return last_result or {
            'success': False,
            'status': 'ERROR',
            'type': self.command,
            'params': [],
            'raw': self.raw,
            'error': 'All retry attempts failed'
        }


# ============================================================================
# 便利函數：建立常用 AT 命令
# ============================================================================

def async_cmd_get_version() -> AsyncATCommand:
    """Get firmware version: AT+VER"""
    return AsyncATCommand("VER")


def async_cmd_get_role() -> AsyncATCommand:
    """Get device role: AT+MRG"""
    return AsyncATCommand("MRG")


def async_cmd_restart() -> AsyncATCommand:
    """Restart module: AT+RST"""
    return AsyncATCommand("RST")


def async_cmd_mesh_clear() -> AsyncATCommand:
    """Clear mesh network / Remove node: AT+NR"""
    return AsyncATCommand("NR")


def async_cmd_start_scan(duration: int = 5) -> AsyncATCommand:
    """
    Start scanning for unprovisioned devices: AT+DIS 1

    Args:
        duration: Scan duration parameter (1 for start)
    """
    return AsyncATCommand("DIS", ["1"])


def async_cmd_stop_scan() -> AsyncATCommand:
    """Stop scanning: AT+DIS 0"""
    return AsyncATCommand("DIS", ["0"])


def async_cmd_open_pbadv(uuid: str) -> AsyncATCommand:
    """
    Open PB-ADV bearer: AT+PBADVCON <uuid>

    Args:
        uuid: Device UUID (32 hex characters)
    """
    return AsyncATCommand("PBADVCON", [uuid])


def async_cmd_provision(
    unicast_addr: str,
    attention_duration: int = 0
) -> AsyncATCommand:
    """
    Provision device: AT+PROV

    Args:
        unicast_addr: Unicast address in hex (e.g., "0x0100") - not used in actual command
        attention_duration: Attention timer duration - not used in actual command

    Note: AT+PROV command doesn't take parameters according to documentation
    """
    return AsyncATCommand("PROV")


def async_cmd_add_appkey(node_addr: str, app_key_index: int = 0, net_key_index: int = 0) -> AsyncATCommand:
    """
    Add AppKey to node: AT+AKA <dst> <app_key_index> <net_key_index>

    Args:
        node_addr: Node unicast address (e.g., "0x0100")
        app_key_index: Application key index (default: 0)
        net_key_index: Network key index (default: 0)
    """
    return AsyncATCommand("AKA", [node_addr, str(app_key_index), str(net_key_index)])


def async_cmd_bind_model(
    node_addr: str,
    element_index: str,
    model_id: str,
    appkey_index: str = "0"
) -> AsyncATCommand:
    """
    Bind model to AppKey: AT+MAKB <dst> <element_index> <model_id> <app_key_index>

    Args:
        node_addr: Node unicast address
        element_index: Element index (not address!)
        model_id: Model ID (e.g., "0x1000ffff" for Vendor Model)
        appkey_index: AppKey index (default: "0")
    """
    return AsyncATCommand("MAKB", [node_addr, element_index, model_id, appkey_index])


def async_cmd_list_nodes() -> AsyncATCommand:
    """List all provisioned nodes: AT+NL"""
    return AsyncATCommand("NL")


def async_cmd_remove_node(node_index: int) -> AsyncATCommand:
    """
    Remove node from network: AT+MRN <node_index>

    Args:
        node_index: Node index from list (0-based)
    """
    return AsyncATCommand("MRN", [str(node_index)])


def async_cmd_set_publish(
    node_addr: str,
    element_idx: int,
    model_id: str,
    publish_addr: str,
    appkey_index: int = 0
) -> AsyncATCommand:
    """
    Set model publication: AT+MPAS <dst> <element_idx> <model_id> <publish_addr> <publish_app_key_idx>

    Args:
        node_addr: Node unicast address (dst)
        element_idx: Element index
        model_id: Model ID
        publish_addr: Publish address (group or unicast)
        appkey_index: AppKey index (default: 0)
    """
    return AsyncATCommand("MPAS", [node_addr, str(element_idx), model_id, publish_addr, str(appkey_index)])


def async_cmd_clear_publish(
    node_addr: str,
    element_idx: int,
    model_id: str,
    appkey_index: int = 0
) -> AsyncATCommand:
    """
    Clear model publication: AT+MPAD <dst> <element_idx> <model_id> <publish_app_key_idx>

    Args:
        node_addr: Node unicast address (dst)
        element_idx: Element index
        model_id: Model ID
        appkey_index: AppKey index (default: 0)
    """
    return AsyncATCommand("MPAD", [node_addr, str(element_idx), model_id, str(appkey_index)])


def async_cmd_add_subscription(
    node_addr: str,
    element_idx: int,
    model_id: str,
    group_addr: str
) -> AsyncATCommand:
    """
    Add subscription to model: AT+MSAA <dst> <element_index> <model_id> <Group_addr>

    Args:
        node_addr: Node unicast address (dst)
        element_idx: Element index
        model_id: Model ID
        group_addr: Group address (0xc000 ~ 0xffff)
    """
    return AsyncATCommand("MSAA", [node_addr, str(element_idx), model_id, group_addr])


def async_cmd_remove_subscription(
    node_addr: str,
    element_idx: int,
    model_id: str,
    group_addr: str
) -> AsyncATCommand:
    """
    Remove subscription from model: AT+MSAD <dst> <element_index> <model_id> <Group_addr>

    Args:
        node_addr: Node unicast address (dst)
        element_idx: Element index
        model_id: Model ID
        group_addr: Group address
    """
    return AsyncATCommand("MSAD", [node_addr, str(element_idx), model_id, group_addr])


def async_cmd_send_vendor_data(
    dst_addr: str,
    element_index: int = 0,
    app_key_idx: int = 0,
    ack: int = 0,
    data: str = ""
) -> AsyncATCommand:
    """
    Send vendor model data: AT+MDTS <dst> <element_index> <app_key_idx> <ack> <data(1~20bytes)>

    Args:
        dst_addr: Destination address (unicast or group)
        element_index: Element index (default: 0)
        app_key_idx: AppKey index (default: 0)
        ack: Acknowledgment required (1=yes, 0=no, default: 0)
        data: Hex data string (1-20 bytes)

    Example:
        >>> # Send vendor data without ACK
        >>> cmd = async_cmd_send_vendor_data("0x0100", 0, 0, 1, "0x1122335566778899")
    """
    return AsyncATCommand("MDTS", [dst_addr, str(element_index), str(app_key_idx), str(ack), data])
