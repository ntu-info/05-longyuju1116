# Neurosynth Backend - 專案結構

## 📁 目錄結構

```
05-longyuju1116/
├── data/                          # 資料檔案目錄
│   ├── annotations.parquet        # 詞彙標註資料
│   ├── coordinates.parquet        # MNI 座標資料
│   └── metadata.parquet           # 研究元數據
│
├── src/                           # 源代碼目錄
│   ├── app.py                     # Flask 應用主程式
│   ├── check_db.py                # 資料庫連接檢查工具
│   └── create_db.py               # 資料庫建立與填充工具
│
├── amygdala.gif                   # 示例靜態圖片
├── LICENSE                        # MIT 授權條款
├── README.md                      # 專案說明文件
├── requirements.txt               # Python 依賴清單
│
├── render.yaml                    # Render 部署配置（Blueprint）
├── Procfile                       # 備用啟動配置
│
├── DATABASE_SETUP.md              # 詳細資料庫設置指南
├── DEPLOYMENT_QUICKSTART.md       # 快速部署指南
├── PROJECT_STRUCTURE.md           # 本文件
└── test_endpoints.py              # API 端點測試腳本
```

## 🔧 核心檔案說明

### `src/app.py`

Flask Web 應用程式，提供以下端點：

- **`GET /`**: 健康檢查
- **`GET /img`**: 返回靜態圖片（amygdala.gif）
- **`GET /test_db`**: 測試資料庫連接並返回統計資料
- **`GET /dissociate/terms/<term_a>/<term_b>`**: 詞彙解離查詢
- **`GET /dissociate/locations/<coords_a>/<coords_b>`**: 座標解離查詢

**關鍵功能**：
- 單例資料庫連接池
- 自動處理 `postgres://` 和 `postgresql://` URL 格式
- 完整的錯誤處理和 JSON 響應

### `src/check_db.py`

資料庫功能檢查工具，驗證：
- PostgreSQL 連接
- PostGIS 擴展
- pgvector 擴展（向量相似度）
- tsvector（全文檢索）

**使用方式**：
```bash
python src/check_db.py --url "postgresql://USER:PASSWORD@HOST:PORT/DB"
```

### `src/create_db.py`

資料庫建立和資料載入工具，執行以下任務：

1. 創建 `ns` schema
2. 啟用必要的 PostgreSQL 擴展（PostGIS, pg_trgm, unaccent）
3. 載入 Parquet 檔案到資料庫表：
   - `coordinates.parquet` → `ns.coordinates`（PostGIS POINTZ geometry）
   - `metadata.parquet` → `ns.metadata`（全文檢索支援）
   - `annotations.parquet` → `ns.annotations_terms`（稀疏格式）
4. 創建索引以優化查詢效能

**使用方式**：
```bash
python src/create_db.py \
  --url "postgresql://USER:PASSWORD@HOST:PORT/DB" \
  --data-dir ./data \
  --schema ns \
  --if-exists replace
```

**參數說明**：
- `--url`: 資料庫連接字串
- `--data-dir`: Parquet 檔案目錄（預設：`./`）
- `--schema`: 目標 schema（預設：`ns`）
- `--if-exists`: 現有表的處理方式（`replace` 或 `append`）
- `--batch-cols`: 批次處理的 term 欄位數量（預設：150）
- `--enable-json`: 是否建立 JSON 聚合表（可選，較慢）

### `render.yaml`

Render Blueprint 配置檔案，定義：
- PostgreSQL 資料庫服務配置
- Flask Web Service 配置
- 環境變數和啟動命令

**優點**：
- 一鍵部署資料庫和應用
- 自動配置環境變數
- Infrastructure as Code（IaC）

### `requirements.txt`

Python 依賴清單：

**生產依賴**：
- `Flask` - Web 框架
- `gunicorn` - WSGI 伺服器
- `SQLAlchemy` - ORM 和資料庫工具
- `psycopg2-binary` - PostgreSQL 驅動

**開發/設置依賴**：
- `pandas` - 資料處理
- `numpy` - 數值運算
- `pyarrow` - Parquet 檔案讀取

### `test_endpoints.py`

API 端點測試腳本，自動測試所有端點：

```bash
python test_endpoints.py https://ns-nano.onrender.com
```

**測試項目**：
- 健康檢查
- 靜態檔案服務
- 資料庫連接
- 詞彙解離查詢（雙向）
- 座標解離查詢（雙向）

## 🗄️ 資料庫 Schema

### `ns.coordinates`

儲存 MNI 座標資料，使用 PostGIS geometry。

| 欄位 | 類型 | 說明 |
|------|------|------|
| `study_id` | TEXT | 研究識別碼 |
| `geom` | GEOMETRY(POINTZ, 4326) | 3D 座標點（X, Y, Z） |

**索引**：
- `idx_coordinates_study` on `study_id`
- `idx_coordinates_geom_gist` (GIST) on `geom`

### `ns.metadata`

儲存研究元數據，支援全文檢索。

| 欄位 | 類型 | 說明 |
|------|------|------|
| 動態欄位 | TEXT/DOUBLE PRECISION | 依 Parquet 檔案而定 |
| `fts` | TSVECTOR | 全文檢索向量 |

**索引**：
- `idx_metadata_fts` (GIN) on `fts`

**觸發器**：
- `metadata_fts_update` - 自動更新 `fts` 欄位

### `ns.annotations_terms`

儲存研究-詞彙關聯（稀疏格式）。

| 欄位 | 類型 | 說明 |
|------|------|------|
| `study_id` | TEXT | 研究識別碼 |
| `contrast_id` | TEXT | 對比識別碼（可為 NULL） |
| `term` | TEXT | 詞彙標籤 |
| `weight` | DOUBLE PRECISION | 權重/分數 |

**索引**：
- `idx_annotations_terms_term` on `term`
- `idx_annotations_terms_study` on `study_id`
- `idx_annotations_terms_term_study` on `(term, study_id)`
- `pk_annotations_terms` (PRIMARY KEY) on `(study_id, contrast_id, term)`

## 🚀 API 端點詳細說明

### 健康檢查

```
GET /
```

**回應**：
```html
<p>Server working!</p>
```

### 靜態圖片

```
GET /img
```

**回應**：圖片檔案（image/gif）

### 資料庫測試

```
GET /test_db
```

**回應範例**：
```json
{
  "ok": true,
  "dialect": "postgresql",
  "version": "PostgreSQL 15.x...",
  "coordinates_count": 12345,
  "metadata_count": 678,
  "annotations_terms_count": 123456,
  "coordinates_sample": [...],
  "metadata_sample": [...],
  "annotations_terms_sample": [...]
}
```

### 詞彙解離查詢

```
GET /dissociate/terms/<term_a>/<term_b>
```

查詢包含 `term_a` 但**不包含** `term_b` 的研究。

**範例**：
```bash
GET /dissociate/terms/posterior_cingulate/ventromedial_prefrontal
```

**回應範例**：
```json
{
  "term_a": "posterior_cingulate",
  "term_b": "ventromedial_prefrontal",
  "dissociation": "posterior_cingulate \\ ventromedial_prefrontal",
  "count": 42,
  "studies": ["study001", "study002", ...]
}
```

**注意**：
- 詞彙使用底線（`_`）而非空格
- 查詢區分大小寫

### 座標解離查詢

```
GET /dissociate/locations/<x1_y1_z1>/<x2_y2_z2>
```

查詢接近座標 `[x1, y1, z1]` 但**不接近** `[x2, y2, z2]` 的研究。

**範例**（Default Mode Network）：
```bash
GET /dissociate/locations/0_-52_26/-2_50_-6
```

**回應範例**：
```json
{
  "location_a": {"x": 0, "y": -52, "z": 26},
  "location_b": {"x": -2, "y": 50, "z": -6},
  "dissociation": "[0, -52, 26] \\ [-2, 50, -6]",
  "radius_mm": 10.0,
  "count": 15,
  "studies": ["study001", "study005", ...]
}
```

**注意**：
- 座標使用底線（`_`）分隔
- 預設搜尋半徑：10mm（歐氏距離）
- 使用 PostGIS `ST_3DDistance` 進行 3D 空間查詢

## 🔐 環境變數

| 變數名 | 必需 | 說明 |
|--------|------|------|
| `DB_URL` | ✅ | PostgreSQL 連接字串 |
| `PORT` | ⚠️ | 伺服器埠（Render 自動設置） |
| `PYTHON_VERSION` | ❌ | Python 版本（預設 3.10） |

**`DB_URL` 格式**：
```
postgresql://USER:PASSWORD@HOST:PORT/DATABASE
```

## 📊 部署架構

```
┌─────────────────┐
│   GitHub Repo   │
└────────┬────────┘
         │
         │ Push / Deploy
         ▼
┌─────────────────┐     ┌──────────────────┐
│  Render Web     │────▶│  Render          │
│  Service        │     │  PostgreSQL DB   │
│  (Flask + Gun.) │◀────│  (ns schema)     │
└─────────────────┘     └──────────────────┘
         │
         │ HTTPS
         ▼
┌─────────────────┐
│   End Users     │
│   (API Calls)   │
└─────────────────┘
```

## 📝 開發建議

### 本機開發

```bash
# 1. 安裝依賴
pip install -r requirements.txt

# 2. 設置環境變數
export DB_URL="postgresql://USER:PASSWORD@localhost:5432/neurosynth_dev"

# 3. 運行開發伺服器
flask --app src.app run --debug --port 5000
```

### 生產部署檢查清單

- [ ] 所有 Parquet 檔案已準備好
- [ ] 資料庫已創建並填充
- [ ] `DB_URL` 環境變數已設置
- [ ] `requirements.txt` 包含所有依賴
- [ ] `render.yaml` 配置正確
- [ ] 所有端點測試通過
- [ ] 監控和日誌已設置

## 🐛 除錯技巧

### 查看 Render 日誌

在 Render Dashboard → 你的 Web Service → Logs

### 本機測試資料庫連接

```bash
python src/check_db.py --url "$DB_URL"
```

### 測試端點

```bash
# 使用測試腳本
python test_endpoints.py https://ns-nano.onrender.com

# 或使用 curl
curl -v https://ns-nano.onrender.com/test_db
```

### 常見錯誤

| 錯誤 | 可能原因 | 解決方案 |
|------|----------|----------|
| `Missing DB_URL` | 環境變數未設置 | 在 Render 設置 `DB_URL` |
| `OperationalError` | 資料庫連接失敗 | 檢查 URL、網路、防火牆 |
| `ProgrammingError: relation does not exist` | 資料表未創建 | 執行 `create_db.py` |
| `Empty results` | 資料未載入或參數錯誤 | 檢查 `/test_db`，驗證參數 |

## 📚 相關文件

- [README.md](README.md) - 專案概述和 API 說明
- [DEPLOYMENT_QUICKSTART.md](DEPLOYMENT_QUICKSTART.md) - 快速部署指南
- [DATABASE_SETUP.md](DATABASE_SETUP.md) - 詳細資料庫設置
- [Render Documentation](https://render.com/docs)
- [Flask Documentation](https://flask.palletsprojects.com/)
- [PostGIS Documentation](https://postgis.net/documentation/)

---

**維護者**: 請根據專案演進更新此文件。

