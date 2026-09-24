"""
PredictCNC Database Seeder — Populates initial users, machines, predictions, and tickets into PostgreSQL.
"""
import os
import json
from datetime import datetime
from db import init_db, query_all, execute_insert

def seed_database():
    print("--- Initializing PredictCNC Database Schema ---")
    init_db()

    seed_file_path = os.path.join(os.path.dirname(__file__), "database_seed.json")
    if not os.path.exists(seed_file_path):
        print(f"Seed file not found at {seed_file_path}")
        return

    with open(seed_file_path, "r", encoding="utf-8") as f:
        data = json.load(f)

    users = data.get("users", [])
    machines = data.get("machines", [])
    predictions = data.get("predictions", [])
    maintenance = data.get("maintenance", [])

    # 1. Users
    existing_users = {u["id"] for u in query_all("SELECT id FROM users")}
    users_added = 0
    for u in users:
        if u["id"] not in existing_users:
            execute_insert(
                "INSERT INTO users (id, company_name, admin_name, email, username, password, role, created_at) VALUES (%s, %s, %s, %s, %s, %s, %s, %s)",
                (u["id"], u["company_name"], u["admin_name"], u["email"], u["username"], u["password"], u.get("role", "Administrator"), u.get("created_at"))
            )
            users_added += 1

    # 2. Machines
    existing_machines = {m["id"] for m in query_all("SELECT id FROM machines")}
    machines_added = 0
    for m in machines:
        if m["id"] not in existing_machines:
            execute_insert(
                "INSERT INTO machines (id, user_id, machine_code, machine_name, department, manufacturer, installation_date, status, supervisor_name, supervisor_email, created_at) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)",
                (m["id"], m.get("user_id"), m["machine_code"], m["machine_name"], m.get("department"), m.get("manufacturer"), m.get("installation_date"), m.get("status", "Healthy"), m.get("supervisor_name", "Divya Santoki"), m.get("supervisor_email", "forldrpml456@gmail.com"), m.get("created_at"))
            )
            machines_added += 1

    # 3. Predictions
    existing_preds = {p["id"] for p in query_all("SELECT id FROM predictions")}
    preds_added = 0
    for p in predictions:
        if p["id"] not in existing_preds:
            execute_insert(
                """INSERT INTO predictions (
                    id, machine_id, air_temperature, process_temperature, rotational_speed, torque, tool_wear,
                    load_density, rpm_torque_interaction, temperature_difference, temperature_ratio, load_stress,
                    prediction, predicted_class, model_version, probability, healthy_probability,
                    warning_probability, critical_probability, confidence, predicted_at
                ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)""",
                (
                    p["id"], p["machine_id"], p["air_temperature"], p["process_temperature"], p["rotational_speed"], p["torque"], p["tool_wear"],
                    p.get("load_density"), p.get("rpm_torque_interaction"), p.get("temperature_difference"), p.get("temperature_ratio"), p.get("load_stress"),
                    p["prediction"], p.get("predicted_class", 0), p.get("model_version", "LightGBM_No_SMOTE_Final v4.2"),
                    p["probability"], p.get("healthy_probability"), p.get("warning_probability"), p.get("critical_probability"),
                    p.get("confidence"), p.get("predicted_at")
                )
            )
            preds_added += 1

    # 4. Maintenance Tickets
    existing_maint = {mt["id"] for mt in query_all("SELECT id FROM maintenance")}
    maint_added = 0
    for mt in maintenance:
        if mt["id"] not in existing_maint:
            execute_insert(
                "INSERT INTO maintenance (id, machine_id, prediction_id, priority, status, remarks, created_at) VALUES (%s, %s, %s, %s, %s, %s, %s)",
                (mt["id"], mt["machine_id"], mt.get("prediction_id"), mt.get("priority", "Medium"), mt.get("status", "Pending"), mt.get("remarks"), mt.get("created_at"))
            )
            maint_added += 1

    print(f"Database Seed Complete: +{users_added} Users, +{machines_added} Machines, +{preds_added} Predictions, +{maint_added} Maintenance Tickets.")

if __name__ == "__main__":
    seed_database()
