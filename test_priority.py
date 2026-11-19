from datetime import date
from priority import format_reasons, score_action

T = date(2026, 11, 19)


def test_rahul_max():
    score, label, reasons = score_action(
        date(2026, 11, 14), date(2026, 11, 14), "High", "Pending", T
    )
    assert (score, label) == (45, "High")
    assert format_reasons(reasons) == (
        "+15 5 days overdue, +10 Waiting 5 days, "
        "+10 High priority job, +10 Feedback pending"
    )


def test_low():
    score, label, reasons = score_action(
        date(2026, 11, 30), date(2026, 11, 18), "Low", "None", T
    )
    assert (score, label) == (0, "Low")
    assert format_reasons(reasons) == "No urgency factors active"


def test_label_thresholds():
    # 17 -> Low (3 days overdue=12 + Normal=5)
    assert score_action(date(2026, 11, 16), date(2026, 11, 19), "Normal", "None", T)[:2] == (17, "Low")
    # 18 -> Medium (1 day overdue=12 + waiting 3 days=6)
    assert score_action(date(2026, 11, 18), date(2026, 11, 16), "Low", "None", T)[:2] == (18, "Medium")
    # 31 -> Medium (4 days overdue=15 + waiting 3 days=6 + High=10)
    assert score_action(date(2026, 11, 15), date(2026, 11, 16), "High", "None", T)[:2] == (31, "Medium")
    # 32 -> High (1 day overdue=12 + High=10 + Pending=10)
    assert score_action(date(2026, 11, 18), date(2026, 11, 19), "High", "Pending", T)[:2] == (32, "High")


def test_due_date_bands():
    assert score_action(date(2026, 11, 19), date(2026, 11, 19), "Low", "None", T)[0] == 9   # Due today
    assert score_action(date(2026, 11, 20), date(2026, 11, 19), "Low", "None", T)[0] == 6   # Due tomorrow
    assert score_action(date(2026, 11, 21), date(2026, 11, 19), "Low", "None", T)[0] == 0   # 2+ days out


def test_accepts_sqlite_iso_strings():
    score, label, _ = score_action(
        "2026-11-18", "2026-11-14T10:15:00", "Critical", "Pending", "2026-11-19"
    )
    assert (score, label) == (42, "High")