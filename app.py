import streamlit as st
import pandas as pd
import plotly.express as px

from data import (
    get_default_employees, get_default_dept_constraints,
    randomize_employee_preferences, randomize_dept_constraints,
    SHIFT_NAMES_JA, DAY_NAMES_JA, DEPT_IDS, DEPT_NAMES_JA, DEPT_COLORS,
    ROLE_NAMES_JA, N_DAYS, N_SHIFTS,
)
from optimizer import run_optimizer

st.set_page_config(page_title="シフトオプティマイザー", layout="wide")
st.title("🗓️ シフト最適化システム")
st.caption("OR-Tools CP-SAT による自動シフト作成 ｜ 30名 / 3デパートメント / 週次")

if "employees" not in st.session_state:
    st.session_state.employees = get_default_employees()
if "dept_constraints" not in st.session_state:
    st.session_state.dept_constraints = get_default_dept_constraints()
if "result" not in st.session_state:
    st.session_state.result = None


# ── Step 1: 従業員シフト希望 ──────────────────────────────────────
st.header("Step 1: 従業員シフト希望")

c1, c2, _ = st.columns([1, 1, 5])
with c1:
    if st.button("🎲 ランダム設定", key="rand_emp"):
        st.session_state.employees = randomize_employee_preferences(get_default_employees())
        st.rerun()
with c2:
    if st.button("🔄 リセット", key="reset_emp"):
        st.session_state.employees = get_default_employees()
        st.rerun()

dept_tabs = st.tabs([f"{DEPT_NAMES_JA[d]}（{d}）" for d in DEPT_IDS])
for tab, dept_id in zip(dept_tabs, DEPT_IDS):
    with tab:
        dept_emps = [e for e in st.session_state.employees if e["dept"] == dept_id]
        for emp in dept_emps:
            eid = emp["id"]
            with st.expander(f"{emp['name']}　｜　{ROLE_NAMES_JA[emp['role']]}"):
                cols = st.columns([1, 1, 1, 2, 2])
                with cols[0]:
                    mn = st.number_input("最低勤務日", 0, 7, emp["min_days"], step=1, key=f"mn_{eid}")
                with cols[1]:
                    mx = st.number_input("最高勤務日", 0, 7, emp["max_days"], step=1, key=f"mx_{eid}")
                with cols[2]:
                    p_options = ["指定なし", "朝", "昼", "夜"]
                    p_idx     = 0 if emp["shift_pref"] is None else emp["shift_pref"] + 1
                    p_sel     = st.selectbox("シフト希望", p_options, index=p_idx, key=f"pref_{eid}")
                with cols[3]:
                    abs_ng = st.multiselect(
                        "絶対NG", list(range(7)), default=emp["abs_ng"],
                        format_func=lambda d: DAY_NAMES_JA[d], key=f"absng_{eid}",
                    )
                with cols[4]:
                    remain  = [d for d in range(7) if d not in abs_ng]
                    soft_ng = st.multiselect(
                        "できればNG", remain,
                        default=[d for d in emp["soft_ng"] if d in remain],
                        format_func=lambda d: DAY_NAMES_JA[d], key=f"softng_{eid}",
                    )

                idx = next(i for i, e in enumerate(st.session_state.employees) if e["id"] == eid)
                st.session_state.employees[idx].update({
                    "min_days":   mn,
                    "max_days":   mx,
                    "shift_pref": None if p_sel == "指定なし" else ["朝", "昼", "夜"].index(p_sel),
                    "abs_ng":     abs_ng,
                    "soft_ng":    soft_ng,
                })

st.divider()


# ── Step 2: デパートメント制約 ────────────────────────────────────
st.header("Step 2: デパートメント制約")

c3, c4, _ = st.columns([1, 1, 5])
with c3:
    if st.button("🎲 ランダム設定", key="rand_dept"):
        st.session_state.dept_constraints = randomize_dept_constraints(get_default_dept_constraints())
        st.rerun()
with c4:
    if st.button("🔄 リセット", key="reset_dept"):
        st.session_state.dept_constraints = get_default_dept_constraints()
        st.rerun()

for dept_id in DEPT_IDS:
    c = st.session_state.dept_constraints[dept_id]
    with st.expander(f"**{DEPT_NAMES_JA[dept_id]}（{dept_id}）**", expanded=True):
        shift_cols = st.columns(4)
        new_mins, new_maxs = [], []
        for si, sname in enumerate(SHIFT_NAMES_JA):
            with shift_cols[si]:
                st.caption(f"{sname}シフト")
                mn = st.number_input("最低人数", 0, 10, c["min_per_shift"][si], step=1, key=f"dmin_{dept_id}_{si}")
                mx = st.number_input("最高人数", 0, 10, c["max_per_shift"][si], step=1, key=f"dmax_{dept_id}_{si}")
                new_mins.append(mn)
                new_maxs.append(mx)
        with shift_cols[3]:
            st.caption("連続勤務")
            max_c = st.number_input("最大連続日", 1, 7, c["max_consecutive"], step=1, key=f"maxc_{dept_id}")

        chk1, chk2 = st.columns(2)
        need_mgr  = chk1.checkbox("1日1名以上マネージャー必須", c.get("need_manager_per_day", True),     key=f"mgr_{dept_id}")
        need_cert = chk2.checkbox("各シフト1名以上資格保持者必須", c.get("need_certified_per_shift", True), key=f"cert_{dept_id}")

        st.session_state.dept_constraints[dept_id].update({
            "min_per_shift":            new_mins,
            "max_per_shift":            new_maxs,
            "max_consecutive":          max_c,
            "need_manager_per_day":     need_mgr,
            "need_certified_per_shift": need_cert,
        })

st.divider()


# ── 最適化実行 ────────────────────────────────────────────────────
if st.button("🚀 シフトを最適化する", type="primary", use_container_width=True):
    with st.spinner("最適化中... (最大15秒)"):
        st.session_state.result = run_optimizer(
            st.session_state.employees,
            st.session_state.dept_constraints,
        )

result = st.session_state.result
if result is None:
    st.stop()

if result["status"] == "no_solution":
    st.error("❌ 条件を満たすシフトが見つかりませんでした。制約を緩めてください。")
    st.stop()

label = "✅ 最適解が見つかりました" if result.get("is_optimal") else "✅ 実行可能解が見つかりました（時間制限内）"
st.success(label)

schedule  = result["schedule"]
employees = st.session_state.employees

SHIFT_LABELS = {0: "朝", 1: "昼", 2: "夜", None: "休"}


def _style_shift(val: str) -> str:
    if val == "朝": return "background-color:#d4edda;font-weight:500"
    if val == "昼": return "background-color:#d1ecf1;font-weight:500"
    if val == "夜": return "background-color:#e2d9f3;font-weight:500"
    return "color:#bbb"


# ── シフト表 ──────────────────────────────────────────────────────
st.header("📋 シフト表")

for dept_id in DEPT_IDS:
    st.subheader(f"{DEPT_NAMES_JA[dept_id]}（{dept_id}）")
    dept_emps = [e for e in employees if e["dept"] == dept_id]
    rows = []
    for emp in dept_emps:
        row = {"名前": emp["name"], "役割": ROLE_NAMES_JA[emp["role"]]}
        for d in range(N_DAYS):
            row[DAY_NAMES_JA[d]] = SHIFT_LABELS[schedule[emp["id"], d]]
        row["勤務日数"] = sum(1 for d in range(N_DAYS) if schedule[emp["id"], d] is not None)
        rows.append(row)
    df = pd.DataFrame(rows)
    st.dataframe(
        df.style.applymap(_style_shift, subset=DAY_NAMES_JA),
        use_container_width=True,
        hide_index=True,
    )


# ── 配置人数サマリー ──────────────────────────────────────────────
st.header("📊 各デパートメント配置人数サマリー")

for dept_id in DEPT_IDS:
    dept_emps = [e for e in employees if e["dept"] == dept_id]
    constr    = st.session_state.dept_constraints[dept_id]
    st.caption(f"**{DEPT_NAMES_JA[dept_id]}**")
    rows = []
    for s, sname in enumerate(SHIFT_NAMES_JA):
        row = {"シフト帯": sname}
        ok  = True
        for d in range(N_DAYS):
            count = sum(1 for emp in dept_emps if schedule[emp["id"], d] == s)
            mn    = constr["min_per_shift"][s]
            flag  = "" if count >= mn else " ⚠️"
            row[DAY_NAMES_JA[d]] = f"{count}人{flag}"
            if flag:
                ok = False
        row["状態"] = "✅" if ok else "⚠️ 制約未達"
        rows.append(row)
    st.dataframe(pd.DataFrame(rows), use_container_width=True, hide_index=True)


# ── 満足度 ───────────────────────────────────────────────────────
st.header("😊 従業員満足度")

sat = result["satisfaction"]
avg = sum(s["score"] for s in sat) / len(sat)

m1, m2, m3 = st.columns(3)
m1.metric("平均満足度",       f"{avg:.1f} / 100")
m2.metric("100点（完全満足）", f"{sum(1 for s in sat if s['score'] == 100)} 人")
m3.metric("要確認（70点未満）",f"{sum(1 for s in sat if s['score'] < 70)} 人")

sat_df = pd.DataFrame(sat)
sat_df["デパートメント"] = sat_df["dept"].map(DEPT_NAMES_JA)

fig = px.bar(
    sat_df.sort_values("score"),
    x="score",
    y="name",
    color="デパートメント",
    color_discrete_map={v: DEPT_COLORS[k] for k, v in DEPT_NAMES_JA.items()},
    orientation="h",
    title="従業員別満足度スコア",
    labels={"score": "満足度スコア", "name": ""},
    hover_data={"soft_ng_violated": True, "pref_missed": True, "days_worked": True},
)
fig.add_vline(x=70, line_dash="dash", line_color="red", annotation_text="70点ライン")
fig.update_layout(height=700, xaxis_range=[0, 100], yaxis={"categoryorder": "total ascending"})
st.plotly_chart(fig, use_container_width=True)

# デパートメント別集計
st.subheader("デパートメント別サマリー")
dept_rows = []
for dept_id in DEPT_IDS:
    ds = [s for s in sat if s["dept"] == dept_id]
    dept_rows.append({
        "デパートメント":           f"{DEPT_NAMES_JA[dept_id]}（{dept_id}）",
        "人数":                     len(ds),
        "平均満足度":               f"{sum(s['score'] for s in ds) / len(ds):.1f}",
        "soft NG 違反合計":         sum(s["soft_ng_violated"] for s in ds),
        "シフト希望未達合計":       sum(s["pref_missed"] for s in ds),
        "平均勤務日数":             f"{sum(s['days_worked'] for s in ds) / len(ds):.1f}",
    })
st.dataframe(pd.DataFrame(dept_rows), use_container_width=True, hide_index=True)
