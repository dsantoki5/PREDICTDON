"""
PredictCNC Database Layer — PostgreSQL Native Engine.
Provides PostgreSQL connection management, query execution, automatic database/schema initialization, and seeder logic.
"""
import os
import logging
from datetime import datetime, timezone
import psycopg2
import psycopg2.extras

try:
    from dotenv import load_dotenv
except ImportError:
    def load_dotenv(*args, **kwargs):
        pass

# Load environment variables
backend_dir = os.path.dirname(os.path.abspath(__file__))
if load_dotenv:
    load_dotenv(os.path.join(backend_dir, ".env"))

logger = logging.getLogger("predictcnc.db")

# PostgreSQL Configuration
PG_HOST = os.getenv("PG_HOST", "localhost")
PG_PORT = int(os.getenv("PG_PORT", 5432))
PG_USER = os.getenv("PG_USER", "postgres")
PG_PASSWORD = os.getenv("PG_PASSWORD", "")
PG_DB = os.getenv("PG_DB", "predictcnc")

def get_db_connection():
    """
    Establishes and returns a connection to the PostgreSQL database.
    Auto-creates the database if it doesn't exist on the PostgreSQL server.
    """
    try:
        conn = psycopg2.connect(
            host=PG_HOST,
            port=PG_PORT,
            user=PG_USER,
            password=PG_PASSWORD,
            dbname=PG_DB,
            connect_timeout=3
        )
        conn.autocommit = True
        return conn
    except Exception as e:
        err_str = str(e).lower()
        if "does not exist" in err_str or f'database "{PG_DB.lower()}" does not exist' in err_str:
            try:
                root_conn = psycopg2.connect(
                    host=PG_HOST,
                    port=PG_PORT,
                    user=PG_USER,
                    password=PG_PASSWORD,
                    dbname="postgres",
                    connect_timeout=3
                )
                root_conn.autocommit = True
                with root_conn.cursor() as cur:
                    cur.execute(f'CREATE DATABASE "{PG_DB}";')
                root_conn.close()
                conn = psycopg2.connect(
                    host=PG_HOST,
                    port=PG_PORT,
                    user=PG_USER,
                    password=PG_PASSWORD,
                    dbname=PG_DB,
                    connect_timeout=3
                )
                conn.autocommit = True
                return conn
            except Exception as create_err:
                logger.error(f"Could not auto-create PostgreSQL database '{PG_DB}': {create_err}")
                raise e
        raise e

def query_all(sql, params=None):
    """Executes a SELECT query on PostgreSQL and returns a list of dictionaries."""
    conn = get_db_connection()
    try:
        with conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor) as cur:
            cur.execute(sql, params or ())
            rows = cur.fetchall()
            return [dict(r) for r in rows]
    finally:
        conn.close()

def query_one(sql, params=None):
    """Executes a SELECT query on PostgreSQL and returns a single dictionary or None."""
    rows = query_all(sql, params)
    return rows[0] if rows else None

def execute_insert(sql, params=None):
    """Executes an INSERT query on PostgreSQL and returns the newly inserted ID."""
    conn = get_db_connection()
    try:
        clean_sql = sql.strip().rstrip(";")
        if " RETURNING " not in clean_sql.upper():
            clean_sql += " RETURNING id"
        with conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor) as cur:
            cur.execute(clean_sql, params or ())
            res = cur.fetchone()
            return res["id"] if res and "id" in res else None
    finally:
        conn.close()

def execute_update(sql, params=None):
    """Executes an UPDATE or DELETE query on PostgreSQL and returns the affected rows count."""
    conn = get_db_connection()
    try:
        with conn.cursor() as cur:
            cur.execute(sql, params or ())
            return cur.rowcount
    finally:
        conn.close()

def init_db():
    """Initializes all PostgreSQL database tables and indices."""
    conn = get_db_connection()
    try:
        with conn.cursor() as cur:
            cur.execute("""
            CREATE TABLE IF NOT EXISTS users (
                id SERIAL PRIMARY KEY,
                company_name VARCHAR(150) NOT NULL,
                admin_name VARCHAR(100) NOT NULL,
                email VARCHAR(100) NOT NULL,
                username VARCHAR(50) NOT NULL UNIQUE,
                password VARCHAR(255) NOT NULL,
                role VARCHAR(50) DEFAULT 'Administrator',
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            );
            """)

            cur.execute("""
            CREATE TABLE IF NOT EXISTS machines (
                id SERIAL PRIMARY KEY,
                user_id INT NULL,
                machine_code VARCHAR(30) NOT NULL,
                machine_name VARCHAR(100) NOT NULL,
                department VARCHAR(100) NULL,
                manufacturer VARCHAR(100) NULL,
                installation_date DATE NULL,
                status VARCHAR(30) DEFAULT 'Pending Assessment',
                supervisor_name VARCHAR(100) NULL,
                supervisor_email VARCHAR(100) NULL,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE SET NULL
            );
            """)

            # Ensure multi-tenant scoped unique index for (user_id, machine_code) and drop legacy global constraint
            cur.execute("""
            ALTER TABLE machines DROP CONSTRAINT IF EXISTS machines_machine_code_key;
            CREATE UNIQUE INDEX IF NOT EXISTS ix_machines_user_code ON machines (user_id, machine_code);
            """)

            cur.execute("""
            CREATE TABLE IF NOT EXISTS predictions (
                id SERIAL PRIMARY KEY,
                machine_id INT NOT NULL,
                air_temperature DOUBLE PRECISION NOT NULL,
                process_temperature DOUBLE PRECISION NOT NULL,
                rotational_speed DOUBLE PRECISION NOT NULL,
                torque DOUBLE PRECISION NOT NULL,
                tool_wear DOUBLE PRECISION NOT NULL,
                load_density DOUBLE PRECISION NULL,
                rpm_torque_interaction DOUBLE PRECISION NULL,
                temperature_difference DOUBLE PRECISION NULL,
                temperature_ratio DOUBLE PRECISION NULL,
                load_stress DOUBLE PRECISION NULL,
                prediction VARCHAR(50) NOT NULL,
                predicted_class INT DEFAULT 0,
                model_version VARCHAR(100) NULL,
                probability DOUBLE PRECISION NOT NULL,
                healthy_probability DOUBLE PRECISION NULL,
                warning_probability DOUBLE PRECISION NULL,
                critical_probability DOUBLE PRECISION NULL,
                confidence NUMERIC(5,2) NULL,
                predicted_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (machine_id) REFERENCES machines(id) ON DELETE CASCADE
            );
            """)

            cur.execute("""
            CREATE TABLE IF NOT EXISTS maintenance (
                id SERIAL PRIMARY KEY,
                machine_id INT NOT NULL,
                prediction_id INT NULL,
                priority VARCHAR(20) DEFAULT 'Medium',
                status VARCHAR(20) DEFAULT 'Pending',
                remarks TEXT NULL,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (machine_id) REFERENCES machines(id) ON DELETE CASCADE,
                FOREIGN KEY (prediction_id) REFERENCES predictions(id) ON DELETE SET NULL
            );
            """)

            cur.execute("""
            CREATE TABLE IF NOT EXISTS notification_logs (
                id SERIAL PRIMARY KEY,
                machine_id INT NOT NULL,
                recipient_email VARCHAR(150) NOT NULL,
                alert_type VARCHAR(50) NOT NULL,
                health_status VARCHAR(50) NOT NULL,
                prediction VARCHAR(255) NULL,
                delivery_status VARCHAR(50) NOT NULL,
                error_message TEXT NULL,
                sent_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (machine_id) REFERENCES machines(id) ON DELETE CASCADE
            );
            """)

            cur.execute("""
            CREATE TABLE IF NOT EXISTS security_audit_logs (
                id SERIAL PRIMARY KEY,
                user_id INT NULL,
                username VARCHAR(50) NULL,
                user_role VARCHAR(50) NULL,
                action VARCHAR(100) NOT NULL,
                target_resource VARCHAR(100) NULL,
                ip_address VARCHAR(50) NULL,
                status VARCHAR(20) NOT NULL,
                details TEXT NULL,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            );
            """)

    finally:
        conn.close()

    try:
        execute_update("UPDATE machines SET user_id = 1 WHERE user_id IS NULL")
    except Exception as e:
        logger.warning(f"Orphaned machine fleet migration notice: {e}")

def seed_default_data():
    """Seeds default admin user and initial machine fleet if empty, and synchronizes admin credentials."""
    init_db()
    users_count = query_one("SELECT COUNT(*) as count FROM users")
    if not users_count or users_count['count'] == 0:
        import hashlib
        pwd_hash = hashlib.sha256("admin123".encode()).hexdigest()
        admin_id = execute_insert(
            "INSERT INTO users (company_name, admin_name, email, username, password, role) VALUES (%s, %s, %s, %s, %s, %s)",
            ("LDRP Precision Engineering", "Divya Santoki", "forldrpml456@gmail.com", "admin", pwd_hash, "Administrator")
        )
        
        default_machines = [
            ("CNC001", "CNC Lathe Heavy Duty", "Workshop A", "Haas", "2024-01-10", "Healthy", "Divya Santoki", "forldrpml456@gmail.com"),
            ("CNC002", "CNC 5-Axis Milling", "Workshop A", "Mazak", "2023-06-20", "Healthy", "Aarav Shah", "forldrpml456@gmail.com"),
            ("CNC003", "CNC Precision Drilling", "Workshop B", "DMG Mori", "2022-09-15", "Warning", "Divya Santoki", "forldrpml456@gmail.com"),
            ("CNC004", "CNC High-Speed Turning", "Workshop C", "Okuma", "2024-03-12", "Critical", "Aarav Shah", "forldrpml456@gmail.com"),
            ("CNC005", "CNC Surface Grinding", "Workshop B", "Makino", "2023-11-08", "Healthy", "Divya Santoki", "forldrpml456@gmail.com"),
        ]
        for code, name, dept, mfg, inst_date, status, sup_name, sup_email in default_machines:
            execute_insert(
                "INSERT INTO machines (user_id, machine_code, machine_name, department, manufacturer, installation_date, status, supervisor_name, supervisor_email) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)",
                (admin_id, code, name, dept, mfg, inst_date, status, sup_name, sup_email)
            )
        logger.info("Default seed data loaded into PostgreSQL database.")
    else:
        import hashlib
        expected_hash = hashlib.sha256("admin123".encode()).hexdigest()
        execute_update("UPDATE users SET password = %s WHERE LOWER(username) = 'admin' AND password != %s", (expected_hash, expected_hash))

def get_active_db_info():
    """Returns metadata about the PostgreSQL database engine."""
    return {
        "driver": "PostgreSQL",
        "host": f"{PG_HOST}:{PG_PORT}",
        "database": PG_DB,
        "status": "Connected"
    }
