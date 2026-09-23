"""
PredictCNC Prediction Service — Telemetry history rolling window calculation,
LightGBM inference execution, persistence to MySQL, automated maintenance ticketing,
and non-blocking Gmail SMTP alerts dispatch.
"""
from datetime import datetime
from typing import Dict, Any, List, Optional
from db import query_one, query_all, execute_insert, execute_update
from services.ml_service import MLService
from services.notification_service import NotificationService

class PredictionService:
    @staticmethod
    def run_prediction(
        machine_id: int,
        air_temperature: float,
        process_temperature: float,
        rotational_speed: float,
        torque: float,
        tool_wear: float,
        user_id: Optional[int] = None
    ) -> Dict[str, Any]:
        """
        Executes end-to-end machine health prediction workflow.
        Verifies machine ownership when user_id is provided.
        """
        if user_id is not None:
            machine = query_one("SELECT * FROM machines WHERE id = %s AND user_id = %s", (machine_id, user_id))
        else:
            machine = query_one("SELECT * FROM machines WHERE id = %s", (machine_id,))

        if not machine:
            raise ValueError(f"Machine with ID {machine_id} not found or access denied.")


        # Compute rolling window statistics from recent historical predictions for this machine
        recent_records = query_all(
            "SELECT tool_wear, air_temperature, process_temperature, rotational_speed, torque FROM predictions WHERE machine_id = %s ORDER BY predicted_at DESC LIMIT 10",
            (machine_id,)
        )

        rolling_history = {}
        if recent_records:
            air_temps = [float(r["air_temperature"]) for r in recent_records]
            proc_temps = [float(r["process_temperature"]) for r in recent_records]
            rpms = [float(r["rotational_speed"]) for r in recent_records]
            torques = [float(r["torque"]) for r in recent_records]

            rolling_history = {
                'air_temp_mean': sum(air_temps) / len(air_temps),
                'proc_temp_mean': sum(proc_temps) / len(proc_temps),
                'rpm_mean': sum(rpms) / len(rpms),
                'torque_mean': sum(torques) / len(torques),
                'air_temp_min': min(air_temps),
                'air_temp_max': max(air_temps),
                'proc_temp_min': min(proc_temps),
                'proc_temp_max': max(proc_temps),
                'rpm_min': min(rpms),
                'rpm_max': max(rpms),
                'torque_min': min(torques),
                'torque_max': max(torques),
            }

        # Run LightGBM inference
        result = MLService.run_prediction(
            air_temp=air_temperature,
            process_temp=process_temperature,
            rotational_speed=rotational_speed,
            torque=torque,
            tool_wear=tool_wear,
            machine_type="L",
            shift="Morning",
            humidity=60.0,
            rolling_history=rolling_history
        )

        pred_class = result["predicted_class"]
        class_probs = result.get("class_probabilities", {})
        if pred_class == 0:
            confidence_val = class_probs.get("normal", result["machine_health"])
        elif pred_class == 1:
            confidence_val = class_probs.get("warning", result["failure_probability"])
        else:
            confidence_val = class_probs.get("critical", result["failure_probability"])

        # Derived physical metrics
        load_density = torque / 100.0
        rpm_torque_interaction = rotational_speed * torque
        temp_diff = process_temperature - air_temperature
        temp_ratio = process_temperature / air_temperature if air_temperature != 0 else 1.0
        load_stress = torque * (torque / 100.0)

        # Persist prediction to MySQL
        prediction_id = execute_insert(
            """INSERT INTO predictions (
                machine_id, air_temperature, process_temperature, rotational_speed, torque, tool_wear,
                load_density, rpm_torque_interaction, temperature_difference, temperature_ratio, load_stress,
                prediction, predicted_class, model_version, probability, healthy_probability,
                warning_probability, critical_probability, confidence, predicted_at
            ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)""",
            (
                machine_id, air_temperature, process_temperature, rotational_speed, torque, tool_wear,
                load_density, rpm_torque_interaction, temp_diff, temp_ratio, load_stress,
                result["prediction"], pred_class, result.get("model_version", "LightGBM_No_SMOTE_Final v4.2"),
                result["failure_probability"], class_probs.get("normal", result["machine_health"]),
                class_probs.get("warning", 0.0), class_probs.get("critical", 0.0),
                round(confidence_val, 2), datetime.now()
            )
        )

        # Update machine status
        suggested_status = result["suggested_machine_status"]
        execute_update(
            "UPDATE machines SET status = %s WHERE id = %s",
            (suggested_status, machine_id)
        )

        # Auto-create maintenance ticket if Warning or Critical
        ticket_created = False
        ticket_priority = None
        if result["is_failure"]:
            ticket_priority = "High"
            execute_insert(
                "INSERT INTO maintenance (machine_id, prediction_id, priority, status, remarks, created_at) VALUES (%s, %s, %s, %s, %s, %s)",
                (machine_id, prediction_id, "High", "Pending", f"High Priority AI Alert: {result['root_cause_analysis']['diagnosis']} ({result['failure_probability']}% failure risk).", datetime.now())
            )
            ticket_created = True
        elif result["is_warning"] or result["failure_probability"] > 35.0:
            ticket_priority = "Medium"
            execute_insert(
                "INSERT INTO maintenance (machine_id, prediction_id, priority, status, remarks, created_at) VALUES (%s, %s, %s, %s, %s, %s)",
                (machine_id, prediction_id, "Medium", "Pending", f"Preventative Inspection Ticket: Telemetry anomaly detected ({result['failure_probability']}% risk probability).", datetime.now())
            )
            ticket_created = True

        # Dispatch automated Gmail SMTP alert (failsafe non-blocking)
        sensor_data = {
            "air_temperature": air_temperature,
            "process_temperature": process_temperature,
            "rotational_speed": rotational_speed,
            "torque": torque,
            "tool_wear": tool_wear
        }
        result_with_conf = dict(result)
        result_with_conf["confidence"] = round(confidence_val, 2)

        notification_info = NotificationService.dispatch_alert_if_needed(
            machine=machine,
            prediction_result=result_with_conf,
            sensor_data=sensor_data
        )

        return {
            "id": prediction_id,
            "machine_id": machine["id"],
            "machine_code": machine["machine_code"],
            "machine_name": machine["machine_name"],
            "prediction": result["prediction"],
            "predicted_class": result["predicted_class"],
            "is_failure": result["is_failure"],
            "is_warning": result["is_warning"],
            "failure_probability": result["failure_probability"],
            "machine_health": result["machine_health"],
            "risk_level": result["risk_level"],
            "suggested_machine_status": suggested_status,
            "ticket_created": ticket_created,
            "ticket_priority": ticket_priority,
            "model_version": result["model_version"],
            "class_probabilities": result["class_probabilities"],
            "root_cause_analysis": result["root_cause_analysis"],
            "notification": notification_info,
            "confidence": round(confidence_val, 2),
            "predicted_at": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        }

    @staticmethod
    def get_history(machine_id: Optional[int] = None, user_id: Optional[int] = None, limit: int = 100, offset: int = 0) -> List[Dict[str, Any]]:
        """Retrieves prediction history with machine details."""
        sql = """
        SELECT p.*, m.machine_code, m.machine_name 
        FROM predictions p 
        JOIN machines m ON p.machine_id = m.id
        """
        params = []
        conditions = []
        if user_id is not None:
            conditions.append("m.user_id = %s")
            params.append(user_id)
        if machine_id:
            conditions.append("p.machine_id = %s")
            params.append(machine_id)

        if conditions:
            sql += " WHERE " + " AND ".join(conditions)
        
        sql += " ORDER BY p.predicted_at DESC LIMIT %s OFFSET %s"
        params.extend([limit, offset])

        rows = query_all(sql, tuple(params))
        for r in rows:
            if "confidence" not in r or r["confidence"] is None:
                prob = float(r.get("probability", 0.0))
                r["confidence"] = round(100 - prob, 2) if r.get("prediction") == "Normal Operation" else prob
        return rows

    @staticmethod
    def delete_history_item(item_id: int, user_id: Optional[int] = None) -> bool:
        """Deletes a historical prediction record, ensuring tenant ownership if user_id is provided."""
        if user_id is not None:
            count = execute_update(
                "DELETE FROM predictions WHERE id = %s AND machine_id IN (SELECT id FROM machines WHERE user_id = %s)",
                (item_id, user_id)
            )
        else:
            count = execute_update("DELETE FROM predictions WHERE id = %s", (item_id,))
        return count > 0

