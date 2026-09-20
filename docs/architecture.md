# PredictCNC — System Architecture Specification

## 1. Overview
PredictCNC transitions from a monolithic Flask server-side rendered (SSR) application to a decoupled, modular, microservice-ready system architecture.

`mermaid
graph TD
    Client[React + Vite Frontend (SPA)] -->|REST JSON / JWT| API[FastAPI Backend (/api/v1)]
    API -->|Inference| MLEngine[ML Inference Service (LightGBM)]
    API -->|CRUD & Persistence| DB[(Relational DB - SQLite / MySQL)]
    MLEngine -->|Model Artifacts| Models[(ml/models/*.pkl)]
    MLPipeline[ml/src/train.py] -->|Retrain & Evaluate| Models
`

## 2. Technology Stack

### Frontend
- **Framework**: React 18 / 19 with TypeScript
- **Build Tool**: Vite 6.x
- **Styling**: Tailwind CSS with custom Industrial Control Panel dark theme palette
- **Icons**: Lucide React
- **HTTP Client**: Axios with request/response interceptors for JWT token handling
- **Routing**: React Router v6

### Backend
- **API Framework**: FastAPI 0.141+ (Asynchronous, High-Performance, OpenAPI native)
- **Validation**: Pydantic v2 schemas
- **ORM / Database**: SQLAlchemy 2.0 (pluggable SQLite for lightweight dev, MySQL for enterprise production)
- **Authentication**: Stateless JWT (pyjwt) with rgon2 / crypt password hashing
- **Testing**: pytest + httpx TestClient

### Machine Learning
- **Core Classifier**: LightGBM (LGBMClassifier)
- **Supporting Libraries**: Scikit-Learn, Pandas, NumPy, Joblib
- **Feature Pipeline**: Hybrid physics-based domain features (rpm-torque interaction, thermal gradients, load density) + rolling historical window statistics.

## 3. Communication Strategy
- Communication between Frontend and Backend is strictly over JSON REST API.
- All endpoints are versioned under /api/v1/.
- Cross-Origin Resource Sharing (CORS) is explicitly configured to whitelist localhost dev servers.
- Auth tokens are passed via standard Authorization: Bearer <token> HTTP header.

## 4. Multi-Tenancy & Data Isolation
Unlike the legacy system where all machines were globally visible across all users:
- Every Machine, Prediction, and Maintenance ticket is strictly tied to an organization / company_id.
- Queries enforce organizational tenant filters at the repository/service layer.
