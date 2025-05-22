from flask import Flask, request, jsonify, render_template
from flask_cors import CORS
import psycopg2

app = Flask(__name__)
CORS(app)

def get_connection():
    return psycopg2.connect(
        host="localhost",
        port="5432",
        dbname="riesgos",
        user="postgres",
        password="admin123"
    )

@app.route('/')
def home():
    return render_template('index.html')

@app.route('/data')
def get_data():
    bbox = request.args.get("bbox", default=None, type=str)
    if not bbox:
        return jsonify({"error": "Falta parámetro bbox"}), 400

    try:
        xmin, ymin, xmax, ymax = map(float, bbox.split(','))
    except:
        return jsonify({"error": "bbox inválido"}), 400

    sql = """
        SELECT ST_AsGeoJSON(geom)::json, r_hid_1, proyecto_2
        FROM riesgo_hidrico
        WHERE geom && ST_MakeEnvelope(%s, %s, %s, %s, 4326)
        LIMIT 5000;
    """

    conn = get_connection()
    cur = conn.cursor()
    cur.execute(sql, (xmin, ymin, xmax, ymax))
    features = []
    for row in cur.fetchall():
        geometry, riesgo, proyecto = row
        features.append({
            "type": "Feature",
            "geometry": geometry,
            "properties": {
                "riesgo": riesgo,
                "proyecto": proyecto
            }
        })
    cur.close()
    conn.close()

    return jsonify({
        "type": "FeatureCollection",
        "features": features
    })

if __name__ == "__main__":
    import os
port = int(os.environ.get("PORT", 5000))
app.run(host='0.0.0.0', port=port)

