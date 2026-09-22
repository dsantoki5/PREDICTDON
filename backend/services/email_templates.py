"""
PredictCNC Email Templates — Professional HTML and plain-text templates for WARNING and CRITICAL alerts.
Compatible with standard Gmail web and mobile rendering.
"""
from typing import Dict, Any, Optional

def build_warning_email(
    machine_code: str,
    machine_name: str,
    owner_name: str,
    supervisor_name: str,
    prediction: str,
    confidence: float,
    failure_probability: float,
    sensor_data: Dict[str, Any],
    rca: Optional[Dict[str, Any]] = None,
    timestamp: Optional[str] = None
) -> tuple[str, str, str]:
    """
    Constructs a Warning (Class 1) Alert Email.
    Returns: (subject, html_content, plain_text_content)
    """
    subject = f"[PREDICTCNC WARNING] Machine Health Warning - {machine_name}"
    
    air_t = sensor_data.get("air_temperature", "--")
    proc_t = sensor_data.get("process_temperature", "--")
    rpm = sensor_data.get("rotational_speed", "--")
    torque = sensor_data.get("torque", "--")
    wear = sensor_data.get("tool_wear", "--")
    
    diagnosis = rca.get("diagnosis", "Thermal or mechanical parameter deviation detected.") if rca else "Parameter drift observed."
    causes = rca.get("causes", ["Increased cutting resistance", "Elevated thermal gradient"]) if rca else []
    maintenance = rca.get("maintenance", ["Perform visual tool wear inspection", "Verify spindle lubricant and cooling cycle"]) if rca else []
    
    causes_html = "".join(f"<li style='margin-bottom: 6px;'>{c}</li>" for c in causes)
    maintenance_html = "".join(f"<li style='margin-bottom: 6px;'>{m}</li>" for m in maintenance)
    
    html = f"""<!DOCTYPE html>
<html>
<head>
  <meta charset="utf-8">
  <title>{subject}</title>
</head>
<body style="margin: 0; padding: 20px; background-color: #0f172a; font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif; color: #e2e8f0;">
  <div style="max-width: 600px; margin: 0 auto; background-color: #1e293b; border: 1px solid #334155; border-radius: 8px; overflow: hidden; box-shadow: 0 4px 12px rgba(0,0,0,0.4);">
    <!-- Header -->
    <div style="background: linear-gradient(135deg, #1e293b 0%, #0f172a 100%); padding: 20px 24px; border-bottom: 2px solid #f59e0b;">
      <h2 style="margin: 0; color: #ffffff; font-size: 20px; font-weight: 700;">Predict<span style="color: #38bdf8;">CNC</span> Machine Health Alert</h2>
      <div style="margin-top: 6px; display: inline-block; background-color: #f59e0b; color: #0f172a; font-size: 11px; font-weight: 800; padding: 4px 10px; border-radius: 4px; text-transform: uppercase;">
        🟡 WARNING ALERT
      </div>
    </div>

    <!-- Body -->
    <div style="padding: 24px;">
      <p style="margin-top: 0; font-size: 14px; line-height: 1.5; color: #cbd5e1;">
        Dear <strong>{supervisor_name or owner_name or 'Machine Administrator'}</strong>,
      </p>
      <p style="font-size: 14px; line-height: 1.5; color: #cbd5e1;">
        An automated telemetry evaluation has detected abnormal operating conditions requiring inspection on the following CNC asset:
      </p>

      <!-- Asset Summary Card -->
      <table style="width: 100%; border-collapse: collapse; margin: 16px 0; background-color: #0f172a; border-radius: 6px; border: 1px solid #334155; font-size: 13px;">
        <tr>
          <td style="padding: 10px 14px; border-bottom: 1px solid #1e293b; color: #94a3b8; width: 40%;">Machine Name:</td>
          <td style="padding: 10px 14px; border-bottom: 1px solid #1e293b; color: #ffffff; font-weight: 600;">{machine_name}</td>
        </tr>
        <tr>
          <td style="padding: 10px 14px; border-bottom: 1px solid #1e293b; color: #94a3b8;">Machine ID / Code:</td>
          <td style="padding: 10px 14px; border-bottom: 1px solid #1e293b; color: #38bdf8; font-weight: 600;">{machine_code}</td>
        </tr>
        <tr>
          <td style="padding: 10px 14px; border-bottom: 1px solid #1e293b; color: #94a3b8;">Machine Owner / Admin:</td>
          <td style="padding: 10px 14px; border-bottom: 1px solid #1e293b; color: #ffffff;">{owner_name or 'Plant Supervisor'}</td>
        </tr>
        <tr>
          <td style="padding: 10px 14px; border-bottom: 1px solid #1e293b; color: #94a3b8;">Health Status:</td>
          <td style="padding: 10px 14px; border-bottom: 1px solid #1e293b; color: #f59e0b; font-weight: 700;">WARNING</td>
        </tr>
        <tr>
          <td style="padding: 10px 14px; border-bottom: 1px solid #1e293b; color: #94a3b8;">AI Prediction:</td>
          <td style="padding: 10px 14px; border-bottom: 1px solid #1e293b; color: #ffffff;">{prediction}</td>
        </tr>
        <tr>
          <td style="padding: 10px 14px; border-bottom: 1px solid #1e293b; color: #94a3b8;">Prediction Confidence:</td>
          <td style="padding: 10px 14px; border-bottom: 1px solid #1e293b; color: #ffffff;">{confidence:.1f}% (Risk: {failure_probability:.1f}%)</td>
        </tr>
        <tr>
          <td style="padding: 10px 14px; color: #94a3b8;">Timestamp:</td>
          <td style="padding: 10px 14px; color: #ffffff;">{timestamp}</td>
        </tr>
      </table>

      <!-- Sensor Snapshot -->
      <h3 style="color: #38bdf8; font-size: 14px; margin: 18px 0 8px 0; text-transform: uppercase;">Observed Telemetry Snapshot</h3>
      <table style="width: 100%; border-collapse: collapse; font-size: 12px; margin-bottom: 16px;">
        <tr style="background-color: #0f172a; text-align: left; color: #94a3b8;">
          <th style="padding: 8px 10px; border: 1px solid #334155;">Air Temp</th>
          <th style="padding: 8px 10px; border: 1px solid #334155;">Process Temp</th>
          <th style="padding: 8px 10px; border: 1px solid #334155;">Spindle Speed</th>
          <th style="padding: 8px 10px; border: 1px solid #334155;">Torque</th>
          <th style="padding: 8px 10px; border: 1px solid #334155;">Tool Wear</th>
        </tr>
        <tr style="color: #e2e8f0;">
          <td style="padding: 8px 10px; border: 1px solid #334155;">{air_t} K</td>
          <td style="padding: 8px 10px; border: 1px solid #334155;">{proc_t} K</td>
          <td style="padding: 8px 10px; border: 1px solid #334155;">{rpm} RPM</td>
          <td style="padding: 8px 10px; border: 1px solid #334155;">{torque} Nm</td>
          <td style="padding: 8px 10px; border: 1px solid #334155;">{wear} min</td>
        </tr>
      </table>

      <!-- RCA & Actions -->
      <div style="background-color: rgba(245, 158, 11, 0.1); border-left: 4px solid #f59e0b; padding: 12px 16px; border-radius: 4px; margin-bottom: 16px;">
        <div style="font-weight: 700; color: #f59e0b; font-size: 13px; margin-bottom: 4px;">Telemetry Diagnosis:</div>
        <div style="font-size: 13px; color: #e2e8f0; line-height: 1.4;">{diagnosis}</div>
      </div>

      <div style="font-weight: 700; color: #ffffff; font-size: 13px; margin: 12px 0 6px 0;">Recommended Action:</div>
      <p style="font-size: 13px; color: #cbd5e1; margin-top: 0; line-height: 1.5;">
        Please inspect the machine and review the latest prediction and sensor information. Preventative maintenance before the next production shift is advised.
      </p>
      {f"<ul style='font-size: 12px; color: #94a3b8; padding-left: 20px; margin-top: 4px;'>{maintenance_html}</ul>" if maintenance else ""}
    </div>

    <!-- Footer -->
    <div style="background-color: #0f172a; padding: 14px 24px; border-top: 1px solid #334155; font-size: 11px; color: #64748b; text-align: center;">
      PredictCNC AI Predictive Maintenance System &bull; Automated Telemetry Alert
    </div>
  </div>
</body>
</html>"""

    plain_text = f"""PredictCNC Machine Health Alert

Machine Name: {machine_name}
Machine ID: {machine_code}
Machine Owner: {owner_name or supervisor_name or 'Plant Administrator'}
Health Status: WARNING
Prediction: {prediction}
Confidence: {confidence:.1f}% (Risk: {failure_probability:.1f}%)
Timestamp: {timestamp}

Observed Telemetry:
- Air Temperature: {air_t} K
- Process Temperature: {proc_t} K
- Spindle Speed: {rpm} RPM
- Torque: {torque} Nm
- Tool Wear: {wear} min

Diagnosis: {diagnosis}

Recommended Action:
Please inspect the machine and review the latest prediction and sensor information.
"""
    return subject, html, plain_text


def build_critical_email(
    machine_code: str,
    machine_name: str,
    owner_name: str,
    supervisor_name: str,
    prediction: str,
    confidence: float,
    failure_probability: float,
    sensor_data: Dict[str, Any],
    rca: Optional[Dict[str, Any]] = None,
    timestamp: Optional[str] = None
) -> tuple[str, str, str]:
    """
    Constructs a Critical (Class 2) Alert Email.
    Returns: (subject, html_content, plain_text_content)
    """
    subject = f"[PREDICTCNC CRITICAL] Immediate Attention Required - {machine_name}"
    
    air_t = sensor_data.get("air_temperature", "--")
    proc_t = sensor_data.get("process_temperature", "--")
    rpm = sensor_data.get("rotational_speed", "--")
    torque = sensor_data.get("torque", "--")
    wear = sensor_data.get("tool_wear", "--")
    
    diagnosis = rca.get("diagnosis", "Critical sensor anomaly indicating imminent mechanical failure.") if rca else "Critical failure imminent."
    causes = rca.get("causes", ["Over-torque loading", "Tool wear threshold exceeded", "Spindle instability"]) if rca else []
    maintenance = rca.get("maintenance", ["Halt spindle immediately", "Replace carbide insert", "Inspect drive bearings"]) if rca else []
    
    causes_html = "".join(f"<li style='margin-bottom: 6px;'>{c}</li>" for c in causes)
    maintenance_html = "".join(f"<li style='margin-bottom: 6px;'>{m}</li>" for m in maintenance)
    
    html = f"""<!DOCTYPE html>
<html>
<head>
  <meta charset="utf-8">
  <title>{subject}</title>
</head>
<body style="margin: 0; padding: 20px; background-color: #0f172a; font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif; color: #e2e8f0;">
  <div style="max-width: 600px; margin: 0 auto; background-color: #1e293b; border: 1px solid #ef4444; border-radius: 8px; overflow: hidden; box-shadow: 0 4px 16px rgba(239, 68, 68, 0.25);">
    <!-- Header -->
    <div style="background: linear-gradient(135deg, #450a0a 0%, #1e293b 100%); padding: 20px 24px; border-bottom: 2px solid #ef4444;">
      <h2 style="margin: 0; color: #ffffff; font-size: 20px; font-weight: 700;">Predict<span style="color: #ef4444;">CNC</span> Critical Alert</h2>
      <div style="margin-top: 6px; display: inline-block; background-color: #ef4444; color: #ffffff; font-size: 11px; font-weight: 800; padding: 4px 10px; border-radius: 4px; text-transform: uppercase;">
        🔴 CRITICAL ATTENTION REQUIRED
      </div>
    </div>

    <!-- Body -->
    <div style="padding: 24px;">
      <p style="margin-top: 0; font-size: 14px; line-height: 1.5; color: #cbd5e1;">
        Dear <strong>{supervisor_name or owner_name or 'Machine Administrator'}</strong>,
      </p>
      <p style="font-size: 14px; line-height: 1.5; color: #fca5a5; font-weight: 600;">
        URGENT: High probability of imminent machine breakdown detected. Immediate intervention is required to avoid tooling destruction and unplanned downtime.
      </p>

      <!-- Asset Summary Card -->
      <table style="width: 100%; border-collapse: collapse; margin: 16px 0; background-color: #0f172a; border-radius: 6px; border: 1px solid #334155; font-size: 13px;">
        <tr>
          <td style="padding: 10px 14px; border-bottom: 1px solid #1e293b; color: #94a3b8; width: 40%;">Machine Name:</td>
          <td style="padding: 10px 14px; border-bottom: 1px solid #1e293b; color: #ffffff; font-weight: 700;">{machine_name}</td>
        </tr>
        <tr>
          <td style="padding: 10px 14px; border-bottom: 1px solid #1e293b; color: #94a3b8;">Machine ID / Code:</td>
          <td style="padding: 10px 14px; border-bottom: 1px solid #1e293b; color: #ef4444; font-weight: 700;">{machine_code}</td>
        </tr>
        <tr>
          <td style="padding: 10px 14px; border-bottom: 1px solid #1e293b; color: #94a3b8;">Machine Owner / Admin:</td>
          <td style="padding: 10px 14px; border-bottom: 1px solid #1e293b; color: #ffffff;">{owner_name or 'Plant Supervisor'}</td>
        </tr>
        <tr>
          <td style="padding: 10px 14px; border-bottom: 1px solid #1e293b; color: #94a3b8;">Health Status:</td>
          <td style="padding: 10px 14px; border-bottom: 1px solid #1e293b; color: #ef4444; font-weight: 800;">CRITICAL</td>
        </tr>
        <tr>
          <td style="padding: 10px 14px; border-bottom: 1px solid #1e293b; color: #94a3b8;">AI Prediction:</td>
          <td style="padding: 10px 14px; border-bottom: 1px solid #1e293b; color: #ef4444; font-weight: 600;">{prediction}</td>
        </tr>
        <tr>
          <td style="padding: 10px 14px; border-bottom: 1px solid #1e293b; color: #94a3b8;">Failure Probability:</td>
          <td style="padding: 10px 14px; border-bottom: 1px solid #1e293b; color: #ffffff; font-weight: 700;">{failure_probability:.1f}% (Confidence: {confidence:.1f}%)</td>
        </tr>
        <tr>
          <td style="padding: 10px 14px; color: #94a3b8;">Timestamp:</td>
          <td style="padding: 10px 14px; color: #ffffff;">{timestamp}</td>
        </tr>
      </table>

      <!-- Sensor Snapshot -->
      <h3 style="color: #ef4444; font-size: 14px; margin: 18px 0 8px 0; text-transform: uppercase;">Critical Telemetry Snapshot</h3>
      <table style="width: 100%; border-collapse: collapse; font-size: 12px; margin-bottom: 16px;">
        <tr style="background-color: #0f172a; text-align: left; color: #94a3b8;">
          <th style="padding: 8px 10px; border: 1px solid #334155;">Air Temp</th>
          <th style="padding: 8px 10px; border: 1px solid #334155;">Process Temp</th>
          <th style="padding: 8px 10px; border: 1px solid #334155;">Spindle Speed</th>
          <th style="padding: 8px 10px; border: 1px solid #334155;">Torque</th>
          <th style="padding: 8px 10px; border: 1px solid #334155;">Tool Wear</th>
        </tr>
        <tr style="color: #ffffff; font-weight: 600;">
          <td style="padding: 8px 10px; border: 1px solid #334155;">{air_t} K</td>
          <td style="padding: 8px 10px; border: 1px solid #334155;">{proc_t} K</td>
          <td style="padding: 8px 10px; border: 1px solid #334155;">{rpm} RPM</td>
          <td style="padding: 8px 10px; border: 1px solid #334155;">{torque} Nm</td>
          <td style="padding: 8px 10px; border: 1px solid #334155; color: #ef4444;">{wear} min</td>
        </tr>
      </table>

      <!-- Diagnosis Alert Box -->
      <div style="background-color: rgba(239, 68, 68, 0.15); border-left: 4px solid #ef4444; padding: 12px 16px; border-radius: 4px; margin-bottom: 16px;">
        <div style="font-weight: 700; color: #ef4444; font-size: 13px; margin-bottom: 4px;">Root Cause Diagnosis:</div>
        <div style="font-size: 13px; color: #ffffff; line-height: 1.4;">{diagnosis}</div>
      </div>

      <div style="font-weight: 700; color: #ffffff; font-size: 13px; margin: 12px 0 6px 0;">Recommended Action:</div>
      <p style="font-size: 13px; color: #fca5a5; margin-top: 0; line-height: 1.5; font-weight: 600;">
        Immediate machine inspection and corrective action is recommended. A High-Priority Maintenance Ticket has been automatically registered in the system.
      </p>
      {f"<ul style='font-size: 12px; color: #cbd5e1; padding-left: 20px; margin-top: 4px;'>{maintenance_html}</ul>" if maintenance else ""}
    </div>

    <!-- Footer -->
    <div style="background-color: #0f172a; padding: 14px 24px; border-top: 1px solid #334155; font-size: 11px; color: #64748b; text-align: center;">
      PredictCNC AI Predictive Maintenance System &bull; Critical Emergency Dispatch
    </div>
  </div>
</body>
</html>"""

    plain_text = f"""PredictCNC Critical Machine Health Alert

Machine Name: {machine_name}
Machine ID: {machine_code}
Machine Owner: {owner_name or supervisor_name or 'Plant Administrator'}
Health Status: CRITICAL
Prediction: {prediction}
Confidence: {confidence:.1f}% (Failure Probability: {failure_probability:.1f}%)
Timestamp: {timestamp}

Critical Telemetry:
- Air Temperature: {air_t} K
- Process Temperature: {proc_t} K
- Spindle Speed: {rpm} RPM
- Torque: {torque} Nm
- Tool Wear: {wear} min

Diagnosis: {diagnosis}

Recommended Action:
Immediate machine inspection and corrective action is recommended.
"""
    return subject, html, plain_text
