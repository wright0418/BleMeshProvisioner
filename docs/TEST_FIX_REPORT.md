# 測試錯誤修正報告

**修正日期**: 2025-11-10  
**版本**: 0.2.0

## 問題描述

在互動式測試中發現以下問題:

1. **Unrouted DIS messages** - 前一次掃描的殘留訊息產生警告
2. **重複掃描失敗** - 連續執行掃描時,第二次掃描會失敗
3. **掃描命令錯誤檢查** - `AT+DIS` 命令不回傳 SUCCESS,導致誤判失敗

## 根本原因

### 1. 掃描未正確停止
```python
# 問題: 掃描結束後沒有明確停止掃描
await asyncio.sleep(duration + 1)  # 只等待,沒停止
```

### 2. 錯誤的成功判斷
```python
# 問題: DIS 命令不回傳 SUCCESS,只回傳 DIS-MSG
if not result['success']:
    raise RuntimeError(f"Failed to start scan: {result.get('error')}")
```

### 3. Handler 未清理
```python
# 問題: finally 中只移除 handler,但掃描可能仍在運行
finally:
    self.listener.remove_handler('DIS', scan_handler)
```

## 修正方案

### async_provisioner_manager.py 修正

```python
async def scan_devices(self, duration: int = 10, on_device_found = None):
    """修正後的掃描方法"""
    
    # 註冊處理器
    self.listener.add_handler('DIS', scan_handler)

    try:
        # 啟動 listener
        if not self.listener._running:
            await self.listener.start()

        # 開始掃描
        logger.info(f"Starting device scan for {duration} seconds...")
        await async_cmd_start_scan(duration).execute(self.serial)

        # ✅ 修正: 移除錯誤檢查 (DIS 命令不回傳 SUCCESS)
        # ✅ 修正: 等待指定時間
        await asyncio.sleep(duration)

        # ✅ 修正: 明確停止掃描
        logger.debug("Stopping device scan...")
        await async_cmd_stop_scan().execute(self.serial)

        # ✅ 修正: 額外等待以接收最後的訊息
        await asyncio.sleep(0.5)

        # 返回結果
        async with self._scan_lock:
            devices = self._scan_results.copy()

        logger.info(f"Scan complete. Found {len(devices)} devices")
        return devices

    finally:
        # ✅ 修正: 確保掃描已停止
        try:
            await async_cmd_stop_scan().execute(self.serial)
        except Exception as e:
            logger.debug(f"Error stopping scan: {e}")
        
        # 移除處理器
        self.listener.remove_handler('DIS', scan_handler)
```

## 測試結果

### 修正前
```
測試 1: 掃描成功 ✅
測試 2: 立即第二次掃描 ❌ (失敗: "Failed to start scan")
測試 3: 並發命令 ✅ (但有 10+ 個 "Unrouted message: DIS" 警告)
測試 4: 掃描 ❌ (失敗)
```

### 修正後
```
測試 1: 掃描成功 ✅ (3秒,找到 2 個設備)
測試 2: 立即第二次掃描 ✅ (3秒,找到 2 個設備)
測試 3: 並發命令 ✅ (0.015秒,無警告)
測試 4: 並發後掃描 ✅ (3秒,找到 2 個設備)
```

### 單元測試
```bash
$ python -m pytest tests/ -v --ignore=tests/test_hardware.py

14 passed, 1 skipped in 4.48s ✅
```

### 硬體測試
```bash
$ python test_dis_scan.py
測試 1: 基本掃描功能 (5秒) ✅
測試 2: 短時間掃描 (3秒) ✅
```

### 連續掃描壓力測試
```bash
$ python test_scan_fix.py

測試 1: 短掃描 (3秒) ✅ - 2 devices
測試 2: 立即第二次掃描 (3秒) ✅ - 2 devices
測試 3: 並發命令測試 ✅ - 0.015s
測試 4: 並發命令後掃描 (3秒) ✅ - 2 devices

🎉 所有測試通過!
```

## 影響範圍

### 修改的檔案
- `ble_mesh_provisioner/network/async_provisioner_manager.py` (scan_devices 方法)

### 向後兼容性
✅ 完全兼容 - API 介面未變更

### 效能影響
- 掃描時間更精確 (原: duration+1秒,現: duration+0.5秒)
- 無多餘警告訊息
- 支援立即連續掃描

## 相關測試檔案

- `test_dis_scan.py` - DIS 掃描基本測試
- `test_scan_fix.py` - 連續掃描壓力測試
- `interactive_test.py` - 互動式測試程式
- `tests/test_async_at_command.py` - 單元測試

## 總結

本次修正解決了以下問題:

✅ **問題 1**: 掃描未正確停止 → 在 finally 中確保停止掃描  
✅ **問題 2**: 錯誤的成功判斷 → 移除不必要的 success 檢查  
✅ **問題 3**: 殘留訊息警告 → 正確清理 handler 和停止掃描  
✅ **問題 4**: 不支援連續掃描 → 現在可以立即連續掃描

系統現在可以穩定運行,支援:
- 連續多次掃描
- 掃描前後執行其他命令
- 並發命令執行
- 無多餘警告訊息

**測試覆蓋率**: 21% (829 statements, 172 covered)  
**測試通過率**: 100% (14/14 tests passed)
