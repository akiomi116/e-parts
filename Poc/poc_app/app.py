import os
import pandas as pd
from flask import Flask, render_template, request, redirect, url_for, session
from flask_sqlalchemy import SQLAlchemy
from werkzeug.utils import secure_filename # Import secure_filename

app = Flask(__name__)
# Use absolute path for the database
db_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'instance', 'app.db')
db_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'instance')
os.makedirs(db_dir, exist_ok=True)

app.config["SQLALCHEMY_DATABASE_URI"] = f"sqlite:///{db_path}"
app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False
app.config["SECRET_KEY"] = "your_secret_key_here" # IMPORTANT: Change this to a strong random key in production!
db = SQLAlchemy(app)

# --- モデル定義 ---
class BomLine(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    reference = db.Column(db.String(50))
    value = db.Column(db.String(100))
    footprint = db.Column(db.String(100))
    mpn = db.Column(db.String(100))
    quantity = db.Column(db.Integer) # Keep quantity, but set to 1 after unrolling

# --- 初期化 ---
with app.app_context():
    db.create_all()

# --- ルート ---
@app.route("/")
def index():
    return render_template("index.html")

@app.route("/upload_bom", methods=["POST"])
def upload_bom():
    file = request.files.get("file")
    if not file or file.filename == '':
        return redirect(url_for("index"))
    
    # Clear existing data
    db.session.query(BomLine).delete()

    try:
        df = pd.read_csv(file)
        for _, row in df.iterrows():
            references_str = str(row.get("Reference", "")).strip()
            if not references_str: # Skip empty reference rows
                continue

            # Split references by comma and handle potential spaces
            references = [r.strip() for r in references_str.split(',') if r.strip()]

            for ref in references:
                db.session.add(BomLine(
                    reference=ref,
                    value=row.get("Value"),
                    footprint=row.get("Footprint"),
                    mpn=row.get("MPN"),
                    quantity=1 # Always 1 after unrolling
                ))
        db.session.commit()
    except Exception as e:
        db.session.rollback()
        print(f"Error processing CSV: {e}")
        return "Error processing CSV file.", 400

    return redirect(url_for("bom"))

@app.route("/upload_svgs", methods=["POST"])
def upload_svgs():
    schematic_file = request.files.get("schematic_svg")
    pcb_file = request.files.get("pcb_svg")

    if schematic_file and schematic_file.filename:
        schematic_filename = secure_filename(schematic_file.filename)
        schematic_file.save(os.path.join(app.static_folder, schematic_filename))
        session['schematic_svg'] = schematic_filename
    
    if pcb_file and pcb_file.filename:
        pcb_filename = secure_filename(pcb_file.filename)
        pcb_file.save(os.path.join(app.static_folder, pcb_filename))
        session['pcb_svg'] = pcb_filename

    return redirect(url_for("bom"))

@app.route("/bom")
def bom():
    lines = BomLine.query.all()
    # Pass SVG filenames from session to template
    schematic_svg = session.get('schematic_svg', 'sample_schematic.svg')
    pcb_svg = session.get('pcb_svg', 'sample_pcb.svg')
    return render_template("bom.html", lines=lines, schematic_svg=schematic_svg, pcb_svg=pcb_svg)

if __name__ == "__main__":
    app.run(debug=True)