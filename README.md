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

This app eliminates all of that — enter preferences, click Optimize, get a provably optimal schedule.

---

## Features

### ⚙️ Constraint-Based Optimization
- **Hard constraints** — guaranteed, never violated:
  - Must-off days (absolute unavailability)
  - Minimum & maximum staff per shift per department
  - Manager/assistant manager coverage every day
  - Certified staff coverage per shift (Grocery department)
  - Maximum consecutive working days
  - Minimum & maximum working days per week per employee

- **Soft constraints** — best-effort, penalized if violated:
  - Prefer-off days (penalty: 100 per violation)
  - Shift time preferences — morning/afternoon/night (penalty: 50 per mismatch)

### 📊 Visualizations
- Weekly schedule heatmap per department
- Employee satisfaction bar chart (penalty score per employee)
- Shift distribution summary

### 🌐 Bilingual
- Full English / 日本語 toggle

### 🎲 Demo Mode
- Randomize employee availability and preferences with one click
- Useful for demonstrations and testing

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

```
shift-optimizer/
├── app.py              # Streamlit UI — tabs, data editor, result display
├── optimizer.py        # OR-Tools CP-SAT model — constraints + objective
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
git clone https://github.com/mona2083/shift-optimizer.git
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

### 3. Optimize
- Click **"🚀 Optimize Shifts"**
- The solver runs for up to 15 seconds
- Results display the optimal schedule with satisfaction scores

### 4. Read the Results
- **Schedule heatmap** — color-coded by department, shows assigned shifts per employee per day
- **Satisfaction bar chart** — lower score = happier employee (penalty score)
- **Summary table** — total shifts assigned, satisfaction score, violations per employee

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

**Hard constraints** are added as mathematical equalities/inequalities — the solver will never produce a schedule that violates them. If no valid schedule exists, it reports "no solution" rather than returning an invalid result.

**Soft constraints** are converted into penalty terms. The solver's objective is to minimize the total penalty score — maximizing overall employee satisfaction subject to all hard rules being satisfied.

```python
# Example: must-off day → force variable to 0
model.Add(x[employee, day, shift] == 0)

# Example: minimum staff per shift
model.Add(sum(x[e, day, shift] for e in dept_employees) >= min_staff)

# Example: soft preference penalty
penalty += x[employee, day, wrong_shift] * 50
model.Minimize(sum(penalties))
```
---

## Author

**Manami Oyama** — AI Engineer / Product Manager  
🌺 Honolulu, Hawaii  
🔗 [Portfolio](https://mona2083.github.io/portfolio-2026/index.html) | [GitHub](https://github.com/mona2083) | [LinkedIn](https://www.linkedin.com/in/manami-oyama/)
