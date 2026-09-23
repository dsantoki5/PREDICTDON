"""
PredictCNC Database Layer — PyMySQL / MySQL with XAMPP Compatibility & Resilient Fallback.
Provides unified query execution, connection pooling, schema initialization, and seeder logic.
"""
import os
import sqlite3
import logging
from datetime import datetime, timezone
import pymysql
from pymysql.cursors import DictCursor
from dotenv import load_dotenv

# Load environment variables
backend_dir = os.path.dirname(os.path.abspath(__file__))
load_dotenv(os.path.join(backend_dir, ".env"))

logger = logging.getLogger("predictcnc.db")

MYSQL_HOST = os.getenv("MYSQL_HOST", "localhost")
MYSQL_PORT = int(os.getenv("MYSQL_PORT", 3306))
MYSQL_USER = os.getenv("MYSQL_USER", "root")
MYSQL_PASSWORD = os.getenv("MYSQL_PASSWORD", "")
MYSQL_DB = os.getenv("MYSQL_DB", "predictcnc")
SQLITE_DB_PATH = os.path.join(backend_dir, "predictcnc.db")

# Flag indicating if active driver is MySQL or SQLite fallback
_DB_DRIVER = None
_MYSQL_LAST_CHECK = 0

def get_db_connection():
    """
    Attempts to connect to MySQL (e.g. XAMPP MySQL on port 3306).
    If MySQL server is unavailable, transparently falls back to local SQLite database.
    """
    global _DB_DRIVER, _MYSQL_LAST_CHECK
    import time
    
    now = time.time()
    # If MySQL previously failed within last 10 seconds, quickly use SQLite fallback
    if _DB_DRIVER == "sqlite" and (now - _MYSQL_LAST_CHECK) < 10:
        conn = sqlite3.connect(SQLITE_DB_PATH)
        conn.row_factory = sqlite3.Row
        return conn, "sqlite"

    # Try MySQL / PyMySQL first
    try:
        conn = pymysql.connect(
            host=MYSQL_HOST,
            port=MYSQL_PORT,
            user=MYSQL_USER,
            password=MYSQL_PASSWORD,
            database=MYSQL_DB,
            charset='utf8mb4',
            cursorclass=DictCursor,
            autocommit=True,
            connect_timeout=1
        )
        if _DB_DRIVER != "mysql":
            logger.info(f"Connected to MySQL database '{MYSQL_DB}' on {MYSQL_HOST}:{MYSQL_PORT}")
            _DB_DRIVER = "mysql"
        return conn, "mysql"
    except Exception as mysql_err:
        _MYSQL_LAST_CHECK = now
        # If database doesn't exist yet, try creating it in MySQL
        if "Unknown database" in str(mysql_err) or "1049" in str(mysql_err):
            try:
                root_conn = pymysql.connect(
                    host=MYSQL_HOST,
                    port=MYSQL_PORT,
                    user=MYSQL_USER,
                    password=MYSQL_PASSWORD,
                    charset='utf8mb4',
                    autocommit=True,
                    connect_timeout=1
                )
                with root_conn.cursor() as cur:
                    cur.execute(f"CREATE DATABASE IF NOT EXISTS `{MYSQL_DB}` CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci")
                root_conn.close()
                return get_db_connection()
            except Exception:
                pass

        # Fallback to local SQLite
        if _DB_DRIVER != "sqlite":
            logger.warning(f"MySQL unavailable ({mysql_err}). Falling back to SQLite at '{SQLITE_DB_PATH}'.")
            _DB_DRIVER = "sqlite"
        
        conn = sqlite3.connect(SQLITE_DB_PATH)
        conn.row_factory = sqlite3.Row
        return conn, "sqlite"

def _prepare_sqlite_params(params):
    if not params:
        return ()
    cleaned = []
    for p in params:
        if isinstance(p, datetime):
            cleaned.append(p.strftime("%Y-%m-%d %H:%M:%S"))
        else:
            cleaned.append(p)
    return tuple(cleaned)

def query_all(sql, params=None):
    """Executes a SELECT query and returns a list of dictionaries."""
    conn, driver = get_db_connection()
    try:
        if driver == "mysql":
            with conn.cursor() as cur:
                cur.execute(sql, params or ())
                return cur.fetchall()
        else:
            sqlite_sql = sql.replace("%s", "?")
            cur = conn.cursor()
            cur.execute(sqlite_sql, _prepare_sqlite_params(params))
            rows = cur.fetchall()
            return [dict(row) for row in rows]
    finally:
        conn.close()

def query_one(sql, params=None):
    """Executes a SELECT query and returns a single dictionary or None."""
    rows = query_all(sql, params)
    return rows[0] if rows else None

def execute_insert(sql, params=None):
    """Executes an INSERT query and returns the newly inserted ID."""
    conn, driver = get_db_connection()
    try:
        if driver == "mysql":
            with conn.cursor() as cur:
                cur.execute(sql, params or ())
                return cur.lastrowid
        else:
            sqlite_sql = sql.replace("%s", "?")
            cur = conn.cursor()
            cur.execute(sqlite_sql, _prepare_sqlite_params(params))
            conn.commit()
            return cur.lastrowid
    finally:
        conn.close()

def execute_update(sql, params=None):
    """Executes an UPDATE or DELETE query and returns the affected rows count."""
    conn, driver = get_db_connection()
    try:
        if driver == "mysql":
            with conn.cursor() as cur:
                cur.execute(sql, params or ())
                return cur.rowcount
        else:
            sqlite_sql = sql.replace("%s", "?")
            cur = conn.cursor()
            cur.execute(sqlite_sql, _prepare_sqlite_params(params))
            conn.commit()
            return cur.rowcount
    finally:
        conn.close()

def init_db():
    """Initializes all database tables with proper MySQL / SQLite syntax."""
    conn, driver = get_db_connection()
    try:
        if driver == "mysql":
            with conn.cursor() as cur:
                cur.execute("""
                CREATE TABLE IF NOT EXISTS users (
                    id INT AUTO_INCREMENT PRIMARY KEY,
                    company_name VARCHAR(150) NOT NULL,
                    admin_name VARCHAR(100) NOT NULL,
                    email VARCHAR(100) NOT NULL,
                    username VARCHAR(50) NOT NULL UNIQUE,
                    password VARCHAR(255) NOT NULL,
                    role VARCHAR(50) DEFAULT 'Administrator',
                    created_at DATETIME DEFAULT CURRENT_TIMESTAMP
                ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;
                """)

                cur.execute("""
                CREATE TABLE IF NOT EXISTS machines (
                    id INT AUTO_INCREMENT PRIMARY KEY,
                    user_id INT NULL,
                    machine_code VARCHAR(30) NOT NULL UNIQUE,
                    machine_name VARCHAR(100) NOT NULL,
                    department VARCHAR(100) NULL,
                    manufacturer VARCHAR(100) NULL,
                    installation_date DATE NULL,
                    status VARCHAR(30) DEFAULT 'Pending Assessment',
                    supervisor_name VARCHAR(100) NULL,
                    supervisor_email VARCHAR(100) NULL,
                    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE SET NULL
                ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;
                """)

                cur.execute("""
                CREATE TABLE IF NOT EXISTS predictions (
                    id INT AUTO_INCREMENT PRIMARY KEY,
                    machine_id INT NOT NULL,
                    air_temperature DOUBLE NOT NULL,
                    process_temperature DOUBLE NOT NULL,
                    rotational_speed DOUBLE NOT NULL,
                    torque DOUBLE NOT NULL,
                    tool_wear DOUBLE NOT NULL,
                    load_density DOUBLE NULL,
                    rpm_torque_interaction DOUBLE NULL,
                    temperature_difference DOUBLE NULL,
                    temperature_ratio DOUBLE NULL,
                    load_stress DOUBLE NULL,
                    prediction VARCHAR(50) NOT NULL,
                    predicted_class INT DEFAULT 0,
                    model_version VARCHAR(100) NULL,
                    probability DOUBLE NOT NULL,
                    healthy_probability DOUBLE NULL,
                    warning_probability DOUBLE NULL,
                    critical_probability DOUBLE NULL,
                    confidence DECIMAL(5,2) NULL,
                    predicted_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (machine_id) REFERENCES machines(id) ON DELETE CASCADE
                ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;
                """)

                cur.execute("""
                CREATE TABLE IF NOT EXISTS maintenance (
                    id INT AUTO_INCREMENT PRIMARY KEY,
                    machine_id INT NOT NULL,
                    prediction_id INT NULL,
                    priority VARCHAR(20) DEFAULT 'Medium',
                    status VARCHAR(20) DEFAULT 'Pending',
                    remarks TEXT NULL,
                    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (machine_id) REFERENCES machines(id) ON DELETE CASCADE,
                    FOREIGN KEY (prediction_id) REFERENCES predictions(id) ON DELETE SET NULL
                ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;
                """)

                cur.execute("""
                CREATE TABLE IF NOT EXISTS notification_logs (
                    id INT AUTO_INCREMENT PRIMARY KEY,
                    machine_id INT NOT NULL,
                    recipient_email VARCHAR(150) NOT NULL,
                    alert_type VARCHAR(50) NOT NULL,
                    health_status VARCHAR(50) NOT NULL,
                    prediction VARCHAR(255) NULL,
                    delivery_status VARCHAR(50) NOT NULL,
                    error_message TEXT NULL,
                    sent_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (machine_id) REFERENCES machines(id) ON DELETE CASCADE
                ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;
                """)
        else:
            cur = conn.cursor()
            cur.execute("""
            CREATE TABLE IF NOT EXISTS users (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                company_name VARCHAR(150) NOT NULL,
                admin_name VARCHAR(100) NOT NULL,
                email VARCHAR(100) NOT NULL,
                username VARCHAR(50) NOT NULL UNIQUE,
                password VARCHAR(255) NOT NULL,
                role VARCHAR(50) DEFAULT 'Administrator',
                created_at DATETIME DEFAULT CURRENT_TIMESTAMP
            );
            """)
            cur.execute("""
            CREATE TABLE IF NOT EXISTS machines (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER NULL,
                machine_code VARCHAR(30) NOT NULL UNIQUE,
                machine_name VARCHAR(100) NOT NULL,
                department VARCHAR(100) NULL,
                manufacturer VARCHAR(100) NULL,
                installation_date DATE NULL,
                status VARCHAR(30) DEFAULT 'Pending Assessment',
                supervisor_name VARCHAR(100) NULL,
                supervisor_email VARCHAR(100) NULL,
                created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE SET NULL
            );
            """)
            cur.execute("""
            CREATE TABLE IF NOT EXISTS predictions (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                machine_id INTEGER NOT NULL,
                air_temperature FLOAT NOT NULL,
                process_temperature FLOAT NOT NULL,
                rotational_speed FLOAT NOT NULL,
                torque FLOAT NOT NULL,
                tool_wear FLOAT NOT NULL,
                load_density FLOAT NULL,
                rpm_torque_interaction FLOAT NULL,
                temperature_difference FLOAT NULL,
                temperature_ratio FLOAT NULL,
                load_stress FLOAT NULL,
                prediction VARCHAR(50) NOT NULL,
                predicted_class INTEGER DEFAULT 0,
                model_version VARCHAR(100) NULL,
                probability FLOAT NOT NULL,
                healthy_probability FLOAT NULL,
                warning_probability FLOAT NULL,
                critical_probability FLOAT NULL,
                confidence NUMERIC(5,2) NULL,
                predicted_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (machine_id) REFERENCES machines(id) ON DELETE CASCADE
            );
            """)
            cur.execute("""
            CREATE TABLE IF NOT EXISTS maintenance (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                machine_id INTEGER NOT NULL,
                prediction_id INTEGER NULL,
                priority VARCHAR(20) DEFAULT 'Medium',
                status VARCHAR(20) DEFAULT 'Pending',
                remarks TEXT NULL,
                created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (machine_id) REFERENCES machines(id) ON DELETE CASCADE,
                FOREIGN KEY (prediction_id) REFERENCES predictions(id) ON DELETE SET NULL
            );
            """)
            cur.execute("""
            CREATE TABLE IF NOT EXISTS notification_logs (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                machine_id INTEGER NOT NULL,
                recipient_email VARCHAR(150) NOT NULL,
                alert_type VARCHAR(50) NOT NULL,
                health_status VARCHAR(50) NOT NULL,
                prediction VARCHAR(255) NULL,
                delivery_status VARCHAR(50) NOT NULL,
                error_message TEXT NULL,
                sent_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (machine_id) REFERENCES machines(id) ON DELETE CASCADE
            );
            """)

            # Ensure all columns exist in machines table (schema evolution)
            machine_cols = {row[1] for row in cur.execute("PRAGMA table_info(machines)").fetchall()}
            if "user_id" not in machine_cols:
                cur.execute("ALTER TABLE machines ADD COLUMN user_id INTEGER NULL")
            if "supervisor_name" not in machine_cols:
                cur.execute("ALTER TABLE machines ADD COLUMN supervisor_name VARCHAR(100) NULL")
            if "supervisor_email" not in machine_cols:
                cur.execute("ALTER TABLE machines ADD COLUMN supervisor_email VARCHAR(100) NULL")

            conn.commit()
    finally:
        conn.close()

def seed_default_data():
    """Seeds default admin user and initial machine fleet if empty."""
    init_db()
    users_count = query_one("SELECT COUNT(*) as count FROM users")
    if not users_count or users_count['count'] == 0:
        import hashlib
        # Hash 'admin123'
        pwd_hash = hashlib.sha256("admin123".encode()).hexdigest()
        admin_id = execute_insert(
            "INSERT INTO users (company_name, admin_name, email, username, password, role) VALUES (%s, %s, %s, %s, %s, %s)",
            ("LDRP Precision Engineering", "Divya Santoki", "forldrpml456@gmail.com", "admin", pwd_hash, "Administrator")
        )
        
        # Add default CNC machines with designated supervisor emails
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
        logger.info("Default seed data loaded into database.")
