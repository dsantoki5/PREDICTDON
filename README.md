# PredictCNC — AI Predictive Maintenance System

PredictCNC is an enterprise-grade AI-powered predictive maintenance platform designed for CNC machines. It processes multi-sensor telemetry (spindle speed, torque, air and process temperatures, tool wear) to predict machine failure risk, diagnose failure modes, automate maintenance ticketing, and generate compliance-ready operational reports.

## Architecture

This project is built using a modern decoupled architecture:

- **rontend/**: React 18, TypeScript, Vite, Tailwind CSS, Lucide icons, Chart.js.
- **ackend/**: FastAPI (Python), Pydantic v2, SQLAlchemy ORM, JWT Authentication.
- **ml/**: Machine Learning pipeline, model training, feature engineering, and inference engine.
- **docs/**: Comprehensive system architecture, migration notes, and API documentation.

## Getting Started

### 1. Backend Setup
`ash
cd backend
python -m venv .venv
# Windows:
.venv\Scripts\activate
pip install -r requirements.txt
cp .env.example .env
uvicorn src.main:app --reload --port 8000
`
Interactive API docs will be available at http://localhost:8000/docs.

### 2. Frontend Setup
`ash
cd frontend
npm install
npm run dev
`
The dashboard will be available at http://localhost:5173.

### 3. Machine Learning Pipeline
`ash
cd ml
pip install -r requirements.txt
python src/inference.py
`

## Documentation
Refer to the [docs/](docs/) directory for:
- [System Architecture](docs/architecture.md)
- [Migration Notes](docs/migration-notes.md)
- [Database Schema](docs/database-schema.md)
