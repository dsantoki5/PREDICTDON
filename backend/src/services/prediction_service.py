import os
import sys
from typing import List, Optional, Dict, Any
from sqlalchemy.orm import Session
from sqlalchemy import func
from src.models.machine import Machine
from src.models.prediction import Prediction
from src.models.maintenance import MaintenanceTicket
from src.schemas.prediction import PredictionInput, PredictionRunResponse, PredictionHistoryOut

# Import ML engine from ml/src
ml_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", "..", "ml", "src"))
if ml_dir not in sys.path:
    sys.path.insert(0, ml_dir)

from inference import PredictCNCEngine

# Initialize ML engine singleton
_engine: Optional[PredictCNCEngine] = None

def get_engine() -> PredictCNCEngine:
    global _engine
    if _engine is None:
        model_path = os.path.abspath(
            os.path.join(os.path.dirname(__file__), "..", "..", "..", "ml", "models", "final_lightgbm_model.pkl")
        )
        _engine = PredictCNCEngine(model_path=model_path)
    return _engine

class PredictionService:
    @staticmethod
    def run_prediction(db: Session, payload: PredictionInput) -> PredictionRunResponse:
        machine = db.query(Machine).filter(Machine.id == payload.machine_id).first()
        if not machine:
            raise ValueError(f"Machine with ID {payload.machine_id} not found.")

        # Compute rolling window features from last 10 historical predictions for this machine
        last_10 = (
            db.query(Prediction.tool_wear, Prediction.air_temperature)
            .filter(Prediction.machine_id == payload.machine_id)
            .order_by(Prediction.predicted_at.desc())
            .limit(10)
            .all()
        )

        tool_avg = sum(r[0] for r in last_10) / len(last_10) if last_10 else payload.tool_wear
        air_avg = sum(r[1] for r in last_10) / len(last_10) if last_10 else payload.air_temperature

        # Evaluate ML engine
        engine = get_engine()
        result = engine.predict(
            air_temp=payload.air_temperature,
            process_temp=payload.process_temperature,
            rotational_speed=payload.rotational_speed,
            torque=payload.torque,
            tool_wear=payload.tool_wear,
            tool_wear_mean_10=tool_avg,
            air_temp_mean_10=air_avg
        )

        # Persist prediction
        confidence_val = result["failure_probability"] if result["is_failure"] else result["machine_health"]

        prediction_rec = Prediction(
            machine_id=payload.machine_id,
            air_temperature=payload.air_temperature,
            process_temperature=payload.process_temperature,
            rotational_speed=payload.rotational_speed,
            torque=payload.torque,
            tool_wear=payload.tool_wear,
            load_density=result["features"]["load_density"],
            rpm_torque_interaction=result["features"]["rpm_torque_interaction"],
            temperature_difference=result["features"]["temperature_difference"],
            temperature_ratio=result["features"]["temperature_ratio"],
            load_stress=result["features"]["load_stress"],
            tool_wear_mean_10=tool_avg,
            air_temp_mean_10=air_avg,
            prediction=result["prediction"],
            probability=result["failure_probability"],
            healthy_probability=result["machine_health"],
            confidence=confidence_val
        )
        db.add(prediction_rec)
        db.flush()

        # Update machine status
        machine.status = result["suggested_machine_status"]

        # Automatically create maintenance ticket if failure predicted
        ticket_created = False
        ticket_priority = None
        if result["is_failure"]:
            ticket_priority = result["ticket_priority"]
            ticket = MaintenanceTicket(
                machine_id=payload.machine_id,
                prediction_id=prediction_rec.id,
                priority=ticket_priority,
                status="Pending",
                remarks=f"Auto-generated ticket: {result['root_cause_analysis']['diagnosis']} risk detected ({result['failure_probability']}% failure probability)."
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
            is_failure=result["is_failure"],
            failure_probability=result["failure_probability"],
            machine_health=result["machine_health"],
            risk_level=result["risk_level"],
            suggested_machine_status=result["suggested_machine_status"],
            ticket_created=ticket_created,
            ticket_priority=ticket_priority,
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
