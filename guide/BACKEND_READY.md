# ✅ 後端已準備就緒 - 測試指南

## 🎉 已完成的工作

### 1. ✅ API 端點實現

**已實現的端點**：

- `GET /` - 健康檢查
- `GET /img` - 靜態圖片服務（已修正路徑）
- `GET /test_db` - 資料庫連接測試
- **`GET /dissociate/terms/<term_a>/<term_b>`** - 詞彙解離查詢 ⭐ 新實現
- **`GET /dissociate/locations/<x1_y1_z1>/<x2_y2_z2>`** - 座標解離查詢 ⭐ 新實現

### 2. ✅ 部署配置檔案

- `render.yaml` - Render Blueprint 配置（一鍵部署）
- `Procfile` - 備用啟動配置
- `requirements.txt` - 更新所有依賴項並添加版本號

### 3. ✅ 文件和工具

- `DATABASE_SETUP.md` - 詳細的資料庫設置指南
- `DEPLOYMENT_QUICKSTART.md` - 快速部署步驟
- `PROJECT_STRUCTURE.md` - 完整專案結構說明
- `test_endpoints.py` - 自動化測試腳本

## 🧪 本機測試步驟

在部署到 Render 之前，你可以先在本機測試後端功能。

### 前置條件

```bash
# 1. 安裝依賴
pip install -r requirements.txt

# 2. 設置資料庫（假設你已有本機 PostgreSQL）
# 或直接使用 Render 的資料庫 URL 進行測試
export DB_URL="postgresql://USER:PASSWORD@HOST:PORT/DATABASE"
```

### 本機運行 Flask 應用

```bash
# 開發模式
flask --app src.app run --debug --port 5000

# 或使用 gunicorn（模擬生產環境）
gunicorn src.app:app --bind 0.0.0.0:5000 --workers 2
```

### 測試端點（本機）

開啟另一個終端，執行：

```bash
# 健康檢查
curl http://localhost:5000/

# 資料庫測試（需要先填充資料庫）
curl http://localhost:5000/test_db

# 靜態圖片
curl http://localhost:5000/img --output test_amygdala.gif

# 詞彙解離（需要先填充資料庫）
curl http://localhost:5000/dissociate/terms/posterior_cingulate/ventromedial_prefrontal

# 座標解離（需要先填充資料庫）
curl http://localhost:5000/dissociate/locations/0_-52_26/-2_50_-6
```

## 🚀 Render 部署測試步驟

### 步驟 1: 創建並填充資料庫

```bash
# 1. 在 Render Dashboard 創建 PostgreSQL 資料庫
# 2. 複製資料庫 URL

# 3. 檢查資料庫連接和擴展
python src/check_db.py --url "postgresql://USER:PASSWORD@HOST:PORT/DATABASE"

# 4. 填充資料庫（這會需要 10-30 分鐘）
python src/create_db.py \
  --url "postgresql://USER:PASSWORD@HOST:PORT/DATABASE" \
  --data-dir ./data \
  --schema ns \
  --if-exists replace
```

**預期輸出**：
```
✅ server_version: PostgreSQL 15.x
✅ current_database: neurosynth_db
📦 loading Parquet files...
📐 shapes -> coordinates: (12345, 4), metadata: (678, 20), annotations: (1000, 300)
=== Build: coordinates ===
→ coordinates: preparing dataframe
→ coordinates (POINTZ + GIST) done.
=== Build: metadata ===
→ metadata (FTS + trigger) done.
=== Build: annotations ===
   … copied 50,000 rows (cumulative 50,000)
→ annotations_terms total inserted: XXX,XXX
=== Ready ===
```

### 步驟 2: 部署 Web Service

**方法 A: 使用 Blueprint（推薦）**

1. 提交並推送代碼到 GitHub
2. 在 Render Dashboard: **New +** → **Blueprint**
3. 連接你的 repository
4. 修改 Blueprint 配置中的 `DB_URL` 為你的資料庫 URL
5. 點擊 **Apply**

**方法 B: 手動部署**

1. 在 Render Dashboard: **New +** → **Web Service**
2. 連接你的 repository
3. 配置：
   - Name: `ns-nano`
   - Build Command: `pip install -r requirements.txt`
   - Start Command: `gunicorn src.app:app --bind 0.0.0.0:$PORT --workers 2 --timeout 120`
4. 添加環境變數: `DB_URL` = 你的資料庫 URL
5. 點擊 **Create Web Service**

### 步驟 3: 測試部署的應用

等待部署完成（約 3-5 分鐘），然後運行測試腳本：

```bash
# 使用自動化測試腳本
python test_endpoints.py https://ns-nano.onrender.com
```

**或手動測試**：

```bash
# 健康檢查
curl https://ns-nano.onrender.com/
# 預期: <p>Server working!</p>

# 資料庫連接測試
curl https://ns-nano.onrender.com/test_db
# 預期: JSON with "ok": true

# 詞彙解離 - 方向 A
curl https://ns-nano.onrender.com/dissociate/terms/posterior_cingulate/ventromedial_prefrontal
# 預期: JSON with studies array

# 詞彙解離 - 方向 B
curl https://ns-nano.onrender.com/dissociate/terms/ventromedial_prefrontal/posterior_cingulate
# 預期: JSON with different studies array

# 座標解離 - PCC vs vmPFC
curl https://ns-nano.onrender.com/dissociate/locations/0_-52_26/-2_50_-6
# 預期: JSON with studies array

# 座標解離 - vmPFC vs PCC
curl https://ns-nano.onrender.com/dissociate/locations/-2_50_-6/0_-52_26
# 預期: JSON with different studies array
```

## 📊 預期測試結果

### ✅ 成功的回應範例

#### `/test_db`
```json
{
  "ok": true,
  "dialect": "postgresql",
  "version": "PostgreSQL 15.x...",
  "coordinates_count": 12345,
  "metadata_count": 678,
  "annotations_terms_count": 123456,
  "coordinates_sample": [
    {"study_id": "study001", "x": 0.0, "y": -52.0, "z": 26.0}
  ],
  "metadata_sample": [...],
  "annotations_terms_sample": [
    {"study_id": "study001", "contrast_id": "c01", "term": "posterior_cingulate", "weight": 0.85}
  ]
}
```

#### `/dissociate/terms/posterior_cingulate/ventromedial_prefrontal`
```json
{
  "term_a": "posterior_cingulate",
  "term_b": "ventromedial_prefrontal",
  "dissociation": "posterior_cingulate \\ ventromedial_prefrontal",
  "count": 42,
  "studies": [
    "study001",
    "study023",
    "study045",
    ...
  ]
}
```

#### `/dissociate/locations/0_-52_26/-2_50_-6`
```json
{
  "location_a": {"x": 0, "y": -52, "z": 26},
  "location_b": {"x": -2, "y": 50, "z": -6},
  "dissociation": "[0, -52, 26] \\ [-2, 50, -6]",
  "radius_mm": 10.0,
  "count": 15,
  "studies": [
    "study005",
    "study012",
    ...
  ]
}
```

### ❌ 常見錯誤和解決方案

#### 錯誤 1: `{"error": "Missing DB_URL..."}`
**原因**: 環境變數未設置  
**解決**: 在 Render Web Service → Environment 添加 `DB_URL`

#### 錯誤 2: `/test_db` 返回 `"ok": false`
**原因**: 資料庫未填充或連接失敗  
**解決**: 
1. 檢查資料庫 URL 是否正確
2. 執行 `create_db.py` 填充資料

#### 錯誤 3: `/dissociate/terms/...` 返回 `{"studies": []}`
**可能原因**:
- 資料庫中沒有該 term 的資料
- Term 格式錯誤（應使用 `_` 而非空格）

**解決**: 
1. 訪問 `/test_db` 查看 `annotations_terms_sample` 中有哪些 terms
2. 使用實際存在的 term 進行測試

#### 錯誤 4: `/dissociate/locations/...` 返回 `{"studies": []}`
**可能原因**:
- 搜尋半徑內沒有座標點
- 座標格式錯誤

**解決**: 
1. 訪問 `/test_db` 查看 `coordinates_sample` 中的實際座標
2. 使用實際存在的座標進行測試
3. 可以嘗試增大搜尋半徑（需修改 `app.py` 中的 `radius` 參數）

## 🔍 API 查詢邏輯說明

### 詞彙解離 (Term Dissociation)

查詢邏輯：`A \ B` = 包含 A 但不包含 B 的研究

```sql
SELECT DISTINCT study_id
FROM ns.annotations_terms
WHERE term = 'A'
EXCEPT
SELECT DISTINCT study_id
FROM ns.annotations_terms
WHERE term = 'B'
```

**範例應用**：
- 找出只涉及「後扣帶皮層」但不涉及「腹內側前額葉」的研究
- 用於區分不同認知功能的神經基礎

### 座標解離 (Location Dissociation)

查詢邏輯：接近座標 A（半徑 10mm）但不接近座標 B 的研究

```sql
WITH near_a AS (
  SELECT DISTINCT study_id
  FROM ns.coordinates
  WHERE ST_3DDistance(geom, ST_MakePoint(x1, y1, z1)) <= 10.0
),
near_b AS (
  SELECT DISTINCT study_id
  FROM ns.coordinates
  WHERE ST_3DDistance(geom, ST_MakePoint(x2, y2, z2)) <= 10.0
)
SELECT study_id FROM near_a
EXCEPT
SELECT study_id FROM near_b
```

**範例應用**：
- 找出激活 PCC [0, -52, 26] 但不激活 vmPFC [-2, 50, -6] 的研究
- 用於研究 Default Mode Network 的功能解離

## 📚 下一步

### 已完成 ✅
- [x] 實現 dissociate API 端點
- [x] 修正靜態檔案路徑
- [x] 創建 Render 部署配置
- [x] 更新依賴清單
- [x] 撰寫完整文件

### 你現在可以：

1. **測試本機運行** （如果有本機 PostgreSQL）
2. **部署到 Render**
   - 創建資料庫
   - 填充資料（運行 `create_db.py`）
   - 部署 Web Service
3. **測試部署的 API**
   - 運行 `test_endpoints.py`
   - 或手動測試各端點
4. **分享 API URL**
   - 你的 API 將在 `https://ns-nano.onrender.com` 上線

### 可選的後續工作：

- [ ] 添加 CORS 支援（如果需要前端）
- [ ] 實現速率限制（生產環境）
- [ ] 添加 API 認證（如果需要）
- [ ] 設置自訂域名
- [ ] 配置監控和告警
- [ ] 編寫更多單元測試

## 📞 需要幫助？

如果遇到任何問題：

1. **檢查日誌**: Render Dashboard → 你的服務 → Logs
2. **檢查資料庫**: 訪問 `/test_db` 端點
3. **查閱文件**: 
   - `DATABASE_SETUP.md` - 資料庫問題
   - `DEPLOYMENT_QUICKSTART.md` - 部署問題
   - `PROJECT_STRUCTURE.md` - 架構問題

---

**後端已準備就緒！** 🚀 現在你可以開始測試和部署了。

