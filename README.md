# 🗓️ Shift Optimizer

> AI-powered shift scheduling for retail — satisfying every hard rule while maximizing employee happiness.

A Streamlit app that uses Google OR-Tools CP-SAT to automatically generate optimal weekly shift schedules for 30 employees across 3 departments. Instead of manually juggling spreadsheets, it **mathematically proves** the best possible schedule in under 15 seconds.

---

## Live Demo

🔗 [Open App](https://shift-optimizer-3mw2yb9vwve4iva6b4rpbu.streamlit.app/) 

---

## The Problem It Solves

Manual shift scheduling for 30+ staff across multiple departments typically takes a manager several hours per week. Common pain points:

- Forgetting must-off days leads to employee complaints
- Ensuring manager coverage every day requires careful tracking
- Balancing fairness across employees is nearly impossible by hand
- Any change requires rechecking all constraints from scratch
- **The "Infeasible" Problem:** When constraints are too tight (e.g., too many people requested Friday off), traditional solvers just crash or return "No Solution," leaving the manager in the dark.

This app eliminates all of that — enter preferences, click Optimize, and get a provably optimal schedule. If the math is impossible, it tells you exactly why or offers a "Best Effort" workaround.

---

## Features

### ⚙️ Constraint-Based Optimization
- **Hard constraints** — guaranteed, never violated:
  - Must-off days (absolute unavailability)
  - Maximum warehouse/department capacity per shift
  - Maximum consecutive working days
  - Minimum & maximum working days per week per employee

- **Soft constraints** — best-effort, penalized if violated:
  - Prefer-off days (penalty: 100 per violation)
  - Shift time preferences — morning/afternoon/night (penalty: 50 per mismatch)

### 🛡️ Resilience & Edge-Case Handling (New)
- **Heuristic Pre-check**: Instantly catches mathematically impossible conditions (e.g., total available employee days < required shift slots) before invoking the solver, providing clear, actionable error messages.
- **Best Effort Mode (Slack Variables)**: A toggle that relaxes minimum staffing requirements. It uses slack variables with massive penalty weights to ensure the solver *always* returns the best possible schedule. It highlights understaffed slots with a ⚠️, allowing managers to easily identify bottlenecks and make human decisions (like calling in help).

### 📊 Visualizations
- Weekly schedule heatmap per department
- Employee satisfaction bar chart (based on penalty scores)
- Headcount summary indicating where minimum staffing was missed (if Best Effort Mode is used)

### 🌐 Bilingual
- Full English / 日本語 toggle

### 🎲 Demo Mode
- Randomize employee availability and preferences with one click

---

## Tech Stack

| Component | Technology |
|---|---|
| Optimization Solver | `ortools` CP-SAT (Google OR-Tools) |
| UI | `streamlit` |
| Visualization | `plotly` |
| Data Management | `pandas` |

> **Note:** Use `ortools==9.8.3296`. 

---

## Project Structure

```text
shift-optimizer/
├── app.py              # Streamlit UI — pre-checks, tabs, data editor
├── optimizer.py        # OR-Tools CP-SAT model — constraints, slack variables, objective
├── data.py             # Employee data, department configs, defaults
├── requirements.txt
└── .gitignore
```

---

## Getting Started

### Prerequisites
- Python 3.10+
- pip

### Installation

```bash
git clone [https://github.com/mona2083/shift-optimizer.git](https://github.com/mona2083/shift-optimizer.git)
cd shift-optimizer
python -m venv .venv
source .venv/bin/activate      # Windows: .venv\Scripts\activate
pip install -r requirements.txt
streamlit run app.py
```

Open [http://localhost:8501](http://localhost:8501) in your browser.

---

## Usage

### 1. Set Employee Availability
- Select a department tab (Grocery / Apparel / Cashier)
- Use the data editor to set each employee's availability per day:
  - `○` — Available
  - `△ Prefer off` — Soft constraint (penalty: 100)
  - `× Must off` — Hard constraint (never assigned)
- Optionally set shift time preference (Morning / Afternoon / Night / No preference)

### 2. Configure Department Constraints
- Set minimum and maximum staff per shift
- Configure maximum consecutive working days

### 3. Optimize & Handle Edge Cases
- Click **"🚀 Optimize Shifts"**
- If the constraints are physically impossible (e.g., not enough staff), the pre-check will warn you.
- Toggle **"⚠️ Best Effort Mode"** to allow understaffing, then optimize again. The solver will fill what it can and flag the empty slots.

### 4. Read the Results
- **Schedule heatmap** — color-coded by department, shows assigned shifts and mismatched preferences (⚠)
- **Satisfaction bar chart** — 100 is a perfect score; points are deducted for ignoring soft constraints
- **Headcount Summary** — shows exact staffing per shift and flags (⚠️) if minimums weren't met

---

## Employee & Department Structure

| Department | Employees | Roles |
|---|---|---|
| 🟢 Grocery (A) | 12 | 1 Manager, 2 Asst. Managers, 1 Certified, 8 Staff |
| 🔵 Apparel (B) | 10 | 1 Manager, 2 Asst. Managers, 7 Staff |
| 🟤 Cashier (C) | 8 | 1 Manager, 2 Asst. Managers, 5 Staff |

**Employees are named** `A-01` through `C-08` (department prefix + number).

---

## How the Optimizer Works

The CP-SAT solver creates one binary variable per `(employee, day, shift)` combination — **630 variables** total — and assigns each to 0 (not working) or 1 (working).

**Hard constraints** are added as mathematical equalities/inequalities. **Soft constraints** are converted into penalty terms. The solver's objective is to minimize the total penalty score.

To handle real-world infeasibility, **Best Effort Mode** transforms hard "minimum staff" constraints into soft constraints using **slack variables**. 

```python
if allow_understaffing:
    # Add a slack variable for missing staff (0 to min_required)
    shortage = model.NewIntVar(0, min_required, "shortage")
    model.Add(sum(x[e, day, shift]) + shortage >= min_required)
    
    # Massive penalty ensures the solver only understaffs if absolutely necessary
    penalty += shortage * 10000 
else:
    # Strict hard constraint
    model.Add(sum(x[e, day, shift]) >= min_required)

# Normal soft constraints (preferences)
penalty += x[employee, day, wrong_shift] * 50

model.Minimize(sum(penalties))
```

---

## Author

**Manami Oyama** — AI Engineer / Product Manager  
🌺 Honolulu, Hawaii  
🔗 [Portfolio](https://mona2083.github.io/portfolio-2026/index.html) | [GitHub](https://github.com/mona2083) | [LinkedIn](https://www.linkedin.com/in/manami-oyama/)