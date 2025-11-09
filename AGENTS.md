# Project BleMeshProvisioner
The Project is Richlink-Tech BLE Mesh Provisioner module SDK by UART AT Command

# 搭配硬體
UART connect to RL62M Provisioner Module board , Bud rate: 115200bps , 8N1 , Flow control: None

# Software Requirement
- Python 3.6+
- pySerial
- RichLink-Tech BLE Mesh Provisioner Module SDK
- RichLink-Tech BLE Mesh Device Module (RGB Light, Switch, 客製化Sensor AT CMD Command Device, etc.)
- RichLink-Tech BLE Mesh Mobile APP (Optional)
  
# 參考相關文件
- ./SDK_DOC/RL62M02_Provisioner_ATCMD.md  : RL62M02 Provisioner Module AT Command Document
- ./SDK_DOC/RL62M02_Device_ATCMD.md      : RL62M02 Device Module AT Command Document
  
# 遵守 
- 使用OOP設計方法
- EPython PEP8 Coding Style
- 模組化設計，方便擴充與維護
- 詳盡的Code註解
- 確認部分完成之後，提供單元測試程式碼，如需要硬體的部分，則提供模擬類別(Mock Class)進行單元測試，以確保程式碼品質，可以實體測試時紀錄需要的 Mock Data 以便模擬測試
- 提供範例程式碼，方便使用者了解如何使用此SDK
- 提供詳細的使用文件，方便使用者了解如何使用此SDK
- 使用 CLI (typer , rich) 介面，方便使用者操作此SDK