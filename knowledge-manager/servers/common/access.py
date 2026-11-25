"""access.py - sprawdzanie uprawnien bez bazy wektorowej (dla Handover i zasobow)."""
from .config import TICKET_THREAD_ACL
from .data import load_csv, split_ids
from .org import Org

_org = Org()


def allowed_groups(doc_id: str) -> list[str] | None:
    if not doc_id.startswith("D"):          # zgloszenia (T...) i watki
        return TICKET_THREAD_ACL
    for row in load_csv("documents_plan.csv"):
        if row["doc_id"] == doc_id:
            return split_ids(row["allowed_groups"])
    return None                              # dokument nie istnieje


def can_access(employee_id: str, doc_id: str) -> bool:
    employee = _org.get_employee(employee_id)
    groups = allowed_groups(doc_id)
    if employee is None or groups is None:
        return False
    return "all" in groups or employee["access_group"] in groups