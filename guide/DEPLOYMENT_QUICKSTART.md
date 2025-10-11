# Render 部署快速開始指南

這是一個簡化的部署指南，幫助你快速將 Neurosynth Backend 部署到 Render。

## 🚀 快速部署流程

### 步驟 1: 準備 GitHub Repository

```bash
# 確保所有檔案都已提交
git add .
git commit -m "Prepare for Render deployment"
git push origin master
```

### 步驟 2: 在 Render 創建 PostgreSQL 資料庫

1. 登入 [Render Dashboard](https://dashboard.render.com/)
2. 點擊 **"New +"** → **"PostgreSQL"**
3. 配置：
   - **Name**: `ns-nano-db`
   - **Database**: `neurosynth_db`
   - **Region**: Oregon (或其他)
   - **Plan**: Free
4. 點擊 **"Create Database"**
5. **重要**：複製 **"External Database URL"** (格式: `postgresql://...`)

### 步驟 3: 填充資料庫（本機執行）

```bash
# 1. 安裝依賴
pip install -r requirements.txt

# 2. 檢查資料庫連接（將 URL 替換為你的資料庫 URL）
python3 src/check_db.py --url "postgresql://neurosynth_db_oche_user:TMD9aHemvX3i7k2SmheqAngKGyRlhOSk@dpg-d3kvohr3fgac73a5oed0-a.oregon-postgres.render.com/neurosynth_db_oche"

# 3. 填充資料庫（這可能需要 10-30 分鐘）
python3 src/create_db.py \
  --url "postgresql://neurosynth_db_oche_user:TMD9aHemvX3i7k2SmheqAngKGyRlhOSk@dpg-d3kvohr3fgac73a5oed0-a.oregon-postgres.render.com/neurosynth_db_oche" \
  --data-dir ./data \
  --schema ns
```

**注意**：確保你的 `data/` 目錄包含以下檔案：
- `coordinates.parquet`
- `metadata.parquet`
- `annotations.parquet`

### 步驟 4: 部署 Web Service 到 Render

#### 方法 A: 使用 Blueprint（推薦）

1. 在 Render Dashboard 點擊 **"New +"** → **"Blueprint"**
2. 連接你的 GitHub repository
3. Render 會自動讀取 `render.yaml` 並配置服務
4. **重要**：在 Blueprint 配置中，手動設置 `DB_URL` 環境變數：
   - 使用你在步驟 2 複製的資料庫 URL
5. 點擊 **"Apply"** 開始部署

#### 方法 B: 手動創建 Web Service

1. 在 Render Dashboard 點擊 **"New +"** → **"Web Service"**
2. 連接你的 GitHub repository
3. 配置：
   - **Name**: `ns-nano`
   - **Environment**: `Python 3`
   - **Branch**: `master`
   - **Build Command**: `pip install -r requirements.txt`
   - **Start Command**: `gunicorn src.app:app --bind 0.0.0.0:$PORT --workers 2 --timeout 120`
4. 添加環境變數：
   - **Key**: `DB_URL`
   - **Value**: 你的資料庫 URL（從步驟 2）
5. 點擊 **"Create Web Service"**

### 步驟 5: 測試部署

等待部署完成（可能需要幾分鐘），然後測試你的 API：

```bash
# 使用測試腳本（推薦）
python3 test_endpoints.py https://ns-nano.onrender.com

# 或手動測試
curl https://ns-nano.onrender.com/
curl https://ns-nano.onrender.com/test_db
curl https://ns-nano.onrender.com/dissociate/terms/posterior_cingulate/ventromedial_prefrontal
curl https://ns-nano.onrender.com/dissociate/locations/0_-52_26/-2_50_-6
```

## ✅ 確認清單

- [ ] GitHub repository 已更新並推送
- [ ] Render PostgreSQL 資料庫已創建
- [ ] 資料庫已填充（check_db.py + create_db.py）
- [ ] Web Service 已部署到 Render
- [ ] 環境變數 `DB_URL` 已設置
- [ ] 所有端點測試通過

## 📝 重要端點

| 端點 | 說明 |
|------|------|
| `GET /` | 健康檢查 |
| `GET /img` | 靜態圖片 (amygdala.gif) |
| `GET /test_db` | 資料庫連接測試 |
| `GET /dissociate/terms/<term_a>/<term_b>` | 詞彙解離查詢 |
| `GET /dissociate/locations/<x1_y1_z1>/<x2_y2_z2>` | 座標解離查詢 |

## 🔧 常見問題

### 問題：部署失敗，顯示 "Missing DB_URL"

**解決方案**：在 Render Web Service 的 Environment 頁面添加 `DB_URL` 環境變數。

### 問題：`/test_db` 返回錯誤或空資料

**解決方案**：
1. 檢查資料庫 URL 是否正確
2. 確認已執行 `create_db.py` 填充資料
3. 檢查資料庫連接是否允許外部訪問

### 問題：查詢返回空結果 `{"studies": []}`

**解決方案**：
1. 確認資料已正確載入：訪問 `/test_db` 端點查看資料統計
2. 檢查 term 參數格式：使用底線而非空格（如 `posterior_cingulate`）
3. 嘗試不同的 term 或座標組合

### 問題：Render Free Tier 限制

**說明**：
- PostgreSQL 免費版有 90 天過期限制
- Web Service 閒置 15 分鐘後會休眠（冷啟動約 30-60 秒）
- 建議升級到付費方案用於生產環境

## 📚 更多資訊

- 詳細資料庫設置：請參閱 `DATABASE_SETUP.md`
- Render 文件：https://render.com/docs
- 問題回報：請在 GitHub repository 開 issue

## 🎯 下一步

1. **設置自訂域名**（可選）：在 Render Dashboard 的 Settings → Custom Domain
2. **配置 CORS**（如果需要前端）：在 `app.py` 添加 Flask-CORS
3. **添加速率限制**（生產環境）：使用 Flask-Limiter
4. **監控和日誌**：使用 Render 的 Logs 和 Metrics 功能

---

**提示**：首次冷啟動可能較慢，建議使用 Render 的 "Keep-Alive" 功能或升級到付費方案以避免休眠。

