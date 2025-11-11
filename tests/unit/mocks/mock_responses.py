"""
Mock responses database for testing without hardware.

Contains pre-recorded responses from actual RL62M02 hardware interactions.
"""

from typing import Dict, List


# Mock responses for different AT commands
MOCK_RESPONSES: Dict[str, str] = {
    # Basic commands
    "AT+VER": "VER-MSG SUCCESS 1.0.0\r\n",
    "AT+MRG": "MRG-MSG SUCCESS PROVISIONER\r\n",
    "AT+REBOOT": "REBOOT-MSG SUCCESS\r\nSYS-MSG PROVISIONER READY\r\n",

    # Scan commands
    "AT+DIS 1": "DIS-MSG SUCCESS\r\n",
    "AT+DIS 0": "DIS-MSG SUCCESS\r\n",

    # Provisioning commands
    "AT+PBADVCON 123E4567E89B12D3A456655600000152": "PBADVCON-MSG SUCCESS\r\n",
    "AT+PBADVCON 123E4567E89B12D3A456655600000153": "PBADVCON-MSG SUCCESS\r\n",
    "AT+PBADVCON 123E4567E89B12D3A456655600000151": "PBADVCON-MSG SUCCESS\r\n",

    "AT+PROV": "PROV-MSG SUCCESS 0x0100\r\n",

    # Node configuration
    "AT+AKA 0x0100 0 0": "AKA-MSG SUCCESS\r\n",
    "AT+AKA 0x0101 0 0": "AKA-MSG SUCCESS\r\n",
    "AT+AKA 0x0102 0 0": "AKA-MSG SUCCESS\r\n",

    "AT+MAKB 0x0100 0 0x1000ffff 0": "MAKB-MSG SUCCESS\r\n",
    "AT+MAKB 0x0101 0 0x1000ffff 0": "MAKB-MSG SUCCESS\r\n",
    "AT+MAKB 0x0102 0 0x1000ffff 0": "MAKB-MSG SUCCESS\r\n",

    # Node list
    "AT+NL": (
        "NL-MSG 0 0x0100 1 1\r\n"
        "NL-MSG 1 0x0101 1 0\r\n"
        "NL-MSG 2 0x0102 1 1\r\n"
    ),

    # Node removal
    "AT+NR 0x0100": "NR-MSG SUCCESS 0x0100\r\n",
    "AT+NR 0x0101": "NR-MSG SUCCESS 0x0101\r\n",
    "AT+NR 0x0102": "NR-MSG SUCCESS 0x0102\r\n",

    # Subscription
    "AT+MSAA 0x0100 0 0x1000ffff 0xc000": "MSAA-MSG SUCCESS\r\n",
    "AT+MSAA 0x0100 0 0x1000ffff 0xc001": "MSAA-MSG SUCCESS\r\n",
    "AT+MSAD 0x0100 0 0x1000ffff 0xc000": "MSAD-MSG SUCCESS\r\n",

    # Publish
    "AT+MPAS 0x0100 0 0x1000ffff 0xc000 0": "MPAS-MSG SUCCESS\r\n",
    "AT+MPAS 0x0100 0 0x1000ffff 0x0101 0": "MPAS-MSG SUCCESS\r\n",
    "AT+MPAD 0x0100 0 0x1000ffff 0": "MPAD-MSG SUCCESS\r\n",

    # Data transfer
    "AT+MDTS 0x0100 0 0 1 0x1122335566778899": (
        "MDTS-MSG SUCCESS\r\n"
        "MDTS-MSG 0x0100 0 8\r\n"
    ),
    "AT+MDTS 0x0100 0 0 0 0x1122335566778899": "MDTS-MSG SUCCESS\r\n",

    "AT+MDTG 0x0100 0 0 3": (
        "MDTG-MSG SUCCESS\r\n"
        "MDTG-MSG 0x0100 0 112233\r\n"
    ),
}


# Mock device scan results
MOCK_SCAN_DEVICES: List[Dict[str, str]] = [
    {
        "mac": "655600000152",
        "rssi": "-48",
        "uuid": "123E4567E89B12D3A456655600000152"
    },
    {
        "mac": "655600000153",
        "rssi": "-52",
        "uuid": "123E4567E89B12D3A456655600000153"
    },
    {
        "mac": "655600000151",
        "rssi": "-45",
        "uuid": "123E4567E89B12D3A456655600000151"
    },
]


def get_mock_response(command: str) -> str:
    """
    Get mock response for a command.

    Args:
        command: AT command string (with or without \\r\\n)

    Returns:
        Mock response string

    Raises:
        KeyError: If command not found in mock database
    """
    # Normalize command
    cmd = command.strip()
    if cmd.endswith('\r\n'):
        cmd = cmd[:-2]

    if cmd in MOCK_RESPONSES:
        return MOCK_RESPONSES[cmd]

    # Try to match partial commands (for dynamic parameters)
    for key in MOCK_RESPONSES:
        if cmd.startswith(key.split()[0]):  # Match command prefix
            return MOCK_RESPONSES[key]

    raise KeyError(f"No mock response for command: {cmd}")


def get_scan_devices_response() -> str:
    """
    Generate mock scan response with multiple devices.

    Returns:
        Multi-line scan response
    """
    lines = ["DIS-MSG SUCCESS\r\n"]
    for device in MOCK_SCAN_DEVICES:
        lines.append(
            f"DIS-MSG {device['mac']} {device['rssi']} {device['uuid']}\r\n"
        )
    return "".join(lines)


# RGB LED device commands
MOCK_RGB_COMMANDS = {
    "AT+MDTS 0x0100 0 0 87010005FF000000FF": "MDTS-MSG SUCCESS\r\n",  # Red
    "AT+MDTS 0x0100 0 0 8701000500FF0000FF": "MDTS-MSG SUCCESS\r\n",  # Green
    "AT+MDTS 0x0100 0 0 870100050000FF00FF": "MDTS-MSG SUCCESS\r\n",  # Blue
    "AT+MDTS 0x0100 0 0 87010005FFFFFFFF00": "MDTS-MSG SUCCESS\r\n",  # White
}


# Plug device commands
MOCK_PLUG_COMMANDS = {
    "AT+MDTS 0x0100 0 0 87020001": "MDTS-MSG SUCCESS\r\n",  # ON
    "AT+MDTS 0x0100 0 0 87020000": "MDTS-MSG SUCCESS\r\n",  # OFF
}


# Alarm device indication
MOCK_ALARM_INDICATION = "MDTG-MSG 0x5151 0 875151\r\n"


# Error responses
MOCK_ERROR_RESPONSES = {
    "AT+PBADVCON INVALID_UUID": "PBADVCON-MSG ERROR\r\n",
    "AT+MAKB 0xFFFF 0 0x1000ffff 0": "MAKB-MSG ERROR\r\n",
    "AT+NR 0xFFFF": "NR-MSG ERROR 0xFFFF\r\n",
}


# Merge error responses into main dictionary
MOCK_RESPONSES.update(MOCK_ERROR_RESPONSES)
MOCK_RESPONSES.update(MOCK_RGB_COMMANDS)
MOCK_RESPONSES.update(MOCK_PLUG_COMMANDS)
