from ortools.sat.python import cp_model

N_DAYS   = 7
N_SHIFTS = 3

PENALTY_SOFT_NG    = 100
PENALTY_SHIFT_PREF = 50
# 【追加】人数不足1枠に対する超巨大なペナルティ（個人の希望より絶対に優先して埋めるため）
PENALTY_UNDERSTAFF = 10000 


def run_optimizer(
    employees: list[dict], 
    dept_constraints: dict, 
    time_limit: float = 15.0, 
    allow_understaffing: bool = False # 【追加】ベストエフォートモードのフラグ
) -> dict:
    model = cp_model.CpModel()
    E = len(employees)

    x = {
        (e, d, s): model.NewBoolVar(f"x_{e}_{d}_{s}")
        for e in range(E)
        for d in range(N_DAYS)
        for s in range(N_SHIFTS)
    }

    for e in range(E):
        for d in range(N_DAYS):
            model.Add(sum(x[e, d, s] for s in range(N_SHIFTS)) <= 1)

    for e, emp in enumerate(employees):
        for d in emp.get("abs_ng", []):
            if 0 <= d < N_DAYS:
                for s in range(N_SHIFTS):
                    model.Add(x[e, d, s] == 0)

    for e, emp in enumerate(employees):
        total = sum(x[e, d, s] for d in range(N_DAYS) for s in range(N_SHIFTS))
        model.Add(total >= emp.get("min_days", 3))
        model.Add(total <= emp.get("max_days", 6))

    for e, emp in enumerate(employees):
        max_c = dept_constraints[emp["dept"]].get("max_consecutive", 5)
        for start in range(N_DAYS - max_c):
            model.Add(
                sum(x[e, d, s]
                    for d in range(start, start + max_c + 1)
                    for s in range(N_SHIFTS)) <= max_c
            )

    dept_emps      = {dept: [] for dept in dept_constraints}
    dept_managers  = {dept: [] for dept in dept_constraints}
    dept_certified = {dept: [] for dept in dept_constraints}
    for e, emp in enumerate(employees):
        d = emp["dept"]
        dept_emps[d].append(e)
        if emp["role"] in ("manager", "asst_manager"):
            dept_managers[d].append(e)
        if emp["role"] in ("manager", "asst_manager", "certified"):
            dept_certified[d].append(e)

    penalty_terms = []

    for dept_id, constr in dept_constraints.items():
        emps  = dept_emps[dept_id]
        mgrs  = dept_managers[dept_id]
        certs = dept_certified[dept_id]
        mins  = constr["min_per_shift"]
        maxs  = constr["max_per_shift"]

        for d in range(N_DAYS):
            for s in range(N_SHIFTS):
                count = sum(x[e, d, s] for e in emps)
                
                # 【追加】ベストエフォートモードのロジック
                if allow_understaffing:
                    # 不足分を補うスラック変数（0 〜 必要最低人数）
                    shortage = model.NewIntVar(0, mins[s], f"shortage_{dept_id}_{d}_{s}")
                    model.Add(count + shortage >= mins[s])
                    penalty_terms.append(shortage * PENALTY_UNDERSTAFF)
                else:
                    # 従来の絶対ルール（ハード制約）
                    model.Add(count >= mins[s])
                
                model.Add(count <= maxs[s])

                if constr.get("need_certified_per_shift") and certs:
                    if allow_understaffing:
                        cert_shortage = model.NewIntVar(0, 1, f"cert_shortage_{dept_id}_{d}_{s}")
                        model.Add(sum(x[e, d, s] for e in certs) + cert_shortage >= 1)
                        penalty_terms.append(cert_shortage * PENALTY_UNDERSTAFF)
                    else:
                        model.Add(sum(x[e, d, s] for e in certs) >= 1)

            if constr.get("need_manager_per_day") and mgrs:
                if allow_understaffing:
                    mgr_shortage = model.NewIntVar(0, 1, f"mgr_shortage_{dept_id}_{d}")
                    model.Add(sum(x[e, d, s] for e in mgrs for s in range(N_SHIFTS)) + mgr_shortage >= 1)
                    penalty_terms.append(mgr_shortage * PENALTY_UNDERSTAFF)
                else:
                    model.Add(sum(x[e, d, s] for e in mgrs for s in range(N_SHIFTS)) >= 1)

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

    schedule = {}
    for e in range(E):
        for d in range(N_DAYS):
            schedule[e, d] = None
            for s in range(N_SHIFTS):
                if solver.Value(x[e, d, s]) == 1:
                    schedule[e, d] = s
                    break

    satisfaction = []
    for e, emp in enumerate(employees):
        soft_hit = sum(
            1 for d in emp.get("soft_ng", [])
            if 0 <= d < N_DAYS and schedule[e, d] is not None
        )
        pref        = emp.get("shift_pref")
        pref_miss   = 0
        days_worked = 0
        for d in range(N_DAYS):
            s = schedule[e, d]
            if s is not None:
                days_worked += 1
                if pref is not None and s != pref:
                    pref_miss += 1

        score = max(0, 100 - soft_hit * 15 - pref_miss * 8)
        satisfaction.append({
            "employee_id":      e,
            "name":             emp["name"],
            "dept":             emp["dept"],
            "score":            score,
            "days_worked":      days_worked,
            "soft_ng_violated": soft_hit,
            "pref_missed":      pref_miss,
        })

    return {
        "status":       "ok",
        "schedule":     schedule,
        "satisfaction": satisfaction,
        "objective":    solver.ObjectiveValue(),
        "is_optimal":   status == cp_model.OPTIMAL,
    }