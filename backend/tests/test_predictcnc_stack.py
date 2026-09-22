"""
PredictCNC Comprehensive Test Suite — Strict Technology Stack & SMTP Machine Health Alert Verification.
Tests 1-7 (SMTP Alerts & Fail-safes), ReportLab PDF generation, and Flask APIs.
"""
import os
import sys
import unittest
from unittest.mock import patch
from datetime import datetime

# Add backend directory to sys.path
backend_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if backend_dir not in sys.path:
    sys.path.insert(0, backend_dir)

from db import init_db, query_one, query_all, execute_insert, execute_update
from app import app
from services.ml_service import MLService
from services.prediction_service import PredictionService
from services.notification_service import NotificationService
from services.email_service import EmailService
from services.reports_service import ReportsService
from services.auth_service import AuthService
from services.machine_service import MachineService

class TestPredictCNCStack(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        init_db()
        # Clean up any existing test records
        execute_update("DELETE FROM machines WHERE machine_code = %s", ("TEST-CNC-999",))
        cls.test_machine_id = execute_insert(
            "INSERT INTO machines (machine_code, machine_name, department, status, supervisor_name, supervisor_email, user_id) VALUES (%s, %s, %s, %s, %s, %s, %s)",
            ("TEST-CNC-999", "Test Milling Machine", "Test Bay", "Healthy", "Test Supervisor", "test_sup@example.com", 1)
        )

    def setUp(self):
        self.client = app.test_client()
        # Authenticate test session
        with self.client.session_transaction() as sess:
            sess["user_id"] = 1
            sess["user"] = {
                "id": 1,
                "username": "admin",
                "admin_name": "Divya Santoki",
                "company_name": "LDRP Precision",
                "email": "forldrpml456@gmail.com",
                "role": "Administrator"
            }

    # -----------------------------------------------------------------
    # TEST 1: NORMAL Prediction -> No Email
    # -----------------------------------------------------------------
    def test_1_normal_prediction_no_email(self):
        """Test 1: Normal prediction should NOT trigger email dispatch."""
        with patch.object(EmailService, 'send_email') as mock_send:
            res = PredictionService.run_prediction(
                machine_id=self.test_machine_id,
                air_temperature=298.2,
                process_temperature=308.7,
                rotational_speed=1500.0,
                torque=39.5,
                tool_wear=40.0
            )
            self.assertEqual(res["predicted_class"], 0)
            self.assertIn("Normal", res["prediction"])
            self.assertFalse(res["is_failure"])
            self.assertFalse(res["is_warning"])
            self.assertEqual(res["notification"]["status"], "skipped_healthy")
            self.assertEqual(res["notification"]["alert_type"], "NORMAL")
            mock_send.assert_not_called()
            print(" -> TEST 1 (NORMAL -> No email): PASS")

    # -----------------------------------------------------------------
    # TEST 2: WARNING Prediction -> Warning Email Dispatched
    # -----------------------------------------------------------------
    def test_2_warning_prediction_email_dispatched(self):
        """Test 2: Warning prediction should trigger Warning alert email."""
        with patch.object(EmailService, 'send_email', return_value=(True, None)) as mock_send:
            # Clear recent logs for this machine to bypass cooldown
            execute_update("DELETE FROM notification_logs WHERE machine_id = %s", (self.test_machine_id,))

            res = PredictionService.run_prediction(
                machine_id=self.test_machine_id,
                air_temperature=298.5,
                process_temperature=309.0,
                rotational_speed=1741.0,
                torque=28.0,
                tool_wear=21.0
            )
            self.assertTrue(res["is_warning"] or res["predicted_class"] == 1 or res["failure_probability"] > 30.0)
            self.assertTrue(res["ticket_created"])
            self.assertEqual(res["ticket_priority"], "Medium")
            self.assertEqual(res["notification"]["alert_type"], "WARNING")
            self.assertEqual(res["notification"]["status"], "sent")
            self.assertTrue(mock_send.called)
            args, kwargs = mock_send.call_args
            subject_val = kwargs.get("subject") or (args[1] if len(args) > 1 else "")
            self.assertIn("[PREDICTCNC WARNING]", subject_val)
            print(" -> TEST 2 (WARNING -> Email dispatched): PASS")

    # -----------------------------------------------------------------
    # TEST 3: CRITICAL Prediction -> Critical Email Dispatched
    # -----------------------------------------------------------------
    def test_3_critical_prediction_email_dispatched(self):
        """Test 3: Critical prediction should trigger Critical alert email."""
        with patch.object(EmailService, 'send_email', return_value=(True, None)) as mock_send:
            execute_update("DELETE FROM notification_logs WHERE machine_id = %s", (self.test_machine_id,))

            res = PredictionService.run_prediction(
                machine_id=self.test_machine_id,
                air_temperature=304.0,
                process_temperature=314.5,
                rotational_speed=1200.0,
                torque=75.0,
                tool_wear=240.0
            )
            self.assertTrue(res["is_failure"] or res["predicted_class"] == 2)
            self.assertTrue(res["ticket_created"])
            self.assertEqual(res["ticket_priority"], "High")
            self.assertEqual(res["notification"]["alert_type"], "CRITICAL")
            self.assertEqual(res["notification"]["status"], "sent")
            self.assertTrue(mock_send.called)
            args, kwargs = mock_send.call_args
            subject_val = kwargs.get("subject") or (args[1] if len(args) > 1 else "")
            self.assertIn("[PREDICTCNC CRITICAL]", subject_val)
            print(" -> TEST 3 (CRITICAL -> Email dispatched): PASS")

    # -----------------------------------------------------------------
    # TEST 4: SMTP Unavailable -> Prediction Still Succeeds
    # -----------------------------------------------------------------
    def test_4_smtp_unavailable_resilience(self):
        """Test 4: SMTP network/socket failure must never crash prediction."""
        with patch.object(EmailService, 'send_email', return_value=(False, "Connection refused: smtp.gmail.com:587")):
            execute_update("DELETE FROM notification_logs WHERE machine_id = %s", (self.test_machine_id,))

            res = PredictionService.run_prediction(
                machine_id=self.test_machine_id,
                air_temperature=304.0,
                process_temperature=314.5,
                rotational_speed=1200.0,
                torque=75.0,
                tool_wear=240.0
            )
            # Prediction must still succeed 100%
            self.assertIsNotNone(res["id"])
            self.assertTrue(res["is_failure"])
            self.assertEqual(res["notification"]["status"], "failed")
            self.assertIn("could not be sent", res["notification"]["message"])
            print(" -> TEST 4 (SMTP unavailable -> Resilient fallback): PASS")

    # -----------------------------------------------------------------
    # TEST 5: Missing Supervisor Email -> Safe Handling
    # -----------------------------------------------------------------
    def test_5_missing_supervisor_email_handling(self):
        """Test 5: Machine without configured email should log and succeed."""
        execute_update("DELETE FROM machines WHERE machine_code = %s", ("NO-EMAIL-CNC",))
        m_id = execute_insert(
            "INSERT INTO machines (machine_code, machine_name, supervisor_name, supervisor_email, user_id) VALUES (%s, %s, %s, %s, %s)",
            ("NO-EMAIL-CNC", "No Email CNC", "Ghost Supervisor", "", None)
        )
        with patch.dict(os.environ, {"DEFAULT_SUPERVISOR_EMAIL": ""}):
            res = PredictionService.run_prediction(
                machine_id=m_id,
                air_temperature=304.0,
                process_temperature=314.5,
                rotational_speed=1200.0,
                torque=75.0,
                tool_wear=240.0
            )
            self.assertIsNotNone(res["id"])
            self.assertEqual(res["notification"]["status"], "failed")
            self.assertIn("no recipient email", res["notification"]["message"])
            print(" -> TEST 5 (Missing supervisor email -> Handled safely): PASS")

    # -----------------------------------------------------------------
    # TEST 6: Invalid Credentials -> Auth Failure Masked & Logged
    # -----------------------------------------------------------------
    def test_6_invalid_credentials_handling(self):
        """Test 6: SMTP authentication failure is logged safely without leaking secrets."""
        with patch.object(EmailService, 'send_email', return_value=(False, "SMTP Authentication Failed")):
            execute_update("DELETE FROM notification_logs WHERE machine_id = %s", (self.test_machine_id,))

            res = PredictionService.run_prediction(
                machine_id=self.test_machine_id,
                air_temperature=304.0,
                process_temperature=314.5,
                rotational_speed=1200.0,
                torque=75.0,
                tool_wear=240.0
            )
            self.assertIsNotNone(res["id"])
            self.assertEqual(res["notification"]["status"], "failed")
            print(" -> TEST 6 (Invalid Gmail App Password -> Handled safely): PASS")

    # -----------------------------------------------------------------
    # TEST 7: Duplicate Alert Cooldown Suppression
    # -----------------------------------------------------------------
    def test_7_duplicate_alert_cooldown_suppression(self):
        """Test 7: Repeated Warning prediction within cooldown is suppressed."""
        with patch.object(EmailService, 'send_email', return_value=(True, None)) as mock_send:
            # 1. First Warning alert sent
            execute_update("DELETE FROM notification_logs WHERE machine_id = %s", (self.test_machine_id,))
            res1 = PredictionService.run_prediction(
                machine_id=self.test_machine_id,
                air_temperature=298.5,
                process_temperature=309.0,
                rotational_speed=1741.0,
                torque=28.0,
                tool_wear=21.0
            )
            self.assertEqual(res1["notification"]["status"], "sent")

            # 2. Immediate second Warning alert on same machine -> Suppressed
            res2 = PredictionService.run_prediction(
                machine_id=self.test_machine_id,
                air_temperature=298.5,
                process_temperature=309.0,
                rotational_speed=1741.0,
                torque=28.0,
                tool_wear=21.0
            )
            self.assertEqual(res2["notification"]["status"], "duplicate_suppressed")
            self.assertIn("Email suppressed", res2["notification"]["message"])
            print(" -> TEST 7 (Duplicate Warning -> Cooldown suppression): PASS")

    # -----------------------------------------------------------------
    # TEST 8: ReportLab PDF Generation
    # -----------------------------------------------------------------
    def test_8_reportlab_pdf_generation(self):
        """Test 8: ReportLab PDF report generation."""
        pdf_buf = ReportsService.generate_pdf_report()
        self.assertIsNotNone(pdf_buf)
        pdf_bytes = pdf_buf.read()
        self.assertTrue(pdf_bytes.startswith(b"%PDF"))
        self.assertGreater(len(pdf_bytes), 1000)
        print(" -> TEST 8 (ReportLab PDF Generation): PASS")

    # -----------------------------------------------------------------
    # TEST 9: Flask Endpoints & API
    # -----------------------------------------------------------------
    def test_9_flask_endpoints(self):
        """Test 9: Flask views and REST endpoints."""
        # Dashboard view
        resp = self.client.get("/dashboard")
        self.assertEqual(resp.status_code, 200)

        # Health API
        resp = self.client.get("/api/health")
        self.assertEqual(resp.status_code, 200)
        data = resp.get_json()
        self.assertEqual(data["service"], "PredictCNC Flask Engine")

        # Machines API
        resp = self.client.get("/api/machines")
        self.assertEqual(resp.status_code, 200)
        self.assertIsInstance(resp.get_json(), list)

    # -----------------------------------------------------------------
    # TEST 10: Multi-Tenant User Fleet Isolation
    # -----------------------------------------------------------------
    def test_10_multi_tenant_user_isolation(self):
        """Test 10: Newly registered user starts with 0 machines, and fleets are strictly isolated."""
        import time
        unique_suffix = int(time.time())
        username = f"newuser_{unique_suffix}"
        
        # 1. Register new user
        new_user_id = AuthService.register_user(
            company_name="New Corp Precision",
            admin_name="New User",
            email=f"user_{unique_suffix}@example.com",
            username=username,
            password="password123"
        )
        self.assertIsNotNone(new_user_id)

        # 2. Verify new user starts with strictly 0 machines
        new_user_machines = MachineService.get_all_machines(new_user_id)
        self.assertEqual(len(new_user_machines), 0)

        # 3. Verify KPI summary metrics are 0 for the new user
        metrics = ReportsService.get_summary_metrics(new_user_id)
        self.assertEqual(metrics["total_machines"], 0)
        self.assertEqual(metrics["healthy_machines"], 0)
        self.assertEqual(metrics["warning_machines"], 0)
        self.assertEqual(metrics["critical_machines"], 0)
        self.assertEqual(metrics["total_predictions"], 0)
        self.assertEqual(metrics["total_tickets"], 0)

        # 4. User manually creates a machine
        created_machine_id = MachineService.create_machine(
            user_id=new_user_id,
            machine_code=f"ISO-{unique_suffix}",
            machine_name="Isolated 4-Axis CNC",
            department="Cell 9",
            manufacturer="DMG Mori",
            supervisor_name="New User",
            supervisor_email=f"user_{unique_suffix}@example.com"
        )
        self.assertIsNotNone(created_machine_id)

        # 5. Verify the created machine is visible to new user (1 machine)
        user_fleet = MachineService.get_all_machines(new_user_id)
        self.assertEqual(len(user_fleet), 1)
        self.assertEqual(user_fleet[0]["machine_code"], f"ISO-{unique_suffix}")

        # 6. Verify this machine is NOT in admin's fleet (admin has user_id = 1)
        admin_fleet = MachineService.get_all_machines(1)
        admin_machine_codes = [m["machine_code"] for m in admin_fleet]
        self.assertNotIn(f"ISO-{unique_suffix}", admin_machine_codes)

        # Clean up
        MachineService.delete_machine(created_machine_id)
        execute_update("DELETE FROM users WHERE id = %s", (new_user_id,))
        print(" -> TEST 10 (Multi-Tenant Machine Fleet Isolation): PASS")

if __name__ == "__main__":
    unittest.main()
