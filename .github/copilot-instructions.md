# AI Coding Instructions for BleMeshProvisioner SDK

## Project Overview
Python SDK for RichLink RL62M BLE Mesh Provisioner modules using UART AT commands. This project bridges BLE Mesh networks with Python applications through serial communication.

## Architecture & Key Concepts

### Core Communication Pattern
- **UART Interface**: 115200 baud, 8N1, no flow control
- **AT Command Protocol**: Commands follow `AT+COMMAND {<param>…}\r\n` format
- **Response Format**: `INDICATION {<param>…}\r\n` with SUCCESS/ERROR status
- **Mesh Network Roles**: Provisioner (this SDK) manages Device nodes (RGB lights, switches, sensors)

### Essential AT Command Categories
1. **Basic Commands**: Firmware version (`AT+VER`), module restart (`AT+RST`)
2. **Network Configuration**: Mesh clear (`AT+MCLR`), node scan (`AT+MSCAN`), provisioning (`AT+MPBADV`)
3. **Node Management**: AppKey binding, model subscription/publish configuration
4. **Data Transfer**: Vendor model commands (`AT+MDTS`), GATT passthrough

### Device Communication Protocol
See `SDK_DOC/Richlink_Mesh_Device_產品通訊格式.md`:
- **Packet Format**: `0x87 + OpCode(2) + Length(1) + Payload(1-16)`
- **Device Types**: RGB LED (0x0100), Plug (0x0200), Alarm (0x5151)
- **Command Structure**: `AT+MDTS <device_uid> 0 <hex_command>`

## Development Standards

### Code Organization (per AGENTS.md)
```python
# Expected module structure:
# ble_mesh_provisioner/
#   ├── core/           # AT command protocols
#   ├── devices/        # Device-specific implementations
#   ├── network/        # Mesh network management
#   ├── cli/            # Typer-based CLI interface
#   └── tests/          # Unit tests with mocks
```

### Key Implementation Requirements
- **OOP Design**: Device classes inherit from base provisioner interface
- **Serial Communication**: Use pySerial for UART AT command handling
- **Error Handling**: 
  - Parse SUCCESS/ERROR responses, handle timeouts
  - **Retry Policy**: Retry once on communication failure
  - **Logging**: Log all error messages with context (command, timestamp, failure reason)
- **CLI Interface**: Implement with `typer` and `rich` for user interaction
  - Start with basic device control commands
  - Incrementally add network topology management features per development phase
- **Mock Testing**: 
  - Create hardware simulation that mimics real device behavior exactly
  - Record real hardware interactions into a test database
  - Tests run without physical hardware using recorded data

### AT Command Implementation Pattern
```python
class ATCommand:
    def __init__(self, command: str, params: list = None):
        self.raw = f"AT+{command}" + (" " + " ".join(params) if params else "") + "\r\n"
    
    def parse_response(self, response: str) -> dict:
        # Parse INDICATION responses and SUCCESS/ERROR status
        pass
    
    def execute_with_retry(self, serial_port) -> dict:
        """Execute command with single retry on failure"""
        for attempt in range(2):  # Max 1 retry
            try:
                result = self.execute(serial_port)
                if result['status'] == 'SUCCESS':
                    return result
            except Exception as e:
                if attempt == 1:  # Last attempt
                    logger.error(f"Command failed: {self.raw.strip()}, Error: {e}, Time: {datetime.now()}")
                    raise
        return result
```

### Device Control Examples
```python
# RGB LED: Send 0x87 0x01 0x00 0x05 C W R G B
rgb_command = "87010005" + f"{c:02x}{w:02x}{r:02x}{g:02x}{b:02x}"
at_cmd = f"AT+MDTS {device_uid} 0 {rgb_command}"

# Plug control: Send 0x87 0x02 0x00 0x01 [0x01|0x00]
plug_command = f"870200010{'1' if on else '0'}"
```

## Critical Files to Reference
- `SDK_DOC/RL62M02_Provisioner_ATCMD.md`: Complete AT command reference
- `SDK_DOC/Richlink_Mesh_Device_產品通訊格式.md`: Device packet formats
- `AGENTS.md`: Development guidelines and requirements

## Testing Strategy
- **Unit Tests**: Mock serial communication for AT command testing
- **Integration Tests**: Record real hardware interactions for replay
- **CLI Tests**: Validate typer interface and command parsing
- **Device Simulation**: Create mock classes for each device type
- **Hardware Behavior Database**: 
  - Record actual hardware responses (commands, responses, timings)
  - Store in structured format (JSON/SQLite) for test replay
  - Tests should run identically with or without physical hardware
  - Include edge cases: timeouts, malformed responses, connection errors

## Common Patterns to Follow
1. **Command Builder**: Fluent interface for AT command construction
2. **Response Parser**: Structured parsing of INDICATION messages
3. **Device Factory**: Create device instances based on discovered node types
4. **Network State**: Track provisioned nodes and their configurations
5. **Error Recovery**: Retry mechanisms for failed AT commands

# python 開發環境設置
- 使用 uv 建構 venv 與安裝相關套件與 Python