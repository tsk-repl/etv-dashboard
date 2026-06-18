"""
ETV Auto Sticker Dashboard - Lightweight Version
No heavy OCR libraries - works on Render free plan
Team manually confirms location/number when needed
"""
from flask import Flask, request, jsonify, send_from_directory, send_file
import os, re, hashlib, base64, io
from pathlib import Path
from datetime import datetime
from collections import defaultdict

app = Flask(__name__, static_folder=os.path.join(os.path.dirname(os.path.abspath(__file__)), "static"))

UPLOAD_FOLDER = Path("uploads")
OUTPUT_FOLDER = Path("output")
UPLOAD_FOLDER.mkdir(exist_ok=True)
OUTPUT_FOLDER.mkdir(exist_ok=True)

SUPPORTED_EXTS = {".jpg", ".jpeg", ".png", ".webp", ".bmp"}

from pymongo import MongoClient
MONGO_URI = os.environ.get("MONGO_URI", "")
_db = None

def get_db():
    global _db
    if _db is None and MONGO_URI:
        client = MongoClient(MONGO_URI, serverSelectionTimeoutMS=5000)
        _db = client["etv_dashboard"]["photos"]
    return _db

def save_record(r):
    col = get_db()
    if col is not None:
        col.update_one({"id": r["id"]}, {"$set": r}, upsert=True)

def load_records():
    col = get_db()
    return list(col.find({}, {"_id": 0})) if col is not None else []

def record_exists(pid):
    col = get_db()
    return col.find_one({"id": pid}) is not None if col is not None else False

SERIES_MAP = {
  "A":{"location":"VISHAKAPATNAM","state":"Andhra Pradesh","qty":250},
  "B":{"location":"ANAKAPALLI","state":"Andhra Pradesh","qty":13},
  "C":{"location":"VIJAYAWADA","state":"Andhra Pradesh","qty":150},
  "D":{"location":"GUDIWADA","state":"Andhra Pradesh","qty":16},
  "E":{"location":"Machilipatnam","state":"Andhra Pradesh","qty":40},
  "F":{"location":"GUNTUR","state":"Andhra Pradesh","qty":150},
  "G":{"location":"NARSARAOPET","state":"Andhra Pradesh","qty":21},
  "H":{"location":"TENALI","state":"Andhra Pradesh","qty":30},
  "I":{"location":"Mangalagiri","state":"Andhra Pradesh","qty":50},
  "J":{"location":"NELLORE","state":"Andhra Pradesh","qty":60},
  "K":{"location":"KAVALI","state":"Andhra Pradesh","qty":16},
  "L":{"location":"ELURU","state":"Andhra Pradesh","qty":45},
  "M":{"location":"BHIMAVARAM","state":"Andhra Pradesh","qty":28},
  "N":{"location":"TANUKU","state":"Andhra Pradesh","qty":14},
  "O":{"location":"TADEPALLIGUDEM","state":"Andhra Pradesh","qty":19},
  "P":{"location":"Dubacharla","state":"Andhra Pradesh","qty":4},
  "Q":{"location":"Athili","state":"Andhra Pradesh","qty":6},
  "R":{"location":"Narasapuram","state":"Andhra Pradesh","qty":20},
  "S":{"location":"Yarnagudem","state":"Andhra Pradesh","qty":7},
  "T":{"location":"Palakollu","state":"Andhra Pradesh","qty":22},
  "U":{"location":"Gokavaram","state":"Andhra Pradesh","qty":6},
  "V":{"location":"Nidadavolu","state":"Andhra Pradesh","qty":14},
  "W":{"location":"Rajahmundry-Bypass","state":"Andhra Pradesh","qty":12},
  "X":{"location":"Rajahmundry-Gokavaram","state":"Andhra Pradesh","qty":14},
  "Y":{"location":"Rajahmundry-LalaCheruvu","state":"Andhra Pradesh","qty":11},
  "Z":{"location":"Rajahmundry-NandamGaniraju","state":"Andhra Pradesh","qty":10},
  "AA":{"location":"Rajahmundry-ShyamalaTheater","state":"Andhra Pradesh","qty":10},
  "AB":{"location":"Rajahmundry-ThaditotaMarket","state":"Andhra Pradesh","qty":13},
  "AC":{"location":"Seetanagaram","state":"Andhra Pradesh","qty":5},
  "AD":{"location":"Thallapudi","state":"Andhra Pradesh","qty":5},
  "AE":{"location":"Undrajavaram","state":"Andhra Pradesh","qty":4},
  "AF":{"location":"Vadapally","state":"Andhra Pradesh","qty":5},
  "AG":{"location":"Kolamuru","state":"Andhra Pradesh","qty":4},
  "AH":{"location":"Kovvuru","state":"Andhra Pradesh","qty":12},
  "AI":{"location":"Korukonda","state":"Andhra Pradesh","qty":6},
  "AJ":{"location":"Chagallu","state":"Andhra Pradesh","qty":6},
  "AK":{"location":"Amalapuram","state":"Andhra Pradesh","qty":18},
  "AL":{"location":"Ambajipeta","state":"Andhra Pradesh","qty":5},
  "AM":{"location":"Kothapeta","state":"Andhra Pradesh","qty":9},
  "AN":{"location":"Pulletikuru","state":"Andhra Pradesh","qty":3},
  "AO":{"location":"Ravulapalem","state":"Andhra Pradesh","qty":14},
  "AP":{"location":"OldGunturRoad","state":"Andhra Pradesh","qty":12},
  "AQ":{"location":"Peddapuram","state":"Andhra Pradesh","qty":14},
  "AR":{"location":"Pithapuram","state":"Andhra Pradesh","qty":14},
  "AS":{"location":"Samarlakota","state":"Andhra Pradesh","qty":16},
  "AT":{"location":"Kakinada","state":"Andhra Pradesh","qty":90},
  "AU":{"location":"Tuni","state":"Andhra Pradesh","qty":22},
  "AV":{"location":"Jaggampeta","state":"Andhra Pradesh","qty":8},
  "AW":{"location":"Bhimadolu","state":"Andhra Pradesh","qty":5},
  "AX":{"location":"DwarakaTirumala","state":"Andhra Pradesh","qty":8},
  "AY":{"location":"Polavaram","state":"Andhra Pradesh","qty":5},
  "AZ":{"location":"Nuzvid","state":"Andhra Pradesh","qty":18},
  "BA":{"location":"ONGOLE","state":"Andhra Pradesh","qty":32},
  "BB":{"location":"CHIRALA","state":"Andhra Pradesh","qty":27},
  "BC":{"location":"Markapur","state":"Andhra Pradesh","qty":18},
  "BD":{"location":"SRIKAKULAM","state":"Andhra Pradesh","qty":24},
  "BE":{"location":"Vizianagaram","state":"Andhra Pradesh","qty":65},
  "BF":{"location":"Bapatla","state":"Andhra Pradesh","qty":20},
  "BG":{"location":"Sattenapalle","state":"Andhra Pradesh","qty":18},
  "BH":{"location":"Raghavapuram","state":"Andhra Pradesh","qty":3},
  "BI":{"location":"Secunderabad","state":"Telangana","qty":25},
  "BJ":{"location":"Bowenpally","state":"Telangana","qty":25},
  "BK":{"location":"Karkhana","state":"Telangana","qty":22},
  "BL":{"location":"Lingampally","state":"Telangana","qty":25},
  "BM":{"location":"Shamsabad","state":"Telangana","qty":25},
  "BN":{"location":"Bandlaguda","state":"Telangana","qty":22},
  "BO":{"location":"Shaapur","state":"Telangana","qty":15},
  "BP":{"location":"BalajiNagar","state":"Telangana","qty":12},
  "BQ":{"location":"Mallapur","state":"Telangana","qty":20},
  "BR":{"location":"Nizampet","state":"Telangana","qty":25},
  "BS":{"location":"Chintal","state":"Telangana","qty":18},
  "BT":{"location":"ECIL","state":"Telangana","qty":30},
  "BU":{"location":"Kompally","state":"Telangana","qty":30},
  "BV":{"location":"Medchal","state":"Telangana","qty":25},
  "BW":{"location":"Malkajgiri","state":"Telangana","qty":35},
  "BX":{"location":"Bollaram","state":"Telangana","qty":15},
  "BY":{"location":"Patancheru-BHEL","state":"Telangana","qty":35},
  "BZ":{"location":"Mallepalli","state":"Telangana","qty":18},
  "CA":{"location":"Ramanthapur","state":"Telangana","qty":22},
  "CB":{"location":"Malakpet","state":"Telangana","qty":30},
  "CC":{"location":"Kukatpalli","state":"Telangana","qty":35},
  "CD":{"location":"Ameerpet","state":"Telangana","qty":50},
  "CE":{"location":"Dilsukhnagar","state":"Telangana","qty":50},
  "CF":{"location":"LBNagar","state":"Telangana","qty":49},
  "CG":{"location":"Mehdipatnam","state":"Telangana","qty":45},
  "CH":{"location":"Charminar","state":"Telangana","qty":50},
  "CI":{"location":"Koti-Abids","state":"Telangana","qty":45},
  "CJ":{"location":"Miyapur","state":"Telangana","qty":40},
  "CK":{"location":"Uppal","state":"Telangana","qty":40},
  "CL":{"location":"Gachibowli","state":"Telangana","qty":35},
  "CM":{"location":"Madhapur","state":"Telangana","qty":35},
  "CN":{"location":"Tarnaka","state":"Telangana","qty":25},
  "CO":{"location":"RahmatNagar","state":"Telangana","qty":20},
  "CP":{"location":"LakdiKaPul","state":"Telangana","qty":30},
  "CQ":{"location":"WARANGAL","state":"Telangana","qty":120},
  "CR":{"location":"Kazipet","state":"Telangana","qty":18},
  "CS":{"location":"KARIMNAGAR","state":"Telangana","qty":50},
  "CT":{"location":"JAGITYAL","state":"Telangana","qty":16},
  "CU":{"location":"KHAMMAM","state":"Telangana","qty":50},
  "CV":{"location":"PALLONCHA","state":"Telangana","qty":14},
  "CW":{"location":"Sathupally","state":"Telangana","qty":18},
  "CX":{"location":"NIZAMABAD","state":"Telangana","qty":57},
  "CY":{"location":"KAMAREDDY","state":"Telangana","qty":14},
  "CZ":{"location":"Armoor","state":"Telangana","qty":18},
  "DA":{"location":"Bodhan","state":"Telangana","qty":18},
  "DB":{"location":"ADILABAD","state":"Telangana","qty":24},
  "DC":{"location":"MANCHERIAL","state":"Telangana","qty":14},
  "DD":{"location":"Jangaon","state":"Telangana","qty":18},
  "DE":{"location":"Bhongir","state":"Telangana","qty":22},
  "DF":{"location":"NALGONDA","state":"Telangana","qty":25},
  "DG":{"location":"SURYAPET","state":"Telangana","qty":19},
  "DH":{"location":"MIRYALAGUDA","state":"Telangana","qty":18},
  "DI":{"location":"MAHABOOBNAGAR","state":"Telangana","qty":35},
  "DJ":{"location":"Tandur","state":"Telangana","qty":22},
  "DK":{"location":"Vikarabad","state":"Telangana","qty":20},
  "DL":{"location":"Gadwal","state":"Telangana","qty":18},
  "DM":{"location":"Wanaparthy","state":"Telangana","qty":18},
  "DN":{"location":"SIDDIPET","state":"Telangana","qty":19},
  "DO":{"location":"Bhadrachalam","state":"Telangana","qty":22},
  "DP":{"location":"Manuguru","state":"Telangana","qty":16},
  "DQ":{"location":"KURNOOL","state":"Andhra Pradesh","qty":75},
  "DR":{"location":"ADONI","state":"Andhra Pradesh","qty":24},
  "DS":{"location":"YEMMIGANUR","state":"Andhra Pradesh","qty":14},
  "DT":{"location":"Tadipatri","state":"Andhra Pradesh","qty":25},
  "DU":{"location":"Hindupur","state":"Andhra Pradesh","qty":35},
  "DV":{"location":"Dharmavaram","state":"Andhra Pradesh","qty":30},
  "DW":{"location":"ANANTAPURAM","state":"Andhra Pradesh","qty":56},
  "DX":{"location":"GUNTAKAL","state":"Andhra Pradesh","qty":19},
  "DY":{"location":"KADIRI","state":"Andhra Pradesh","qty":13},
  "DZ":{"location":"PRODDUTUR","state":"Andhra Pradesh","qty":30},
  "EA":{"location":"RAYACHOTI","state":"Andhra Pradesh","qty":13},
  "EB":{"location":"KADAPA","state":"Andhra Pradesh","qty":54},
  "EC":{"location":"TIRUPATHI","state":"Andhra Pradesh","qty":60},
  "ED":{"location":"CHITOOR","state":"Andhra Pradesh","qty":27},
  "EE":{"location":"MADANAPALLY","state":"Andhra Pradesh","qty":25},
  "EF":{"location":"Nandyal","state":"Andhra Pradesh","qty":55},
}

DESIGNS = ["Aaro_Pranam","Ammoru","Andhal_Rakshasi","Bommarillu","Janaki_Parinayam",
           "Jhansi","Manasantha_Nuvve","Merupu_Kalalu","Rangula_Ratnam","Sandhya_Ragam",
           "Vasundhara","Veyi_Shubhamulu_Kaluguniku","Yashodha"]

def image_hash(path):
    with open(path,"rb") as f: return hashlib.sha256(f.read()).hexdigest()

def thumb_b64(path):
    try:
        from PIL import Image
        img = Image.open(path).convert("RGB")
        img.thumbnail((400,400))
        buf = io.BytesIO()
        img.save(buf, format="JPEG", quality=65)
        return base64.b64encode(buf.getvalue()).decode()
    except: return ""

def process_photo(file_path, filename, reviewer, location, series, f_number, design):
    """Lightweight processing — no OCR, uses form data from uploader"""
    record = {
        "id": image_hash(file_path)[:12],
        "filename": filename,
        "filepath": str(file_path),
        "reviewer": reviewer,
        "uploaded_at": datetime.now().strftime("%Y-%m-%d %H:%M"),
        "series": series.upper() if series else None,
        "location": None, "state": None,
        "design": design or "—",
        "f_number": f_number or None,
        "gps_text": "", "datetime_stamp": "",
        "status": "Manual Check", "issues": [],
        "image_b64": thumb_b64(file_path)
    }

    # Auto-detect location from series
    s = (series or "").upper()
    if s and s in SERIES_MAP:
        record["location"] = SERIES_MAP[s]["location"]
        record["state"]    = SERIES_MAP[s]["state"]
    elif location:
        record["location"] = location
    else:
        record["location"] = "Unknown"
        record["issues"].append("Location not set")

    if not f_number:
        record["issues"].append("Sticker number not entered")
    if not design or design == "—":
        record["issues"].append("Design not selected")

    record["status"] = "Manual Check" if record["issues"] else "Approved"
    return record

@app.route("/")
def index():
    static_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), "static")
    return send_from_directory(static_dir, "index.html")

@app.route("/series_map")
def series_map():
    return jsonify(SERIES_MAP)

@app.route("/designs")
def designs():
    return jsonify(DESIGNS)

@app.route("/upload", methods=["POST"])
def upload():
    files    = request.files.getlist("photos")
    reviewer = request.form.get("reviewer", "Team")
    series   = request.form.get("series", "")
    f_number = request.form.get("f_number", "")
    design   = request.form.get("design", "")
    location = request.form.get("location", "")
    results  = []

    for f in files:
        if not f.filename: continue
        if Path(f.filename).suffix.lower() not in SUPPORTED_EXTS: continue
        save_path = UPLOAD_FOLDER / f.filename
        f.save(save_path)
        pid = image_hash(save_path)[:12]
        if record_exists(pid):
            results.append({"filename":f.filename,"status":"Duplicate","id":pid,"issues":["Already uploaded"]})
            continue
        rec = process_photo(save_path, f.filename, reviewer, location, series, f_number, design)
        save_record(rec)
        results.append({k:v for k,v in rec.items() if k!="image_b64"})

    return jsonify({"processed":len(results),"results":results})

@app.route("/records")
def get_records():
    return jsonify([{k:v for k,v in r.items() if k!="image_b64"} for r in load_records()])

@app.route("/stats")
def get_stats():
    records = load_records()
    by_loc = defaultdict(lambda:{"approved":0,"manual":0,"rejected":0,"total":0})
    for r in records:
        loc = r.get("location","Unknown")
        by_loc[loc]["total"] += 1
        s = r.get("status","")
        if s=="Approved": by_loc[loc]["approved"]+=1
        elif s=="Manual Check": by_loc[loc]["manual"]+=1
        elif s=="Rejected": by_loc[loc]["rejected"]+=1
    return jsonify({
        "total":len(records),
        "approved":sum(1 for r in records if r.get("status")=="Approved"),
        "manual":sum(1 for r in records if r.get("status")=="Manual Check"),
        "rejected":sum(1 for r in records if r.get("status")=="Rejected"),
        "duplicate":sum(1 for r in records if r.get("status")=="Duplicate"),
        "by_location":dict(by_loc)
    })

@app.route("/image/<photo_id>")
def serve_image(photo_id):
    col = get_db()
    if col:
        rec = col.find_one({"id":photo_id},{"image_b64":1})
        if rec and rec.get("image_b64"):
            return send_file(io.BytesIO(base64.b64decode(rec["image_b64"])), mimetype="image/jpeg")
    return "Not found", 404

@app.route("/update", methods=["POST"])
def update():
    d = request.json
    col = get_db()
    if col:
        fields = {k:d[k] for k in ["status","design","f_number","location","series"] if d.get(k)}
        if fields: col.update_one({"id":d["id"]},{"$set":fields})
    return jsonify({"ok":True})

@app.route("/export_excel")
def export_excel():
    try:
        import pandas as pd
        records = load_records()
        df = pd.DataFrame([{k:v for k,v in r.items() if k!="image_b64"} for r in records])
        out = OUTPUT_FOLDER/"ETV_QC_Report.xlsx"
        df.to_excel(str(out), index=False)
        return send_file(str(out.resolve()), as_attachment=True, download_name="ETV_QC_Report.xlsx")
    except Exception as e:
        return jsonify({"error":str(e)}),500

@app.route("/export_ppt")
def export_ppt():
    try:
        from pptx import Presentation
        from pptx.util import Inches, Pt
        from pptx.dml.color import RGBColor
        from pptx.enum.text import PP_ALIGN
        records = load_records()
        prs=Presentation(); prs.slide_width=Inches(13.33); prs.slide_height=Inches(7.5)
        blank=prs.slide_layouts[6]
        DARK=RGBColor(0x1A,0x1A,0x2E); ACCENT=RGBColor(0xE9,0x4F,0x37)
        WHITE=RGBColor(0xFF,0xFF,0xFF); GOLD=RGBColor(0xF5,0xA6,0x23); GREEN=RGBColor(0x27,0xAE,0x60)
        def t(sl,tx,l,tp,w,h,sz,bold=False,col=WHITE,al=PP_ALIGN.LEFT):
            tb=sl.shapes.add_textbox(l,tp,w,h); tf=tb.text_frame; tf.word_wrap=True
            p=tf.paragraphs[0]; p.alignment=al; run=p.add_run(); run.text=str(tx)
            run.font.size=Pt(sz); run.font.bold=bold; run.font.color.rgb=col; run.font.name="Calibri"
        s1=prs.slides.add_slide(blank)
        bg=s1.shapes.add_shape(1,0,0,prs.slide_width,prs.slide_height)
        bg.fill.solid(); bg.fill.fore_color.rgb=DARK; bg.line.fill.background()
        t(s1,"ETV Auto Sticker Campaign Report",Inches(0.7),Inches(2.0),Inches(12),Inches(1),38,True,ACCENT,PP_ALIGN.CENTER)
        t(s1,f"{datetime.now().strftime('%d %B %Y')}  |  {len(records)} photos",Inches(0.7),Inches(3.2),Inches(12),Inches(0.5),16,col=WHITE,al=PP_ALIGN.CENTER)
        for r in [x for x in records if x.get("status")=="Approved"]:
            sl=prs.slides.add_slide(blank)
            if r.get("image_b64"):
                try: sl.shapes.add_picture(io.BytesIO(base64.b64decode(r["image_b64"])),Inches(0.3),Inches(0.3),Inches(6.5),Inches(6.9))
                except: pass
            card=sl.shapes.add_shape(1,Inches(7.1),Inches(0.3),Inches(5.9),Inches(6.9))
            card.fill.solid(); card.fill.fore_color.rgb=DARK; card.line.fill.background()
            t(sl,"ETV AUTO STICKER",Inches(7.3),Inches(0.5),Inches(5.5),Inches(0.5),14,True,ACCENT)
            y=1.1
            for lbl,val in [("Location",r.get("location","—")),("Series / Number",f"{r.get('series','')} — {r.get('f_number','')}"),
                ("Design",r.get("design","—")),("Reviewer",r.get("reviewer","—")),("Date",r.get("uploaded_at","—"))]:
                t(sl,lbl,Inches(7.3),Inches(y),Inches(5.5),Inches(0.25),8,True,GOLD)
                t(sl,str(val),Inches(7.3),Inches(y+0.25),Inches(5.5),Inches(0.4),13,col=WHITE)
                y+=0.9
            b=sl.shapes.add_shape(1,Inches(7.3),Inches(6.55),Inches(2.8),Inches(0.45))
            b.fill.solid(); b.fill.fore_color.rgb=GREEN; b.line.fill.background()
            t(sl,"APPROVED",Inches(7.3),Inches(6.57),Inches(2.8),Inches(0.4),12,True,WHITE,PP_ALIGN.CENTER)
        buf=io.BytesIO(); prs.save(buf); buf.seek(0)
        return send_file(buf,as_attachment=True,download_name="ETV_Campaign_Report.pptx",
                        mimetype="application/vnd.openxmlformats-officedocument.presentationml.presentation")
    except Exception as e:
        return jsonify({"error":str(e)}),500

if __name__=="__main__":
    port=int(os.environ.get("PORT",5000))
    print(f"\n  ETV Dashboard → http://localhost:{port}\n")
    app.run(debug=False, host="0.0.0.0", port=port)
