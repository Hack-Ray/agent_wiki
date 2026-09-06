# Personal AI Brain Skill 安裝與還原


## 若無法執行

```powershell
Set-ExecutionPolicy -Scope Process -ExecutionPolicy Bypass
```
會開啟該視窗的檔案變更權限

## install-skill.ps1

用途：

- 將 repository 內的 `personal-ai-brain` Skill 安裝到 Codex global Skills。
- 安裝前自動備份目前版本。
- 驗證安裝後檔案是否一致。
- 自動清理舊備份。

### 執行

```powershell
.\scripts\install-skill.ps1
```

預設保留最近 5 份 backup。

指定保留數量：

```powershell
.\scripts\install-skill.ps1 -KeepBackups 10
```

### Backup 命名

```text
yyyyMMdd-HHmmss-install
```

例如：

```text
20260906-131500-install
```

---

## restore-skill.ps1

用途：

- 將 Codex Global Skill 還原成先前 backup。
- 還原前會先備份目前 installed Skill。
- 還原後會驗證檔案。
- 自動清理舊備份。

### 還原最新 Backup

```powershell
.\scripts\restore-skill.ps1
```

### 指定 Backup

先查看目前備份：

```powershell
Get-ChildItem "$env:USERPROFILE\.codex\skill-backups\personal-ai-brain" -Directory
```

再指定要還原的版本：

```powershell
.\scripts\restore-skill.ps1 `
  -BackupName "20260906-131500-install"
```

指定保留數量：

```powershell
.\scripts\restore-skill.ps1 `
  -BackupName "20260906-131500-install" `
  -KeepBackups 10
```

### Restore 前 Backup 命名

```text
yyyyMMdd-HHmmss-before-restore
```

例如：

```text
20260906-140220-before-restore
```

---

# 目錄位置

Repository source：

```text
D:\agent_wiki\skills\personal-ai-brain
```

Codex runtime：

```text
%USERPROFILE%\.codex\skills\personal-ai-brain
```

Backup：

```text
%USERPROFILE%\.codex\skill-backups\personal-ai-brain
```

---

# 驗證結果

兩支 script 都會檢查：

```text
[OK]       檔案一致
[MISSING]  缺少檔案
[MISMATCH] SHA256 不一致
[EXTRA]    出現不應存在的額外檔案
```

只要驗證失敗，script 會停止並回報錯誤。

---

# 注意事項

- 只修改 repository 內的 Skill，不要直接修改 global installed copy。
- Repository Skill 是 source of truth。
- Backup 只用於快速 rollback，長期版本歷史仍由 Git 管理。
- `install-skill.ps1` 與 `restore-skill.ps1` 不會修改 Brain Core、Memory、Knowledge、Sources 或 MCP registration。
- Skill 更新後，建議開新的 Codex Session 驗證新版 Skill 是否正常載入。
- 若指定很舊的 backup 進行 restore，該舊 backup 可能在 retention cleanup 後被刪除，但已還原的 runtime Skill 不受影響。
