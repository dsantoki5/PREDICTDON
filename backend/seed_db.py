"""
Database Seeder Script for PredictCNC.
Loads initial user accounts, CNC machines, historical predictions, and maintenance tickets
from database_seed.json into the target database configured in backend Settings / .env.

Usage:
    python seed_db.py
"""
import os
import json
from datetime import datetime, date
from decimal import Decimal
from src.database.session import SessionLocal, Base, engine
from src.models.user import User
from src.models.machine import Machine
from src.models.prediction import Prediction
from src.models.maintenance import MaintenanceTicket

def seed_database():
    print("--- Initializing PredictCNC Database Schema ---")
    Base.metadata.create_all(bind=engine)
    
    seed_file_path = os.path.join(os.path.dirname(__file__), "database_seed.json")
    if not os.path.exists(seed_file_path):
        print(f"Seed file not found at {seed_file_path}")
        return

    with open(seed_file_path, "r", encoding="utf-8") as f:
        data = json.load(f)

    db = SessionLocal()
    try:
        users = data.get("users", [])
        machines = data.get("machines", [])
        predictions = data.get("predictions", [])
        maintenance = data.get("maintenance", [])

        # 1. Seed Users
        existing_users = {u.id for u in db.query(User.id).all()}
        users_added = 0
        for u in users:
            if u["id"] not in existing_users:
                item = u.copy()
                if item.get("created_at"):
                    item["created_at"] = datetime.fromisoformat(item["created_at"])
                db.add(User(**item))
                users_added += 1

        # 2. Seed Machines
        existing_machines = {m.id for m in db.query(Machine.id).all()}
        machines_added = 0
        for m in machines:
            if m["id"] not in existing_machines:
                item = m.copy()
                if item.get("installation_date"):
                    item["installation_date"] = date.fromisoformat(item["installation_date"])
                if item.get("created_at"):
                    item["created_at"] = datetime.fromisoformat(item["created_at"])
                db.add(Machine(**item))
                machines_added += 1

        # 3. Seed Predictions
        existing_preds = {p.id for p in db.query(Prediction.id).all()}
        preds_added = 0
        for p in predictions:
            if p["id"] not in existing_preds:
                item = p.copy()
                if item.get("predicted_at"):
                    item["predicted_at"] = datetime.fromisoformat(item["predicted_at"])
                db.add(Prediction(**item))
                preds_added += 1

        # 4. Seed Maintenance Tickets
        existing_maint = {mt.id for mt in db.query(MaintenanceTicket.id).all()}
        maint_added = 0
        for mt in maintenance:
            if mt["id"] not in existing_maint:
                item = mt.copy()
                if item.get("created_at"):
                    item["created_at"] = datetime.fromisoformat(item["created_at"])
                db.add(MaintenanceTicket(**item))
                maint_added += 1

        db.commit()
        print(f"Database Seed Complete: +{users_added} Users, +{machines_added} Machines, +{preds_added} Predictions, +{maint_added} Maintenance Tickets.")

    except Exception as e:
        db.rollback()
        print(f"Error seeding database: {e}")
        raise
    finally:
        db.close()

if __name__ == "__main__":
    seed_database()
