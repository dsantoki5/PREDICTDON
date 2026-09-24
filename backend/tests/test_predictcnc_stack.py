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
            password="Password@123"
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

    # -----------------------------------------------------------------
    # TEST 11: Shared Email Across Multiple Companies
    # -----------------------------------------------------------------
    def test_11_same_email_multiple_companies(self):
        """Test 11: An admin can use one email to manage multiple company accounts with distinct usernames."""
        import time
        ts = int(time.time())
        shared_email = f"multiadmin_{ts}@gmail.com"
        
        # Company 1
        user1_id = AuthService.register_user(
            company_name="Alpha Tech CNC",
            admin_name="Aarav",
            email=shared_email,
            username=f"aarav_alpha_{ts}",
            password="Password@123"
        )
        self.assertIsNotNone(user1_id)

        # Company 2 with SAME EMAIL
        user2_id = AuthService.register_user(
            company_name="Beta Precision",
            admin_name="Aarav",
            email=shared_email,
            username=f"aarav_beta_{ts}",
            password="Password@123"
        )
        self.assertIsNotNone(user2_id)
        self.assertNotEqual(user1_id, user2_id)

        # Duplicate username should still raise error
        with self.assertRaises(ValueError):
            AuthService.register_user(
                company_name="Gamma Mills",
                admin_name="Aarav",
                email=shared_email,
                username=f"aarav_alpha_{ts}", # duplicate username
                password="Password@123"
            )

        # Authenticate by username
        u1 = AuthService.authenticate_user(f"aarav_alpha_{ts}", "Password@123")
        self.assertIsNotNone(u1)
        self.assertEqual(u1["company_name"], "Alpha Tech CNC")

        u2 = AuthService.authenticate_user(f"aarav_beta_{ts}", "Password@123")
        self.assertIsNotNone(u2)
        self.assertEqual(u2["company_name"], "Beta Precision")

        # Authenticate with company disambiguation
        u1_by_email = AuthService.authenticate_user(shared_email, "Password@123", company_name="Alpha Tech CNC")
        self.assertIsNotNone(u1_by_email)
        self.assertEqual(u1_by_email["id"], user1_id)

        # Clean up
        execute_update("DELETE FROM users WHERE id IN (%s, %s)", (user1_id, user2_id))
        print(" -> TEST 11 (Shared Email Across Multiple Companies): PASS")

    # -----------------------------------------------------------------
    # TEST 12: Machine Initial Status Lifecycle (Unassessed -> Predicted)
    # -----------------------------------------------------------------
    def test_12_machine_unpredicted_status_lifecycle(self):
        """Test 12: Newly created machine is 'Pending Assessment' until its first prediction runs."""
        import time
        ts = int(time.time())
        
        # 1. Create a fresh machine
        m_id = MachineService.create_machine(
            user_id=1,
            machine_code=f"LIFE-{ts}",
            machine_name="Lifecycle Test Milling CNC",
            department="QA Bay",
            manufacturer="Haas",
            supervisor_name="QA Lead",
            supervisor_email="qa@example.com"
        )
        self.assertIsNotNone(m_id)

        # 2. Verify initial status is 'Pending Assessment' (NOT directly 'Healthy')
        machine = MachineService.get_machine_by_id(m_id)
        self.assertEqual(machine["status"], "Pending Assessment")

        # 3. Run first normal telemetry prediction on this machine
        pred_res = PredictionService.run_prediction(
            machine_id=m_id,
            air_temperature=298.15,
            process_temperature=308.65,
            rotational_speed=1500,
            torque=40.0,
            tool_wear=30
        )
        self.assertEqual(pred_res["suggested_machine_status"], "Healthy")

        # 4. Verify machine status has now transitioned to 'Healthy'
        updated_machine = MachineService.get_machine_by_id(m_id)
        self.assertEqual(updated_machine["status"], "Healthy")

        # Clean up
        MachineService.delete_machine(m_id)
        print(" -> TEST 12 (Machine Initial Status Lifecycle): PASS")

    # -----------------------------------------------------------------
    # TEST 13: RBAC Operator Restrictions & Audit Logging
    # -----------------------------------------------------------------
    def test_13_rbac_operator_restrictions(self):
        """Test 13: Factory Operator role cannot create/edit/delete machines (403 Forbidden + Audit Log)."""
        operator_client = app.test_client()
        with operator_client.session_transaction() as sess:
            sess["user_id"] = 999
            sess["user"] = {
                "id": 999,
                "username": "worker_john",
                "admin_name": "John Doe",
                "company_name": "ShopFloor Precision",
                "email": "john@shopfloor.local",
                "role": "Operator"
            }

        # 1. Attempt machine creation -> 403 Forbidden
        res_create = operator_client.post("/api/machines", json={
            "machine_code": "OP-DENIED-01",
            "machine_name": "Unauthorized Mill"
        })
        self.assertEqual(res_create.status_code, 403)
        data_create = res_create.get_json()
        self.assertEqual(data_create["status"], "access_denied")
        self.assertEqual(data_create["error_code"], "INSUFFICIENT_ROLE_PERMISSIONS")
        self.assertIn("Operator", data_create["detail"])

        # 2. Attempt machine update -> 403 Forbidden
        res_update = operator_client.put(f"/api/machines/{self.test_machine_id}", json={
            "machine_name": "Hacked Mill"
        })
        self.assertEqual(res_update.status_code, 403)

        # 3. Attempt machine deletion -> 403 Forbidden
        res_delete = operator_client.delete(f"/api/machines/{self.test_machine_id}")
        self.assertEqual(res_delete.status_code, 403)

        # 4. Verify security incident was recorded in security_audit_logs
        incident = query_one(
            "SELECT * FROM security_audit_logs WHERE user_id = 999 AND status = 'DENIED' ORDER BY id DESC LIMIT 1"
        )
        self.assertIsNotNone(incident)
        self.assertIn("Operator", incident["details"])
        print(" -> TEST 13 (RBAC Operator Restrictions & Audit Logging): PASS")

    # -----------------------------------------------------------------
    # TEST 14: Multi-Tenant Machine IDOR Prevention
    # -----------------------------------------------------------------
    def test_14_idor_cross_tenant_isolation(self):
        """Test 14: Tenant B cannot update, delete, or run predictions on Tenant A's machine."""
        tenant_b_client = app.test_client()
        with tenant_b_client.session_transaction() as sess:
            sess["user_id"] = 888
            sess["user"] = {
                "id": 888,
                "username": "tenant_b_admin",
                "admin_name": "Tenant B Admin",
                "company_name": "Company B",
                "email": "admin@companyb.local",
                "role": "Administrator"
            }

        # Attempt to modify machine belonging to user_id=1
        res_update = tenant_b_client.put(f"/api/machines/{self.test_machine_id}", json={
            "machine_name": "Hostile Takeover"
        })
        self.assertEqual(res_update.status_code, 404)

        # Attempt to delete machine belonging to user_id=1
        res_delete = tenant_b_client.delete(f"/api/machines/{self.test_machine_id}")
        self.assertEqual(res_delete.status_code, 404)

        # Attempt to run prediction on machine belonging to user_id=1
        res_pred = tenant_b_client.post("/api/predict", json={
            "machine_id": self.test_machine_id,
            "air_temperature": 298.15,
            "process_temperature": 308.15,
            "rotational_speed": 1500,
            "torque": 40.0,
            "tool_wear": 50
        })
        self.assertEqual(res_pred.status_code, 400)
        self.assertIn("access denied", res_pred.get_json()["detail"].lower())
        print(" -> TEST 14 (Multi-Tenant Machine IDOR Prevention): PASS")

    # -----------------------------------------------------------------
    # TEST 15: Password Hashing & Secure Password Change
    # -----------------------------------------------------------------
    def test_15_password_hashing_and_change(self):
        """Test 15: Werkzeug password hashing verification and secure password change."""
        import time
        ts = int(time.time())
        uname = f"pwdtest_{ts}"
        uid = AuthService.register_user("Security Labs", "Sec Lead", f"{uname}@test.com", uname, "InitialPass@123")
        
        # Verify user hash is modern Werkzeug format
        u = AuthService.get_user_by_id(uid)
        self.assertTrue(u["password"].startswith("scrypt:") or u["password"].startswith("pbkdf2:"))

        # Authenticate succeeds
        self.assertIsNotNone(AuthService.authenticate_user(uname, "InitialPass@123"))

        # Wrong old password fails change
        with self.assertRaises(ValueError):
            AuthService.change_password(uid, "WrongPassword", "NewSecurePass@456")

        # Correct old password succeeds change
        self.assertTrue(AuthService.change_password(uid, "InitialPass@123", "NewSecurePass@456"))

        # Old password no longer works
        self.assertIsNone(AuthService.authenticate_user(uname, "InitialPass@123"))

        # New password works
        self.assertIsNotNone(AuthService.authenticate_user(uname, "NewSecurePass@456"))

        # Clean up
        execute_update("DELETE FROM users WHERE id = %s", (uid,))
        print(" -> TEST 15 (Password Hashing & Secure Password Change): PASS")

    # -----------------------------------------------------------------
    # TEST 16: PDF Report Null-Safety Coalescing
    # -----------------------------------------------------------------
    def test_16_pdf_null_coalescing(self):
        """Test 16: ReportsService.generate_pdf_report handles None telemetry values safely."""
        # Insert a dummy prediction record with None nullable values
        pred_id = execute_insert(
            """INSERT INTO predictions (
                machine_id, air_temperature, process_temperature, rotational_speed, torque, tool_wear,
                load_density, rpm_torque_interaction, temperature_difference, temperature_ratio, load_stress,
                prediction, predicted_class, model_version, probability, confidence, predicted_at
            ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)""",
            (
                self.test_machine_id, 298.0, 308.0, 1500.0, 40.0, 10.0,
                None, None, None, None, None,
                "Normal Operation", 0, "Test Model", 15.0, None, datetime.now()
            )
        )
        pdf_buf = ReportsService.generate_pdf_report(user_id=1)
        self.assertIsNotNone(pdf_buf)
        self.assertGreater(len(pdf_buf.getvalue()), 1000)

        # Clean up
        execute_update("DELETE FROM predictions WHERE id = %s", (pred_id,))
        print(" -> TEST 16 (PDF Report Null-Safety Coalescing): PASS")

    # -----------------------------------------------------------------
    # TEST 17: Industrial Authentication Input & Password Complexity Validation
    # -----------------------------------------------------------------
    def test_17_auth_input_validation(self):
        """Test 17: Strict validation for single-char/weak passwords, invalid emails, and usernames."""
        import time
        ts = int(time.time())

        # 1. Reject 1-character password
        with self.assertRaises(ValueError) as ctx:
            AuthService.register_user("ACME Corp", "John", f"test_{ts}@acme.com", f"user_len_{ts}", ".")
        self.assertIn("at least 8 characters", str(ctx.exception).lower())

        # 2. Reject password lacking uppercase
        with self.assertRaises(ValueError) as ctx:
            AuthService.register_user("ACME Corp", "John", f"test_{ts}@acme.com", f"user_upper_{ts}", "password@123")
        self.assertIn("uppercase", str(ctx.exception).lower())

        # 3. Reject password lacking lowercase
        with self.assertRaises(ValueError) as ctx:
            AuthService.register_user("ACME Corp", "John", f"test_{ts}@acme.com", f"user_lower_{ts}", "PASSWORD@123")
        self.assertIn("lowercase", str(ctx.exception).lower())

        # 4. Reject password lacking digit
        with self.assertRaises(ValueError) as ctx:
            AuthService.register_user("ACME Corp", "John", f"test_{ts}@acme.com", f"user_digit_{ts}", "Password@XYZ")
        self.assertIn("numeric digit", str(ctx.exception).lower())

        # 5. Reject password lacking special character
        with self.assertRaises(ValueError) as ctx:
            AuthService.register_user("ACME Corp", "John", f"test_{ts}@acme.com", f"user_spec_{ts}", "Password123")
        self.assertIn("special character", str(ctx.exception).lower())

        # 6. Reject invalid email format
        with self.assertRaises(ValueError) as ctx:
            AuthService.register_user("ACME Corp", "John", "invalid_email_format", f"user_email_{ts}", "Password@123")
        self.assertIn("valid email", str(ctx.exception).lower())

        # 7. Reject invalid username
        with self.assertRaises(ValueError) as ctx:
            AuthService.register_user("ACME Corp", "John", f"test_{ts}@acme.com", "ab", "Password@123")
        self.assertIn("between 3 and 50 characters", str(ctx.exception).lower())

        # 8. Reject short company name
        with self.assertRaises(ValueError) as ctx:
            AuthService.register_user("A", "John", f"test_{ts}@acme.com", f"user_co_{ts}", "Password@123")
        self.assertIn("company name", str(ctx.exception).lower())

        # 9. API endpoint reject 1-char password
        res = self.client.post("/api/auth/register", json={
            "company_name": "Precision CNC",
            "admin_name": "Supervisor",
            "email": f"operator_{ts}@precision.com",
            "username": f"op_{ts}",
            "password": "."
        })
        self.assertEqual(res.status_code, 400)
        self.assertIn("at least 8 characters", res.get_json()["detail"].lower())

        print(" -> TEST 17 (Auth Input & Password Complexity Validation): PASS")


if __name__ == "__main__":
    unittest.main()




