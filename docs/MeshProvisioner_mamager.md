規劃一個 Provision Manager CLI工具
# 基本功能
1. ✅ 查詢韌體版本，與模組角色是否為 Provisioner (AT+VER, AT+MRG)
2. 📋 掃描Mesh 網路上未綁定的裝置，列出(列表編號)可綁定裝置清單，3秒後關閉掃描 (AT+DIS 1/0)
3. 📋 綁定裝置，輸入裝置UUID，選定列表編號綁定裝置 (AT+PBADVCON, AT+PROV, AT+AKA, AT+MAKB)
4. 📋 如果沒有綁定到AT+MAKB完成綁定，則執行AT+NR <unicast id> 移除綁定 
5. 📋 列出已綁定裝置清單 (AT+NL)
6. 📋 解除綁定裝置功能，輸入列表編號解除 (AT+NR)

7. 📋 設定推播與取消推播功能 (AT+MPAS, AT+MPAD)
8. 📋 設定訂閱與取消訂閱功能 (AT+MSAA, AT+MSAD)
9. 📋 查詢裝置設定推播與訂閱狀態

10. 📋 Provisioner持續接收 MDTG , MDTPG 等網路訊息並顯示在終端機上

# 實作狀態

## Phase 1: 核心通訊層 ✅ (完成)
- ✅ SerialInterface - UART 串口通訊
- ✅ ATCommand - AT 指令封裝與執行
- ✅ ResponseParser - 回應解析
- ✅ Logger - 日誌系統
- ✅ Mock 測試框架
- ✅ 16 個單元測試通過

## Phase 2: Provisioner Manager 📋 (下一步)
- [ ] ProvisionerManager 類別
- [ ] 實作功能 1-6
- [ ] 實作功能 7-9
- [ ] 單元測試

## Phase 3: CLI 工具 📋 (規劃完成)
詳見 [PROVISIONER_CLI_DESIGN.md](PROVISIONER_CLI_DESIGN.md)
- [ ] `provisioner-cli info` - 功能 1
- [ ] `provisioner-cli scan` - 功能 2
- [ ] `provisioner-cli provision` - 功能 3-4
- [ ] `provisioner-cli list` - 功能 5
- [ ] `provisioner-cli unprovision` - 功能 6
- [ ] `provisioner-cli publish` - 功能 7
- [ ] `provisioner-cli subscribe` - 功能 8
- [ ] `provisioner-cli config` - 功能 9
- [ ] `provisioner-cli monitor` - 功能 10

## Phase 4: Message Listener 📋
- [ ] MessageListener 類別
- [ ] 背景執行緒監聽
- [ ] 即時訊息顯示

---
更新: 2025-11-09 | 進度: Phase 1 完成 (20%)