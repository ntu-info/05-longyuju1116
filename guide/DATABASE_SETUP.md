# Database Setup Guide for Render Deployment

This guide walks you through setting up the PostgreSQL database for the Neurosynth backend on Render.

## Prerequisites

- A Render account (https://render.com)
- Python 3.10+ installed locally
- The Neurosynth Parquet data files in the `data/` directory

## Step 1: Create PostgreSQL Database on Render

1. Log in to your Render dashboard
2. Click **"New +"** → **"PostgreSQL"**
3. Configure the database:
   - **Name**: `ns-nano-db` (or your preferred name)
   - **Database**: `neurosynth_db`
   - **User**: `neurosynth_user`
   - **Region**: Choose a region (e.g., Oregon)
   - **Plan**: Free tier is sufficient for testing
4. Click **"Create Database"**
5. Wait for the database to be provisioned (may take a few minutes)

## Step 2: Get Database Connection URL

1. In the database dashboard, find the **"Connections"** section
2. Copy the **"External Database URL"**
   - Format: `postgresql://user:password@host:port/database`
3. Save this URL securely (you'll need it for the next steps)

## Step 3: Verify Database Connection and Extensions

Run the check script locally to verify the database is ready:

```bash
python src/check_db.py --url "postgresql://USER:PASSWORD@HOST:PORT/DATABASE"
```

This script will:
- ✅ Verify database connectivity
- ✅ Check PostgreSQL version
- ✅ Enable required extensions (PostGIS, pg_trgm, unaccent, vector)
- ✅ Test extension functionality

**Expected Output:**
```
✅ server_version: OK
✅ current database: OK
✅ tsvector type exists: OK
✅ enable postgis: OK
✅ PostGIS_Full_Version() works: OK
...
```

## Step 4: Populate the Database

Run the database creation script to load the Neurosynth data:

```bash
python src/create_db.py \
  --url "postgresql://USER:PASSWORD@HOST:PORT/DATABASE" \
  --data-dir ./data \
  --schema ns \
  --if-exists replace
```

**Parameters:**
- `--url`: Your database connection string from Step 2
- `--data-dir`: Directory containing the Parquet files (default: `./data`)
- `--schema`: Database schema name (default: `ns`)
- `--if-exists`: Behavior for existing tables (`replace` or `append`)

**What this script does:**
1. Creates the `ns` schema
2. Loads `coordinates.parquet` → `ns.coordinates` table with PostGIS geometry
3. Loads `metadata.parquet` → `ns.metadata` table with full-text search
4. Loads `annotations.parquet` → `ns.annotations_terms` table (sparse format)
5. Creates indexes for optimal query performance

**Expected Output:**
```
✅ server_version: PostgreSQL 15.x
✅ current_database: neurosynth_db
→ coordinates: preparing dataframe
→ coordinates: loading staging (to_sql)
→ coordinates: populating geometry from staging
→ coordinates (POINTZ + GIST) done.
→ metadata: preparing & creating table
→ metadata (FTS + trigger) done.
→ annotations: preparing
   … copied 50,000 rows (cumulative 50,000)
   … copied 45,231 rows (cumulative 95,231)
→ annotations_terms total inserted: XXX,XXX
=== Ready ===
```

**Note:** This process may take 10-30 minutes depending on data size.

## Step 5: Configure Environment Variables in Render

1. Go to your Render dashboard
2. If using `render.yaml` (recommended):
   - The database connection is automatically configured
   - Push your code to GitHub and connect the repository to Render
3. If configuring manually:
   - Go to your Web Service settings
   - Navigate to **"Environment"** tab
   - Add environment variable:
     - **Key**: `DB_URL`
     - **Value**: Your database URL from Step 2

## Step 6: Deploy the Web Service

### Option A: Using render.yaml (Blueprint)

1. Push your code to GitHub (including `render.yaml`)
2. In Render dashboard, click **"New +"** → **"Blueprint"**
3. Connect your GitHub repository
4. Render will automatically:
   - Create the PostgreSQL database
   - Create the Web Service
   - Set up environment variables
5. Approve the blueprint and deploy

### Option B: Manual Web Service Creation

1. In Render dashboard, click **"New +"** → **"Web Service"**
2. Connect your GitHub repository
3. Configure:
   - **Name**: `ns-nano`
   - **Environment**: Python 3
   - **Build Command**: `pip install -r requirements.txt`
   - **Start Command**: `gunicorn src.app:app --bind 0.0.0.0:$PORT`
4. Add environment variable `DB_URL` (from Step 5)
5. Click **"Create Web Service"**

## Step 7: Test Your Deployment

Once deployed, test the following endpoints:

### Health Check
```bash
curl https://ns-nano.onrender.com/
# Expected: <p>Server working!</p>
```

### Database Connectivity
```bash
curl https://ns-nano.onrender.com/test_db
# Expected: JSON with database stats and sample data
```

### Static File
```bash
curl https://ns-nano.onrender.com/img
# Expected: Image data (amygdala.gif)
```

### Dissociate by Terms
```bash
curl https://ns-nano.onrender.com/dissociate/terms/posterior_cingulate/ventromedial_prefrontal
# Expected: JSON with studies mentioning posterior_cingulate but not ventromedial_prefrontal
```

### Dissociate by Locations (Default Mode Network)
```bash
curl https://ns-nano.onrender.com/dissociate/locations/0_-52_26/-2_50_-6
# Expected: JSON with studies near [0, -52, 26] but not near [-2, 50, -6]
```

## Troubleshooting

### Database Connection Errors

**Issue**: `OperationalError: could not connect to server`

**Solution**:
- Verify the database URL is correct
- Check that the database is running in Render dashboard
- Ensure IP whitelist allows connections (use `0.0.0.0/0` for public access)

### Extension Errors

**Issue**: `ERROR: extension "postgis" is not available`

**Solution**:
- Render's PostgreSQL should support PostGIS by default
- If not, contact Render support or use a different hosting provider

### Empty Query Results

**Issue**: API returns empty arrays `{"studies": []}`

**Solution**:
- Verify database was populated correctly: check `/test_db` endpoint
- Ensure term/coordinate parameters match database values
- Terms should use underscores, not spaces (e.g., `posterior_cingulate`)

### Performance Issues

**Issue**: Queries are slow

**Solution**:
- Check that indexes were created (run `create_db.py` with `ANALYZE` commands)
- Upgrade to a paid Render plan for better database performance
- Consider adding database connection pooling

## Database Schema Reference

### `ns.coordinates`
- `study_id` (TEXT): Study identifier
- `geom` (GEOMETRY): PostGIS POINTZ geometry (MNI coordinates)
- Indexes: `study_id`, GIST spatial index on `geom`

### `ns.metadata`
- Dynamic columns based on Parquet file
- `fts` (TSVECTOR): Full-text search vector
- Indexes: GIN index on `fts`

### `ns.annotations_terms`
- `study_id` (TEXT): Study identifier
- `contrast_id` (TEXT): Contrast identifier
- `term` (TEXT): Term label
- `weight` (DOUBLE PRECISION): Term weight/score
- Indexes: `term`, `study_id`, composite `(term, study_id)`

## Next Steps

- Monitor your application logs in Render dashboard
- Set up custom domains (if needed)
- Configure CORS settings if building a frontend
- Consider implementing rate limiting for production use
- Add authentication if needed for sensitive data

## Support

- Render Documentation: https://render.com/docs
- PostGIS Documentation: https://postgis.net/documentation/
- SQLAlchemy Documentation: https://docs.sqlalchemy.org/

---

**Note**: Render's free tier has limitations:
- Database: 90-day expiration, limited storage
- Web Service: Spins down after inactivity, cold start delays
- Consider upgrading for production use

