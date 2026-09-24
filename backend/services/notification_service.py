"""
PredictCNC Notification Service — Alert trigger evaluation, recipient resolution,
duplicate suppression cooldown, and PostgreSQL notification logging.
"""
import os
import logging
from datetime import datetime, timezone, timedelta
from typing import Optional, Dict, Any
from dotenv import load_dotenv

from db import query_one, execute_insert
from services.email_service import EmailService
from services.email_templates import build_warning_email, build_critical_email

backend_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
load_dotenv(os.path.join(backend_dir, ".env"))

logger = logging.getLogger("predictcnc.notifications")

class NotificationService:
    @staticmethod
    def resolve_recipient(machine: Dict[str, Any], user_id: Optional[int] = None) -> tuple[Optional[str], Optional[str]]:
        """
        Resolves the recipient email and name for a machine alert.
        Prioritizes the signed-in user / account owner's registered email so that
        alerts are dispatched directly to the active operator/administrator.
        """
        target_user_id = user_id or machine.get("user_id")
        user = query_one("SELECT * FROM users WHERE id = %s", (target_user_id,)) if target_user_id else None

        recipient_email = None
        recipient_name = None

        if user and user.get("email") and "@" in user.get("email"):
            recipient_email = user["email"].strip()
            recipient_name = user.get("admin_name") or user.get("username")

        # Fallback to machine supervisor_email if no registered user email found
        if not recipient_email:
            sup_email = (machine.get("supervisor_email") or "").strip()
            if sup_email and "@" in sup_email and "supervisor@predictcnc.local" not in sup_email.lower():
                recipient_email = sup_email
                recipient_name = (machine.get("supervisor_name") or "").strip()

        # Fallback to DEFAULT_SUPERVISOR_EMAIL from .env
        if not recipient_email:
            default_email = os.getenv("DEFAULT_SUPERVISOR_EMAIL", "").strip()
            if default_email and "@" in default_email:
                recipient_email = default_email

        return recipient_email, (recipient_name or "Machine Supervisor")

    @classmethod
    def dispatch_alert_if_needed(
        cls,
        machine: Dict[str, Any],
        prediction_result: Dict[str, Any],
        sensor_data: Dict[str, Any],
        user_id: Optional[int] = None
    ) -> Dict[str, Any]:
        """
        Evaluates prediction result and dispatches Warning or Critical alerts.
        Guaranteed to never raise unhandled exceptions (will never break predictions).
        """
        try:
            is_critical = bool(
                prediction_result.get("is_failure") or 
                prediction_result.get("predicted_class") == 2 or
                prediction_result.get("suggested_machine_status") == "Critical"
            )
            is_warning = bool(
                prediction_result.get("is_warning") or 
                prediction_result.get("predicted_class") == 1 or 
                prediction_result.get("failure_probability", 0) > 25.0 or
                prediction_result.get("suggested_machine_status") == "Warning"
            )

            # Rule 1: NORMAL -> No Email
            if not is_critical and not is_warning:
                return {
                    "attempted": False,
                    "status": "skipped_healthy",
                    "alert_type": "NORMAL",
                    "message": "Normal operation. No alert email required."
                }

            alert_type = "CRITICAL" if is_critical else "WARNING"
            health_status = "Critical" if is_critical else "Warning"
            recipient_email, recipient_name = cls.resolve_recipient(machine, user_id=user_id)

            machine_id = machine.get("id")

            # Check if recipient email exists
            if not recipient_email or "@" not in recipient_email:
                execute_insert(
                    "INSERT INTO notification_logs (machine_id, recipient_email, alert_type, health_status, prediction, delivery_status, error_message, sent_at) VALUES (%s, %s, %s, %s, %s, %s, %s, %s)",
                    (machine_id, recipient_email or "UNKNOWN", alert_type, health_status, prediction_result.get("prediction"), "FAILED", "No valid supervisor or owner email configured for this machine.", datetime.now())
                )
                return {
                    "attempted": True,
                    "status": "failed",
                    "alert_type": alert_type,
                    "recipient": recipient_email,
                    "message": "Machine alert detected, but no recipient email configured."
                }

            # Rule 2: Duplicate alert suppression cooldown (scoped to recipient & alert type)
            cooldown_minutes = int(os.getenv("SMTP_ALERT_COOLDOWN_MINUTES", 15))
            cutoff_time = datetime.now() - timedelta(minutes=cooldown_minutes)

            recent_sent = query_one(
                "SELECT * FROM notification_logs WHERE machine_id = %s AND LOWER(recipient_email) = LOWER(%s) AND delivery_status = 'SENT' AND sent_at >= %s ORDER BY sent_at DESC LIMIT 1",
                (machine_id, recipient_email, cutoff_time)
            )

            # If recent was sent to this recipient and not escalating from WARNING to CRITICAL, suppress duplicate
            if recent_sent and not (recent_sent.get("alert_type") == "WARNING" and alert_type == "CRITICAL"):
                execute_insert(
                    "INSERT INTO notification_logs (machine_id, recipient_email, alert_type, health_status, prediction, delivery_status, error_message, sent_at) VALUES (%s, %s, %s, %s, %s, %s, %s, %s)",
                    (machine_id, recipient_email, alert_type, health_status, prediction_result.get("prediction"), "SUPPRESSED", f"Duplicate alert suppressed within {cooldown_minutes}m cooldown.", datetime.now())
                )
                return {
                    "attempted": True,
                    "status": "duplicate_suppressed",
                    "alert_type": alert_type,
                    "recipient": recipient_email,
                    "message": f"Alert generated. Email suppressed because a recent alert was sent to {recipient_email} within the last {cooldown_minutes} minutes."
                }

            # Check if SMTP credentials configured
            if not EmailService.is_configured():
                execute_insert(
                    "INSERT INTO notification_logs (machine_id, recipient_email, alert_type, health_status, prediction, delivery_status, error_message, sent_at) VALUES (%s, %s, %s, %s, %s, %s, %s, %s)",
                    (machine_id, recipient_email, alert_type, health_status, prediction_result.get("prediction"), "DISABLED", "SMTP credentials not configured in .env.", datetime.now())
                )
                return {
                    "attempted": False,
                    "status": "unconfigured",
                    "alert_type": alert_type,
                    "recipient": recipient_email,
                    "message": f"Machine {alert_type} detected. Email notification skipped because SMTP credentials are not yet configured in .env."
                }

            now_str = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            confidence = float(prediction_result.get("confidence", 0.0) or prediction_result.get("failure_probability", 50.0))
            fail_prob = float(prediction_result.get("failure_probability", 50.0))
            rca = prediction_result.get("root_cause_analysis")

            if alert_type == "CRITICAL":
                subject, html_body, text_body = build_critical_email(
                    machine_code=machine.get("machine_code", f"CNC-{machine_id}"),
                    machine_name=machine.get("machine_name", "CNC Machine"),
                    owner_name=recipient_name,
                    supervisor_name=recipient_name,
                    prediction=prediction_result.get("prediction", "Critical Machine Failure"),
                    confidence=confidence,
                    failure_probability=fail_prob,
                    sensor_data=sensor_data,
                    rca=rca,
                    timestamp=now_str
                )
            else:
                subject, html_body, text_body = build_warning_email(
                    machine_code=machine.get("machine_code", f"CNC-{machine_id}"),
                    machine_name=machine.get("machine_name", "CNC Machine"),
                    owner_name=recipient_name,
                    supervisor_name=recipient_name,
                    prediction=prediction_result.get("prediction", "Warning / Anomaly Alert"),
                    confidence=confidence,
                    failure_probability=fail_prob,
                    sensor_data=sensor_data,
                    rca=rca,
                    timestamp=now_str
                )

            # Dispatch via EmailService
            success, err_msg = EmailService.send_email(
                to_email=recipient_email,
                subject=subject,
                html_content=html_body,
                text_content=text_body
            )

            delivery_status = "SENT" if success else "FAILED"
            execute_insert(
                "INSERT INTO notification_logs (machine_id, recipient_email, alert_type, health_status, prediction, delivery_status, error_message, sent_at) VALUES (%s, %s, %s, %s, %s, %s, %s, %s)",
                (machine_id, recipient_email, alert_type, health_status, prediction_result.get("prediction"), delivery_status, err_msg, datetime.now())
            )

            if success:
                return {
                    "attempted": True,
                    "status": "sent",
                    "alert_type": alert_type,
                    "recipient": recipient_email,
                    "message": f"{alert_type} alert email successfully dispatched to {recipient_email}."
                }
            else:
                return {
                    "attempted": True,
                    "status": "failed",
                    "alert_type": alert_type,
                    "recipient": recipient_email,
                    "message": f"Alert email could not be sent: {err_msg}"
                }

        except Exception as ex:
            logger.error(f"Unexpected error in NotificationService: {ex}")
            return {
                "attempted": False,
                "status": "failed",
                "message": f"Notification handling error: {type(ex).__name__}"
            }
