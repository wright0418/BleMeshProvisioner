"""
Response Parser for AT command responses.

Parses INDICATION messages from the RL62M02 module.
"""

import re
from typing import Dict, List, Optional, Any
from ble_mesh_provisioner.utils.logger import setup_logger


logger = setup_logger(
    "ble_mesh_provisioner",
    level=20,
    log_file="logs/provisioner.log",
    console=True
)


class ResponseParser:
    """
    Parser for AT command responses from RL62M02 module.

    Response format: INDICATION {<param>…}\\r\\n
    - INDICATION is the message type (e.g., VER-MSG, DIS-MSG, PROV-MSG)
    - params are space-separated values
    - First param after MSG is usually SUCCESS or ERROR
    """

    @staticmethod
    def parse_response(response: str) -> Dict[str, Any]:
        """
        Parse a single response line.

        Args:
            response: Raw response string from module

        Returns:
            Dictionary with parsed response:
            {
                'type': str,         # Message type (e.g., 'VER', 'DIS', 'PROV')
                'status': str,       # 'SUCCESS', 'ERROR', or None
                'params': List[str], # Additional parameters
                'raw': str          # Original response
            }

        Example:
            >>> ResponseParser.parse_response("VER-MSG SUCCESS 1.0.0\\r\\n")
            {'type': 'VER', 'status': 'SUCCESS', 'params': ['1.0.0'], 'raw': '...'}
        """
        response = response.strip()

        if not response:
            return {
                'type': None,
                'status': None,
                'params': [],
                'raw': response
            }

        # Match pattern: TYPE-MSG [STATUS] [params...]
        # Example: VER-MSG SUCCESS 1.0.0
        # Example: DIS-MSG 655600000152 -48 123E4567E89B12D3A456655600000152
        match = re.match(r'^(\w+)-MSG\s+(.*?)$', response)

        if not match:
            logger.warning(f"Failed to parse response: {response}")
            return {
                'type': 'UNKNOWN',
                'status': None,
                'params': [response],
                'raw': response
            }

        msg_type = match.group(1)
        rest = match.group(2).strip()

        # Split parameters
        params = rest.split() if rest else []

        # Check if first param is SUCCESS or ERROR
        status = None
        if params and params[0] in ('SUCCESS', 'ERROR'):
            status = params[0]
            params = params[1:]

        result = {
            'type': msg_type,
            'status': status,
            'params': params,
            'raw': response
        }

        logger.debug(f"Parsed response: {result}")
        return result

    @staticmethod
    def parse_indication(indication: str) -> List[Dict[str, Any]]:
        """
        Parse multiple indication lines.

        Some commands return multiple responses. This method parses
        all lines and returns a list of parsed responses.

        Args:
            indication: Multi-line response string

        Returns:
            List of parsed response dictionaries

        Example:
            >>> text = "DIS-MSG SUCCESS\\r\\nDIS-MSG 655600000152 -48 UUID1\\r\\n"
            >>> ResponseParser.parse_indication(text)
            [{'type': 'DIS', 'status': 'SUCCESS', ...}, {'type': 'DIS', ...}]
        """
        lines = indication.strip().split('\n')
        results = []

        for line in lines:
            line = line.strip()
            if line:
                parsed = ResponseParser.parse_response(line)
                results.append(parsed)

        return results

    @staticmethod
    def is_success(response: Dict[str, Any]) -> bool:
        """
        Check if response indicates success.

        Args:
            response: Parsed response dictionary

        Returns:
            True if status is SUCCESS, False otherwise
        """
        return response.get('status') == 'SUCCESS'

    @staticmethod
    def is_error(response: Dict[str, Any]) -> bool:
        """
        Check if response indicates error.

        Args:
            response: Parsed response dictionary

        Returns:
            True if status is ERROR, False otherwise
        """
        return response.get('status') == 'ERROR'

    @staticmethod
    def get_param(response: Dict[str, Any], index: int, default: Any = None) -> Any:
        """
        Safely get a parameter by index.

        Args:
            response: Parsed response dictionary
            index: Parameter index (0-based)
            default: Default value if parameter doesn't exist

        Returns:
            Parameter value or default

        Example:
            >>> resp = ResponseParser.parse_response("VER-MSG SUCCESS 1.0.0")
            >>> ResponseParser.get_param(resp, 0)
            '1.0.0'
        """
        params = response.get('params', [])
        if 0 <= index < len(params):
            return params[index]
        return default
