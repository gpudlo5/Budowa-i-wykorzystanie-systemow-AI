"""
eval_interview.py - ewaluacja wywiadu przekazania obowiazkow (E003 -> E023).

1. Symuluje Anne: na pytanie wywiadu odpowiada faktem z data/interview_scenario.json
   TYLKO gdy pytanie dotyczy tematu faktu (reguly TRIGGERS). Kazdy fakt ujawnia raz.
   Na pozostale pytania odpowiada "Nie mam nic do dodania."
2. Generuje dokument przekazania (generate_handover_doc).
3. Sprawdza, ile faktow H01-H05 jest w sekcji 11 dokumentu (wywiad). Fakt zaliczony,
   gdy wystepuje co najmniej 3 z 5 slow kluczowych. Tylko sekcja 11, bo pozostale
   sekcje zawieraja dane z systemow, w ktorych czesc slow kluczowych wystepuje
   niezaleznie od wywiadu.
4. Kontrola negatywna: przebieg z samymi odpowiedziami "Nie mam nic do dodania"
   musi dac 0 z 5.

Prog: co najmniej 4 z 5. Kod wyjscia: 0 = zaliczone, 1 = nie.
Uruchomienie (z katalogu knowledge-manager): uv run servers/handover/eval_interview.py
"""

import json
import os
import re
import sys
from datetime import datetime, timezone
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(BASE_DIR))
os.environ.setdefault("KM_USER_ID", "E003")

from servers.common.config import HANDOVER_DIR, INTERVIEW_DIR, PROCESSED_DIR  # noqa: E402
from servers.common.data import load_json  # noqa: E402
from servers.handover import server as h  # noqa: E402

FROM, TO = "E003", "E023"
THRESHOLD = 4          # ile faktow z 5 musi trafic do dokumentu
MIN_KEYWORDS = 3       # ile slow kluczowych z 5 oznacza, ze fakt jest w dokumencie
STEM = 4               # porownanie po pierwszych literach (polska odmiana)
NO_ANSWER = "Nie mam nic do dodania."

# Kiedy symulowana Anna ujawnia fakt: slowa w PYTANIU (male litery, wyrazenia regularne).
# Reguly ustalone przed testem i niezmieniane pod wynik.
TRIGGERS = {
    "H01": r"aktualizac|ręcznie",                 # poprawki po zmianach w ERP
    "H02": r"zatwierdz|konsultac|zgod",           # dodatkowe zatwierdzenia
    "H03": r"ustaleni\w* z klient|płat|płac",     # nieformalne ustalenia z klientami
    "H04": r"dostęp|token|nośnik",                # dostepy i nosniki
    "H05": r"obejś|tymczasow",                    # obejscia w projektach
}


def stems(phrase: str) -> list[str]:
    return [w[:STEM] for w in re.findall(r"[\w:]+", phrase.lower())]


def keyword_found(keyword: str, text: str) -> bool:
    return all(s in text for s in stems(keyword))


def clean():
    """Usuwa wyniki poprzedniego przebiegu, zeby test byl powtarzalny."""
    for f in [*HANDOVER_DIR.glob(f"handover_{FROM}_to_{TO}*"),
              *INTERVIEW_DIR.glob(f"interview_{FROM}_to_{TO}*")]:
        f.unlink()


def run_interview(facts: list[dict], reveal: bool) -> tuple[str, dict]:
    """Przeprowadza caly wywiad i zwraca tresc dokumentu oraz pytania, ktore ujawnily fakty."""
    clean()
    h.CURRENT_USER_ID = FROM
    revealed = {}
    r = json.loads(h.interview_next_question(FROM, TO))
    while r["status"] == "in_progress":
        question = r["question"]
        answer = NO_ANSWER
        if reveal:
            for fact in facts:
                if fact["id"] not in revealed and re.search(TRIGGERS[fact["id"]], question.lower()):
                    revealed[fact["id"]] = f'{r["section"]}: {question}'
                    answer = fact["anna_answer"]
                    break
        r = json.loads(h.interview_next_question(FROM, TO, answer=answer))
    document = json.loads(h.generate_handover_doc(FROM, TO))["document"]
    return document, revealed


def interview_section(document: str) -> str:
    marker = "## 11. Informacje z wywiadu"
    if marker not in document:
        raise RuntimeError("W dokumencie brak sekcji 11 (Informacje z wywiadu).")
    return document.split(marker, 1)[1].lower()


def score(document: str, facts: list[dict]) -> list[dict]:
    text = interview_section(document)
    rows = []
    for fact in facts:
        found = [k for k in fact["verification_keywords"] if keyword_found(k, text)]
        rows.append({
            "id": fact["id"],
            "fact": fact["fact"],
            "keywords_found": found,
            "score": f"{len(found)}/{len(fact['verification_keywords'])}",
            "passed": len(found) >= MIN_KEYWORDS,
        })
    return rows


def main():
    facts = load_json("interview_scenario.json")["facts"]

    # Najpierw kontrola negatywna, potem wlasciwy przebieg
    # (na dysku zostaje dokument z wlasciwego przebiegu).
    control_doc, _ = run_interview(facts, reveal=False)
    control_passed = sum(r["passed"] for r in score(control_doc, facts))

    document, revealed = run_interview(facts, reveal=True)
    rows = score(document, facts)
    for row in rows:
        row["asked_by"] = revealed.get(row["id"], "BRAK PYTANIA")
    passed = sum(r["passed"] for r in rows)
    ok = passed >= THRESHOLD and control_passed == 0

    print(f"\nEwaluacja wywiadu {FROM} -> {TO}\n")
    for row in rows:
        mark = "OK " if row["passed"] else "NIE"
        print(f"[{mark}] {row['id']} {row['score']:>4}  pytanie: {row['asked_by']}")
    print(f"\nWynik: {passed}/{len(facts)} (prog {THRESHOLD}/{len(facts)})")
    print(f"Kontrola negatywna: {control_passed}/{len(facts)} (oczekiwane 0)")
    print("ZALICZONE" if ok else "NIEZALICZONE")

    out = PROCESSED_DIR / "interview_eval_results.json"
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps({
        "run_at": datetime.now(timezone.utc).isoformat(),
        "from": FROM, "to": TO,
        "threshold": THRESHOLD, "min_keywords": MIN_KEYWORDS, "stem": STEM,
        "passed": passed, "total": len(facts),
        "negative_control_passed": control_passed,
        "result": "pass" if ok else "fail",
        "facts": rows,
    }, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"Wyniki zapisane: {out.relative_to(BASE_DIR)}")

    sys.exit(0 if ok else 1)


if __name__ == "__main__":
    main()