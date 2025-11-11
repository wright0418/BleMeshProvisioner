# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [0.2.0] - 2024-01-XX

### Added
- 完整 AsyncIO 架構實作
  - `async_serial_interface.py`: 非同步串口通訊介面
  - `async_at_command.py`: 非同步 AT 指令執行
  - 支援 `async`/`await` 語法
  - Future-based 指令回應機制
  - asyncio.Queue 實作通知訊息佇列

- 所有 14 種 AT 指令支援
  - **基礎指令**: AT+VER, AT+RST, AT+MCLR
  - **掃描綁定**: AT+DIS, AT+PBADVCON, AT+PROV
  - **AppKey 管理**: AT+AKA, AT+MAKB
  - **節點管理**: AT+NL
  - **訂閱管理**: AT+MSAA, AT+MSAD
  - **發布管理**: AT+MPAS, AT+MPAD
  - **資料傳輸**: AT+MDTS

- 完整綁定流程測試
  - `test_provisioning_flow.py`: 端對端綁定測試
  - 流程: DIS → PBADVCON → PROV → AKA → MAKB → MSAA/MPAS
  - 自動解析 PROV 回傳的實際分配位址

- 功能測試程式
  - `test_nl.py`: 節點列表查詢測試
  - `test_subscription.py`: 訂閱管理測試 (MSAA/MSAD)
  - `test_publish.py`: 發布管理測試 (MPAS/MPAD)
  - `test_basic_commands.py`: 基礎指令驗證
  - `test_commands_validation.py`: 指令格式驗證

- 文件組織
  - 建立 `docs/` 目錄存放開發文件
  - 移動 11 個開發記錄文件至 `docs/`
  - 更新 README.md 包含 AsyncIO 範例和完整指令清單

### Changed
- AT 指令名稱修正 (11 處)
  - MLN → NL (節點列表)
  - MSCAN → DIS (裝置掃描)
  - MPBADV → PBADVCON (綁定連線)
  - MPROV → PROV (綁定分配位址)
  - MAKA → AKA (新增 AppKey)
  - MMAKB → MAKB (綁定 Model AppKey)
  - MMSAA → MSAA (新增訂閱)
  - MMSAD → MSAD (刪除訂閱)
  - MMPAS → MPAS (設定發布)
  - MMPAD → MPAD (清除發布)
  - MMDTS → MDTS (傳送資料)

- AT 指令參數修正
  - AT+MSAA: Model ID 必須與 MAKB 一致
  - AT+MPAS: Model ID 必須與 MAKB 一致
  - AT+PROV: 回傳實際分配的 unicast address

### Fixed
- 修正 DIS 通知訊息路由問題
  - DIS-MSG 未正確路由至通知佇列
  - 新增 DIS-MSG 至 `_notification_patterns`

- 修正 NL 通知訊息路由問題
  - NL-MSG 顯示 "Unrouted message: NL"
  - 新增 NL-MSG 至 `_notification_patterns`

- 修正 PROV 位址分配機制
  - test_step_3_prov() 現在回傳實際分配位址
  - 後續步驟 (AKA/MAKB/MSAA/MPAS) 使用實際位址

- 統一 Model ID 使用
  - 所有測試使用統一的 Model ID: 0x4005D

### Removed
- 刪除重複/除錯測試檔案 (9 個)
  - test_dis_debug.py
  - test_dis_scan.py
  - test_nl_fix.py
  - test_scan_fix.py
  - test_model_id_consistency.py
  - test_prov_response.py
  - interactive_test.py
  - quick_test.py
  - test_menu.py

### Hardware Tested
- **Module**: RichLink RL62M02 Provisioner
- **Firmware**: v1.0.6
- **Interface**: UART COM17, 115200 baud, 8N1
- **Devices**: 2 nodes provisioned (0x0100, 0x0101)
- **Status**: All AT commands verified ✅

## [0.1.0] - 2024-01-XX

### Added
- 初始專案建立
- 同步版本 AT 指令實作
- 基礎串口通訊功能
- Mock 測試框架

---

## Legend
- **Added**: 新增功能
- **Changed**: 變更既有功能
- **Deprecated**: 即將移除的功能
- **Removed**: 已移除的功能
- **Fixed**: 錯誤修正
- **Security**: 安全性修正
