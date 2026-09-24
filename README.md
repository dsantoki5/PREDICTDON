# PredictCNC — AI Predictive Maintenance System

PredictCNC is an industrial AI predictive maintenance platform designed for CNC machinery. It processes multi-sensor telemetry (spindle rotational speed, torque, air and process temperatures, and tool wear) to predict machine failure risk, diagnose root-cause anomalies, automate maintenance work orders, and dispatch real-time Gmail SMTP alerts.

---

## 1. Approved Technology Stack

PredictCNC is strictly built using the following approved engineering and academic stack:

### Frontend
- **HTML5 & CSS3**
- **JavaScript (Vanilla ES6+)**
- **Bootstrap 5.3**

### Backend
- **Python 3.10+**
- **Flask** (Modular routing, session authentication, and REST APIs)

### Artificial Intelligence / Machine Learning
- **LightGBM** (Authoritative 44-feature multi-class classifier `LightGBM_No_SMOTE_Final.joblib`)
- **Scikit-learn**
- **Pandas**
- **NumPy**
- **Joblib**

### Database
- **PostgreSQL & psycopg2-binary** (Native relational database on `localhost:5432`)

### Visualization
- **Chart.js** (Interactive health gauges and telemetry trend charts)
- **Matplotlib** (Statistical distribution plots)

### Reporting
- **ReportLab** (Compliance-ready automated executive PDF maintenance reports)

### Email Notifications
- **Python smtplib**
- **Python email.mime**
- **Gmail SMTP Gateway** (TLS / STARTTLS on Port 587)

### Development Environment
- **Visual Studio Code**
- **Git & GitHub**
- **PostgreSQL Server (Port 5432)**

---

## 2. System Architecture

```
User (Web Browser)
        ↓
HTML5 + CSS3 + JavaScript + Bootstrap 5 + Chart.js
        ↓ (HTTP / REST)
Python Flask (app.py)
        ↓
PostgreSQL Database (psycopg2)
        ↓
Feature Engineering (44 Dynamic Physics Dimensions)
        ↓
LightGBM Multi-Class ML Inference
        ↓
Machine Health Classification
├── NORMAL (Class 0)   ──> Normal Operation (No Email)
├── WARNING (Class 1)  ──> Python smtplib / email.mime ──> Gmail SMTP ──> Supervisor Email
└── CRITICAL (Class 2) ──> Python smtplib / email.mime ──> Gmail SMTP ──> Supervisor Email
```

---

## 3. Quick Start Guide

### Prerequisites
- Python 3.10+ installed
- PostgreSQL (running on port 5432)

### Installation

1. **Clone the repository and navigate to backend**:
   ```bash
   cd backend
   ```

2. **Install Python dependencies**:
   ```bash
   pip install -r requirements.txt
   ```

3. **Configure Environment Variables (`backend/.env`)**:
   ```env
   SECRET_KEY=predictcnc-academic-secret-key-2026
   FLASK_ENV=development
   FLASK_PORT=5000

   # PostgreSQL Configuration
   PG_HOST=localhost
   PG_PORT=5432
   PG_USER=postgres
   PG_PASSWORD=your_postgres_password
   PG_DB=predictcnc

   # Gmail SMTP Configuration
   SMTP_HOST=smtp.gmail.com
   SMTP_PORT=587
   SMTP_USER=your-email@gmail.com
   SMTP_PASSWORD=your-16-character-app-password
   SMTP_FROM=your-email@gmail.com
   SMTP_ALERT_COOLDOWN_MINUTES=15
   DEFAULT_SUPERVISOR_EMAIL=supervisor@predictcnc.local
   ```

4. **Seed Database**:
   ```bash
   python seed_db.py
   ```

5. **Start Flask Server**:
   ```bash
   python app.py
   ```
   Open your browser at **http://localhost:5000**

---

## 4. Default Credentials

- **Username**: `admin`
- **Password**: `admin123`

---

## 5. Gmail SMTP Alert System

### Alert Trigger Policy
| Machine Status | AI Probability | Action Taken |
| :--- | :--- | :--- |
| **NORMAL** | $< 25\%$ | No email dispatched (`skipped_healthy`). |
| **WARNING** | $25\% - 75\%$ | High-priority Warning alert with telemetry snapshot & preventative maintenance checklist. |
| **CRITICAL** | $> 75\%$ | Emergency Critical alert with root-cause analysis + automated High priority ticket. |

### Gmail App Password Setup
1. Go to **Google Account** &rarr; **Security**.
2. Enable **2-Step Verification**.
3. Go to **App Passwords** and generate a 16-character password for `PredictCNC`.
4. Add your email and 16-character password to `backend/.env`.

### Anti-Spam Cooldown & Fault Tolerance
- **Duplicate Suppression**: Repeated Warning alerts within 15 minutes (`SMTP_ALERT_COOLDOWN_MINUTES=15`) are suppressed to prevent inbox flooding.
- **Non-Blocking Execution**: If the SMTP server is unavailable or credentials are invalid, the prediction still completes instantly with 100% success and the incident is logged safely in `notification_logs`.

---

## 6. Automated Testing

Run the full stack test suite:
```bash
python -m unittest tests/test_predictcnc_stack.py -v
```

All 9 test cases cover:
1. NORMAL prediction (No email)
2. WARNING alert dispatch
3. CRITICAL alert dispatch
4. SMTP network failure resilience
5. Missing supervisor email safe handling
6. Invalid credentials handling
7. Duplicate alert cooldown suppression
8. ReportLab PDF generation
9. Flask endpoints and REST APIs
