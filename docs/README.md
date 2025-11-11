# 開發文件索引

本目錄包含 BleMeshProvisioner SDK 的開發過程文件和技術報告。

## 架構遷移文件

### AsyncIO 遷移
- **[ASYNCIO_REFACTOR_REPORT.md](ASYNCIO_REFACTOR_REPORT.md)**: AsyncIO 架構重構計畫
- **[ASYNCIO_MIGRATION_COMPLETE.md](ASYNCIO_MIGRATION_COMPLETE.md)**: AsyncIO 遷移完成報告

### AT 指令修正
- **[AT_COMMAND_REVIEW.md](AT_COMMAND_REVIEW.md)**: AT 指令規格審查
- **[AT_COMMAND_FIX_REPORT.md](AT_COMMAND_FIX_REPORT.md)**: AT 指令名稱修正報告
- **[AT_COMMAND_FIX_COMPLETE.md](AT_COMMAND_FIX_COMPLETE.md)**: AT 指令修正完成報告

## 測試報告

- **[HARDWARE_TEST_REPORT.md](HARDWARE_TEST_REPORT.md)**: 硬體測試報告
- **[AT_NL_TEST_REPORT.md](AT_NL_TEST_REPORT.md)**: AT+NL 指令測試報告
- **[TEST_FIX_REPORT.md](TEST_FIX_REPORT.md)**: 測試修正報告

## 開發狀態

- **[DEVELOPMENT_STATUS.md](DEVELOPMENT_STATUS.md)**: 專案開發狀態追蹤

## 設計文件

- **[PROVISIONER_CLI_DESIGN.md](PROVISIONER_CLI_DESIGN.md)**: CLI 工具設計文檔
- **[MeshProvisioner_mamager.md](MeshProvisioner_mamager.md)**: Provisioner Manager 設計

## 文件使用指南

### 新開發者
建議閱讀順序：
1. [ASYNCIO_MIGRATION_COMPLETE.md](ASYNCIO_MIGRATION_COMPLETE.md) - 了解當前架構
2. [AT_COMMAND_FIX_COMPLETE.md](AT_COMMAND_FIX_COMPLETE.md) - 了解 AT 指令規格
3. [HARDWARE_TEST_REPORT.md](HARDWARE_TEST_REPORT.md) - 了解硬體測試狀態

### 維護開發者
重點文件：
- [DEVELOPMENT_STATUS.md](DEVELOPMENT_STATUS.md) - 追蹤當前開發進度
- [PROVISIONER_CLI_DESIGN.md](PROVISIONER_CLI_DESIGN.md) - 了解未來開發方向

### 問題排查
- [TEST_FIX_REPORT.md](TEST_FIX_REPORT.md) - 常見問題和解決方案
- [AT_NL_TEST_REPORT.md](AT_NL_TEST_REPORT.md) - NL 指令特定問題

## 相關文件

專案根目錄的重要文件：
- [../README.md](../README.md) - 專案總覽和快速開始
- [../PROVISIONING_FLOW.md](../PROVISIONING_FLOW.md) - 綁定流程說明
- [../PROV_ADDRESS_ALLOCATION.md](../PROV_ADDRESS_ALLOCATION.md) - 地址分配機制
- [../CHANGELOG.md](../CHANGELOG.md) - 版本變更記錄
- [../SDK_DOC/](../SDK_DOC/) - SDK 參考文件
