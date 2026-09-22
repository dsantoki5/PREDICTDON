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
    def get_machine_by_id(machine_id: int) -> Optional[Dict[str, Any]]:
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
        return execute_insert(
            """INSERT INTO machines (
                user_id, machine_code, machine_name, department, manufacturer,
                installation_date, status, supervisor_name, supervisor_email, created_at
            ) VALUES (%s, %s, %s, %s, %s, %s, 'Healthy', %s, %s, %s)""",
            (user_id, machine_code.strip(), machine_name.strip(), department, manufacturer, installation_date, supervisor_name, supervisor_email, datetime.now())
        )

    @staticmethod
    def update_machine(
        machine_id: int,
        machine_name: str,
        department: Optional[str] = None,
        manufacturer: Optional[str] = None,
        installation_date: Optional[str] = None,
        status: Optional[str] = None,
        supervisor_name: Optional[str] = None,
        supervisor_email: Optional[str] = None
    ) -> bool:
        sql = """UPDATE machines SET 
            machine_name = %s, department = %s, manufacturer = %s, 
            installation_date = %s, supervisor_name = %s, supervisor_email = %s"""
        params = [machine_name.strip(), department, manufacturer, installation_date, supervisor_name, supervisor_email]
        if status:
            sql += ", status = %s"
            params.append(status)
        sql += " WHERE id = %s"
        params.append(machine_id)
        count = execute_update(sql, tuple(params))
        return count > 0

    @staticmethod
    def delete_machine(machine_id: int) -> bool:
        count = execute_update("DELETE FROM machines WHERE id = %s", (machine_id,))
        return count > 0
