"""
PredictCNC Flask Application — Main Entry Point.
Serving HTML5 + Bootstrap 5 UI & RESTful APIs powered by LightGBM & PyMySQL.
"""
import os
import sys
from datetime import datetime
from functools import wraps
from flask import Flask, render_template, request, jsonify, session, redirect, url_for, send_file, flash
from dotenv import load_dotenv

# Ensure backend root is in sys.path
backend_dir = os.path.dirname(os.path.abspath(__file__))
if backend_dir not in sys.path:
    sys.path.insert(0, backend_dir)

load_dotenv(os.path.join(backend_dir, ".env"))

from db import init_db, seed_default_data, query_all, query_one
from services.auth_service import AuthService
from services.machine_service import MachineService
from services.prediction_service import PredictionService
from services.maintenance_service import MaintenanceService
from services.reports_service import ReportsService
from services.email_service import EmailService

app = Flask(
    __name__,
    template_folder=os.path.join(backend_dir, "templates"),
    static_folder=os.path.join(backend_dir, "static")
)
app.secret_key = os.getenv("SECRET_KEY", "predictcnc-academic-session-key-2026")

# Initialize database schema and seeds
with app.app_context():
    seed_default_data()

# ---------------------------------------------------------------------
# Authentication Decorator
# ---------------------------------------------------------------------
def login_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if "user_id" not in session:
            if request.path.startswith("/api/"):
                return jsonify({"detail": "Authentication required. Please log in."}), 401
            return redirect(url_for("login_page"))
        return f(*args, **kwargs)
    return decorated_function

# Context processor for templates
@app.context_processor
def inject_user():
    return {
        "current_user": session.get("user"),
        "now": datetime.now(),
        "str": str
    }

# ---------------------------------------------------------------------
# HTML Template Views
# ---------------------------------------------------------------------
@app.route("/")
def index():
    if "user_id" in session:
        return redirect(url_for("dashboard_page"))
    return redirect(url_for("login_page"))

@app.route("/login", methods=["GET", "POST"])
def login_page():
    if request.method == "POST":
        company_name = request.form.get("company_name", "").strip()
        username = request.form.get("username", "").strip()
        password = request.form.get("password", "").strip()
        user = AuthService.authenticate_user(username, password, company_name=company_name)
        if user:
            session["user_id"] = user["id"]
            session["user"] = {
                "id": user["id"],
                "username": user["username"],
                "admin_name": user["admin_name"],
                "company_name": user["company_name"],
                "email": user["email"],
                "role": user["role"]
            }
            return redirect(url_for("dashboard_page"))
        else:
            flash("Invalid username or password.", "danger")
    return render_template("login.html")

@app.route("/register", methods=["GET", "POST"])
def register_page():
    if request.method == "POST":
        company = request.form.get("company_name", "").strip()
        name = request.form.get("admin_name", "").strip()
        email = request.form.get("email", "").strip()
        username = request.form.get("username", "").strip()
        password = request.form.get("password", "").strip()
        try:
            AuthService.register_user(company, name, email, username, password)
            flash("Registration successful! Please log in.", "success")
            return redirect(url_for("login_page"))
        except Exception as e:
            flash(str(e), "danger")
    return render_template("register.html")

@app.route("/logout")
def logout():
    session.clear()
    flash("You have been logged out.", "info")
    return redirect(url_for("login_page"))

@app.route("/dashboard")
@login_required
def dashboard_page():
    user_id = session.get("user_id")
    metrics = ReportsService.get_summary_metrics(user_id)
    machines = MachineService.get_all_machines(user_id)
    recent_history = PredictionService.get_history(user_id=user_id, limit=5)
    return render_template(
        "dashboard.html",
        metrics=metrics,
        machines=machines,
        recent_history=recent_history
    )

@app.route("/predict")
@login_required
def predict_page():
    machines = MachineService.get_all_machines(session.get("user_id"))
    return render_template("predict.html", machines=machines)

@app.route("/machines")
@login_required
def machines_page():
    machines = MachineService.get_all_machines(session.get("user_id"))
    return render_template("machines.html", machines=machines)

@app.route("/maintenance")
@login_required
def maintenance_page():
    tickets = MaintenanceService.get_all_tickets(session.get("user_id"))
    machines = MachineService.get_all_machines(session.get("user_id"))
    return render_template("maintenance.html", tickets=tickets, machines=machines)

@app.route("/history")
@login_required
def history_page():
    user_id = session.get("user_id")
    history = PredictionService.get_history(user_id=user_id, limit=100)
    machines = MachineService.get_all_machines(user_id)
    return render_template("history.html", history=history, machines=machines)

@app.route("/reports")
@login_required
def reports_page():
    user_id = session.get("user_id")
    metrics = ReportsService.get_summary_metrics(user_id)
    return render_template("reports.html", metrics=metrics)

# ---------------------------------------------------------------------
# JSON API Endpoints
# ---------------------------------------------------------------------
@app.route("/api/health")
def api_health():
    smtp_ready = EmailService.is_configured()
    return jsonify({
        "status": "healthy",
        "service": "PredictCNC Flask Engine",
        "stack": "Flask + MySQL + LightGBM + smtplib",
        "smtp_configured": smtp_ready,
        "timestamp": datetime.now().isoformat()
    })

@app.route("/api/auth/login", methods=["POST"])
def api_login():
    data = request.get_json() or {}
    company_name = data.get("company_name", "").strip()
    username = data.get("username", "")
    password = data.get("password", "")
    user = AuthService.authenticate_user(username, password, company_name=company_name)
    if not user:
        return jsonify({"detail": "Invalid username or password"}), 401
    
    session["user_id"] = user["id"]
    user_info = {
        "id": user["id"],
        "username": user["username"],
        "admin_name": user["admin_name"],
        "company_name": user["company_name"],
        "email": user["email"],
        "role": user["role"]
    }
    session["user"] = user_info
    return jsonify({"message": "Login successful", "user": user_info})

@app.route("/api/auth/register", methods=["POST"])
def api_register():
    data = request.get_json() or {}
    company = data.get("company_name", "").strip()
    name = data.get("admin_name", "").strip()
    email = data.get("email", "").strip()
    username = data.get("username", "").strip()
    password = data.get("password", "").strip()
    
    if not all([company, name, email, username, password]):
        return jsonify({"detail": "All fields are required"}), 400
    try:
        new_id = AuthService.register_user(company, name, email, username, password)
        return jsonify({"message": "Account created successfully", "user_id": new_id}), 201
    except Exception as e:
        return jsonify({"detail": str(e)}), 400

@app.route("/api/auth/reset-password", methods=["POST"])
def api_reset_password():
    data = request.get_json() or {}
    identifier = data.get("identifier", "").strip()
    new_password = data.get("new_password", "").strip()
    company_name = data.get("company_name", "").strip()
    if not identifier or not new_password:
        return jsonify({"detail": "Identifier and new password are required"}), 400
    try:
        AuthService.reset_password(identifier, new_password, company_name)
        return jsonify({"message": "Password reset successfully! Please log in with your new password."})
    except Exception as e:
        return jsonify({"detail": str(e)}), 400

@app.route("/api/auth/logout", methods=["POST"])
def api_logout():
    session.clear()
    return jsonify({"message": "Logged out successfully"})

@app.route("/api/auth/me")
@login_required
def api_me():
    return jsonify(session.get("user"))

@app.route("/api/machines", methods=["GET", "POST"])
@login_required
def api_machines():
    user_id = session.get("user_id")
    if request.method == "POST":
        data = request.get_json() or {}
        try:
            m_id = MachineService.create_machine(
                user_id=user_id,
                machine_code=data["machine_code"],
                machine_name=data["machine_name"],
                department=data.get("department"),
                manufacturer=data.get("manufacturer"),
                installation_date=data.get("installation_date"),
                supervisor_name=data.get("supervisor_name"),
                supervisor_email=data.get("supervisor_email")
            )
            return jsonify({"id": m_id, "message": "Machine registered successfully"}), 201
        except Exception as e:
            return jsonify({"detail": str(e)}), 400
    
    machines = MachineService.get_all_machines(user_id)
    return jsonify(machines)

@app.route("/api/machines/<int:machine_id>", methods=["GET", "PUT", "DELETE"])
@login_required
def api_machine_detail(machine_id):
    if request.method == "GET":
        m = MachineService.get_machine_by_id(machine_id)
        if not m:
            return jsonify({"detail": "Machine not found"}), 404
        return jsonify(m)

    elif request.method == "PUT":
        data = request.get_json() or {}
        success = MachineService.update_machine(
            machine_id=machine_id,
            machine_name=data["machine_name"],
            department=data.get("department"),
            manufacturer=data.get("manufacturer"),
            installation_date=data.get("installation_date"),
            status=data.get("status"),
            supervisor_name=data.get("supervisor_name"),
            supervisor_email=data.get("supervisor_email")
        )
        if not success:
            return jsonify({"detail": "Machine not found or update failed"}), 404
        return jsonify({"message": "Machine updated successfully"})

    elif request.method == "DELETE":
        success = MachineService.delete_machine(machine_id)
        if not success:
            return jsonify({"detail": "Machine not found"}), 404
        return jsonify({"message": "Machine deleted successfully"})

@app.route("/api/predict", methods=["POST"])
@login_required
def api_predict():
    """
    Core AI prediction endpoint.
    Runs LightGBM inference, persists to MySQL, and triggers Gmail SMTP alert.
    """
    data = request.get_json() or {}
    try:
        machine_id = int(data.get("machine_id", 0))
        air_t = float(data.get("air_temperature", 298.0))
        proc_t = float(data.get("process_temperature", 308.0))
        rpm = float(data.get("rotational_speed", 1500.0))
        torque = float(data.get("torque", 40.0))
        tool_wear = float(data.get("tool_wear", 0.0))

        result = PredictionService.run_prediction(
            machine_id=machine_id,
            air_temperature=air_t,
            process_temperature=proc_t,
            rotational_speed=rpm,
            torque=torque,
            tool_wear=tool_wear
        )
        return jsonify(result), 200
    except ValueError as ve:
        return jsonify({"detail": str(ve)}), 400
    except Exception as ex:
        app.logger.error(f"Prediction execution failed: {ex}")
        return jsonify({"detail": f"Internal Prediction Error: {str(ex)}"}), 500

@app.route("/api/history", methods=["GET"])
@login_required
def api_history():
    user_id = session.get("user_id")
    machine_id = request.args.get("machine_id", type=int)
    limit = request.args.get("limit", default=100, type=int)
    history = PredictionService.get_history(machine_id=machine_id, user_id=user_id, limit=limit)
    return jsonify(history)

@app.route("/api/history/<int:item_id>", methods=["DELETE"])
@login_required
def api_delete_history(item_id):
    success = PredictionService.delete_history_item(item_id)
    if not success:
        return jsonify({"detail": "History record not found"}), 404
    return jsonify({"message": "History record deleted successfully"})

@app.route("/api/maintenance", methods=["GET", "POST"])
@login_required
def api_maintenance():
    if request.method == "POST":
        data = request.get_json() or {}
        try:
            t_id = MaintenanceService.create_ticket(
                machine_id=int(data["machine_id"]),
                priority=data.get("priority", "Medium"),
                remarks=data.get("remarks"),
                prediction_id=data.get("prediction_id")
            )
            return jsonify({"id": t_id, "message": "Ticket created successfully"}), 201
        except Exception as e:
            return jsonify({"detail": str(e)}), 400

    tickets = MaintenanceService.get_all_tickets(session.get("user_id"))
    return jsonify(tickets)

@app.route("/api/maintenance/<int:ticket_id>", methods=["PUT", "DELETE"])
@login_required
def api_maintenance_detail(ticket_id):
    if request.method == "PUT":
        data = request.get_json() or {}
        success = MaintenanceService.update_ticket_status(
            ticket_id=ticket_id,
            status=data.get("status", "Pending"),
            remarks=data.get("remarks")
        )
        if not success:
            return jsonify({"detail": "Ticket not found"}), 404
        return jsonify({"message": "Ticket updated successfully"})

    elif request.method == "DELETE":
        success = MaintenanceService.delete_ticket(ticket_id)
        if not success:
            return jsonify({"detail": "Ticket not found"}), 404
        return jsonify({"message": "Ticket deleted successfully"})

@app.route("/api/reports/metrics")
@login_required
def api_reports_metrics():
    metrics = ReportsService.get_summary_metrics(session.get("user_id"))
    return jsonify(metrics)

@app.route("/api/reports/pdf")
@login_required
def api_reports_pdf():
    pdf_buffer = ReportsService.generate_pdf_report(session.get("user_id"))
    return send_file(
        pdf_buffer,
        mimetype="application/pdf",
        as_attachment=True,
        download_name=f"PredictCNC_Maintenance_Report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.pdf"
    )

@app.route("/api/notifications")
@login_required
def api_notifications():
    user_id = session.get("user_id")
    if user_id:
        logs = query_all("""
            SELECT n.*, m.machine_code, m.machine_name 
            FROM notification_logs n 
            JOIN machines m ON n.machine_id = m.id 
            WHERE m.user_id = %s
            ORDER BY n.sent_at DESC LIMIT 50
        """, (user_id,))
    else:
        logs = query_all("""
            SELECT n.*, m.machine_code, m.machine_name 
            FROM notification_logs n 
            JOIN machines m ON n.machine_id = m.id 
            ORDER BY n.sent_at DESC LIMIT 50
        """)
    return jsonify(logs)

# ---------------------------------------------------------------------
# Application Runner
# ---------------------------------------------------------------------
if __name__ == "__main__":
    port = int(os.getenv("FLASK_PORT", 5000))
    app.run(host="0.0.0.0", port=port, debug=True)
