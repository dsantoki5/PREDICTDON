# PredictCNC — System Architecture Specification

## 1. Overview
PredictCNC is an academic/engineering predictive maintenance system built using the approved **Flask + Bootstrap + MySQL + LightGBM** technology stack.

```mermaid
graph TD
    Client[HTML5 + CSS3 + Bootstrap 5 + Chart.js UI] -->|HTTP Form / REST| App[Flask Backend (app.py)]
    App -->|Inference Engine| MLEngine[LightGBM Multi-Class ML Predictor]
    App -->|CRUD & Persistence| DB[(MySQL / PyMySQL Database)]
    App -->|Alert Dispatch| SMTP[Python smtplib + email.mime]
    SMTP -->|TLS 587| Gmail[Gmail SMTP Gateway]
    Gmail --> Supervisor[Machine Supervisor Email]
    App -->|PDF Generation| Reports[ReportLab Reporting Engine]
```

## 2. Technology Stack

### Frontend
- **Structure**: HTML5 Semantic markup
- **Styling**: CSS3 + Bootstrap 5.3 (Industrial Dark theme)
- **Scripting**: Vanilla JavaScript (ES6+)
- **Visualization**: Chart.js

### Backend
- **Framework**: Python Flask
- **Session & Auth**: Secure Flask Session with SHA-256 password hashing
- **Database Driver**: PyMySQL (compatible with XAMPP MySQL)
- **PDF Engine**: ReportLab

### Machine Learning
- **Algorithm**: LightGBM Multi-Class Classifier (`LightGBM_No_SMOTE_Final.joblib`)
- **Libraries**: Scikit-learn, Pandas, NumPy, Joblib
- **Feature Engineering**: 44 Physical & Rolling-window telemetry dimensions

### Email Alert Gateway
- **Transport**: Python `smtplib` + `email.mime`
- **Security**: TLS / STARTTLS on Port 587
- **Authentication**: Gmail App Password via `.env`
