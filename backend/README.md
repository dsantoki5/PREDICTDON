# PredictCNC — Backend Service

Flask-powered service providing predictive maintenance inference, fleet telemetry management, automated ticketing, audit logging, and role-based access control.

## Features
- **Flask 3.0+**: Session-based authentication and REST APIs.
- **PostgreSQL**: High-performance relational database persistence with psycopg2-binary.
- **ML Integration**: Seamless bridge to LightGBM multi-class model with 44 physics features.
- **Automated Alerts**: Non-blocking Gmail SMTP dispatch with cooldown duplicate suppression.

## Running Locally
```bash
# 1. Install dependencies
pip install -r requirements.txt

# 2. Configure environment
# Ensure .env has PostgreSQL credentials (PG_HOST, PG_PORT, PG_USER, PG_PASSWORD, PG_DB)

# 3. Start server
python app.py
```
Application interface: [http://localhost:5000](http://localhost:5000)

## Running Tests
```bash
python -m unittest discover -s tests
```
