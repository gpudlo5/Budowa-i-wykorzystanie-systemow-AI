#!/usr/bin/env python3
"""Walidacja spójności danych syntetycznych Northway (stdlib, bez zależności).

Uruchom z głównego folderu projektu:
    python data/validate_data.py
    python data/validate_data.py --data-dir data

Kod wyjścia: 0 = brak błędów (ostrzeżenia dozwolone), 1 = są błędy.
"""
from __future__ import annotations

import argparse
import csv
import json
import re
import sys
from pathlib import Path

DEFAULT_DIR = Path(__file__).resolve().parent

REQUIRED_CSV = {
    "employees.csv": ["employee_id", "first_name", "last_name", "email", "department_id",
                      "role_id", "manager_id", "hire_date", "status", "end_date", "access_group"],
    "roles.csv": ["role_id", "role_name", "department_id", "access_group"],
    "departments.csv": ["department_id", "name", "head_employee_id", "default_access_group"],
    "processes.csv": ["process_id", "name", "department_id", "system_ids"],
    "systems.csv": ["system_id", "name", "owner_department_id"],
    "projects.csv": ["project_id", "name", "owner_id", "participant_ids"],
    "access_groups.csv": ["access_group", "name"],
    "counterparties.csv": ["counterparty_id", "name", "account_owner_id", "finance_contact_id"],
}
REQUIRED_JSON = ["tickets.json", "threads.json", "recurring_tasks.json", "interview_scenario.json"]
DOC_FIELDS = ["doc_id", "title", "doc_type", "process_id", "department_id", "owner_id",
              "author_id", "created_date", "last_modified", "allowed_groups"]
DATE_RE = re.compile(r"^\d{4}-\d{2}-\d{2}")

errors: list[str] = []
warnings: list[str] = []


def err(msg: str) -> None:
    errors.append(msg)


def warn(msg: str) -> None:
    warnings.append(msg)


def read_csv(path: Path) -> list[dict]:
    with path.open(encoding="utf-8-sig", newline="") as f:
        return list(csv.DictReader(f))


def read_json(path: Path):
    with path.open(encoding="utf-8") as f:
        return json.load(f)


def split_ids(value: str) -> list[str]:
    return [x.strip() for x in (value or "").split(";") if x.strip()]


def parse_front_matter(text: str) -> dict:
    if not text.startswith("---"):
        return {}
    end = text.find("\n---", 3)
    if end == -1:
        return {}
    meta = {}
    for line in text[3:end].splitlines():
        if ":" not in line:
            continue
        k, v = line.split(":", 1)
        v = v.strip()
        if v.startswith("[") and v.endswith("]"):
            meta[k.strip()] = [x.strip() for x in v[1:-1].split(",") if x.strip()]
        else:
            meta[k.strip()] = v.strip("\"'")
    return meta


def check_unique(rows: list[dict], key: str, fname: str) -> set[str]:
    seen: set[str] = set()
    for r in rows:
        v = r[key]
        if v in seen:
            err(f"{fname}: zduplikowany {key} = {v}")
        seen.add(v)
    return seen


def check_ref(value: str, valid: set[str], where: str, allow_empty: bool = True) -> None:
    if not value:
        if not allow_empty:
            err(f"{where}: puste pole referencji")
        return
    if value not in valid:
        err(f"{where}: nieznane ID '{value}'")


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--data-dir", default=str(DEFAULT_DIR))
    data = Path(ap.parse_args().data_dir).resolve()
    print(f"Walidacja: {data}\n")

    # ---- obecność plików ----
    tables: dict[str, list[dict]] = {}
    for fname, cols in REQUIRED_CSV.items():
        p = data / fname
        if not p.exists():
            err(f"brak pliku {fname}")
            continue
        rows = read_csv(p)
        tables[fname] = rows
        if rows:
            missing = [c for c in cols if c not in rows[0]]
            if missing:
                err(f"{fname}: brak kolumn {missing}")
        else:
            err(f"{fname}: pusty plik")
    jsons = {}
    for fname in REQUIRED_JSON:
        p = data / fname
        if not p.exists():
            err(f"brak pliku {fname}")
            continue
        try:
            jsons[fname] = read_json(p)
        except json.JSONDecodeError as e:
            err(f"{fname}: niepoprawny JSON ({e})")
    docs_dir = data / "documents"
    if not docs_dir.is_dir():
        err("brak folderu documents/")
    if errors:
        return report()

    # ---- słowniki ID ----
    emp_ids = check_unique(tables["employees.csv"], "employee_id", "employees.csv")
    role_ids = check_unique(tables["roles.csv"], "role_id", "roles.csv")
    dep_ids = check_unique(tables["departments.csv"], "department_id", "departments.csv")
    proc_ids = check_unique(tables["processes.csv"], "process_id", "processes.csv")
    sys_ids = check_unique(tables["systems.csv"], "system_id", "systems.csv")
    proj_ids = check_unique(tables["projects.csv"], "project_id", "projects.csv")
    groups = check_unique(tables["access_groups.csv"], "access_group", "access_groups.csv")
    cp_ids = check_unique(tables["counterparties.csv"], "counterparty_id", "counterparties.csv")
    groups_valid = groups | {"all"}

    # ---- employees ----
    emails = set()
    for r in tables["employees.csv"]:
        w = f"employees.csv/{r['employee_id']}"
        check_ref(r["department_id"], dep_ids, w, False)
        check_ref(r["role_id"], role_ids, w, False)
        check_ref(r["manager_id"], emp_ids, w)
        check_ref(r["access_group"], groups, w, False)
        if r["email"] in emails:
            err(f"{w}: zduplikowany email {r['email']}")
        emails.add(r["email"])
        if not DATE_RE.match(r["hire_date"]):
            err(f"{w}: zła data zatrudnienia '{r['hire_date']}'")
        if r["status"] == "odchodzący" and not r["end_date"]:
            err(f"{w}: odchodzący bez end_date")
        if r["manager_id"] == r["employee_id"]:
            err(f"{w}: jest własnym przełożonym")
    if sum(1 for r in tables["employees.csv"] if r["status"] == "odchodzący") != 1:
        warn("employees.csv: oczekiwano dokładnie 1 osoby 'odchodzący' (scenariusz handover)")

    # ---- roles / departments / processes / systems / projects / counterparties ----
    for r in tables["roles.csv"]:
        w = f"roles.csv/{r['role_id']}"
        check_ref(r["department_id"], dep_ids, w, False)
        check_ref(r["access_group"], groups, w, False)
        check_ref(r.get("reports_to_role_id", ""), role_ids, w)
    for r in tables["departments.csv"]:
        w = f"departments.csv/{r['department_id']}"
        check_ref(r["head_employee_id"], emp_ids, w)
        check_ref(r["default_access_group"], groups, w, False)
    for r in tables["processes.csv"]:
        w = f"processes.csv/{r['process_id']}"
        check_ref(r["department_id"], dep_ids, w, False)
        check_ref(r.get("owner_role_id", ""), role_ids, w)
        for s in split_ids(r["system_ids"]):
            check_ref(s, sys_ids, w)
    for r in tables["systems.csv"]:
        check_ref(r["owner_department_id"], dep_ids, f"systems.csv/{r['system_id']}")
    for r in tables["projects.csv"]:
        w = f"projects.csv/{r['project_id']}"
        check_ref(r["owner_id"], emp_ids, w, False)
        for e in split_ids(r["participant_ids"]):
            check_ref(e, emp_ids, w)
    for r in tables["counterparties.csv"]:
        w = f"counterparties.csv/{r['counterparty_id']}"
        check_ref(r["account_owner_id"], emp_ids, w)
        check_ref(r["finance_contact_id"], emp_ids, w)

    # ---- dokumenty ----
    doc_meta: dict[str, dict] = {}
    for p in sorted(docs_dir.glob("D*.md")):
        text = p.read_text(encoding="utf-8")
        m = parse_front_matter(text)
        w = p.name
        if not m:
            err(f"{w}: brak front-matter")
            continue
        miss = [k for k in DOC_FIELDS if k not in m]
        if miss:
            err(f"{w}: brak pól front-matter {miss}")
            continue
        if not p.name.startswith(m["doc_id"]):
            err(f"{w}: doc_id '{m['doc_id']}' nie pasuje do nazwy pliku")
        if m["doc_id"] in doc_meta:
            err(f"{w}: zduplikowany doc_id {m['doc_id']}")
        doc_meta[m["doc_id"]] = m
        check_ref(m["process_id"], proc_ids, w)
        check_ref(m["department_id"], dep_ids, w, False)
        check_ref(m["owner_id"], emp_ids, w, False)
        check_ref(m["author_id"], emp_ids, w, False)
        for g in m["allowed_groups"] if isinstance(m["allowed_groups"], list) else [m["allowed_groups"]]:
            if g not in groups_valid:
                err(f"{w}: nieznana grupa dostępu '{g}'")
        if m["created_date"] > m["last_modified"]:
            err(f"{w}: created_date późniejsza niż last_modified")
        hire = {r["employee_id"]: r["hire_date"] for r in tables["employees.csv"]}
        if m["author_id"] in hire and m["created_date"] < hire[m["author_id"]]:
            err(f"{w}: autor {m['author_id']} zatrudniony po dacie utworzenia dokumentu")
        if len(text.split()) < 100:
            warn(f"{w}: bardzo krótki dokument ({len(text.split())} słów)")
    for did, m in doc_meta.items():
        for rel in m.get("related_docs", []) or []:
            if rel not in doc_meta:
                err(f"{did}: related_docs wskazuje nieistniejący {rel}")

    plan = data / "documents_plan.csv"
    if plan.exists():
        planned = {r["doc_id"] for r in read_csv(plan)}
        for d in sorted(planned - set(doc_meta)):
            err(f"documents_plan.csv: brak pliku dla {d}")
        for d in sorted(set(doc_meta) - planned):
            warn(f"dokument {d} nie jest w documents_plan.csv")

    # ---- tickets ----
    tickets = jsons["tickets.json"]
    tids = set()
    for t in tickets:
        w = f"tickets.json/{t['ticket_id']}"
        if t["ticket_id"] in tids:
            err(f"{w}: zduplikowany ticket_id")
        tids.add(t["ticket_id"])
        check_ref(t.get("process_id", ""), proc_ids, w)
        check_ref(t["reporter_id"], emp_ids, w, False)
        check_ref(t["assignee_id"], emp_ids, w)
        check_ref(t.get("related_project_id") or "", proj_ids, w)
        for s in t.get("related_system_ids") or []:
            check_ref(s, sys_ids, w)
        for d in t.get("related_doc_ids") or []:
            check_ref(d, set(doc_meta), w)
        if t["status"] in ("zamknięte", "rozwiązane") and not t.get("resolved_at"):
            warn(f"{w}: status '{t['status']}' bez resolved_at")
        if t.get("resolved_at") and t["resolved_at"] < t["created_at"]:
            err(f"{w}: resolved_at wcześniejsze niż created_at")

    # ---- threads ----
    for th in jsons["threads.json"]:
        w = f"threads.json/{th['thread_id']}"
        if not th["messages"]:
            err(f"{w}: wątek bez wiadomości")
        prev = ""
        for i, msg in enumerate(th["messages"]):
            check_ref(msg["author_id"], emp_ids, f"{w}/msg{i}", False)
            if prev and msg["timestamp"] < prev:
                warn(f"{w}/msg{i}: znacznik czasu wcześniejszy niż poprzedni")
            prev = msg["timestamp"]

    # ---- recurring tasks ----
    for r in jsons["recurring_tasks.json"]:
        w = f"recurring_tasks.json/{r['task_id']}"
        check_ref(r["owner_id"], emp_ids, w, False)
        for e in r.get("collaborators") or []:
            check_ref(e, emp_ids, w)
        check_ref(r.get("process_id", ""), proc_ids, w)

    # ---- scenariusz wywiadu i ukryte fakty ----
    scen = jsons["interview_scenario.json"]
    facts = scen.get("facts", [])
    if len(facts) < 5:
        warn(f"interview_scenario.json: {len(facts)} ukrytych faktów (oczekiwano 5)")
    leaver = next((r["employee_id"] for r in tables["employees.csv"] if r["status"] == "odchodzący"), None)
    if leaver and not any(t["assignee_id"] == leaver for t in tickets):
        warn(f"brak zgłoszeń przypisanych do odchodzącego {leaver}")

    print(f"Sprawdzono: {len(emp_ids)} pracowników, {len(doc_meta)} dokumentów, "
          f"{len(tickets)} zgłoszeń, {len(jsons['threads.json'])} wątków.")
    return report()


def report() -> int:
    for w in warnings:
        print(f"  [OSTRZEŻENIE] {w}")
    for e in errors:
        print(f"  [BŁĄD] {e}")
    print(f"\nBłędy: {len(errors)}, ostrzeżenia: {len(warnings)}")
    print("OK" if not errors else "NIEPOWODZENIE")
    return 1 if errors else 0


if __name__ == "__main__":
    sys.exit(main())