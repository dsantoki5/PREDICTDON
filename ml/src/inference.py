"""
Inference Engine for PredictCNC
Provides prediction and Root Cause Analysis (RCA) diagnostics.
"""
import os
import joblib
from typing import Dict, Any, Optional
try:
    from .feature_engineering import engineer_features, create_feature_dataframe
except (ImportError, ValueError):
    from feature_engineering import engineer_features, create_feature_dataframe

class PredictCNCEngine:
    def __init__(self, model_path: Optional[str] = None):
        if model_path is None:
            base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
            model_path = os.path.join(base_dir, "models", "final_lightgbm_model.pkl")
        self.model_path = model_path
        self.model = joblib.load(model_path)

    def diagnose_root_causes(
        self,
        rotational_speed: float,
        torque: float,
        tool_wear: float,
        temperature_difference: float,
        rpm_torque_interaction: float,
        load_stress: float
    ) -> Dict[str, Any]:
        causes = []
        components = []
        maintenance = []
        analysis_table = []
        risk_score = 0

        if rotational_speed >= 2100:
            risk_score += 20
            causes.append("Very high spindle speed detected.")
            components.extend(["Spindle", "Main Bearings"])
            maintenance.extend(["Reduce spindle speed.", "Inspect spindle bearings.", "Check spindle lubrication."])
            analysis_table.append({
                "parameter": "Rotational Speed",
                "current": f"{rotational_speed:.0f} RPM",
                "normal": "1200 - 1800 RPM",
                "status": "Critical",
                "effect": "Overspeed causing spindle stress"
            })
        elif rotational_speed >= 1800:
            risk_score += 10
            causes.append("High spindle speed.")
            components.append("Spindle")
            maintenance.append("Monitor spindle speed.")
            analysis_table.append({
                "parameter": "Rotational Speed",
                "current": f"{rotational_speed:.0f} RPM",
                "normal": "1200 - 1800 RPM",
                "status": "High",
                "effect": "High spindle load"
            })
        else:
            analysis_table.append({
                "parameter": "Rotational Speed",
                "current": f"{rotational_speed:.0f} RPM",
                "normal": "1200 - 1800 RPM",
                "status": "Normal",
                "effect": "Stable spindle operation"
            })

        if torque >= 60:
            risk_score += 20
            causes.append("Excessive cutting load detected.")
            components.extend(["Drive Motor", "Drive Shaft"])
            maintenance.extend(["Inspect drive motor.", "Reduce machining load."])
            analysis_table.append({
                "parameter": "Torque",
                "current": f"{torque:.1f} Nm",
                "normal": "20 - 45 Nm",
                "status": "Critical",
                "effect": "Excessive cutting load on motor and drive shaft"
            })
        elif torque >= 45:
            risk_score += 10
            causes.append("High cutting load detected due to increased torque.")
            components.extend(["Drive Motor", "Drive Shaft"])
            maintenance.extend(["Monitor cutting load.", "Inspect drive motor."])
            analysis_table.append({
                "parameter": "Torque",
                "current": f"{torque:.1f} Nm",
                "normal": "20 - 45 Nm",
                "status": "High",
                "effect": "Motor load is higher than recommended"
            })
        else:
            analysis_table.append({
                "parameter": "Torque",
                "current": f"{torque:.1f} Nm",
                "normal": "20 - 45 Nm",
                "status": "Normal",
                "effect": "Normal cutting load"
            })

        if tool_wear >= 180:
            risk_score += 25
            causes.append("Cutting tool has exceeded its safe operating life.")
            components.extend(["Cutting Tool", "Tool Holder"])
            maintenance.extend(["Replace cutting tool immediately.", "Inspect tool holder alignment."])
            analysis_table.append({
                "parameter": "Tool Wear",
                "current": f"{tool_wear:.0f} min",
                "normal": "0 - 120 min",
                "status": "Critical",
                "effect": "Severe tool wear increases failure risk and reduces machining accuracy."
            })
        elif tool_wear >= 120:
            risk_score += 15
            causes.append("Tool wear has reached the recommended maintenance threshold.")
            components.extend(["Cutting Tool", "Tool Holder"])
            maintenance.extend(["Schedule tool replacement.", "Inspect tool holder."])
            analysis_table.append({
                "parameter": "Tool Wear",
                "current": f"{tool_wear:.0f} min",
                "normal": "0 - 120 min",
                "status": "High",
                "effect": "Tool performance is degrading."
            })
        else:
            analysis_table.append({
                "parameter": "Tool Wear",
                "current": f"{tool_wear:.0f} min",
                "normal": "0 - 120 min",
                "status": "Normal",
                "effect": "Tool condition is within safe limits."
            })

        if temperature_difference >= 11.5:
            risk_score += 18
            causes.append("Process temperature is significantly higher than air temperature.")
            components.extend(["Cooling System", "Coolant Pump"])
            maintenance.extend(["Inspect coolant circulation.", "Check coolant level.", "Clean cooling channels."])
            analysis_table.append({
                "parameter": "Temperature Difference",
                "current": f"{temperature_difference:.2f} K",
                "normal": "8 - 10.5 K",
                "status": "Critical",
                "effect": "Cooling system efficiency has reduced."
            })
        elif temperature_difference >= 10.5:
            risk_score += 8
            components.extend(["Cooling System", "Coolant Pump"])
            maintenance.extend(["Check coolant level.", "Inspect cooling system."])
            analysis_table.append({
                "parameter": "Temperature Difference",
                "current": f"{temperature_difference:.2f} K",
                "normal": "8 - 10.5 K",
                "status": "High",
                "effect": "Machine is operating under thermal stress."
            })
        else:
            analysis_table.append({
                "parameter": "Temperature Difference",
                "current": f"{temperature_difference:.2f} K",
                "normal": "8 - 10.5 K",
                "status": "Normal",
                "effect": "Cooling system operating normally."
            })

        if rpm_torque_interaction >= 70000:
            risk_score += 20
        elif rpm_torque_interaction >= 55000:
            risk_score += 10

        if load_stress >= 35:
            risk_score += 15
        elif load_stress >= 20:
            risk_score += 8

        if risk_score >= 70:
            diagnosis = "Critical"
        elif risk_score >= 40:
            diagnosis = "High"
        elif risk_score >= 20:
            diagnosis = "Moderate"
        else:
            diagnosis = "Low"

        return {
            "risk_score": min(risk_score, 100),
            "diagnosis": diagnosis,
            "causes": list(dict.fromkeys(causes)),
            "components": list(dict.fromkeys(components)),
            "maintenance": list(dict.fromkeys(maintenance)),
            "analysis_table": analysis_table
        }

    def predict(
        self,
        air_temp: float,
        process_temp: float,
        rotational_speed: float,
        torque: float,
        tool_wear: float,
        tool_wear_mean_10: Optional[float] = None,
        air_temp_mean_10: Optional[float] = None
    ) -> Dict[str, Any]:
        features = engineer_features(
            air_temp=air_temp,
            process_temp=process_temp,
            rotational_speed=rotational_speed,
            torque=torque,
            tool_wear=tool_wear,
            tool_wear_mean_10=tool_wear_mean_10,
            air_temp_mean_10=air_temp_mean_10
        )
        X = create_feature_dataframe(features)
        pred_label = int(self.model.predict(X)[0])
        probabilities = self.model.predict_proba(X)[0]
        normal_prob = round(float(probabilities[0]) * 100.0, 2)
        failure_prob = round(float(probabilities[1]) * 100.0, 2)

        is_failure = pred_label == 1
        prediction_text = "Machine Failure" if is_failure else "Normal Operation"
        risk_level = "High" if is_failure else "Low"

        if failure_prob >= 70:
            machine_status = "Critical"
        elif failure_prob >= 30:
            machine_status = "Warning"
        else:
            machine_status = "Healthy"

        ticket_required = is_failure
        if failure_prob >= 95:
            ticket_priority = "High"
        elif failure_prob >= 80:
            ticket_priority = "Medium"
        else:
            ticket_priority = "Low"

        rca = self.diagnose_root_causes(
            rotational_speed=rotational_speed,
            torque=torque,
            tool_wear=tool_wear,
            temperature_difference=features["temperature_difference"],
            rpm_torque_interaction=features["rpm_torque_interaction"],
            load_stress=features["load_stress"]
        )

        return {
            "prediction": prediction_text,
            "is_failure": is_failure,
            "failure_probability": failure_prob,
            "machine_health": normal_prob,
            "risk_level": risk_level,
            "suggested_machine_status": machine_status,
            "ticket_required": ticket_required,
            "ticket_priority": ticket_priority if ticket_required else None,
            "features": features,
            "root_cause_analysis": rca
        }
