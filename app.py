import streamlit as st
import pandas as pd
import plotly.express as px

from data import (
    get_default_employees, get_default_dept_constraints,
    randomize_employee_preferences, randomize_dept_constraints,
    employees_to_df, df_to_employees,
    SHIFT_NAMES, DAY_NAMES, DEPT_IDS, DEPT_NAMES, DEPT_COLORS,
    ROLE_NAMES, AVAIL_OPTS, SHIFT_PREF_NONE, N_DAYS, N_SHIFTS,
)
from optimizer import run_optimizer

st.set_page_config(page_title="Shift Optimizer", layout="wide")

PORTFOLIO_URL = "https://mona2083.github.io/portfolio-2026/index.html"

LANG = {
    "ja": {
        "title":        "🗓️ シフト最適化システム",
        "caption":      "OR-Tools CP-SAT による自動シフト作成 ｜ 30名 / 3デパートメント / 週次",
        "portfolio_btn":"🔗 ポートフォリオを見る",
        "portfolio_label":"ポートフォリオ",
        "step1":        "Step 1: 従業員シフト希望",
        "step2":        "Step 2: デパートメント制約",
        "run":          "🚀 シフトを最適化する",
        "random":       "🎲 ランダム設定",
        "reset":        "🔄 リセット",
        "col_name":     "名前",
        "col_role":     "役割",
        "col_min":      "最低日",
        "col_max":      "最高日",
        "col_pref":     "希望シフト",
        "dept_morning": "朝",
        "dept_noon":    "昼",
        "dept_night":   "夜",
        "dept_min":     "最低人数",
        "dept_max":     "最高人数",
        "dept_maxc":    "最大連続日",
        "need_mgr":     "マネージャー必須（1日1名）",
        "need_cert":    "資格保持者必須（各シフト）",
        "optimizing":   "最適化中... (最大15秒)",
        "result_ok":    "✅ 最適解が見つかりました",
        "result_feas":  "✅ 実行可能解が見つかりました（時間制限内）",
        "result_none":  "❌ 条件を満たすシフトが見つかりませんでした。制約を緩めてください。",
        "shift_table":  "📋 シフト表",
        "headcount":    "📊 配置人数サマリー",
        "shift_col":    "シフト帯",
        "status_col":   "状態",
        "ok_status":    "✅",
        "warn_status":  "⚠️ 制約未達",
        "satisfaction": "😊 従業員満足度",
        "avg_score":    "平均満足度",
        "perfect":      "100点（完全満足）",
        "low_score":    "要確認（70点未満）",
        "dept_summary": "デパートメント別サマリー",
        "dept_col":     "デパートメント",
        "people_col":   "人数",
        "avg_sat":      "平均満足度",
        "soft_viol":    "soft NG 違反合計",
        "pref_miss":    "シフト希望未達合計",
        "avg_days":     "平均勤務日数",
        "shift_rest":   "休",
        "days_worked":  "勤務日数",
    },
    "en": {
        "title":        "🗓️ Shift Optimizer",
        "caption":      "Automated scheduling with OR-Tools CP-SAT ｜ 30 staff / 3 departments / weekly",
        "portfolio_btn":"🔗 View Portfolio",
        "portfolio_label":"Portfolio",
        "step1":        "Step 1: Employee Shift Preferences",
        "step2":        "Step 2: Department Constraints",
        "run":          "🚀 Optimize Shifts",
        "random":       "🎲 Randomize",
        "reset":        "🔄 Reset",
        "col_name":     "Name",
        "col_role":     "Role",
        "col_min":      "Min Days",
        "col_max":      "Max Days",
        "col_pref":     "Shift Pref",
        "dept_morning": "Morning",
        "dept_noon":    "Afternoon",
        "dept_night":   "Night",
        "dept_min":     "Min Staff",
        "dept_max":     "Max Staff",
        "dept_maxc":    "Max Consecutive",
        "need_mgr":     "Manager required (1/day)",
        "need_cert":    "Certified required (per shift)",
        "optimizing":   "Optimizing... (up to 15 seconds)",
        "result_ok":    "✅ Optimal solution found",
        "result_feas":  "✅ Feasible solution found (within time limit)",
        "result_none":  "❌ No valid schedule found. Please relax constraints.",
        "shift_table":  "📋 Shift Schedule",
        "headcount":    "📊 Headcount Summary",
        "shift_col":    "Shift",
        "status_col":   "Status",
        "ok_status":    "✅",
        "warn_status":  "⚠️ Below minimum",
        "satisfaction": "😊 Employee Satisfaction",
        "avg_score":    "Average Satisfaction",
        "perfect":      "Perfect (100pts)",
        "low_score":    "Needs Review (<70pts)",
        "dept_summary": "Department Summary",
        "dept_col":     "Department",
        "people_col":   "Staff",
        "avg_sat":      "Avg Satisfaction",
        "soft_viol":    "Soft NG violations",
        "pref_miss":    "Pref mismatches",
        "avg_days":     "Avg days worked",
        "shift_rest":   "Off",
        "days_worked":  "Days worked",
    },
}

def init_session_state() -> None:
    if "employees" not in st.session_state:
        st.session_state.employees = get_default_employees()
    if "dept_constraints" not in st.session_state:
        st.session_state.dept_constraints = get_default_dept_constraints()
    if "result" not in st.session_state:
        st.session_state.result = None
    if "edit_key" not in st.session_state:
        st.session_state.edit_key = 0
    if "dept_edit_key" not in st.session_state:
        st.session_state.dept_edit_key = 0


def render_sidebar() -> tuple[str, dict]:
    with st.sidebar:
        lang_choice = st.radio("🌐 Language / 言語", ["日本語", "English"], horizontal=True)
        lang = "ja" if lang_choice == "日本語" else "en"
        T = LANG[lang]
        st.link_button(T["portfolio_btn"], PORTFOLIO_URL, use_container_width=True)
        st.divider()
    return lang, T


def render_header(T: dict) -> None:
    head_l, head_r = st.columns([0.78, 0.22], vertical_alignment="center")
    with head_l:
        st.title(T["title"])
        st.caption(T["caption"])
    with head_r:
        st.link_button(T["portfolio_label"], PORTFOLIO_URL, use_container_width=True)


init_session_state()
lang, T = render_sidebar()
render_header(T)


def render_step1_employee_preferences() -> None:
    st.header(T["step1"])

    c1, c2, _ = st.columns([1, 1, 6])
    with c1:
        if st.button(T["random"], key="rand_emp"):
            st.session_state.employees = randomize_employee_preferences(get_default_employees())
            st.session_state.edit_key += 1
            st.rerun()
    with c2:
        if st.button(T["reset"], key="reset_emp"):
            st.session_state.employees = get_default_employees()
            st.session_state.edit_key += 1
            st.rerun()

    dept_tabs = st.tabs([f"{DEPT_NAMES[lang][d]}" for d in DEPT_IDS])
    for tab, dept_id in zip(dept_tabs, DEPT_IDS):
        with tab:
            dept_emps_orig = [e for e in st.session_state.employees if e["dept"] == dept_id]
            df = employees_to_df(dept_emps_orig, lang)

            avail_opts = AVAIL_OPTS[lang]
            shift_opts = [SHIFT_PREF_NONE[lang]] + SHIFT_NAMES[lang]
            day_names = DAY_NAMES[lang]

            column_config = {
                "_id": None,
                "_dept": None,
                "_role": None,
                "name": st.column_config.TextColumn(T["col_name"], disabled=True, width="small"),
                "role_label": st.column_config.TextColumn(T["col_role"], disabled=True, width="small"),
                "min": st.column_config.NumberColumn(T["col_min"], min_value=0, max_value=7, width="small"),
                "max": st.column_config.NumberColumn(T["col_max"], min_value=0, max_value=7, width="small"),
                "pref": st.column_config.SelectboxColumn(T["col_pref"], options=shift_opts, width="small"),
                **{
                    f"d{d}": st.column_config.SelectboxColumn(day_names[d], options=avail_opts, width="small")
                    for d in range(7)
                },
            }

            edited_df = st.data_editor(
                df,
                column_config=column_config,
                key=f"editor_{dept_id}_{st.session_state.edit_key}",
                hide_index=True,
                use_container_width=True,
            )

            new_emps = df_to_employees(edited_df, dept_emps_orig, lang)
            for new_emp in new_emps:
                idx = next(i for i, e in enumerate(st.session_state.employees) if e["id"] == new_emp["id"])
                st.session_state.employees[idx] = new_emp

    st.divider()


def render_step2_department_constraints() -> None:
    st.header(T["step2"])

    c3, c4, _ = st.columns([1, 1, 6])
    with c3:
        if st.button(T["random"], key="rand_dept"):
            st.session_state.dept_constraints = randomize_dept_constraints(get_default_dept_constraints())
            st.session_state.dept_edit_key += 1
            st.rerun()
    with c4:
        if st.button(T["reset"], key="reset_dept"):
            st.session_state.dept_constraints = get_default_dept_constraints()
            st.session_state.dept_edit_key += 1
            st.rerun()

    dept_tabs2 = st.tabs([DEPT_NAMES[lang][d] for d in DEPT_IDS])
    for tab, dept_id in zip(dept_tabs2, DEPT_IDS):
        with tab:
            c = st.session_state.dept_constraints[dept_id]
            shift_labels = [T["dept_morning"], T["dept_noon"], T["dept_night"]]
            new_mins, new_maxs = [], []
            for si, slabel in enumerate(shift_labels):
                st.caption(slabel)
                cc1, cc2 = st.columns(2)
                mn = cc1.number_input(
                    T["dept_min"], 0, 10, c["min_per_shift"][si], step=1,
                    key=f"dmin_{dept_id}_{si}_{st.session_state.dept_edit_key}"
                )
                mx = cc2.number_input(
                    T["dept_max"], 0, 10, c["max_per_shift"][si], step=1,
                    key=f"dmax_{dept_id}_{si}_{st.session_state.dept_edit_key}"
                )
                new_mins.append(mn)
                new_maxs.append(mx)

            max_c = st.number_input(
                T["dept_maxc"], 1, 7, c["max_consecutive"], step=1,
                key=f"maxc_{dept_id}_{st.session_state.dept_edit_key}"
            )
            need_mgr = st.checkbox(
                T["need_mgr"], c.get("need_manager_per_day", True),
                key=f"mgr_{dept_id}_{st.session_state.dept_edit_key}"
            )
            need_cert = st.checkbox(
                T["need_cert"], c.get("need_certified_per_shift", False),
                key=f"cert_{dept_id}_{st.session_state.dept_edit_key}"
            )

            st.session_state.dept_constraints[dept_id].update({
                "min_per_shift": new_mins,
                "max_per_shift": new_maxs,
                "max_consecutive": max_c,
                "need_manager_per_day": need_mgr,
                "need_certified_per_shift": need_cert,
            })

    st.divider()


render_step1_employee_preferences()
render_step2_department_constraints()

if st.button(T["run"], type="primary", use_container_width=True):
    with st.spinner(T["optimizing"]):
        st.session_state.result = run_optimizer(
            st.session_state.employees,
            st.session_state.dept_constraints,
        )

result = st.session_state.result
if result is None:
    st.stop()

if result["status"] == "no_solution":
    st.error(T["result_none"])
    st.stop()

st.success(T["result_ok"] if result.get("is_optimal") else T["result_feas"])

schedule  = result["schedule"]
employees = st.session_state.employees


def _shift_label(s, lang):
    if s is None: return T["shift_rest"]
    return SHIFT_NAMES[lang][s]


def _style_shift(val):
    mapping = {
        SHIFT_NAMES["ja"][0]: "background-color:#d4edda;font-weight:500",
        SHIFT_NAMES["ja"][1]: "background-color:#d1ecf1;font-weight:500",
        SHIFT_NAMES["ja"][2]: "background-color:#e2d9f3;font-weight:500",
        SHIFT_NAMES["en"][0]: "background-color:#d4edda;font-weight:500",
        SHIFT_NAMES["en"][1]: "background-color:#d1ecf1;font-weight:500",
        SHIFT_NAMES["en"][2]: "background-color:#e2d9f3;font-weight:500",
    }
    return mapping.get(val, "color:#bbb")


def render_shift_table(schedule: dict, employees: list[dict]) -> None:
    st.header(T["shift_table"])

    day_names = DAY_NAMES[lang]
    result_tabs = st.tabs([DEPT_NAMES[lang][d] for d in DEPT_IDS])
    for tab, dept_id in zip(result_tabs, DEPT_IDS):
        with tab:
            dept_emps = [e for e in employees if e["dept"] == dept_id]
            constr = st.session_state.dept_constraints[dept_id]

            rows = []
            for emp in dept_emps:
                row = {T["col_name"]: emp["name"], T["col_role"]: ROLE_NAMES[lang][emp["role"]]}
                for d in range(N_DAYS):
                    row[day_names[d]] = _shift_label(schedule[emp["id"], d], lang)
                row[T["days_worked"]] = sum(1 for d in range(N_DAYS) if schedule[emp["id"], d] is not None)
                rows.append(row)
            df = pd.DataFrame(rows)
            st.dataframe(
                df.style.applymap(_style_shift, subset=day_names),
                use_container_width=True,
                hide_index=True,
            )

            st.caption(T["headcount"])
            rows2 = []
            for s in range(N_SHIFTS):
                row2 = {T["shift_col"]: SHIFT_NAMES[lang][s]}
                ok = True
                for d in range(N_DAYS):
                    count = sum(1 for emp in dept_emps if schedule[emp["id"], d] == s)
                    mn = constr["min_per_shift"][s]
                    flag = "" if count >= mn else " ⚠️"
                    row2[day_names[d]] = f"{count}{flag}"
                    if flag:
                        ok = False
                row2[T["status_col"]] = T["ok_status"] if ok else T["warn_status"]
                rows2.append(row2)
            st.dataframe(pd.DataFrame(rows2), use_container_width=True, hide_index=True)


def render_satisfaction(result: dict) -> None:
    st.header(T["satisfaction"])

    sat = result["satisfaction"]
    avg = sum(s["score"] for s in sat) / len(sat)

    m1, m2, m3 = st.columns(3)
    m1.metric(T["avg_score"], f"{avg:.1f} / 100")
    m2.metric(T["perfect"], f"{sum(1 for s in sat if s['score'] == 100)} 人" if lang == "ja" else f"{sum(1 for s in sat if s['score'] == 100)} staff")
    m3.metric(T["low_score"], f"{sum(1 for s in sat if s['score'] < 70)} 人" if lang == "ja" else f"{sum(1 for s in sat if s['score'] < 70)} staff")

    sat_df = pd.DataFrame(sat)
    sat_df[T["dept_col"]] = sat_df["dept"].map(DEPT_NAMES[lang])

    fig = px.bar(
        sat_df.sort_values("score"),
        x="score",
        y="name",
        color=T["dept_col"],
        color_discrete_map={v: DEPT_COLORS[k] for k, v in DEPT_NAMES[lang].items()},
        orientation="h",
        title=T["satisfaction"],
        labels={"score": T["avg_score"], "name": ""},
        hover_data={"soft_ng_violated": True, "pref_missed": True, "days_worked": True},
    )
    fig.add_vline(x=70, line_dash="dash", line_color="red", annotation_text="70")
    fig.update_layout(height=700, xaxis_range=[0, 100], yaxis={"categoryorder": "total ascending"})
    st.plotly_chart(fig, use_container_width=True)

    st.subheader(T["dept_summary"])
    dept_rows = []
    for dept_id in DEPT_IDS:
        ds = [s for s in sat if s["dept"] == dept_id]
        dept_rows.append({
            T["dept_col"]: f"{DEPT_NAMES[lang][dept_id]} ({dept_id})",
            T["people_col"]: len(ds),
            T["avg_sat"]: f"{sum(s['score'] for s in ds) / len(ds):.1f}",
            T["soft_viol"]: sum(s["soft_ng_violated"] for s in ds),
            T["pref_miss"]: sum(s["pref_missed"] for s in ds),
            T["avg_days"]: f"{sum(s['days_worked'] for s in ds) / len(ds):.1f}",
        })
    st.dataframe(pd.DataFrame(dept_rows), use_container_width=True, hide_index=True)


render_shift_table(schedule, employees)
render_satisfaction(result)