"""
ETV Auto Sticker Dashboard - Flask Backend
Run: python app.py
Open: http://localhost:5000
"""
from flask import Flask, request, jsonify, send_from_directory, send_file
import os, re, shutil, hashlib, json
from pathlib import Path
from datetime import datetime
from collections import defaultdict

app = Flask(__name__, static_folder=os.path.join(os.path.dirname(os.path.abspath(__file__)), "static"))

UPLOAD_FOLDER  = Path("uploads")
OUTPUT_FOLDER  = Path("output")
MASTERS_FOLDER = Path("../Masters")

UPLOAD_FOLDER.mkdir(exist_ok=True)
OUTPUT_FOLDER.mkdir(exist_ok=True)

SUPPORTED_EXTS = {".jpg", ".jpeg", ".png", ".webp", ".bmp"}

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

GPS_KEYWORDS = {
    "guntur":"GUNTUR","vijayawada":"VIJAYAWADA","visakhapatnam":"VISHAKAPATNAM",
    "vizag":"VISHAKAPATNAM","nellore":"NELLORE","kakinada":"Kakinada",
    "rajahmundry":"Rajahmundry","eluru":"ELURU","warangal":"WARANGAL",
    "karimnagar":"KARIMNAGAR","khammam":"KHAMMAM","nizamabad":"NIZAMABAD",
    "hyderabad":"Hyderabad","secunderabad":"Secunderabad","tirupati":"TIRUPATHI",
    "tirupathi":"TIRUPATHI","kurnool":"KURNOOL","kadapa":"KADAPA",
    "anantapur":"ANANTAPURAM","anantapuram":"ANANTAPURAM","srikakulam":"SRIKAKULAM",
    "vizianagaram":"Vizianagaram","ongole":"ONGOLE","nalgonda":"NALGONDA",
    "mahaboobnagar":"MAHABOOBNAGAR",
}

photo_records = []
_ocr_reader = None

def get_ocr():
    global _ocr_reader
    if _ocr_reader is None:
        try:
            import easyocr
            _ocr_reader = easyocr.Reader(["en"], gpu=False, verbose=False)
        except: pass
    return _ocr_reader

def image_hash(path):
    with open(path,"rb") as f: return hashlib.sha256(f.read()).hexdigest()

def check_blur(path):
    try:
        import cv2
        img = cv2.imread(str(path), cv2.IMREAD_GRAYSCALE)
        if img is None: return False, 999
        score = cv2.Laplacian(img, cv2.CV_64F).var()
        return score < 80, round(score,1)
    except: return False, 999

def check_brightness(path):
    try:
        import cv2
        img = cv2.imread(str(path), cv2.IMREAD_COLOR)
        if img is None: return False, 128
        hsv = cv2.cvtColor(img, cv2.COLOR_BGR2HSV)
        return float(hsv[:,:,2].mean()) < 50, round(float(hsv[:,:,2].mean()),1)
    except: return False, 128

def do_ocr(path, region="bottom"):
    reader = get_ocr()
    if not reader: return ""
    try:
        import numpy as np
        from PIL import Image, ImageEnhance
        img = Image.open(path).convert("RGB")
        w, h = img.size
        if region == "bottom":
            crop = img.crop((0, int(h*0.72), w, h))
        else:
            crop = img.crop((0, 0, w, int(h*0.72)))
            crop = ImageEnhance.Contrast(crop).enhance(2.0)
        results = reader.readtext(np.array(crop), detail=0, paragraph=True)
        return " ".join(results)
    except: return ""

def process_photo(file_path, filename, reviewer=""):
    record = {
        "id": image_hash(file_path)[:8],
        "filename": filename,
        "filepath": str(file_path),
        "reviewer": reviewer,
        "uploaded_at": datetime.now().strftime("%Y-%m-%d %H:%M"),
        "series": None, "location": None, "state": None,
        "design": "—", "f_number": None,
        "gps_text": "", "datetime_stamp": "",
        "status": "Manual Check", "issues": [],
        "blur_score": 999, "brightness": 128,
    }

    is_blurry, blur = check_blur(file_path)
    is_dark, brightness = check_brightness(file_path)
    record["blur_score"] = blur
    record["brightness"] = brightness
    if is_blurry: record["issues"].append("Photo is blurry")
    if is_dark:   record["issues"].append("Photo is too dark")

    gps = do_ocr(file_path, "bottom")
    record["gps_text"] = gps[:200]
    dt_m = re.search(r'(\d{4}[-/]\d{2}[-/]\d{2}[^\n]{0,20}\d{2}:\d{2})', gps)
    if dt_m: record["datetime_stamp"] = dt_m.group(1)

    location = None
    for kw, city in GPS_KEYWORDS.items():
        if kw in gps.lower(): location = city; break

    sticker = do_ocr(file_path, "top")
    m = re.search(r'\b([A-Z]{1,2})\s*(\d{1,4})\b', sticker, re.IGNORECASE)
    if m:
        series = m.group(1).upper()
        record["series"] = series
        record["f_number"] = f"{series}{m.group(2)}"
        if not location and series in SERIES_MAP:
            location = SERIES_MAP[series]["location"]
        if series in SERIES_MAP:
            record["state"] = SERIES_MAP[series]["state"]

    record["location"] = location or "Unknown"
    if not location:          record["issues"].append("Location not detected")
    if not record["f_number"]: record["issues"].append("Sticker number not readable")
    if not gps.strip():       record["issues"].append("No GPS stamp found")

    critical = sum(1 for i in record["issues"] if "blurry" in i.lower() or "dark" in i.lower())
    if critical >= 2:    record["status"] = "Rejected"
    elif record["issues"]: record["status"] = "Manual Check"
    else:                  record["status"] = "Approved"

    return record

@app.route("/")
def index():
    static_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), "static")
    return send_from_directory(static_dir, "index.html")

@app.route("/upload", methods=["POST"])
def upload():
    files    = request.files.getlist("photos")
    reviewer = request.form.get("reviewer", "Team")
    results  = []
    seen = {r["id"] for r in photo_records}
    for f in files:
        if not f.filename: continue
        if Path(f.filename).suffix.lower() not in SUPPORTED_EXTS: continue
        save_path = UPLOAD_FOLDER / f.filename
        f.save(save_path)
        h = image_hash(save_path)[:8]
        if h in seen:
            results.append({"filename":f.filename,"status":"Duplicate","issues":["Already uploaded"],"id":h})
            continue
        rec = process_photo(save_path, f.filename, reviewer)
        photo_records.append(rec)
        seen.add(rec["id"])
        results.append(rec)
    return jsonify({"processed":len(results),"results":results})

@app.route("/records")
def get_records():
    return jsonify(photo_records)

@app.route("/stats")
def get_stats():
    by_loc = defaultdict(lambda:{"approved":0,"manual":0,"rejected":0,"total":0})
    for r in photo_records:
        loc = r.get("location","Unknown")
        by_loc[loc]["total"] += 1
        s = r.get("status","")
        if s=="Approved": by_loc[loc]["approved"]+=1
        elif s=="Manual Check": by_loc[loc]["manual"]+=1
        elif s=="Rejected": by_loc[loc]["rejected"]+=1
    return jsonify({
        "total":len(photo_records),
        "approved":sum(1 for r in photo_records if r["status"]=="Approved"),
        "manual":sum(1 for r in photo_records if r["status"]=="Manual Check"),
        "rejected":sum(1 for r in photo_records if r["status"]=="Rejected"),
        "duplicate":sum(1 for r in photo_records if r["status"]=="Duplicate"),
        "by_location":dict(by_loc)
    })

@app.route("/update", methods=["POST"])
def update():
    d = request.json
    for r in photo_records:
        if r["id"] == d.get("id"):
            if d.get("status"): r["status"] = d["status"]
            if d.get("design"): r["design"] = d["design"]
            if d.get("f_number"): r["f_number"] = d["f_number"]
            if d.get("location"): r["location"] = d["location"]
            break
    return jsonify({"ok":True})

@app.route("/image/<filename>")
def serve_image(filename):
    return send_from_directory(str(UPLOAD_FOLDER), filename)

@app.route("/export_excel")
def export_excel():
    try:
        import pandas as pd
        df = pd.DataFrame(photo_records)
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
        prs=Presentation()
        prs.slide_width=Inches(13.33); prs.slide_height=Inches(7.5)
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
        t(s1,f"{datetime.now().strftime('%d %B %Y')}  |  {len(photo_records)} photos processed",Inches(0.7),Inches(3.2),Inches(12),Inches(0.5),16,col=WHITE,al=PP_ALIGN.CENTER)
        for r in [x for x in photo_records if x.get("status")=="Approved"]:
            sl=prs.slides.add_slide(blank)
            try: sl.shapes.add_picture(r["filepath"],Inches(0.3),Inches(0.3),Inches(6.5),Inches(6.9))
            except: pass
            card=sl.shapes.add_shape(1,Inches(7.1),Inches(0.3),Inches(5.9),Inches(6.9))
            card.fill.solid(); card.fill.fore_color.rgb=DARK; card.line.fill.background()
            t(sl,"ETV AUTO STICKER",Inches(7.3),Inches(0.5),Inches(5.5),Inches(0.5),14,True,ACCENT)
            y=1.1
            for lbl,val in [("Location",r.get("location","—")),("Series/Number",f"{r.get('series','')} — {r.get('f_number','')}"),
                ("Design",r.get("design","—")),("Date/Time",r.get("datetime_stamp","—")),
                ("Reviewer",r.get("reviewer","—"))]:
                t(sl,lbl,Inches(7.3),Inches(y),Inches(5.5),Inches(0.25),8,True,GOLD)
                t(sl,str(val),Inches(7.3),Inches(y+0.25),Inches(5.5),Inches(0.4),13,col=WHITE)
                y+=0.82
            b=sl.shapes.add_shape(1,Inches(7.3),Inches(6.55),Inches(2.8),Inches(0.45))
            b.fill.solid(); b.fill.fore_color.rgb=GREEN; b.line.fill.background()
            t(sl,"APPROVED",Inches(7.3),Inches(6.57),Inches(2.8),Inches(0.4),12,True,WHITE,PP_ALIGN.CENTER)
        out=OUTPUT_FOLDER/"ETV_Campaign_Report.pptx"
        prs.save(str(out))
        return send_file(str(out.resolve()),as_attachment=True,download_name="ETV_Campaign_Report.pptx")
    except Exception as e:
        return jsonify({"error":str(e)}),500

if __name__=="__main__":
    print("\n"+"="*50)
    print("  ETV Auto Sticker Dashboard")
    print("  Open browser → http://localhost:5000")
    print("="*50+"\n")
    import os; app.run(debug=False, host="0.0.0.0", port=int(os.environ.get("PORT", 5000)))
