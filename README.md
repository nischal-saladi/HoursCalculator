# ⏱️ Time & Payroll Calculator Suite

A complete Python desktop calculator inspired by modern payroll tools, providing quick calculations, time arithmetic, pay/rate computations, auto-advance input, and full bi-weekly timesheets.

---

## 🌟 Modules Included

### 1. ⏱️ Time Calculators (Quick Tools + Auto-Advance + Pay Rate)
- **Fast 2-Digit Auto-Advance Input**:
  - Each time block is strictly limited to **2 digits** and numeric input only.
  - **Auto-Advance**: Typing 2 digits in an **Hour** block immediately jumps focus to the **Minute** block. Typing 2 digits in the **Minute** block automatically jumps to the **Hour block of the next line**!
  - If you reach the last line, completing it automatically adds a new line and places your cursor ready to type.
  - **Smart Backspace**: Pressing Backspace on an empty block automatically steps back into the previous block.
- **Sum Hours & Minutes (Left Side)**:
  - Stacked `Hours : Minutes` entries.
  - Dual live displays for both `[ HH : MM ]` and decimal hours `[ 0.00 ]`.
  - **`+ Add More Lines`**: Add additional rows at any time.
  - **💵 Integrated Pay Calculation**: Directly under the action buttons, enter your **Pay/Hr ($)** to compute total earnings.
  - Action buttons: **CALCULATE**, **CLEAR**, **PRINT** (Export to report with total pay included), and **EMAIL** (Copy formatted time and pay directly to clipboard).
- **Time Between Hours (Top Right)**:
  - Calculate exact duration between two clock times with 2-digit auto-advance (`From H` → `From M` → `To H` → `To M`).
  - Toggle AM/PM buttons with active styling.
  - Displays total decimal hours, `HHh MMm` duration, and **live shift earnings**.
  - **More Options**: Allows deducting unpaid break/lunch minutes.
  - Automatically handles overnight shifts across midnight.
- **Time Between Dates (Bottom Right)**:
  - Calculate days and working hours between two calendar dates (`From` and `To`).
  - Calculates total elapsed calendar days, working business days (Mon–Fri), and estimated work hours.
- **💵 Dedicated Bottom Pay Calculator Bar**:
  - Located across the bottom of the window.
  - Enter your **Pay Rate ($/hr)** to live-calculate **Summed Time Pay** and **Shift Time Pay**.

---

### 2. 📋 Bi-Weekly Payroll Timesheet
Full pay period tracking:
- **Daily In & Out shifts** for Week 1 & Week 2 (with break deduction in minutes).
- **Live Bi-Weekly Total**: Automatically sums all hours across the 2-week period.
- **Overtime & Gross Pay Estimator**: Enter your hourly rate (e.g. `$25.00`) and overtime threshold (e.g. `40 hrs/wk`) to compute regular vs. 1.5x overtime pay.
- **Expandable**: Add Week 3, Week 4, or add extra shifts to any week.
- **Export to CSV**: Save your complete timesheet directly to Excel/CSV.

---

## 🚀 How to Run

### Method 1: Double-Click Launcher (Windows)
Double-click [`run_calculator.bat`](run_calculator.bat).

### Method 2: Command Line
```powershell
python time_calculator.py
```
