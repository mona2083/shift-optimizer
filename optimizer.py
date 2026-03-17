from ortools.sat.python import cp_model

N_DAYS   = 7
N_SHIFTS = 3

PENALTY_SOFT_NG    = 100
PENALTY_SHIFT_PREF = 50


def run_optimizer(employees: list[dict], dept_constraints: dict, time_limit: float = 15.0) -> dict:
    model = cp_model.CpModel()
    E = len(employees)

    x = {
        (e, d, s): model.NewBoolVar(f"x_{e}_{d}_{s}")
        for e in range(E)
        for d in range(N_DAYS)
        for s in range(N_SHIFTS)
    }

    # 1. 1日に最大1シフトのみ
    for e in range(E):
        for d in range(N_DAYS):
            model.Add(sum(x[e, d, s] for s in range(N_SHIFTS)) <= 1)

    # 2. 絶対NG
    for e, emp in enumerate(employees):
        for d in emp.get("abs_ng", []):
            if 0 <= d < N_DAYS:
                for s in range(N_SHIFTS):
                    model.Add(x[e, d, s] == 0)

    # 3. 週の最低・最高勤務日数
    for e, emp in enumerate(employees):
        total = sum(x[e, d, s] for d in range(N_DAYS) for s in range(N_SHIFTS))
        model.Add(total >= emp.get("min_days", 3))
        model.Add(total <= emp.get("max_days", 6))

    # 4. 最大連続勤務日数
    for e, emp in enumerate(employees):
        max_c = dept_constraints[emp["dept"]].get("max_consecutive", 5)
        for start in range(N_DAYS - max_c):
            model.Add(
                sum(x[e, d, s]
                    for d in range(start, start + max_c + 1)
                    for s in range(N_SHIFTS)) <= max_c
            )

    # デパート別インデックス
    dept_emps     = {dept: [] for dept in dept_constraints}
    dept_managers = {dept: [] for dept in dept_constraints}
    dept_certified= {dept: [] for dept in dept_constraints}
    for e, emp in enumerate(employees):
        d = emp["dept"]
        dept_emps[d].append(e)
        if emp["role"] == "manager":
            dept_managers[d].append(e)
        if emp["role"] in ("manager", "certified"):
            dept_certified[d].append(e)

    # 5. デパート・シフト帯ごとの人数制約
    for dept_id, constr in dept_constraints.items():
        emps  = dept_emps[dept_id]
        mgrs  = dept_managers[dept_id]
        certs = dept_certified[dept_id]
        mins  = constr["min_per_shift"]
        maxs  = constr["max_per_shift"]

        for d in range(N_DAYS):
            for s in range(N_SHIFTS):
                count = sum(x[e, d, s] for e in emps)
                model.Add(count >= mins[s])
                model.Add(count <= maxs[s])

                if constr.get("need_certified_per_shift") and certs:
                    model.Add(sum(x[e, d, s] for e in certs) >= 1)

            if constr.get("need_manager_per_day") and mgrs:
                model.Add(sum(x[e, d, s] for e in mgrs for s in range(N_SHIFTS)) >= 1)

    # ソフト制約（ペナルティ最小化）
    penalty_terms = []
    for e, emp in enumerate(employees):
        for d in emp.get("soft_ng", []):
            if 0 <= d < N_DAYS:
                for s in range(N_SHIFTS):
                    penalty_terms.append(x[e, d, s] * PENALTY_SOFT_NG)

        pref = emp.get("shift_pref")
        if pref is not None:
            for d in range(N_DAYS):
                for s in range(N_SHIFTS):
                    if s != pref:
                        penalty_terms.append(x[e, d, s] * PENALTY_SHIFT_PREF)

    model.Minimize(sum(penalty_terms) if penalty_terms else 0)

    solver = cp_model.CpSolver()
    solver.parameters.max_time_in_seconds = time_limit
    status = solver.Solve(model)

    if status not in (cp_model.OPTIMAL, cp_model.FEASIBLE):
        return {"status": "no_solution"}

    # スケジュール構築
    schedule = {}
    for e in range(E):
        for d in range(N_DAYS):
            schedule[e, d] = None
            for s in range(N_SHIFTS):
                if solver.Value(x[e, d, s]) == 1:
                    schedule[e, d] = s
                    break

    # 満足度スコア計算
    satisfaction = []
    for e, emp in enumerate(employees):
        soft_ng_hit = sum(
            1 for d in emp.get("soft_ng", [])
            if 0 <= d < N_DAYS and schedule[e, d] is not None
        )
        pref      = emp.get("shift_pref")
        pref_miss = 0
        days_worked = 0
        for d in range(N_DAYS):
            s = schedule[e, d]
            if s is not None:
                days_worked += 1
                if pref is not None and s != pref:
                    pref_miss += 1

        score = max(0, 100 - soft_ng_hit * 15 - pref_miss * 8)
        satisfaction.append({
            "employee_id":      e,
            "name":             emp["name"],
            "dept":             emp["dept"],
            "score":            score,
            "days_worked":      days_worked,
            "soft_ng_violated": soft_ng_hit,
            "pref_missed":      pref_miss,
        })

    return {
        "status":       "ok",
        "schedule":     schedule,
        "satisfaction": satisfaction,
        "objective":    solver.ObjectiveValue(),
        "is_optimal":   status == cp_model.OPTIMAL,
    }
