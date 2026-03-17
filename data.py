import random

N_DAYS   = 7
N_SHIFTS = 3  # 0=朝, 1=昼, 2=夜

SHIFT_NAMES_JA = ["朝", "昼", "夜"]
DAY_NAMES_JA   = ["月", "火", "水", "木", "金", "土", "日"]
DEPT_IDS       = ["A", "B", "C"]
DEPT_NAMES_JA  = {"A": "食料品", "B": "衣料品", "C": "レジ"}
DEPT_COLORS    = {"A": "#2d6a4f", "B": "#1a4a7a", "C": "#7a3a1a"}
ROLE_NAMES_JA  = {"manager": "マネージャー", "certified": "資格保持者", "staff": "スタッフ"}

_NAMES_A = ["田中A","田中B","田中C","田中D","田中E","田中F","田中G","田中H","田中I","田中J","田中K","田中L"]
_NAMES_B = ["鈴木A","鈴木B","鈴木C","鈴木D","鈴木E","鈴木F","鈴木G","鈴木H","鈴木I","鈴木J"]
_NAMES_C = ["佐藤A","佐藤B","佐藤C","佐藤D","佐藤E","佐藤F","佐藤G","佐藤H"]


def _role(idx_in_dept: int) -> str:
    if idx_in_dept == 0:
        return "manager"
    if idx_in_dept <= 2:
        return "certified"
    return "staff"


def get_default_employees() -> list[dict]:
    emps = []
    configs = [
        (_NAMES_A, "A", 4, 6),
        (_NAMES_B, "B", 4, 6),
        (_NAMES_C, "C", 3, 5),
    ]
    emp_id = 0
    for names, dept, min_d, max_d in configs:
        for i, name in enumerate(names):
            emps.append({
                "id":         emp_id,
                "name":       name,
                "dept":       dept,
                "role":       _role(i),
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
            "min_per_shift":            [2, 2, 1],
            "max_per_shift":            [5, 5, 3],
            "max_consecutive":          5,
            "need_manager_per_day":     True,
            "need_certified_per_shift": True,
        },
        "B": {
            "min_per_shift":            [2, 2, 1],
            "max_per_shift":            [4, 4, 3],
            "max_consecutive":          5,
            "need_manager_per_day":     True,
            "need_certified_per_shift": True,
        },
        "C": {
            "min_per_shift":            [1, 1, 1],
            "max_per_shift":            [3, 3, 2],
            "max_consecutive":          5,
            "need_manager_per_day":     True,
            "need_certified_per_shift": True,
        },
    }


def randomize_employee_preferences(employees: list[dict], seed: int | None = None) -> list[dict]:
    if seed is not None:
        random.seed(seed)
    result = []
    for emp in employees:
        e = dict(emp)
        all_days = list(range(7))
        n_abs    = random.randint(0, 1)
        e["abs_ng"]     = random.sample(all_days, n_abs)
        remain          = [d for d in all_days if d not in e["abs_ng"]]
        n_soft          = random.randint(0, min(2, len(remain)))
        e["soft_ng"]    = random.sample(remain, n_soft)
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
        r    = dict(c)
        mins = [random.randint(1, 2), random.randint(1, 2), random.randint(1, 1)]
        maxs = [mins[0] + random.randint(1, 3), mins[1] + random.randint(1, 3), mins[2] + random.randint(1, 2)]
        r["min_per_shift"]   = mins
        r["max_per_shift"]   = maxs
        r["max_consecutive"] = random.randint(4, 6)
        result[dept_id]      = r
    return result
