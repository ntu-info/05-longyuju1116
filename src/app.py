# app.py
from flask import Flask, jsonify, abort, send_file
import os
from sqlalchemy import create_engine, text
from sqlalchemy.engine import URL
from sqlalchemy.exc import OperationalError

_engine = None

def get_engine():
    global _engine
    if _engine is not None:
        return _engine
    db_url = os.getenv("DB_URL")
    if not db_url:
        raise RuntimeError("Missing DB_URL (or DATABASE_URL) environment variable.")
    # Normalize old 'postgres://' scheme to 'postgresql://'
    if db_url.startswith("postgres://"):
        db_url = "postgresql://" + db_url[len("postgres://"):]
    _engine = create_engine(
        db_url,
        pool_pre_ping=True,
    )
    return _engine

def create_app():
    app = Flask(__name__)

    @app.get("/", endpoint="health")
    def health():
        return "<p>Server working!</p>"

    @app.get("/img", endpoint="show_img")
    def show_img():
        # amygdala.gif is in the project root, but app.py is in src/
        img_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), "amygdala.gif")
        if not os.path.exists(img_path):
            return jsonify({"error": "Image not found"}), 404
        return send_file(img_path, mimetype="image/gif")

    @app.get("/dissociate/terms/<term_a>/<term_b>", endpoint="dissociate_terms")
    def dissociate_by_terms(term_a: str, term_b: str):
        """
        Return studies that mention term_a but NOT term_b.
        
        Args:
            term_a: First term (included)
            term_b: Second term (excluded)
            
        Returns:
            JSON response with studies list
        """
        eng = get_engine()
        try:
            with eng.begin() as conn:
                conn.execute(text("SET search_path TO ns, public;"))
                
                # Query: studies with term_a but not term_b
                query = text("""
                    SELECT DISTINCT study_id
                    FROM ns.annotations_terms
                    WHERE term = :term_a
                    EXCEPT
                    SELECT DISTINCT study_id
                    FROM ns.annotations_terms
                    WHERE term = :term_b
                    ORDER BY study_id
                """)
                
                result = conn.execute(query, {"term_a": term_a, "term_b": term_b})
                studies = [row[0] for row in result]
                
                return jsonify({
                    "term_a": term_a,
                    "term_b": term_b,
                    "dissociation": f"{term_a} \\ {term_b}",
                    "count": len(studies),
                    "studies": studies
                }), 200
                
        except Exception as e:
            return jsonify({
                "error": str(e),
                "term_a": term_a,
                "term_b": term_b
            }), 500

    @app.get("/dissociate/locations/<coords_a>/<coords_b>", endpoint="dissociate_locations")
    def dissociate_by_locations(coords_a: str, coords_b: str):
        """
        Return studies near coords_a but NOT near coords_b.
        Uses 10mm radius for spatial proximity search.
        
        Args:
            coords_a: First coordinate as x_y_z (e.g., "0_-52_26")
            coords_b: Second coordinate as x_y_z (e.g., "-2_50_-6")
            
        Returns:
            JSON response with studies list
        """
        try:
            x1, y1, z1 = map(float, coords_a.split("_"))
            x2, y2, z2 = map(float, coords_b.split("_"))
        except (ValueError, AttributeError):
            return jsonify({
                "error": "Invalid coordinate format. Use x_y_z format (e.g., 0_-52_26)"
            }), 400
        
        eng = get_engine()
        try:
            with eng.begin() as conn:
                conn.execute(text("SET search_path TO ns, public;"))
                
                # Define search radius (in mm)
                radius = 10.0
                
                # Query: studies near coords_a but not near coords_b
                # Using Euclidean distance in 3D space
                query = text("""
                    WITH near_a AS (
                        SELECT DISTINCT study_id
                        FROM ns.coordinates
                        WHERE ST_3DDistance(
                            geom,
                            ST_SetSRID(ST_MakePoint(:x1, :y1, :z1), 4326)
                        ) <= :radius
                    ),
                    near_b AS (
                        SELECT DISTINCT study_id
                        FROM ns.coordinates
                        WHERE ST_3DDistance(
                            geom,
                            ST_SetSRID(ST_MakePoint(:x2, :y2, :z2), 4326)
                        ) <= :radius
                    )
                    SELECT study_id
                    FROM near_a
                    EXCEPT
                    SELECT study_id
                    FROM near_b
                    ORDER BY study_id
                """)
                
                result = conn.execute(query, {
                    "x1": x1, "y1": y1, "z1": z1,
                    "x2": x2, "y2": y2, "z2": z2,
                    "radius": radius
                })
                studies = [row[0] for row in result]
                
                return jsonify({
                    "location_a": {"x": x1, "y": y1, "z": z1},
                    "location_b": {"x": x2, "y": y2, "z": z2},
                    "dissociation": f"[{x1}, {y1}, {z1}] \\ [{x2}, {y2}, {z2}]",
                    "radius_mm": radius,
                    "count": len(studies),
                    "studies": studies
                }), 200
                
        except Exception as e:
            return jsonify({
                "error": str(e),
                "location_a": coords_a,
                "location_b": coords_b
            }), 500

    @app.get("/test_db", endpoint="test_db")
    
    def test_db():
        eng = get_engine()
        payload = {"ok": False, "dialect": eng.dialect.name}

        try:
            with eng.begin() as conn:
                # Ensure we are in the correct schema
                conn.execute(text("SET search_path TO ns, public;"))
                payload["version"] = conn.exec_driver_sql("SELECT version()").scalar()

                # Counts
                payload["coordinates_count"] = conn.execute(text("SELECT COUNT(*) FROM ns.coordinates")).scalar()
                payload["metadata_count"] = conn.execute(text("SELECT COUNT(*) FROM ns.metadata")).scalar()
                payload["annotations_terms_count"] = conn.execute(text("SELECT COUNT(*) FROM ns.annotations_terms")).scalar()

                # Samples
                try:
                    rows = conn.execute(text(
                        "SELECT study_id, ST_X(geom) AS x, ST_Y(geom) AS y, ST_Z(geom) AS z FROM ns.coordinates LIMIT 3"
                    )).mappings().all()
                    payload["coordinates_sample"] = [dict(r) for r in rows]
                except Exception:
                    payload["coordinates_sample"] = []

                try:
                    # Select a few columns if they exist; otherwise select a generic subset
                    rows = conn.execute(text("SELECT * FROM ns.metadata LIMIT 3")).mappings().all()
                    payload["metadata_sample"] = [dict(r) for r in rows]
                except Exception:
                    payload["metadata_sample"] = []

                try:
                    rows = conn.execute(text(
                        "SELECT study_id, contrast_id, term, weight FROM ns.annotations_terms LIMIT 3"
                    )).mappings().all()
                    payload["annotations_terms_sample"] = [dict(r) for r in rows]
                except Exception:
                    payload["annotations_terms_sample"] = []

            payload["ok"] = True
            return jsonify(payload), 200

        except Exception as e:
            payload["error"] = str(e)
            return jsonify(payload), 500

    return app

# WSGI entry point (no __main__)
app = create_app()
