import random

N_DAYS   = 7
N_SHIFTS = 3

SHIFT_NAMES = {
    "ja": ["朝", "昼", "夜"],
    "en": ["Morning", "Afternoon", "Night"],
}
DAY_NAMES = {
    "ja": ["月", "火", "水", "木", "金", "土", "日"],
    "en": ["Mon", "Tue", "Wed", "Thu", "Fri", "Sat", "Sun"],
}
DEPT_IDS = ["A", "B", "C"]
DEPT_NAMES = {
    "ja": {"A": "食料品", "B": "衣料品", "C": "レジ"},
    "en": {"A": "Grocery", "B": "Apparel", "C": "Cashier"},
}
DEPT_COLORS = {"A": "#2d6a4f", "B": "#1a4a7a", "C": "#7a3a1a"}
ROLE_NAMES = {
    "ja": {"manager": "MGR", "asst_manager": "AsMGR", "certified": "資格", "staff": "スタッフ"},
    "en": {"manager": "MGR", "asst_manager": "AsMGR", "certified": "Certified", "staff": "Staff"},
}
AVAIL_OPTS = {
    "ja": ["○", "△できればNG", "×絶対NG"],
    "en": ["○", "△ Prefer off", "× Must off"],
}
SHIFT_PREF_NONE = {"ja": "指定なし", "en": "No preference"}


def _role(dept: str, idx: int) -> str:
    if idx == 0:
        return "manager"
    if idx <= 2:
        return "asst_manager"
    if dept == "A" and idx <= 5:
        return "certified"
    return "staff"


def get_default_employees() -> list[dict]:
    emps = []
    configs = [("A", 12, 4, 6), ("B", 10, 4, 6), ("C", 8, 3, 5)]
    emp_id = 0
    for dept, count, min_d, max_d in configs:
        for i in range(count):
            emps.append({
                "id":         emp_id,
                "name":       f"{dept}-{i+1:02d}",
                "dept":       dept,
                "role":       _role(dept, i),
                "min_days":   min_d,
                "max_days":   max_d,
                "abs_ng":     [],
                "soft_ng":    [],
                "shift_pref": None,
            })
            emp_id += 1
    return emps


def get_default_dept_constraints() -> dict:
    return {
        "A": {
            "min_per_shift":            [2, 1, 1],
            "max_per_shift":            [3, 3, 2],
            "max_consecutive":          5,
            "need_manager_per_day":     True,
            "need_certified_per_shift": True,
        },
        "B": {
            "min_per_shift":            [2, 1, 1],
            "max_per_shift":            [2, 2, 2],
            "max_consecutive":          5,
            "need_manager_per_day":     True,
            "need_certified_per_shift": False,
        },
        "C": {
            "min_per_shift":            [1, 1, 1],
            "max_per_shift":            [2, 2, 1],
            "max_consecutive":          5,
            "need_manager_per_day":     True,
            "need_certified_per_shift": False,
        },
    }


def randomize_employee_preferences(employees: list[dict], seed: int | None = None) -> list[dict]:
    if seed is not None:
        random.seed(seed)
    result = []
    for emp in employees:
        e = dict(emp)
        all_days = list(range(7))
        n_abs = random.randint(0, 1)
        e["abs_ng"] = random.sample(all_days, n_abs)
        remain = [d for d in all_days if d not in e["abs_ng"]]
        n_soft = random.randint(0, min(2, len(remain)))
        e["soft_ng"] = random.sample(remain, n_soft)
        e["shift_pref"] = random.choice([None, None, 0, 1, 2])
        e["min_days"]   = random.randint(3, 4)
        e["max_days"]   = random.randint(5, 6)
        result.append(e)
    return result


def randomize_dept_constraints(constraints: dict, seed: int | None = None) -> dict:
    if seed is not None:
        random.seed(seed)
    result = {}
    for dept_id, c in constraints.items():
        r = dict(c)
        base_mins = c["min_per_shift"]
        base_maxs = c["max_per_shift"]
        mins = []
        maxs = []
        for i in range(N_SHIFTS):
            mn = max(0, base_mins[i] + random.choice([-1, 0, 0, 1]))
            mx = max(mn, base_maxs[i] + random.choice([-1, 0, 1]))
            mins.append(mn)
            maxs.append(mx)
        r["min_per_shift"] = mins
        r["max_per_shift"] = maxs
        r["max_consecutive"] = random.randint(4, 6)
        result[dept_id] = r
    return result


def employees_to_df(employees: list[dict], lang: str):
    import pandas as pd

    avail = AVAIL_OPTS[lang]
    pref_none = SHIFT_PREF_NONE[lang]
    shifts = SHIFT_NAMES[lang]
    rows = []
    for emp in employees:
        row = {
            "_id":        emp["id"],
            "_dept":      emp["dept"],
            "_role":      emp["role"],
            "name":       emp["name"],
            "role_label": ROLE_NAMES[lang][emp["role"]],
            "min":        emp["min_days"],
            "max":        emp["max_days"],
            "pref":       pref_none if emp["shift_pref"] is None else shifts[emp["shift_pref"]],
        }
        for d in range(7):
            if d in emp["abs_ng"]:
                row[f"d{d}"] = avail[2]
            elif d in emp["soft_ng"]:
                row[f"d{d}"] = avail[1]
            else:
                row[f"d{d}"] = avail[0]
        rows.append(row)
    return pd.DataFrame(rows)


def df_to_employees(df, employees_orig: list[dict], lang: str) -> list[dict]:
    avail = AVAIL_OPTS[lang]
    pref_none = SHIFT_PREF_NONE[lang]
    shifts = SHIFT_NAMES[lang]
    orig_map = {e["id"]: e for e in employees_orig}
    result = []
    for _, row in df.iterrows():
        eid = int(row["_id"])
        orig = orig_map[eid]
        abs_ng = [d for d in range(7) if row[f"d{d}"] == avail[2]]
        soft_ng = [d for d in range(7) if row[f"d{d}"] == avail[1]]
        pref_s = row["pref"]
        pref = None if pref_s == pref_none else shifts.index(pref_s)
        result.append({
            **orig,
            "min_days":   int(row["min"]),
            "max_days":   int(row["max"]),
            "shift_pref": pref,
            "abs_ng":     abs_ng,
            "soft_ng":    soft_ng,
        })
    return result