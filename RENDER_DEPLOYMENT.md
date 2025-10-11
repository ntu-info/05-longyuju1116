# Render 部署詳細指南

本指南提供**兩種部署方式**，推薦使用方式 1（更穩定可靠）。

---

## 🎯 方式 1：分步驟部署（推薦）⭐

這種方式更可控，適合初次部署或需要調試的情況。

### 步驟 1: 創建 PostgreSQL 資料庫

1. 登入 [Render Dashboard](https://dashboard.render.com/)
2. 點擊 **"New +"** → **"PostgreSQL"**
3. 配置資料庫：
   ```
   Name: ns-nano-db
   Database: neurosynth_db
   User: neurosynth_user
   Region: Oregon (或任何你喜歡的區域)
   Instance Type: Free
   ```
4. 點擊 **"Create Database"**
5. 等待資料庫創建完成（約 1-2 分鐘）
6. **重要**：在資料庫頁面找到 **"Connections"** 區域，複製 **"External Database URL"**
   - 格式類似：`postgresql://neurosynth_user:xxxxx@dpg-xxxxx-a.oregon-postgres.render.com/neurosynth_db`
   - **保存這個 URL**，後面會用到

### 步驟 2: 填充資料庫（本機執行）

在你的專案目錄執行以下命令：

```bash
# 1. 確保已安裝依賴
pip install -r requirements.txt

# 2. 檢查資料庫連接和擴展
python src/check_db.py --url "postgresql://你的資料庫URL"

# 3. 填充資料庫（需要 10-30 分鐘，取決於資料大小）
python src/create_db.py \
  --url "postgresql://你的資料庫URL" \
  --data-dir ./data \
  --schema ns \
  --if-exists replace
```

**預期輸出**：
```
✅ server_version: PostgreSQL 15.x
✅ current_database: neurosynth_db
📦 loading Parquet files...
→ coordinates (POINTZ + GIST) done.
→ metadata (FTS + trigger) done.
→ annotations_terms total inserted: XXX,XXX
=== Ready ===
```

### 步驟 3: 使用 Blueprint 部署 Web Service

```bash
# 1. 確保所有變更已推送到 GitHub
git add render.yaml
git commit -m "Add simplified render.yaml for manual database setup"
git push origin master
```

2. 在 Render Dashboard 點擊 **"New +"** → **"Blueprint"**
3. 選擇 **"Connect a repository"**
4. 找到並選擇你的 repository: `ntu-info/05-longyuju1116`
5. Render 會自動讀取 `render.yaml` 並顯示配置預覽
6. 在預覽頁面中，找到 **Environment Variables** 區域
7. 設置 `DB_URL` 的值：
   - 點擊 `DB_URL` 旁邊的編輯按鈕
   - 貼上你在步驟 1 複製的資料庫 URL
8. 點擊 **"Apply"** 開始部署

### 步驟 4: 測試部署

等待部署完成（約 3-5 分鐘），然後測試：

```bash
# 使用測試腳本
python test_endpoints.py https://ns-nano.onrender.com

# 或手動測試
curl https://ns-nano.onrender.com/
curl https://ns-nano.onrender.com/test_db
curl https://ns-nano.onrender.com/dissociate/terms/posterior_cingulate/ventromedial_prefrontal
```

---

## 🚀 方式 2：一鍵全自動部署（進階）

使用 `render.full.yaml` 同時創建資料庫和 Web Service。

### 注意事項
- 這種方式需要在 Render Dashboard 手動上傳 Blueprint YAML
- 資料庫會自動創建，但資料填充仍需手動執行
- 如果自動連接失敗，可能需要手動設置環境變數

### 步驟

1. **準備 Blueprint 檔案**
   ```bash
   # 將 render.full.yaml 重命名為 render.yaml（如果想使用此方式）
   cp render.full.yaml render.yaml
   git add render.yaml
   git commit -m "Use full Blueprint with database"
   git push origin master
   ```

2. **在 Render 使用 Blueprint**
   - Dashboard → New + → Blueprint
   - 連接你的 repository
   - Render 會讀取 `render.yaml` 並創建：
     - PostgreSQL 資料庫
     - Web Service
     - 環境變數自動連接

3. **填充資料庫**
   - 等待資料庫創建完成
   - 從 Render Dashboard 獲取資料庫 URL
   - 本機執行：
     ```bash
     python src/create_db.py --url "資料庫URL" --data-dir ./data --schema ns
     ```

4. **測試部署**
   ```bash
   python test_endpoints.py https://ns-nano.onrender.com
   ```

---

## 🔧 方式 3：完全手動創建（最基本）

不使用 Blueprint，完全手動在 Render UI 中創建。

### 步驟

1. **創建 PostgreSQL 資料庫**（同方式 1 步驟 1）

2. **填充資料庫**（同方式 1 步驟 2）

3. **手動創建 Web Service**
   - Dashboard → New + → Web Service
   - 連接你的 GitHub repository
   - 配置：
     ```
     Name: ns-nano
     Environment: Python 3
     Branch: master
     Build Command: pip install -r requirements.txt
     Start Command: gunicorn src.app:app --bind 0.0.0.0:$PORT --workers 2 --timeout 120
     ```
   - 添加環境變數：
     - Key: `DB_URL`
     - Value: 你的資料庫 URL（從步驟 1）
   - 點擊 **"Create Web Service"**

4. **測試部署**（同方式 1 步驟 4）

---

## 📊 三種方式比較

| 方式 | 難度 | 可控性 | 推薦度 | 適用情況 |
|------|------|--------|--------|----------|
| 方式 1 | ⭐⭐ | ⭐⭐⭐⭐⭐ | ⭐⭐⭐⭐⭐ | 初次部署、需要調試 |
| 方式 2 | ⭐⭐⭐⭐ | ⭐⭐⭐ | ⭐⭐⭐ | 熟悉 Render、快速部署 |
| 方式 3 | ⭐ | ⭐⭐⭐⭐⭐ | ⭐⭐⭐⭐ | 不熟悉 YAML、喜歡 UI |

---

## ✅ 部署檢查清單

無論使用哪種方式，請確認：

- [ ] GitHub repository 已更新並推送
- [ ] PostgreSQL 資料庫已創建
- [ ] 資料庫已填充（執行 `create_db.py`）
- [ ] Web Service 已部署
- [ ] 環境變數 `DB_URL` 已正確設置
- [ ] `/test_db` 端點返回 `"ok": true`
- [ ] 所有 API 端點測試通過

---

## 🐛 常見問題排查

### 問題 1: Blueprint 找不到 render.yaml

**解決**：確保 `render.yaml` 在專案根目錄，並已推送到 GitHub。

### 問題 2: DB_URL 環境變數未設置

**現象**：應用啟動失敗，日誌顯示 "Missing DB_URL"

**解決**：
- 檢查 Render Web Service → Environment 頁面
- 手動添加 `DB_URL` 環境變數
- 重新部署

### 問題 3: /test_db 返回錯誤

**現象**：`{"ok": false, "error": "..."}`

**可能原因**：
1. 資料庫未填充
2. 資料庫 URL 錯誤
3. 資料庫連接被拒絕

**解決**：
1. 檢查資料庫 URL 格式
2. 確認已執行 `create_db.py`
3. 檢查 Render 資料庫的 IP 白名單設置

### 問題 4: Gunicorn 啟動失敗

**現象**：部署日誌顯示 "ModuleNotFoundError: No module named 'src'"

**解決**：
- 確認啟動命令為：`gunicorn src.app:app --bind 0.0.0.0:$PORT`
- 確認 `src/app.py` 檔案存在
- 檢查專案結構是否正確

### 問題 5: 冷啟動太慢

**現象**：Free tier 閒置 15 分鐘後休眠，首次請求需等待 30-60 秒

**解決方案**：
- 升級到付費方案避免休眠
- 使用外部監控服務定期 ping 你的應用
- 接受 Free tier 的限制

---

## 📚 相關文件

- [DEPLOYMENT_QUICKSTART.md](DEPLOYMENT_QUICKSTART.md) - 快速部署總覽
- [DATABASE_SETUP.md](DATABASE_SETUP.md) - 詳細資料庫設置
- [BACKEND_READY.md](BACKEND_READY.md) - 測試指南
- [Render 官方文檔](https://render.com/docs)

---

## 💡 推薦流程

**對於你的情況，我推薦：**

1. ✅ 使用**方式 1**（分步驟部署）
2. ✅ 先手動創建資料庫
3. ✅ 本機填充資料
4. ✅ 使用簡化版 `render.yaml`（已修正）部署 Web Service
5. ✅ 在 Blueprint 預覽頁面設置 `DB_URL`

這樣最穩定可靠，問題也最容易排查！

---

**準備好了嗎？開始部署吧！** 🚀

