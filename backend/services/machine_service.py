"""
PredictCNC Machine Service — Machine Fleet CRUD operations and supervisor management.
"""
from typing import List, Dict, Any, Optional
from datetime import datetime
from db import query_all, query_one, execute_insert, execute_update

class MachineService:
    @staticmethod
    def get_all_machines(user_id: Optional[int] = None) -> List[Dict[str, Any]]:
        """Retrieves machines strictly scoped to the user account."""
        if user_id is not None:
            return query_all("SELECT * FROM machines WHERE user_id = %s ORDER BY id ASC", (user_id,))
        return query_all("SELECT * FROM machines ORDER BY id ASC")

    @staticmethod
    def get_machine_by_id(machine_id: int, user_id: Optional[int] = None) -> Optional[Dict[str, Any]]:
        """Retrieves a single machine, optionally verified against owner user_id."""
        if user_id is not None:
            return query_one("SELECT * FROM machines WHERE id = %s AND user_id = %s", (machine_id, user_id))
        return query_one("SELECT * FROM machines WHERE id = %s", (machine_id,))

    @staticmethod
    def create_machine(
        user_id: Optional[int],
        machine_code: str,
        machine_name: str,
        department: Optional[str] = None,
        manufacturer: Optional[str] = None,
        installation_date: Optional[str] = None,
        supervisor_name: Optional[str] = None,
        supervisor_email: Optional[str] = None
    ) -> int:
        code = (machine_code or "").strip()
        name = (machine_name or "").strip()
        if not code:
            raise ValueError("Asset code / identifier is required.")
        if not name:
            raise ValueError("Machine model / description is required.")

        # Check if asset code already exists within this user's fleet
        if user_id is not None:
            existing = query_one(
                "SELECT id FROM machines WHERE user_id = %s AND LOWER(machine_code) = LOWER(%s)",
                (user_id, code)
            )
        else:
            existing = query_one(
                "SELECT id FROM machines WHERE LOWER(machine_code) = LOWER(%s)",
                (code,)
            )

        if existing:
            raise ValueError(f"Asset code '{code}' already exists in your fleet. Please specify a unique machine identifier.")

        try:
            return execute_insert(
                """INSERT INTO machines (
                    user_id, machine_code, machine_name, department, manufacturer,
                    installation_date, status, supervisor_name, supervisor_email, created_at
                ) VALUES (%s, %s, %s, %s, %s, %s, 'Pending Assessment', %s, %s, %s)""",
                (user_id, code, name, department, manufacturer, installation_date, supervisor_name, supervisor_email, datetime.now())
            )
        except Exception as e:
            err_msg = str(e).lower()
            if "duplicate key" in err_msg or "unique constraint" in err_msg or "unique constraint failed" in err_msg or "duplicate entry" in err_msg:
                raise ValueError(f"Asset code '{code}' already exists in your fleet. Please specify a unique machine identifier.")
            raise

    @staticmethod
    def update_machine(
        machine_id: int,
        machine_name: str,
        department: Optional[str] = None,
        manufacturer: Optional[str] = None,
        installation_date: Optional[str] = None,
        status: Optional[str] = None,
        supervisor_name: Optional[str] = None,
        supervisor_email: Optional[str] = None,
        user_id: Optional[int] = None
    ) -> bool:
        """Updates machine parameters, ensuring tenant isolation when user_id is specified."""
        sql = """UPDATE machines SET 
            machine_name = %s, department = %s, manufacturer = %s, 
            installation_date = %s, supervisor_name = %s, supervisor_email = %s"""
        params = [machine_name.strip(), department, manufacturer, installation_date, supervisor_name, supervisor_email]
        if status:
            sql += ", status = %s"
            params.append(status)
        sql += " WHERE id = %s"
        params.append(machine_id)
        if user_id is not None:
            sql += " AND user_id = %s"
            params.append(user_id)
        count = execute_update(sql, tuple(params))
        return count > 0

    @staticmethod
    def delete_machine(machine_id: int, user_id: Optional[int] = None) -> bool:
        """Deletes machine asset, ensuring tenant isolation when user_id is specified."""
        if user_id is not None:
            count = execute_update("DELETE FROM machines WHERE id = %s AND user_id = %s", (machine_id, user_id))
        else:
            count = execute_update("DELETE FROM machines WHERE id = %s", (machine_id,))
        return count > 0

