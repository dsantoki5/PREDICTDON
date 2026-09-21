# PredictCNC — AI Predictive Maintenance System

PredictCNC is an enterprise-grade AI-powered predictive maintenance platform designed for CNC machines. It processes multi-sensor telemetry (spindle speed, torque, air and process temperatures, tool wear) to predict machine failure risk, diagnose failure modes, automate maintenance ticketing, and generate compliance-ready operational reports.

## Architecture

This project is built using a modern decoupled architecture:

- **frontend/**: React 18, TypeScript, Vite, Tailwind CSS, Lucide icons, Chart.js.
- **backend/**: FastAPI (Python), Pydantic v2, SQLAlchemy ORM, JWT Authentication (PostgreSQL / SQLite ready).
- **ml/**: Machine Learning pipeline, model training, feature engineering, and inference engine.
- **docs/**: Comprehensive system architecture, migration notes, and API documentation.

---

## Quick Start Guide for Team Members

### 1. Backend Setup (FastAPI & Database)

```bash
cd backend
python -m venv .venv

# Windows:
.venv\Scripts\activate
# Linux/macOS:
# source .venv/bin/activate

pip install -r requirements.txt
cp .env.example .env

# Optional: Run the seeder to ensure all machines, users, predictions and maintenance tickets are loaded
python seed_db.py

# Start the Backend Server
uvicorn src.main:app --reload --port 8000
```
- Interactive API documentation will be available at: http://localhost:8000/docs
- Health check: http://localhost:8000/api/v1/health

### 2. Frontend Setup (React + Vite)

```bash
cd frontend
npm install
npm run dev
```
- The Web Dashboard will be available at: http://localhost:5173

### 3. Machine Learning Pipeline (LightGBM)

```bash
cd ml
pip install -r requirements.txt
python src/inference.py
```

---

## Database & Data

- Pre-loaded database file: `backend/predictcnc.db` (SQLite)
- SQL Dump file: `backend/database_dump.sql` (can be imported directly into PostgreSQL or SQLite)
- JSON Seed dataset: `backend/database_seed.json`
- Python Seeder: `python backend/seed_db.py`
- Raw Telemetry Training Dataset: `ml/data/raw/ai4i2020.csv`
- Pre-trained Production Models: `ml/models/LightGBM_No_SMOTE_Final.joblib` and `ml/models/final_lightgbm_model.pkl`

---

## Documentation
Refer to the `docs/` directory for detailed documentation:
- [System Architecture](docs/architecture.md)
- [Migration Notes](docs/migration-notes.md)
- [Database Schema](docs/database-schema.md)
