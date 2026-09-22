"""
PredictCNC Maintenance Service — Ticket tracking, resolution, and status workflow.
"""
from typing import List, Dict, Any, Optional
from datetime import datetime
from db import query_all, query_one, execute_insert, execute_update

class MaintenanceService:
    @staticmethod
    def get_all_tickets(user_id: Optional[int] = None) -> List[Dict[str, Any]]:
        sql = """
        SELECT mt.*, m.machine_code, m.machine_name, m.department, p.prediction, p.probability
        FROM maintenance mt
        JOIN machines m ON mt.machine_id = m.id
        LEFT JOIN predictions p ON mt.prediction_id = p.id
        """
        params = []
        if user_id is not None:
            sql += " WHERE m.user_id = %s"
            params.append(user_id)
        sql += " ORDER BY mt.created_at DESC"
        return query_all(sql, tuple(params) if params else None)

    @staticmethod
    def create_ticket(
        machine_id: int,
        priority: str = "Medium",
        remarks: Optional[str] = None,
        prediction_id: Optional[int] = None
    ) -> int:
        return execute_insert(
            "INSERT INTO maintenance (machine_id, prediction_id, priority, status, remarks, created_at) VALUES (%s, %s, %s, 'Pending', %s, %s)",
            (machine_id, prediction_id, priority, remarks, datetime.now())
        )

    @staticmethod
    def update_ticket_status(ticket_id: int, status: str, remarks: Optional[str] = None) -> bool:
        sql = "UPDATE maintenance SET status = %s"
        params = [status]
        if remarks is not None:
            sql += ", remarks = %s"
            params.append(remarks)
        sql += " WHERE id = %s"
        params.append(ticket_id)
        count = execute_update(sql, tuple(params))
        return count > 0

    @staticmethod
    def delete_ticket(ticket_id: int) -> bool:
        count = execute_update("DELETE FROM maintenance WHERE id = %s", (ticket_id,))
        return count > 0
