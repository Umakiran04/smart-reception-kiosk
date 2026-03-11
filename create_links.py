print("🔥🔥🔥 THIS APP.PY IS RUNNING 🔥🔥🔥")

from flask import (
    Flask, render_template, request, redirect,
    session, send_from_directory, send_file
)
import sqlite3
from datetime import datetime
import qrcode
from io import BytesIO
import base64
import os

app = Flask(__name__)
app.secret_key = "nrsc_secret_key"

VISITOR_DB = "visitors.db"
STAFF_DB = "nrsc.db"

# ---------------- DB CONNECTION HELPERS ----------------
def get_visitor_db():
    conn = sqlite3.connect(VISITOR_DB)
    conn.row_factory = sqlite3.Row
    return conn

def get_staff_db():
    conn = sqlite3.connect(STAFF_DB)
    conn.row_factory = sqlite3.Row
    return conn

# ---------------- QR CODE HELPER ----------------
def generate_qr_code(visitor_id, name, visit_date, visit_duration):
    qr_data = f"""
Visitor ID: {visitor_id}
Name: {name}
Visit Date: {visit_date}
Duration: {visit_duration}
"""
    qr = qrcode.QRCode(
        version=1,
        error_correction=qrcode.constants.ERROR_CORRECT_L,
        box_size=10,
        border=4
    )
    qr.add_data(qr_data)
    qr.make(fit=True)

    img = qr.make_image(fill_color="black", back_color="white")
    buffer = BytesIO()
    img.save(buffer, format="PNG")
    return "data:image/png;base64," + base64.b64encode(buffer.getvalue()).decode()

# ---------------- INIT VISITOR DB ----------------
def init_visitor_db():
    conn = sqlite3.connect(VISITOR_DB)
    cur = conn.cursor()
    cur.execute("""
        CREATE TABLE IF NOT EXISTS visitors (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT,
            email TEXT,
            phone TEXT,
            organization TEXT,
            profession TEXT,
            address TEXT,
            visit_date TEXT,
            visit_duration TEXT,
            purpose TEXT,
            person TEXT,
            staff_email TEXT,
            staff_phone TEXT,
            group_count INTEGER,
            date TEXT,
            time TEXT,
            status TEXT,
            qr_code TEXT,
            photo TEXT
        )
    """)
    conn.commit()
    conn.close()

init_visitor_db()

# ---------------- HOME ----------------
@app.route("/")
def home():
    return render_template("home.html")

# ---------------- VISITOR OPTIONS ----------------
@app.route("/visitor/options")
def visitor_options():
    return render_template("visitor_options.html")

# ---------------- VISITOR REGISTRATION ----------------
@app.route("/visitor", methods=["GET", "POST"])
def visitor():
    if request.method == "POST":
        now = datetime.now()
        conn = get_visitor_db()
        cur = conn.cursor()

        cur.execute("""
            INSERT INTO visitors (
                name, email, phone, organization, profession, address,
                visit_date, visit_duration, purpose, person,
                staff_email, staff_phone, group_count,
                date, time, status
            )
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, 'Pending')
        """, (
            request.form["name"],
            request.form["email"],
            request.form["phone"],
            request.form.get("organization"),
            request.form.get("profession"),
            request.form.get("address"),
            request.form["visit_date"],
            request.form["visit_duration"],
            request.form["purpose"],
            request.form["person"],
            None,
            None,
            request.form.get("group_size", 1),
            now.strftime("%d-%m-%Y"),
            now.strftime("%H:%M:%S")
        ))

        visitor_id = cur.lastrowid

        # ---------- PHOTO ----------
        photo_base64 = request.form.get("photo")
        if photo_base64:
            os.makedirs("uploads", exist_ok=True)
            photo_path = f"uploads/visitor_{visitor_id}.png"
            with open(photo_path, "wb") as f:
                f.write(base64.b64decode(photo_base64.split(",")[1]))
            cur.execute(
                "UPDATE visitors SET photo=? WHERE id=?",
                (photo_path, visitor_id)
            )

        conn.commit()
        conn.close()
        session["visitor_id"] = visitor_id
        return redirect("/visitor/status")

    conn = get_staff_db()
    cur = conn.cursor()
    cur.execute("SELECT staff_id, name FROM staff")
    staff_list = cur.fetchall()
    conn.close()
    return render_template("visitor.html", staff_list=staff_list)

# ---------------- VISITOR STATUS ----------------
@app.route("/visitor/status")
def visitor_status():
    visitor_id = session.get("visitor_id")
    if not visitor_id:
        return redirect("/visitor")

    conn = get_visitor_db()
    cur = conn.cursor()
    cur.execute("""
        SELECT
            id,
            name,
            phone,
            person,
            purpose,
            status,
            qr_code
        FROM visitors
        WHERE id = ?
    """, (visitor_id,))
    visitor = cur.fetchone()
    conn.close()

    return render_template("visitor_status.html", visitor=visitor)

# ---------------- GATE PASS (HTML) ----------------
@app.route("/gate_pass/<int:visitor_id>")
def gate_pass(visitor_id):
    conn = get_visitor_db()
    cur = conn.cursor()
    cur.execute("SELECT * FROM visitors WHERE id=?", (visitor_id,))
    visitor = cur.fetchone()
    conn.close()

    if not visitor or visitor["status"] != "Approved":
        return "Gate pass not available", 403

    return render_template("gate_pass.html", visitor=visitor)

# ---------------- STAFF LOGIN ----------------
@app.route("/staff", methods=["GET", "POST"])
def staff_login():
    if request.method == "POST":
        conn = get_staff_db()
        cur = conn.cursor()
        cur.execute(
            "SELECT name, role FROM staff WHERE staff_id=? AND password=?",
            (request.form["staff_id"], request.form["password"])
        )
        staff = cur.fetchone()
        conn.close()

        if staff:
            session["staff_id"] = request.form["staff_id"]
            session["name"] = staff["name"]
            session["role"] = staff["role"]
            return redirect("/staff/visitors")

        return render_template("staff_login.html", error="Invalid credentials")

    return render_template("staff_login.html")
# ---------------- STAFF APPROVE ----------------
@app.route("/staff/approve/<int:visitor_id>", methods=["GET", "POST"])
def staff_approve(visitor_id):
    if "staff_id" not in session:
        return redirect("/staff")

    conn = get_visitor_db()
    cur = conn.cursor()

    cur.execute(
        "SELECT name, visit_date, visit_duration FROM visitors WHERE id=?",
        (visitor_id,)
    )
    visitor = cur.fetchone()

    if visitor:
        qr = generate_qr_code(
            visitor_id,
            visitor["name"],
            visitor["visit_date"],
            visitor["visit_duration"]
        )
        cur.execute(
            "UPDATE visitors SET status='Approved', qr_code=? WHERE id=?",
            (qr, visitor_id)
        )

    conn.commit()
    conn.close()
    return redirect("/staff/visitors")


# ---------------- STAFF REJECT ----------------
@app.route("/staff/reject/<int:visitor_id>", methods=["GET", "POST"])
def staff_reject(visitor_id):
    if "staff_id" not in session:
        return redirect("/staff")

    conn = get_visitor_db()
    cur = conn.cursor()
    cur.execute(
        "UPDATE visitors SET status='Rejected' WHERE id=?",
        (visitor_id,)
    )
    conn.commit()
    conn.close()
    return redirect("/staff/visitors")

# ---------------- STAFF VISITORS ----------------
@app.route("/staff/visitors")
def staff_visitors():
    if "staff_id" not in session:
        return redirect("/staff")

    conn = get_visitor_db()
    cur = conn.cursor()
    cur.execute(
        "SELECT * FROM visitors WHERE person=? ORDER BY id DESC",
        (session["staff_id"],)
    )
    visitors = [dict(row) for row in cur.fetchall()]
    conn.close()

    staff = {
        "staff_id": session["staff_id"],
        "name": session["name"],
        "designation": session["role"]
    }

    return render_template("staff_visitors.html", visitors=visitors, staff=staff)

# ---------------- ADMIN LOGIN ----------------
@app.route("/admin_login", methods=["GET", "POST"])
def admin_login():
    if request.method == "POST":
        conn = get_staff_db()
        cur = conn.cursor()
        cur.execute(
            "SELECT username FROM admin WHERE username=? AND password=?",
            (request.form["username"], request.form["password"])
        )
        admin = cur.fetchone()
        conn.close()

        if admin:
            session["admin_logged_in"] = True
            session["admin_name"] = admin["username"]
            return redirect("/admin_dashboard")

        return render_template("admin_login.html", error="Invalid credentials")

    return render_template("admin_login.html")

# ---------------- ADMIN DASHBOARD ----------------
@app.route("/admin_dashboard")
def admin_dashboard():
    if "admin_logged_in" not in session:
        return redirect("/admin_login")
    return render_template("admin_dashboard.html", admin_name=session["admin_name"])

# ---------------- ADMIN VISITORS ----------------
@app.route("/admin/visitors")
def admin_visitors():
    if "admin_logged_in" not in session:
        return redirect("/admin_login")

    conn = get_visitor_db()
    cur = conn.cursor()
    cur.execute("SELECT * FROM visitors ORDER BY id DESC")
    visitors = cur.fetchall()
    conn.close()

    return render_template("admin_visitors.html", visitors=visitors)

# ---------------- ADMIN VIEW PDF (FINAL) ----------------
@app.route("/admin/view_pdf/<int:visitor_id>")
def admin_view_pdf(visitor_id):
    if "admin_logged_in" not in session:
        return redirect("/admin_login")

    from reportlab.lib.pagesizes import A4
    from reportlab.pdfgen import canvas
    from reportlab.lib.utils import ImageReader

    conn = get_visitor_db()
    cur = conn.cursor()
    cur.execute("SELECT * FROM visitors WHERE id=?", (visitor_id,))
    v = cur.fetchone()
    conn.close()

    if not v:
        return "Visitor not found", 404

    buffer = BytesIO()
    pdf = canvas.Canvas(buffer, pagesize=A4)
    width, height = A4

    pdf.setFont("Helvetica-Bold", 18)
    pdf.drawCentredString(width/2, height-40, "NRSC – VISITOR GATE PASS")

    # PHOTO
    photo_y = height - 220
    if v["photo"] and os.path.exists(v["photo"]):
        pdf.drawImage(
            ImageReader(v["photo"]),
            40, photo_y, width=120, height=150, mask="auto"
        )

    # DETAILS BELOW PHOTO
    y = photo_y - 20
    pdf.setFont("Helvetica", 11)

    for label in [
        "name","email","phone","organization","profession",
        "address","purpose","person","visit_date",
        "visit_duration","group_count","date","time"
    ]:
        pdf.drawString(40, y, f"{label.replace('_',' ').title()} : {v[label]}")
        y -= 18

    # QR
    if v["qr_code"]:
        qr_img = ImageReader(
            BytesIO(base64.b64decode(v["qr_code"].split(",")[1]))
        )
        pdf.drawImage(qr_img, width-200, height-260, 140, 140)

    pdf.showPage()
    pdf.save()
    buffer.seek(0)

    return send_file(
        buffer,
        mimetype="application/pdf",
        download_name=f"visitor_{visitor_id}.pdf",
        as_attachment=False
    )
@app.route("/admin/staff")
def admin_staff():
    if "admin_logged_in" not in session:
        return redirect("/admin_login")

    conn = get_staff_db()
    cur = conn.cursor()
    cur.execute("SELECT * FROM staff ORDER BY staff_id")
    staff = cur.fetchall()
    conn.close()


    return render_template("admin_staff.html", staff=staff)

@app.route("/admin/staff-visitor-count")
def admin_staff_visitor_count():
    if "admin_logged_in" not in session:
        return redirect("/admin_login")

    conn = get_visitor_db()
    cur = conn.cursor()
    cur.execute("""
        SELECT person, COUNT(*) AS visitor_count
        FROM visitors
        GROUP BY person
    """)
    data = cur.fetchall()
    conn.close()

    return render_template("staff_visitor_count.html", data=data)

# ---------------- LOGOUT ----------------
@app.route("/logout")
def logout():
    session.clear()
    return redirect("/")

# ---------------- SERVE UPLOADS ----------------
@app.route("/uploads/<path:filename>")
def uploaded_file(filename):
    return send_from_directory("uploads", filename)

# ---------------- CSIF PAGE ----------------
# ---------------- CSIF / AADHAAR VERIFICATION (FINAL, STRICT) ----------------
import json
from datetime import datetime

# Load Aadhaar JSON database ONCE
with open("aadhaar_db.json", "r") as f:
    AADHAAR_DB = json.load(f)

# ✅ MAIN CSIF PAGE + ALL ALIASES
@app.route("/csif", methods=["GET", "POST"])
@app.route("/csif_verification", methods=["GET", "POST"])
@app.route("/visitor/aadhaar", methods=["GET", "POST"])
def csif():
    if request.method == "POST":
        aadhaar = request.form.get("aadhaar", "").strip()
        dob_input = request.form.get("dob", "").strip()  # comes as YYYY-MM-DD from date picker

        # ---------- STRICT VALIDATION ----------
        if not aadhaar or not dob_input:
            return render_template(
                "visitor_aadhaar.html",
                error="All fields are required."
            )

        if not (aadhaar.isdigit() and len(aadhaar) == 12):
            return render_template(
                "visitor_aadhaar.html",
                error="Aadhaar must be exactly 12 digits."
            )

        # 🔒 STRICT DATE FORMAT (HTML date input)
        try:
            dob_formatted = datetime.strptime(
                dob_input, "%Y-%m-%d"
            ).strftime("%Y-%m-%d")
        except ValueError:
            return render_template(
                "visitor_aadhaar.html",
                error="Invalid date format."
            )

        user = AADHAAR_DB.get(aadhaar)

        if not user:
            return render_template(
                "visitor_aadhaar.html",
                error="Aadhaar number not found."
            )

        if user["dob"] != dob_formatted:
            return render_template(
                "visitor_aadhaar.html",
                error="Date of Birth does not match."
            )

        # ✅ VERIFIED
        return render_template(
            "visitor_aadhaar.html",
            success=True,
            name=user["name"]
        )

    # GET request → show form
    return render_template("visitor_aadhaar.html")



# ---------------- RUN ----------------
if __name__ == "__main__":
    app.run(debug=True)
