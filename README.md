# Neurosynth Backend API

[![Python](https://img.shields.io/badge/Python-3.12.2-blue.svg)](https://www.python.org/)
[![Flask](https://img.shields.io/badge/Flask-3.0+-green.svg)](https://flask.palletsprojects.com/)
[![PostgreSQL](https://img.shields.io/badge/PostgreSQL-12+-blue.svg)](https://www.postgresql.org/)
[![License](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)

A lightweight Flask backend that exposes **functional dissociation** endpoints on top of a Neurosynth-backed PostgreSQL database with PostGIS spatial extensions.

The service provides powerful APIs to query studies mentioning one concept/coordinate **but not** the other (A \ B), enabling researchers to identify distinct functional patterns in neuroimaging data.

**Live Demo**: [https://ns-nano-bzsi.onrender.com](https://ns-nano-bzsi.onrender.com)

---

## ✨ Features

- 🔬 **Term Dissociation**: Query studies by cognitive terms
- 📍 **Spatial Dissociation**: PostGIS-powered 3D coordinate queries with configurable search radius
- 🎯 **Single Location Query**: Find all studies within a specified radius of any MNI coordinate
- 🚀 **Production Ready**: Deployed with Gunicorn, optimized SQL queries with proper indexing
- 📊 **Large Dataset**: 1M+ annotations, 100K+ coordinates from Neurosynth meta-analysis database

---

## 📋 Table of Contents

- [API Endpoints](#-api-endpoints)
  - [Term-Based Dissociation](#1-term-based-dissociation)
  - [Coordinate-Based Dissociation](#2-coordinate-based-dissociation)
  - [Single Location Query](#3-single-location-query)
  - [Utility Endpoints](#4-utility-endpoints)
- [Quick Start](#-quick-start)
- [Installation](#-installation)
- [Deployment](#-deployment)
- [API Examples](#-api-examples)
- [Project Structure](#-project-structure)
- [Configuration](#-configuration)
- [Testing](#-testing)
- [Notes](#-notes)
- [License](#-license)

---

## 🔌 API Endpoints

### 1. Term-Based Dissociation

Find studies that mention one cognitive term but not another.

#### Basic Query (Auto-prefix)

```http
GET /dissociate/terms/<term_a>/<term_b>
```

**Features:**
- ✅ Automatic `terms_abstract_tfidf__` prefix handling
- ✅ Returns both original and database term names
- ✅ Bidirectional queries supported

**Example:**

```bash
# Query studies with "fear" but not "pain"
curl https://ns-nano-bzsi.onrender.com/dissociate/terms/fear/pain

# Response
{
  "term_a": "fear",
  "term_b": "pain",
  "dissociation": "fear \\ pain",
  "count": 333,
  "database_term_a": "terms_abstract_tfidf__fear",
  "database_term_b": "terms_abstract_tfidf__pain",
  "studies": ["10594068", "11239901", ...]
}
```

---

### 2. Coordinate-Based Dissociation

Find studies near one MNI coordinate but not another using PostGIS 3D spatial queries.

#### Default Radius (6mm)

```http
GET /dissociate/locations/<x1_y1_z1>/<x2_y2_z2>
```

**Example:**

```bash
# Default Mode Network: PCC vs vmPFC (6mm radius)
curl https://ns-nano-bzsi.onrender.com/dissociate/locations/0_-52_26/-2_50_-6

# Response
{
  "location_a": {"x": 0.0, "y": -52.0, "z": 26.0},
  "location_b": {"x": -2.0, "y": 50.0, "z": -6.0},
  "dissociation": "[0.0, -52.0, 26.0] \\ [-2.0, 50.0, -6.0]",
  "radius_mm": 6.0,
  "count": 406,
  "studies": ["10838149", "11516444", ...]
}
```

#### Custom Radius

```http
GET /dissociate/locations/<x1_y1_z1>/<x2_y2_z2>/<radius>
```

**Example:**

```bash
# Use 10mm search radius
curl https://ns-nano-bzsi.onrender.com/dissociate/locations/0_-52_26/-2_50_-6/10

# Use 8.5mm search radius (decimals supported)
curl https://ns-nano-bzsi.onrender.com/dissociate/locations/0_-52_26/-2_50_-6/8.5
```

---

### 3. Single Location Query

Find all studies within a specified radius of a single coordinate.

```http
GET /locations/<x_y_z>/<radius>
```

**Example:**

```bash
# Find studies within 6mm of PCC [0, -52, 26]
curl https://ns-nano-bzsi.onrender.com/locations/0_-52_26/6

# Response
{
  "location": {"x": 0.0, "y": -52.0, "z": 26.0},
  "radius_mm": 6.0,
  "count": 523,
  "studies": ["10838149", "11516444", ...]
}
```

---

### 4. Utility Endpoints

#### Health Check

```http
GET /
```

Returns server status.

#### Database Test

```http
GET /test_db
```

Returns database statistics and sample data:
- Total counts for coordinates, metadata, and annotations
- PostgreSQL version
- Sample records from each table

#### Static Image

```http
GET /img
```

Returns example brain image (amygdala.gif).

#### Route Inspector (Debug)

```http
GET /routes
```

Lists all registered API routes for debugging.

---

## 🚀 Quick Start

### Prerequisites

- Python 3.12.2+
- PostgreSQL 12+ with PostGIS extension
- 2GB+ RAM for data loading

### 1. Clone Repository

```bash
git clone https://github.com/ntu-info/05-longyuju1116.git
cd 05-longyuju1116
```

### 2. Install Dependencies

```bash
pip install -r requirements.txt
```

### 3. Setup Database

```bash
# Check database connection and extensions
python3 src/check_db.py --url "postgresql://USER:PASSWORD@HOST:PORT/DATABASE"

# Populate database (takes 10-30 minutes)
python3 src/create_db.py \
  --url "postgresql://USER:PASSWORD@HOST:PORT/DATABASE" \
  --data-dir ./data \
  --schema ns
```

### 4. Run Locally

```bash
# Development mode
export DB_URL="postgresql://USER:PASSWORD@HOST:PORT/DATABASE"
flask --app src.app run --debug

# Production mode
gunicorn src.app:app --bind 0.0.0.0:5000
```

### 5. Run Tests

```bash
python3 test_endpoints.py http://localhost:5000
```

---

## 📦 Installation

### Using pip

```bash
pip install -r requirements.txt
```

### Dependencies

```
Flask>=3.0.0          # Web framework
gunicorn>=21.2.0      # WSGI server
SQLAlchemy>=2.0.0     # ORM
psycopg2-binary>=2.9.9  # PostgreSQL driver
pandas>=2.1.0         # Data processing
numpy>=1.24.0         # Numerical computing
pyarrow>=14.0.0       # Parquet file support
```

---

## 🌐 Deployment

### Deploy to Render (Recommended)

#### Option 1: Using Blueprint (One-Click)

1. Push code to GitHub
2. In [Render Dashboard](https://dashboard.render.com), click **New +** → **Blueprint**
3. Connect your repository
4. Render will automatically read `render.yaml` and deploy

#### Option 2: Manual Setup

1. **Create PostgreSQL Database**
   - Dashboard → New + → PostgreSQL
   - Copy the External Database URL

2. **Populate Database** (local)
   ```bash
   python3 src/create_db.py --url "YOUR_DATABASE_URL" --data-dir ./data --schema ns
   ```

3. **Create Web Service**
   - Dashboard → New + → Web Service
   - Build Command: `pip install -r requirements.txt`
   - Start Command: `gunicorn src.app:app --bind 0.0.0.0:$PORT --workers 2 --timeout 120`
   - Add Environment Variable: `DB_URL=YOUR_DATABASE_URL`

4. **Deploy & Test**
   ```bash
   python3 test_endpoints.py https://YOUR-APP.onrender.com
   ```

**📖 Detailed guides**: See [guide/DEPLOYMENT_QUICKSTART.md](guide/DEPLOYMENT_QUICKSTART.md)

---

## 📚 API Examples

### Example 1: Fear vs Anxiety

```bash
# Studies with fear but not anxiety
curl https://ns-nano-bzsi.onrender.com/dissociate/terms/fear/anxiety

# Studies with anxiety but not fear  
curl https://ns-nano-bzsi.onrender.com/dissociate/terms/anxiety/fear
```

### Example 2: Pain Processing Regions

```bash
# Insula vs ACC with custom 8mm radius
curl https://ns-nano-bzsi.onrender.com/dissociate/locations/-40_0_0/0_24_32/8
```

### Example 3: Find All Studies Near a Coordinate

```bash
# All studies within 10mm of vmPFC
curl https://ns-nano-bzsi.onrender.com/locations/-2_50_-6/10
```

### Example 4: Default Mode Network Analysis

```bash
# PCC-dominant studies (not vmPFC)
curl https://ns-nano-bzsi.onrender.com/dissociate/locations/0_-52_26/-2_50_-6

# vmPFC-dominant studies (not PCC)
curl https://ns-nano-bzsi.onrender.com/dissociate/locations/-2_50_-6/0_-52_26
```

---

## 📁 Project Structure

```
05-longyuju1116/
├── src/                      # Source code
│   ├── app.py               # Flask application & API routes
│   ├── check_db.py          # Database connectivity checker
│   └── create_db.py         # Database population script
│
├── data/                     # Neurosynth dataset (Parquet)
│   ├── annotations.parquet  # Term-study associations (1M+ rows)
│   ├── coordinates.parquet  # MNI coordinates (100K+ rows)
│   └── metadata.parquet     # Study metadata
│
├── guide/                    # Documentation
│   ├── BACKEND_READY.md     # Testing guide
│   ├── DATABASE_SETUP.md    # Database setup details
│   ├── DEPLOYMENT_QUICKSTART.md  # Quick deployment
│   ├── PROJECT_STRUCTURE.md # Architecture overview
│   └── RENDER_DEPLOYMENT.md # Render-specific guide
│
├── test_endpoints.py         # Automated API tests
├── render.yaml              # Render deployment config
├── requirements.txt         # Python dependencies
├── Procfile                 # Alternative start command
├── README.md                # This file
└── LICENSE                  # MIT License
```

---

## ⚙️ Configuration

### Environment Variables

| Variable | Required | Description | Example |
|----------|----------|-------------|---------|
| `DB_URL` | ✅ | PostgreSQL connection string | `postgresql://user:pass@host:5432/db` |
| `PORT` | ⚠️ | Server port (auto-set by Render) | `5000` |
| `PYTHON_VERSION` | ❌ | Python version (for deployment) | `3.12.2` |

### Database Schema

The application uses the `ns` schema in PostgreSQL with three main tables:

- **`ns.coordinates`**: PostGIS POINTZ geometry with GIST spatial index
- **`ns.metadata`**: Study metadata with full-text search (GIN index)
- **`ns.annotations_terms`**: Sparse term-study associations (1M+ rows)

**Total Database Size**: ~500MB after indexing

---

## 🧪 Testing

### Run All Tests

```bash
python3 test_endpoints.py https://ns-nano-bzsi.onrender.com
```

### Test Coverage

- ✅ Health check
- ✅ Static file serving
- ✅ Database connectivity
- ✅ Term dissociation (auto-prefix)
- ✅ Coordinate dissociation (default radius)
- ✅ Coordinate dissociation (custom radius)
- ✅ Single location query

**Expected Output**:
```
============================================================
Total: 11/11 tests passed
============================================================

🎉 All tests passed!
```

---

## 📝 Notes

### Coordinate Format

- Use underscores between coordinates: `x_y_z`
- Example: `0_-52_26` represents MNI coordinate [0, -52, 26]
- Negative values are supported: `-2_50_-6`

### Term Format

- Terms use underscores instead of spaces
- Auto-prefix feature adds `terms_abstract_tfidf__` automatically
- Example: `fear` → `terms_abstract_tfidf__fear`
- Original format still supported for backward compatibility

### Search Radius

- Default radius: 6mm (typical fMRI resolution)
- Custom radius: any positive number (integer or float)
- Radius unit: millimeters (mm)
- Based on 3D Euclidean distance in MNI space

---

## 📄 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.
