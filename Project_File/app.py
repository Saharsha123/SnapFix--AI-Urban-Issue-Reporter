import io
import logging
import numpy as np
import tensorflow as tf
from PIL import Image
from flask import Flask, request, jsonify
from flask_cors import CORS
import joblib
import psycopg2
from psycopg2.extras import RealDictCursor
from flask import render_template, redirect, url_for, session
from telegram import Bot
from fusion import fuse_predictions


bot = Bot(token='YOUR TELEGRAM TOKEN')


def get_db_connection():
    return psycopg2.connect(
        dbname="DB_NAME",
        user="DB_USER",
        password="DB_PASSWORD",
        host="DB_HOST",
        port= DB_PORT,
        cursor_factory=RealDictCursor,
    )


DEPT_MAP = {
    "pothole_road_crack": "Public Works Department (PWD)",
    "damaged_road_sign": "Transport Department (RTO / Traffic Engineering)",
    "garbage": "BBMP – Solid Waste Management (SWM)",
    "graffiti": "BBMP – Ward Maintenance / City Beautification Cell",
    "illegal_parking": "Traffic Police (Bengaluru Traffic Police)",
    "fallen_trees": "BBMP – Forest / Horticulture Wing",
    "damaged_concrete_structures": "PWD / BBMP Engineering",
    "damaged_electric_poles": "BESCOM (Electricity Supply Company)",
    "water_logging": "BBMP – Storm Water Drain (SWD) Dept",
    "no_electricity": "BESCOM",
}


import random, string


def generate_tracking_id():
    suffix = "".join(random.choices(string.ascii_uppercase + string.digits, k=6))
    return f"SNFX-2026-{suffix}"


# ================= CONFIG ================= #

BASE_DIR = os.path.dirname(__file__)

MODEL_PATH = os.path.join(BASE_DIR, "model_output", "image_model_mobilenet.keras")
TEXT_VEC_PATH = os.path.join(BASE_DIR, "text_vectorizer.joblib")
TEXT_CLF_PATH = os.path.join(BASE_DIR, "text_classifier.joblib")

CLASS_NAMES = [
    "damaged_concrete_structures",
    "damaged_electric_poles",
    "damaged_road_sign",
    "fallen_trees",
    "garbage",
    "graffiti",
    "illegal_parking",
    "no_electricity",
    "pothole_road_crack",
    "water_logging"
]

# ================= LOAD MODELS ================= #

logging.basicConfig(level=logging.INFO)

image_model = tf.keras.models.load_model(MODEL_PATH)
logging.info("✅ Image model loaded (MobileNet)")

text_vectorizer = joblib.load(TEXT_VEC_PATH)
text_classifier = joblib.load(TEXT_CLF_PATH)

# ================= APP ================= #

app = Flask(__name__)
CORS(app)
app.secret_key = "FLASK_SECRET_KEY"

# ================= AUTH (TEMP) ================= #

@app.route("/api/login", methods=["POST"])
def login():
    data = request.get_json()
    return jsonify({
        "id": 1,
        "name": "Test User",
        "email": data.get("email"),
        "phone": "0000000000",
        "user_type": data.get("userType", "citizen"),
    }), 200

# ================= CLASSIFY ================= #

@app.route("/api/classify", methods=["POST"])
def classify():
    logging.info("📥 /api/classify")

    file = request.files.get("file")
    description = request.form.get("description", "")

    img_probs = None
    txt_probs = None

    # ---------- IMAGE ----------
    if file:
        try:
            image = Image.open(io.BytesIO(file.read())).convert("RGB")
            image = image.resize((224, 224))
            arr = np.expand_dims(np.array(image) / 255.0, axis=0)
            img_probs = image_model.predict(arr)[0]
        except Exception:
            logging.exception("❌ Image inference failed")

    # ---------- TEXT ----------
    if description:
        try:
            X = text_vectorizer.transform([description])
            txt_probs = text_classifier.predict_proba(X)[0]
        except Exception:
            logging.exception("❌ Text inference failed")

    if img_probs is None and txt_probs is None:
        return jsonify({"error": "No valid input"}), 400
    
    print("IMAGE_PROBS:", img_probs)
    print("TEXT_PROBS :", txt_probs)

    # ---------- FUSION -----------
    final_label, final_conf, source = fuse_predictions(
        image_probs=img_probs,
        text_probs=txt_probs,
        class_names=CLASS_NAMES
    )

    # ---------- PRIORITY ----------
    if final_conf >= 0.85:
        priority = "High"
    elif final_conf >= 0.65:
        priority = "Medium"
    else:
        priority = "Low"

    logging.info(f"FINAL → {final_label} ({final_conf:.2f}) via {source}")

    return jsonify({
        "issueType": final_label,
        "probability": round(final_conf, 2),
        "priority": priority,
        "decisionSource": source
    }), 200

# ================= REPORT ================= #

@app.route("/api/report", methods=["POST"])
def create_report():
    data = request.get_json()

    user_id = 0
    issue_type = data.get("issueType")
    location = data.get("location")
    description = data.get("description", "")
    priority = data.get("priority", "Medium")

    lat = None
    lon = None
    if location:
        try:
            lat_str, lon_str = location.split(",")
            lat = float(lat_str.strip())
            lon = float(lon_str.strip())
        except Exception:
             pass

    telegram_id = data.get("telegram_id")

    probability = data.get("probability")
    decision_source = data.get("decisionSource")
    raw_label = data.get("rawLabel", issue_type)

    primary_dept = DEPT_MAP.get(issue_type, "Unknown")

    conn = get_db_connection()
    cur = conn.cursor()

    cur.execute(
        """
        INSERT INTO reports (
            userId, issueType, location, description, priority,
            status, telegram_id, primary_department,
            decision_source, probability, raw_label,
            latitude, longitude
        )
        VALUES (%s, %s, %s, %s, %s,
                'Pending', %s, %s,
                %s, %s, %s,
                %s, %s)
        RETURNING id;
        """,
        (
            user_id, issue_type, location, description, priority,
            telegram_id, primary_dept,
            decision_source, probability, raw_label,
            lat, lon,
        ),
    )

    row = cur.fetchone()
    numeric_id = row["id"] if isinstance(row, dict) else row[0]
    tracking_id = f"SNFX-{numeric_id:06d}"

    cur.execute(
        "UPDATE reports SET tracking_id = %s WHERE id = %s",
        (tracking_id, numeric_id),
    )

    conn.commit()
    cur.close()
    conn.close()

    return jsonify({"tracking_id": tracking_id}), 200

# ================= TRACK ================= #

@app.route("/api/track", methods=["GET"])
def track_report():
    tracking_id = request.args.get("id")
    if not tracking_id:
        return jsonify({"error": "tracking_id required"}), 400

    conn = get_db_connection()
    cur = conn.cursor()
    cur.execute(
        """
        SELECT tracking_id, issueType, status,
               primary_department, priority, remarks, timestamp,
               dept_status, dept_remarks
        FROM reports
        WHERE tracking_id = %s
        """,
        (tracking_id,),
    )
    row = cur.fetchone()
    cur.close()
    conn.close()

    if not row:
        return jsonify({"error": "Not found"}), 404

    return jsonify(row), 200

# ================= WEB-PAGE ================= #

@app.route('/admin/reports')
def admin_reports():
    status = request.args.get('status', '')
    dept = request.args.get('dept', '')
    
    try:
        conn = get_db_connection()
        cur = conn.cursor()
        
        base_sql = '''SELECT 
        tracking_id, 
        issueType,
        primary_department, 
        status, 
        priority, 
        timestamp, 
        probability, 
        assigned_dept_admin_id, 
        latitude, 
        longitude,
        dept_status,
        dept_remarks
      FROM reports 
      WHERE 1=1'''
        params = []
        
        if status:
            base_sql += ' AND status = %s'
            params.append(status)
        if dept:
            base_sql += ' AND primary_department = %s'
            params.append(dept)
        
        base_sql += ' ORDER BY timestamp DESC'
        
        print(f"DEBUG - SQL Query: {base_sql}")
        print(f"DEBUG - Params: {params}")
        
        cur.execute(base_sql, params)
        rows = cur.fetchall()
        
        print(f"DEBUG - Rows returned: {len(rows)}")
        if rows:
            print(f"DEBUG - First row: {rows[0]}")
        
        cur.execute('SELECT id, department FROM dept_admins ORDER BY department')
        dept_admins = cur.fetchall()
        
        cur.close()
        conn.close()
        
        return render_template('admin_reports.html', reports=rows, dept_admins=dept_admins, selected_status=status, selected_dept=dept)
    except Exception as e:
        print(f"Error in admin_reports: {e}")
        import traceback
        traceback.print_exc()
        return f"Error: {str(e)}", 500

# ================= ADMIN ASSIGN ================= #

@app.route("/admin/assign/<tracking_id>", methods=["POST"])
def admin_assign_report(tracking_id):
    dept_admin_id = request.form.get("dept_admin_id")
    
    conn = get_db_connection()
    cur = conn.cursor()
    cur.execute(
        "UPDATE reports SET assigned_dept_admin_id=%s, dept_status='Assigned' WHERE tracking_id=%s",
        (dept_admin_id, tracking_id),
    )
    conn.commit()
    cur.close()
    conn.close()
    
    return redirect(url_for("admin_reports"))

# ================= DEPT ADMIN LOGIN ================= #

@app.route('/dept/login', methods=['GET', 'POST'])
def deptlogin():
    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')
        
        conn = get_db_connection()
        cur = conn.cursor()
        cur.execute("SELECT id, department FROM dept_admins WHERE username = %s AND password = %s", 
                    (username, password,))
        deptadmin = cur.fetchone()
        cur.close()
        conn.close()
        
        if deptadmin:
            session['deptadminid'] = deptadmin['id']
            session['deptadmindepartment'] = deptadmin['department']
            return redirect(url_for('deptdashboard'))
        else:
            return render_template('dept_login.html', error='Invalid credentials')
    
    return render_template('dept_login.html')

# ================= DEPT ADMIN DASHBOARD ================= #

@app.route("/dept/dashboard")
def deptdashboard():
    if "deptadminid" not in session:
        return redirect(url_for("deptlogin"))
    
    deptadminid = session["deptadminid"]
    department = session["deptadmindepartment"]
    
    conn = get_db_connection()
    cur = conn.cursor()
    
    cur.execute(
    """SELECT tracking_id, issuetype, status, priority, timestamp, 
       dept_status, dept_remarks, description, location, latitude, longitude 
       FROM reports 
       WHERE assigned_dept_admin_id = %s AND (dept_status IS NULL OR dept_status != 'Resolved') 
       ORDER BY timestamp DESC""",
    (deptadminid,)
)
    reports = cur.fetchall()
    cur.close()
    conn.close()
    return render_template("dept_dashboard.html", reports=reports, department=department)

# ================= DEPT ADMIN REPORT DETAIL ================= #

@app.route("/dept/report/<tracking_id>", methods=["GET", "POST"])
def deptreportdetail(tracking_id):
    if "deptadminid" not in session:
        return redirect(url_for("deptlogin"))
    
    deptadminid = session["deptadminid"]
    
    if request.method == "POST":
        dept_status = str(request.form.get("deptstatus", "")).strip()
        dept_remarks = str(request.form.get("deptremarks", "")).strip()
        
        try:
            conn = get_db_connection()
            cursor = conn.cursor(cursor_factory=RealDictCursor)
            
            # Get report details BEFORE updating
            cursor.execute(
                "SELECT telegram_id, issueType FROM reports WHERE tracking_id = %s AND assigned_dept_admin_id = %s",
                (tracking_id, deptadminid)
            )
            reportrow = cursor.fetchone()
            
            if not reportrow:
                cursor.close()
                conn.close()
                return "Report not found or not assigned to you", 404
            
            telegram_id = reportrow["telegram_id"]
            issue_type = reportrow["issueType"]
            
            # Get department name
            cursor.execute(
                "SELECT department FROM dept_admins WHERE id = %s",
                (deptadminid,)
            )
            deptrow = cursor.fetchone()
            deptname = deptrow["department"] if deptrow else "Unknown"
            
            # UPDATE the status
            cursor.execute(
                "UPDATE reports SET dept_status = %s, dept_remarks = %s WHERE tracking_id = %s",
                (dept_status, dept_remarks, tracking_id)
            )
            conn.commit()
            
            # Send Telegram notification
            if telegram_id:
                statusmessages = {
                    "Assigned": f"🔔 Your complaint {tracking_id} has been assigned to {deptname}.",
                    "In Progress": f"⏳ Work is in progress on your complaint {tracking_id}.",
                    "Resolved": f"✅ Your complaint {tracking_id} has been resolved by {deptname}. Thank you!"
                }
                message = statusmessages.get(dept_status, f"📋 Status updated: {dept_status}")
                try:
                    bot.send_message(chat_id=int(telegram_id), text=message, parse_mode="Markdown")
                    print(f"✅ Telegram sent to {telegram_id}: {message}")
                except Exception as e:
                    print(f"❌ Telegram error: {e}")
            else:
                print(f"⚠️ No telegram_id found for {tracking_id}")
            
            cursor.close()
            conn.close()
            return redirect(url_for("deptdashboard"))
        
        except Exception as e:
            print(f"Error: {e}")
            import traceback
            traceback.print_exc()
            return f"Error: {str(e)}", 500
    
    # GET request - show the detail page
    try:
        conn = get_db_connection()
        cursor = conn.cursor(cursor_factory=RealDictCursor)
        cursor.execute(
            """SELECT tracking_id, issueType, status, priority, timestamp, 
               dept_status, dept_remarks, description, location, latitude, longitude, 
               probability, remarks 
               FROM reports 
               WHERE tracking_id = %s AND assigned_dept_admin_id = %s""",
            (tracking_id, deptadminid)
        )
        report = cursor.fetchone()
        cursor.close()
        conn.close()
        
        if not report:
            return "Report not found", 404
        
        # Convert Decimal to float for template rendering
        if report.get("probability") is not None:
            report["probability"] = float(report["probability"])
        if report.get("latitude") is not None:
            report["latitude"] = float(report["latitude"])
        if report.get("longitude") is not None:
            report["longitude"] = float(report["longitude"])
        
        return render_template("dept_report_detail.html", report=report)
    
    except Exception as e:
        print(f"Error: {e}")
        import traceback
        traceback.print_exc()
        return f"Error: {str(e)}", 500

        # ================= DEPT ADMIN LOGOUT ================= #

@app.route('/dept/logout')
def deptlogout():
    session.pop('deptadminid', None)
    session.pop('deptadmindepartment', None)
    return redirect(url_for('deptlogin'))


# ================= ROOT ================= #

@app.route("/")
def index():
    return render_template("home.html")


# ================= MAIN ================= #

if __name__ == "__main__":
    print("ROUTES:", app.url_map)
    app.run(debug=False, port=5000)