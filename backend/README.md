# PredictCNC — Backend API Service

FastAPI-powered REST API service providing predictive maintenance inference, fleet telemetry management, automated ticketing, and JWT authentication.

## Features
- **FastAPI 0.110+**: Asynchronous, auto-generating Swagger UI docs at `/docs`.
- **SQLAlchemy 2.0**: Pluggable database support (default SQLite for dev, MariaDB/MySQL for production).
- **Pydantic v2**: Strict validation for sensor readings and API contracts.
- **ML Integration**: Seamless bridge to LightGBM model in `ml/models/`.

## Running Locally
```bash
# 1. Install dependencies
pip install -r requirements.txt

# 2. Configure environment
cp .env.example .env

# 3. Start server
uvicorn src.main:app --reload --port 8000
```
Interactive docs: [http://localhost:8000/docs](http://localhost:8000/docs)

## Running Tests
```bash
pytest
```
