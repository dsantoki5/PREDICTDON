import os
import sys
from typing import List, Optional, Dict, Any
from sqlalchemy.orm import Session
from sqlalchemy import func
from src.models.machine import Machine
from src.models.prediction import Prediction
from src.models.maintenance import MaintenanceTicket
from src.schemas.prediction import PredictionInput, PredictionRunResponse, PredictionHistoryOut
from src.services.ml_service import MLService

class PredictionService:
    @staticmethod
    def run_prediction(db: Session, payload: PredictionInput) -> PredictionRunResponse:
        machine = db.query(Machine).filter(Machine.id == payload.machine_id).first()
        if not machine:
            raise ValueError(f"Machine with ID {payload.machine_id} not found.")

        # Compute rolling window statistics from recent historical predictions for this machine
        recent_records = (
            db.query(
                Prediction.tool_wear,
                Prediction.air_temperature,
                Prediction.process_temperature,
                Prediction.rotational_speed,
                Prediction.torque
            )
            .filter(Prediction.machine_id == payload.machine_id)
            .order_by(Prediction.predicted_at.desc())
            .limit(10)
            .all()
        )

        rolling_history = {}
        if recent_records:
            air_temps = [r[1] for r in recent_records]
            proc_temps = [r[2] for r in recent_records]
            rpms = [r[3] for r in recent_records]
            torques = [r[4] for r in recent_records]

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

        # Run multi-class inference using authoritative LightGBM_No_SMOTE_Final.joblib
        result = MLService.run_prediction(
            air_temp=payload.air_temperature,
            process_temp=payload.process_temperature,
            rotational_speed=payload.rotational_speed,
            torque=payload.torque,
            tool_wear=payload.tool_wear,
            machine_type="L",
            shift="Morning",
            humidity=60.0,
            rolling_history=rolling_history
        )

        # Determine confidence value
        pred_class = result["predicted_class"]
        class_probs = result.get("class_probabilities", {})
        if pred_class == 0:
            confidence_val = class_probs.get("normal", result["machine_health"])
        elif pred_class == 1:
            confidence_val = class_probs.get("warning", result["failure_probability"])
        else:
            confidence_val = class_probs.get("critical", result["failure_probability"])

        # Persist prediction in DB
        prediction_rec = Prediction(
            machine_id=payload.machine_id,
            air_temperature=payload.air_temperature,
            process_temperature=payload.process_temperature,
            rotational_speed=payload.rotational_speed,
            torque=payload.torque,
            tool_wear=payload.tool_wear,
            load_density=payload.torque / 100.0,
            rpm_torque_interaction=payload.rotational_speed * payload.torque,
            temperature_difference=payload.process_temperature - payload.air_temperature,
            temperature_ratio=payload.process_temperature / payload.air_temperature if payload.air_temperature != 0 else 1.0,
            load_stress=payload.torque * (payload.torque / 100.0),
            prediction=result["prediction"],
            predicted_class=pred_class,
            model_version=result.get("model_version", "LightGBM_No_SMOTE_Final v4.2"),
            probability=result["failure_probability"],
            healthy_probability=class_probs.get("normal", result["machine_health"]),
            warning_probability=class_probs.get("warning", 0.0),
            critical_probability=class_probs.get("critical", 0.0),
            confidence=round(confidence_val, 2)
        )
        db.add(prediction_rec)
        db.flush()

        # Update machine status
        machine.status = result["suggested_machine_status"]

        # Automatically generate maintenance ticket if failure or warning predicted
        ticket_created = False
        ticket_priority = None
        if result["is_failure"]:
            ticket_priority = "High"
            ticket = MaintenanceTicket(
                machine_id=payload.machine_id,
                prediction_id=prediction_rec.id,
                priority="High",
                status="Pending",
                remarks=f"High Priority AI Alert: {result['root_cause_analysis']['diagnosis']} ({result['failure_probability']}% failure probability)."
            )
            db.add(ticket)
            ticket_created = True
        elif result["is_warning"] or result["failure_probability"] > 35.0:
            ticket_priority = "Medium"
            ticket = MaintenanceTicket(
                machine_id=payload.machine_id,
                prediction_id=prediction_rec.id,
                priority="Medium",
                status="Pending",
                remarks=f"Preventive Inspection Ticket: Anomaly detected ({result['failure_probability']}% risk probability)."
            )
            db.add(ticket)
            ticket_created = True

        db.commit()
        db.refresh(prediction_rec)

        return PredictionRunResponse(
            id=prediction_rec.id,
            machine_id=machine.id,
            machine_code=machine.machine_code,
            machine_name=machine.machine_name,
            prediction=result["prediction"],
            predicted_class=result["predicted_class"],
            is_failure=result["is_failure"],
            is_warning=result["is_warning"],
            failure_probability=result["failure_probability"],
            machine_health=result["machine_health"],
            risk_level=result["risk_level"],
            suggested_machine_status=result["suggested_machine_status"],
            ticket_created=ticket_created,
            ticket_priority=ticket_priority,
            model_version=result["model_version"],
            class_probabilities=result["class_probabilities"],
            root_cause_analysis=result["root_cause_analysis"],
            predicted_at=prediction_rec.predicted_at
        )

    @staticmethod
    def get_history(
        db: Session,
        machine_id: Optional[int] = None,
        limit: int = 100,
        offset: int = 0
    ) -> List[Dict[str, Any]]:
        query = (
            db.query(
                Prediction,
                Machine.machine_code,
                Machine.machine_name
            )
            .join(Machine, Prediction.machine_id == Machine.id)
        )
        if machine_id:
            query = query.filter(Prediction.machine_id == machine_id)
        
        rows = query.order_by(Prediction.predicted_at.desc()).offset(offset).limit(limit).all()
        
        result = []
        for p, code, name in rows:
            prob = float(p.probability or 0.0)
            conf = float(p.confidence) if p.confidence is not None else (round(100 - prob, 2) if p.prediction == "Normal Operation" else prob)
            result.append({
                "id": p.id,
                "machine_id": p.machine_id,
                "machine_code": code,
                "machine_name": name,
                "air_temperature": p.air_temperature,
                "process_temperature": p.process_temperature,
                "rotational_speed": p.rotational_speed,
                "torque": p.torque,
                "tool_wear": p.tool_wear,
                "prediction": p.prediction,
                "probability": prob,
                "confidence": conf,
                "predicted_at": p.predicted_at
            })
        return result

    @staticmethod
    def delete_history_item(db: Session, item_id: int) -> bool:
        rec = db.query(Prediction).filter(Prediction.id == item_id).first()
        if not rec:
            return False
        db.delete(rec)
        db.commit()
        return True
