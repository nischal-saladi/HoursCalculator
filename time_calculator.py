"""
Comprehensive Time & Payroll Calculator Suite
Includes:
1. Quick Time Calculator (Exact Match to User Reference + Pay Calculator + Auto-Advance):
   - Sum Hours & Minutes with 2-digit limit & auto-advance between blocks & lines
   - Time Between Hours with 2-digit auto-advance, AM/PM toggles, break options, and shift earnings
   - Time Between Dates with Month/Day/Year selectors and working days
   - Bottom Pay Rate Calculator Bar (live calculation across all tools)
2. Full Bi-Weekly Payroll Timesheet (with In/Out shifts, Overtime, Gross Pay, and CSV Export)
"""

import tkinter as tk
from tkinter import ttk, messagebox, filedialog
from datetime import datetime, date, timedelta
import calendar
import csv

class MultiTimeCalculatorApp(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("Time & Payroll Calculator")
        self.geometry("1180x820")
        self.minsize(1050, 700)

        self.style = ttk.Style(self)
        try:
            self.style.theme_use("clam")
        except tk.TclError:
            pass

        self._configure_styles()

        # Shared Pay Rate Variable for Tab 1
        self.tool_rate_var = tk.StringVar(value="25.00")
        self.tool_rate_var.trace_add("write", lambda *args: self.recalculate_all_tool_pay())

        # State tracking for hours in Tab 1
        self.sum_decimal_hours = 0.0
        self.tbh_decimal_hours = 0.0
        self.tbd_work_hours = 0.0

        # Notebook tabs
        self.notebook = ttk.Notebook(self)
        self.notebook.pack(fill=tk.BOTH, expand=True, padx=12, pady=12)

        # Tab 1: Time Calculators
        self.tab_tools = ttk.Frame(self.notebook)
        self.notebook.add(self.tab_tools, text="⏱️ Time Calculators")
        self._build_time_tools_tab(self.tab_tools)

        # Tab 2: Bi-Weekly Payroll Timesheet
        self.tab_payroll = ttk.Frame(self.notebook)
        self.notebook.add(self.tab_payroll, text="📋 Bi-Weekly Payroll Timesheet")
        self._build_payroll_tab(self.tab_payroll)

    def _configure_styles(self):
        bg_color = "#f4f6f9"
        self.configure(bg=bg_color)
        self.style.configure(".", background=bg_color, font=("Segoe UI", 9))
        self.style.configure("TNotebook", background=bg_color)
        self.style.configure("TNotebook.Tab", font=("Segoe UI", 10, "bold"), padding=[16, 6])
        
        self.style.configure("Card.TFrame", background="#ffffff")
        self.style.configure("Inner.TFrame", background="#ffffff")

    # =========================================================================
    # AUTO-ADVANCE & 2-DIGIT LIMIT VALIDATION HELPERS
    # =========================================================================
    def _validate_2_digits_and_advance(self, proposed, next_getter=None):
        """
        Limits entry to maximum 2 numeric digits.
        When 2 digits are reached, automatically shifts focus to the next entry block.
        """
        if proposed == "":
            return True
        if proposed.isdigit() and len(proposed) <= 2:
            if len(proposed) == 2 and next_getter:
                def advance():
                    nxt = next_getter()
                    if nxt:
                        nxt.focus_set()
                        nxt.selection_range(0, tk.END)
                self.after_idle(advance)
            return True
        return False

    def _on_entry_backspace(self, event, prev_getter=None):
        """
        When Backspace is pressed on an already-empty block, moves focus to the previous block.
        """
        if len(event.widget.get()) == 0 and prev_getter:
            prev = prev_getter()
            if prev:
                prev.focus_set()
                prev.icursor(tk.END)

    def _get_sum_next_entry(self, row_idx, is_hour):
        if is_hour:
            if row_idx < len(self.sum_time_rows):
                return self.sum_time_rows[row_idx]["m_entry"]
        else:
            next_idx = row_idx + 1
            if next_idx < len(self.sum_time_rows):
                return self.sum_time_rows[next_idx]["h_entry"]
            else:
                self.add_sum_row()
                return self.sum_time_rows[next_idx]["h_entry"]
        return None

    def _get_sum_prev_entry(self, row_idx, is_hour):
        if not is_hour:
            if row_idx < len(self.sum_time_rows):
                return self.sum_time_rows[row_idx]["h_entry"]
        else:
            if row_idx > 0:
                return self.sum_time_rows[row_idx - 1]["m_entry"]
        return None

    # =========================================================================
    # TAB 1: TIME CALCULATORS (Exact Layout + Auto-Advance + Bottom Pay)
    # =========================================================================
    def _build_time_tools_tab(self, parent):
        main_box = tk.Frame(parent, bg="#ffffff", bd=1, relief="solid")
        main_box.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)

        # Top area for calculators
        top_grid = tk.Frame(main_box, bg="#ffffff")
        top_grid.pack(fill=tk.BOTH, expand=True, padx=10, pady=(10, 6))

        top_grid.columnconfigure(0, weight=6) # Left section
        top_grid.columnconfigure(1, weight=5) # Right section
        top_grid.rowconfigure(0, weight=1)

        # Left Column: Enter Time & See Your Total
        left_box = tk.Frame(top_grid, bg="#ffffff", bd=1, relief="solid")
        left_box.grid(row=0, column=0, sticky="nsew", padx=8, pady=8)
        self._build_sum_times_section(left_box)

        # Right Column: Time Between Hours & Time Between Dates
        right_box = tk.Frame(top_grid, bg="#ffffff")
        right_box.grid(row=0, column=1, sticky="nsew", padx=8, pady=8)
        right_box.rowconfigure(0, weight=1)
        right_box.rowconfigure(1, weight=1)
        right_box.columnconfigure(0, weight=1)

        # Top Right: Time Between Hours
        tbh_frame = tk.Frame(right_box, bg="#ffffff", bd=1, relief="solid")
        tbh_frame.grid(row=0, column=0, sticky="nsew", pady=(0, 8))
        self._build_time_between_hours_section(tbh_frame)

        # Bottom Right: Time Between Dates
        tbd_frame = tk.Frame(right_box, bg="#ffffff", bd=1, relief="solid")
        tbd_frame.grid(row=1, column=0, sticky="nsew", pady=(8, 0))
        self._build_time_between_dates_section(tbd_frame)

        # ---------------------------------------------------------------------
        # BOTTOM AREA: Dedicated Pay / Hourly Rate Calculator Area
        # ---------------------------------------------------------------------
        bottom_bar = tk.Frame(main_box, bg="#edf2f7", bd=1, relief="solid", padx=16, pady=12)
        bottom_bar.pack(fill=tk.X, padx=10, pady=(4, 10))

        rate_panel = tk.Frame(bottom_bar, bg="#edf2f7")
        rate_panel.pack(side=tk.LEFT)

        tk.Label(
            rate_panel, text="💵 PAY CALCULATOR:", 
            font=("Segoe UI", 11, "bold"), fg="#1a365d", bg="#edf2f7"
        ).pack(side=tk.LEFT, padx=(0, 10))

        tk.Label(rate_panel, text="Pay Rate ($/hr):", font=("Segoe UI", 10), bg="#edf2f7").pack(side=tk.LEFT, padx=(0, 4))
        
        rate_box = ttk.Entry(rate_panel, textvariable=self.tool_rate_var, width=9, justify="right", font=("Segoe UI", 10, "bold"))
        rate_box.pack(side=tk.LEFT, padx=(0, 20))

        totals_panel = tk.Frame(bottom_bar, bg="#edf2f7")
        totals_panel.pack(side=tk.RIGHT)

        # Sum total pay
        sum_p_box = tk.Frame(totals_panel, bg="#ffffff", bd=1, relief="solid", padx=10, pady=4)
        sum_p_box.pack(side=tk.LEFT, padx=6)
        tk.Label(sum_p_box, text="SUMMED TIME PAY", font=("Segoe UI", 8, "bold"), fg="#4a5568", bg="#ffffff").pack(anchor="w")
        self.bottom_sum_pay_lbl = tk.Label(sum_p_box, text="$0.00", font=("Segoe UI", 12, "bold"), fg="#276749", bg="#ffffff")
        self.bottom_sum_pay_lbl.pack(anchor="w")

        # Shift pay
        tbh_p_box = tk.Frame(totals_panel, bg="#ffffff", bd=1, relief="solid", padx=10, pady=4)
        tbh_p_box.pack(side=tk.LEFT, padx=6)
        tk.Label(tbh_p_box, text="HOURS BETWEEN SHIFT PAY", font=("Segoe UI", 8, "bold"), fg="#4a5568", bg="#ffffff").pack(anchor="w")
        self.bottom_tbh_pay_lbl = tk.Label(tbh_p_box, text="$0.00", font=("Segoe UI", 12, "bold"), fg="#2b6cb0", bg="#ffffff")
        self.bottom_tbh_pay_lbl.pack(anchor="w")

    # -------------------------------------------------------------------------
    # SECTION 1: Enter Time & See Your Total (Left side)
    # -------------------------------------------------------------------------
    def _build_sum_times_section(self, parent):
        parent.rowconfigure(1, weight=1)
        parent.columnconfigure(0, weight=1)

        # Top Connected Blue Header Bar
        header_bar = tk.Frame(parent, bg="#4773aa", height=42)
        header_bar.grid(row=0, column=0, sticky="ew")
        header_bar.columnconfigure(0, weight=1)
        header_bar.columnconfigure(1, weight=1)

        lbl_enter = tk.Label(header_bar, text="Enter Time:", bg="#4773aa", fg="#ffffff", font=("Segoe UI", 11, "bold"), pady=8)
        lbl_enter.grid(row=0, column=0, sticky="ew")

        conn = tk.Label(header_bar, text="—", bg="#4773aa", fg="#ffffff", font=("Segoe UI", 12, "bold"))
        conn.place(relx=0.5, rely=0.5, anchor="center")

        lbl_total = tk.Label(header_bar, text="See Your Total:", bg="#4773aa", fg="#ffffff", font=("Segoe UI", 11, "bold"), pady=8)
        lbl_total.grid(row=0, column=1, sticky="ew")

        # Content Split: Inputs on left, Outputs/Buttons on right
        content = tk.Frame(parent, bg="#ffffff")
        content.grid(row=1, column=0, sticky="nsew", padx=10, pady=10)
        content.columnconfigure(0, weight=1)
        content.columnconfigure(1, weight=1)
        content.rowconfigure(0, weight=1)

        # Inputs sub-panel (Scrollable)
        inputs_outer = tk.Frame(content, bg="#ffffff")
        inputs_outer.grid(row=0, column=0, sticky="nsew", padx=(0, 10))
        inputs_outer.rowconfigure(1, weight=1)
        inputs_outer.columnconfigure(0, weight=1)

        sub_header = tk.Frame(inputs_outer, bg="#ffffff")
        sub_header.grid(row=0, column=0, sticky="ew", pady=(0, 6))
        tk.Label(sub_header, text="Hours    Minutes", font=("Segoe UI", 9), fg="#4a5568", bg="#ffffff").pack()

        in_canvas = tk.Canvas(inputs_outer, bg="#ffffff", highlightthickness=0)
        in_scrollbar = ttk.Scrollbar(inputs_outer, orient="vertical", command=in_canvas.yview)
        self.sum_rows_frame = tk.Frame(in_canvas, bg="#ffffff")

        self.sum_rows_frame.bind(
            "<Configure>",
            lambda e: in_canvas.configure(scrollregion=in_canvas.bbox("all"))
        )
        canvas_win = in_canvas.create_window((0, 0), window=self.sum_rows_frame, anchor="nw")
        in_canvas.bind("<Configure>", lambda e: in_canvas.itemconfig(canvas_win, width=e.width))

        in_canvas.configure(yscrollcommand=in_scrollbar.set)
        in_canvas.grid(row=1, column=0, sticky="nsew")
        in_scrollbar.grid(row=1, column=1, sticky="ns")

        add_lines_btn = tk.Button(
            inputs_outer, text="+ Add More Lines", font=("Segoe UI", 9, "underline"),
            bg="#ffffff", fg="#2b6cb0", bd=0, cursor="hand2", command=self.add_sum_row
        )
        add_lines_btn.grid(row=2, column=0, columnspan=2, pady=(8, 4))

        # Outputs sub-panel (Display & Buttons)
        outputs_panel = tk.Frame(content, bg="#ffffff", padx=10, pady=6)
        outputs_panel.grid(row=0, column=1, sticky="nsew")

        disp_frame = tk.Frame(outputs_panel, bg="#ffffff")
        disp_frame.pack(pady=(4, 10))

        hh_mm_box = tk.Frame(disp_frame, bg="#ffffff")
        hh_mm_box.pack(pady=(0, 8))

        self.disp_hh_lbl = tk.Label(
            hh_mm_box, text="00", font=("Segoe UI", 15, "bold"),
            bg="#8b9196", fg="#ffffff", width=4, height=1, relief="flat", padx=6, pady=3
        )
        self.disp_hh_lbl.pack(side=tk.LEFT, padx=3)

        colon_lbl = tk.Label(hh_mm_box, text=":", font=("Segoe UI", 15, "bold"), bg="#ffffff", fg="#4a5568")
        colon_lbl.pack(side=tk.LEFT)

        self.disp_mm_lbl = tk.Label(
            hh_mm_box, text="00", font=("Segoe UI", 15, "bold"),
            bg="#8b9196", fg="#ffffff", width=4, height=1, relief="flat", padx=6, pady=3
        )
        self.disp_mm_lbl.pack(side=tk.LEFT, padx=3)

        self.disp_dec_lbl = tk.Label(
            disp_frame, text="0.00", font=("Segoe UI", 14, "bold"),
            bg="#8b9196", fg="#ffffff", width=10, height=1, relief="flat", pady=3
        )
        self.disp_dec_lbl.pack()

        # Action Buttons
        btn_style_blue = {
            "font": ("Segoe UI", 9, "bold"),
            "bg": "#4372b8",
            "fg": "#ffffff",
            "activebackground": "#345b96",
            "activeforeground": "#ffffff",
            "relief": "flat",
            "cursor": "hand2",
            "pady": 5
        }

        calc_btn = tk.Button(outputs_panel, text="CALCULATE", command=self.calculate_sum_time, **btn_style_blue)
        calc_btn.pack(fill=tk.X, pady=(0, 6))

        clear_btn = tk.Button(outputs_panel, text="CLEAR", command=self.clear_sum_rows, **btn_style_blue)
        clear_btn.pack(fill=tk.X, pady=(0, 6))

        print_btn = tk.Button(outputs_panel, text="PRINT", command=self.print_sum_times, **btn_style_blue)
        print_btn.pack(fill=tk.X, pady=(0, 6))

        email_btn = tk.Button(outputs_panel, text="EMAIL", command=self.email_copy_summary, **btn_style_blue)
        email_btn.pack(fill=tk.X, pady=(0, 8))

        # Integrated Pay/Hr Card under EMAIL
        pay_box = tk.Frame(outputs_panel, bg="#f7fafc", bd=1, relief="solid", padx=8, pady=8)
        pay_box.pack(fill=tk.X)

        tk.Label(pay_box, text="💵 PAY CALCULATION", font=("Segoe UI", 9, "bold"), fg="#2b6cb0", bg="#f7fafc").pack(anchor="w")

        p_rate_row = tk.Frame(pay_box, bg="#f7fafc")
        p_rate_row.pack(fill=tk.X, pady=(4, 2))
        tk.Label(p_rate_row, text="Pay/Hr ($):", font=("Segoe UI", 9), bg="#f7fafc").pack(side=tk.LEFT)
        rate_sub_entry = ttk.Entry(p_rate_row, textvariable=self.tool_rate_var, width=8, justify="right")
        rate_sub_entry.pack(side=tk.RIGHT)

        p_tot_row = tk.Frame(pay_box, bg="#f7fafc")
        p_tot_row.pack(fill=tk.X, pady=(4, 2))
        tk.Label(p_tot_row, text="Total Pay:", font=("Segoe UI", 9, "bold"), bg="#f7fafc").pack(side=tk.LEFT)
        self.side_sum_pay_lbl = tk.Label(p_tot_row, text="$0.00", font=("Segoe UI", 12, "bold"), fg="#276749", bg="#f7fafc")
        self.side_sum_pay_lbl.pack(side=tk.RIGHT)

        # Initialize with 10 rows
        self.sum_time_rows = []
        for _ in range(10):
            self.add_sum_row()

    def add_sum_row(self):
        r_idx = len(self.sum_time_rows)
        row_frame = tk.Frame(self.sum_rows_frame, bg="#ffffff", pady=3)
        row_frame.pack(fill=tk.X)

        h_var = tk.StringVar(value="")
        m_var = tk.StringVar(value="")

        h_var.trace_add("write", lambda *args: self.calculate_sum_time())
        m_var.trace_add("write", lambda *args: self.calculate_sum_time())

        # Next/Prev getters for hour entry
        h_next_getter = lambda idx=r_idx: self._get_sum_next_entry(idx, is_hour=True)
        h_prev_getter = lambda idx=r_idx: self._get_sum_prev_entry(idx, is_hour=True)

        h_vcmd = (self.register(lambda P, g=h_next_getter: self._validate_2_digits_and_advance(P, g)), "%P")
        h_entry = ttk.Entry(row_frame, textvariable=h_var, width=5, justify="center", validate="key", validatecommand=h_vcmd)
        h_entry.pack(side=tk.LEFT, padx=(30, 2))
        h_entry.bind("<BackSpace>", lambda e, g=h_prev_getter: self._on_entry_backspace(e, g))

        colon = tk.Label(row_frame, text=":", font=("Segoe UI", 10, "bold"), bg="#ffffff", fg="#4a5568")
        colon.pack(side=tk.LEFT, padx=1)

        # Next/Prev getters for minute entry
        m_next_getter = lambda idx=r_idx: self._get_sum_next_entry(idx, is_hour=False)
        m_prev_getter = lambda idx=r_idx: self._get_sum_prev_entry(idx, is_hour=False)

        m_vcmd = (self.register(lambda P, g=m_next_getter: self._validate_2_digits_and_advance(P, g)), "%P")
        m_entry = ttk.Entry(row_frame, textvariable=m_var, width=5, justify="center", validate="key", validatecommand=m_vcmd)
        m_entry.pack(side=tk.LEFT, padx=2)
        m_entry.bind("<BackSpace>", lambda e, g=m_prev_getter: self._on_entry_backspace(e, g))

        self.sum_time_rows.append({
            "h_var": h_var,
            "m_var": m_var,
            "h_entry": h_entry,
            "m_entry": m_entry,
            "frame": row_frame
        })

    def calculate_sum_time(self):
        total_minutes = 0
        for r in self.sum_time_rows:
            h_str = r["h_var"].get().strip()
            m_str = r["m_var"].get().strip()

            h = int(h_str) if h_str.isdigit() else 0
            m = int(m_str) if m_str.isdigit() else 0

            total_minutes += (h * 60) + m

        tot_h = total_minutes // 60
        tot_m = total_minutes % 60
        dec_hours = total_minutes / 60.0
        self.sum_decimal_hours = dec_hours

        self.disp_hh_lbl.config(text=f"{tot_h:02d}")
        self.disp_mm_lbl.config(text=f"{tot_m:02d}")
        self.disp_dec_lbl.config(text=f"{dec_hours:.2f}")

        self.recalculate_all_tool_pay()

    def recalculate_all_tool_pay(self):
        try:
            rate = float(self.tool_rate_var.get())
        except ValueError:
            rate = 0.0

        # Summed time pay
        sum_pay = self.sum_decimal_hours * rate
        self.side_sum_pay_lbl.config(text=f"${sum_pay:,.2f}")
        self.bottom_sum_pay_lbl.config(text=f"${sum_pay:,.2f}")

        # Shift time pay
        shift_pay = self.tbh_decimal_hours * rate
        self.bottom_tbh_pay_lbl.config(text=f"${shift_pay:,.2f}")

        if hasattr(self, "tbh_pay_inline_lbl"):
            self.tbh_pay_inline_lbl.config(text=f"Pay: ${shift_pay:,.2f}")

    def clear_sum_rows(self):
        for r in self.sum_time_rows:
            r["h_var"].set("")
            r["m_var"].set("")
        self.sum_decimal_hours = 0.0
        self.disp_hh_lbl.config(text="00")
        self.disp_mm_lbl.config(text="00")
        self.disp_dec_lbl.config(text="0.00")
        self.recalculate_all_tool_pay()

    def print_sum_times(self):
        lines = []
        tot_min = 0
        for idx, r in enumerate(self.sum_time_rows):
            h_val = r["h_var"].get().strip()
            m_val = r["m_var"].get().strip()
            if h_val or m_val:
                h = int(h_val) if h_val.isdigit() else 0
                m = int(m_val) if m_val.isdigit() else 0
                tot_min += (h * 60) + m
                lines.append(f"Line {idx+1:02d}: {h:02d} hrs : {m:02d} mins")

        if not lines:
            messagebox.showinfo("Print / Export", "No time entries to export.")
            return

        tot_h = tot_min // 60
        tot_m = tot_min % 60
        dec = tot_min / 60.0
        try:
            rate = float(self.tool_rate_var.get())
        except ValueError:
            rate = 0.0
        pay = dec * rate

        summary = "--- TIME SUM & PAY REPORT ---\n\n" + "\n".join(lines)
        summary += f"\n\nTOTAL TIME: {tot_h:02d} Hours : {tot_m:02d} Minutes ({dec:.2f} Decimal Hours)"
        summary += f"\nPAY RATE:   ${rate:.2f}/hr"
        summary += f"\nTOTAL PAY:  ${pay:,.2f}"

        file_path = filedialog.asksaveasfilename(
            defaultextension=".txt",
            filetypes=[("Text File", "*.txt"), ("All Files", "*.*")],
            title="Save Time Summary Report"
        )
        if file_path:
            with open(file_path, "w", encoding="utf-8") as f:
                f.write(summary)
            messagebox.showinfo("Saved", f"Report saved to:\n{file_path}")

    def email_copy_summary(self):
        hh = self.disp_hh_lbl.cget("text")
        mm = self.disp_mm_lbl.cget("text")
        dec = self.disp_dec_lbl.cget("text")
        pay = self.side_sum_pay_lbl.cget("text")
        rate = self.tool_rate_var.get()

        text = f"Time Total: {hh} Hours : {mm} Minutes ({dec} Decimal Hours) | Pay Rate: ${rate}/hr | Total Pay: {pay}"
        self.clipboard_clear()
        self.clipboard_append(text)
        messagebox.showinfo("Copied to Clipboard", f"The following total has been copied to your clipboard to paste into your email:\n\n\"{text}\"")

    # -------------------------------------------------------------------------
    # SECTION 2: Time Between Hours (Top Right - with 2-digit auto-advance)
    # -------------------------------------------------------------------------
    def _build_time_between_hours_section(self, parent):
        h_bar = tk.Frame(parent, bg="#dd5643", height=38)
        h_bar.pack(fill=tk.X)
        tk.Label(h_bar, text="Time Between Hours", bg="#dd5643", fg="#ffffff", font=("Segoe UI", 11, "bold"), pady=6, padx=10).pack(anchor="w")

        body = tk.Frame(parent, bg="#ffffff", padx=16, pady=10)
        body.pack(fill=tk.BOTH, expand=True)

        # From Row
        row_from = tk.Frame(body, bg="#ffffff")
        row_from.pack(fill=tk.X, pady=3)
        tk.Label(row_from, text="From:", width=6, anchor="w", font=("Segoe UI", 10), bg="#ffffff").pack(side=tk.LEFT)

        tbh_from_m_getter = lambda: self.tbh_from_m
        tbh_to_h_getter = lambda: self.tbh_to_h
        tbh_to_m_getter = lambda: self.tbh_to_m

        vcmd_fh = (self.register(lambda P: self._validate_2_digits_and_advance(P, tbh_from_m_getter)), "%P")
        self.tbh_from_h = ttk.Entry(row_from, width=4, justify="center", validate="key", validatecommand=vcmd_fh)
        self.tbh_from_h.insert(0, "09")
        self.tbh_from_h.pack(side=tk.LEFT, padx=2)

        tk.Label(row_from, text=":", font=("Segoe UI", 10, "bold"), bg="#ffffff").pack(side=tk.LEFT)

        vcmd_fm = (self.register(lambda P: self._validate_2_digits_and_advance(P, tbh_to_h_getter)), "%P")
        self.tbh_from_m = ttk.Entry(row_from, width=4, justify="center", validate="key", validatecommand=vcmd_fm)
        self.tbh_from_m.insert(0, "00")
        self.tbh_from_m.pack(side=tk.LEFT, padx=2)
        self.tbh_from_m.bind("<BackSpace>", lambda e: self._on_entry_backspace(e, lambda: self.tbh_from_h))

        self.tbh_from_ampm = tk.StringVar(value="AM")
        self.from_am_btn, self.from_pm_btn = self._create_ampm_toggle(row_from, self.tbh_from_ampm)

        # To Row
        row_to = tk.Frame(body, bg="#ffffff")
        row_to.pack(fill=tk.X, pady=3)
        tk.Label(row_to, text="To:", width=6, anchor="w", font=("Segoe UI", 10), bg="#ffffff").pack(side=tk.LEFT)

        vcmd_th = (self.register(lambda P: self._validate_2_digits_and_advance(P, tbh_to_m_getter)), "%P")
        self.tbh_to_h = ttk.Entry(row_to, width=4, justify="center", validate="key", validatecommand=vcmd_th)
        self.tbh_to_h.insert(0, "05")
        self.tbh_to_h.pack(side=tk.LEFT, padx=2)
        self.tbh_to_h.bind("<BackSpace>", lambda e: self._on_entry_backspace(e, lambda: self.tbh_from_m))

        tk.Label(row_to, text=":", font=("Segoe UI", 10, "bold"), bg="#ffffff").pack(side=tk.LEFT)

        vcmd_tm = (self.register(lambda P: self._validate_2_digits_and_advance(P, lambda: None)), "%P")
        self.tbh_to_m = ttk.Entry(row_to, width=4, justify="center", validate="key", validatecommand=vcmd_tm)
        self.tbh_to_m.insert(0, "00")
        self.tbh_to_m.pack(side=tk.LEFT, padx=2)
        self.tbh_to_m.bind("<BackSpace>", lambda e: self._on_entry_backspace(e, lambda: self.tbh_to_h))

        self.tbh_to_ampm = tk.StringVar(value="PM")
        self.to_am_btn, self.to_pm_btn = self._create_ampm_toggle(row_to, self.tbh_to_ampm)

        # Calculate Button
        calc_btn = tk.Button(
            body, text="CALCULATE", font=("Segoe UI", 10, "bold"),
            bg="#9aa0a6", fg="#ffffff", activebackground="#7f858a",
            relief="flat", cursor="hand2", pady=4, command=self.calculate_time_between_hours
        )
        calc_btn.pack(fill=tk.X, pady=(6, 4))

        # Total Display Box with Pay
        tot_row = tk.Frame(body, bg="#ffffff")
        tot_row.pack(fill=tk.X, pady=2)
        tk.Label(tot_row, text="Total:", font=("Segoe UI", 10), width=6, anchor="w", bg="#ffffff").pack(side=tk.LEFT)

        self.tbh_total_entry = tk.Label(
            tot_row, text="00.00", font=("Segoe UI", 10, "bold"),
            bg="#ffffff", fg="#2d3748", bd=1, relief="solid", pady=3
        )
        self.tbh_total_entry.pack(side=tk.LEFT, fill=tk.X, expand=True)

        self.tbh_pay_inline_lbl = tk.Label(
            tot_row, text="Pay: $0.00", font=("Segoe UI", 10, "bold"),
            fg="#2b6cb0", bg="#ffffff", padx=8
        )
        self.tbh_pay_inline_lbl.pack(side=tk.RIGHT)

        # Clear and More Options Footer
        foot_row = tk.Frame(body, bg="#ffffff")
        foot_row.pack(fill=tk.X, pady=(4, 0))

        clr_link = tk.Button(
            foot_row, text="Clear", font=("Segoe UI", 9, "underline"),
            bg="#ffffff", fg="#4a5568", bd=0, cursor="hand2", command=self.clear_tbh
        )
        clr_link.pack(side=tk.LEFT)

        opt_link = tk.Button(
            foot_row, text="More Options", font=("Segoe UI", 9, "underline"),
            bg="#ffffff", fg="#4a5568", bd=0, cursor="hand2", command=self.tbh_more_options
        )
        opt_link.pack(side=tk.RIGHT)

        self.tbh_break_minutes = 0

    def _create_ampm_toggle(self, parent, var):
        frame = tk.Frame(parent, bg="#ffffff")
        frame.pack(side=tk.LEFT, padx=(10, 0))

        def update_buttons():
            val = var.get()
            if val == "AM":
                btn_am.config(bg="#70767c", fg="#ffffff")
                btn_pm.config(bg="#e2e8f0", fg="#4a5568")
            else:
                btn_am.config(bg="#e2e8f0", fg="#4a5568")
                btn_pm.config(bg="#70767c", fg="#ffffff")

        def set_val(val):
            var.set(val)
            update_buttons()

        btn_am = tk.Button(frame, text="AM", font=("Segoe UI", 8, "bold"), bd=1, relief="solid", padx=5, pady=1, cursor="hand2", command=lambda: set_val("AM"))
        btn_am.pack(side=tk.LEFT)

        btn_pm = tk.Button(frame, text="PM", font=("Segoe UI", 8, "bold"), bd=1, relief="solid", padx=5, pady=1, cursor="hand2", command=lambda: set_val("PM"))
        btn_pm.pack(side=tk.LEFT, padx=(2, 0))

        update_buttons()
        return btn_am, btn_pm

    def calculate_time_between_hours(self):
        try:
            fh = int(self.tbh_from_h.get().strip())
            fm = int(self.tbh_from_m.get().strip())
            th = int(self.tbh_to_h.get().strip())
            tm = int(self.tbh_to_m.get().strip())
        except ValueError:
            messagebox.showerror("Invalid Input", "Please enter valid numeric hours and minutes.")
            return

        if self.tbh_from_ampm.get() == "PM" and fh != 12:
            fh += 12
        elif self.tbh_from_ampm.get() == "AM" and fh == 12:
            fh = 0

        if self.tbh_to_ampm.get() == "PM" and th != 12:
            th += 12
        elif self.tbh_to_ampm.get() == "AM" and th == 12:
            th = 0

        dt_from = datetime(2000, 1, 1, fh, fm)
        dt_to = datetime(2000, 1, 1, th, tm)

        if dt_to <= dt_from:
            dt_to += timedelta(days=1)

        diff = dt_to - dt_from
        tot_min = max(0, (diff.total_seconds() / 60.0) - self.tbh_break_minutes)
        hours = tot_min / 60.0
        h_part = int(tot_min // 60)
        m_part = int(tot_min % 60)
        self.tbh_decimal_hours = hours

        self.tbh_total_entry.config(text=f"{hours:.2f} hrs ({h_part}h {m_part}m)")
        self.recalculate_all_tool_pay()

    def clear_tbh(self):
        self.tbh_from_h.delete(0, tk.END)
        self.tbh_from_h.insert(0, "00")
        self.tbh_from_m.delete(0, tk.END)
        self.tbh_from_m.insert(0, "00")
        self.tbh_to_h.delete(0, tk.END)
        self.tbh_to_h.insert(0, "00")
        self.tbh_to_m.delete(0, tk.END)
        self.tbh_to_m.insert(0, "00")
        self.tbh_break_minutes = 0
        self.tbh_decimal_hours = 0.0
        self.tbh_total_entry.config(text="00.00")
        self.recalculate_all_tool_pay()

    def tbh_more_options(self):
        dlg = tk.Toplevel(self)
        dlg.title("More Options - Time Between Hours")
        dlg.geometry("340x180")
        dlg.transient(self)
        dlg.grab_set()

        tk.Label(dlg, text="Deduct Unpaid Break (Minutes):", font=("Segoe UI", 10)).pack(pady=(20, 5))
        brk_var = tk.StringVar(value=str(self.tbh_break_minutes))
        entry = ttk.Entry(dlg, textvariable=brk_var, width=12, justify="center")
        entry.pack(pady=5)
        entry.focus()

        def apply_opt():
            try:
                self.tbh_break_minutes = float(brk_var.get())
            except ValueError:
                self.tbh_break_minutes = 0
            dlg.destroy()
            self.calculate_time_between_hours()

        ttk.Button(dlg, text="Apply & Recalculate", command=apply_opt).pack(pady=15)

    # -------------------------------------------------------------------------
    # SECTION 3: Time Between Dates (Bottom Right)
    # -------------------------------------------------------------------------
    def _build_time_between_dates_section(self, parent):
        h_bar = tk.Frame(parent, bg="#1b7837", height=38)
        h_bar.pack(fill=tk.X)
        tk.Label(h_bar, text="Time Between Dates", bg="#1b7837", fg="#ffffff", font=("Segoe UI", 11, "bold"), pady=6, padx=10).pack(anchor="w")

        body = tk.Frame(parent, bg="#ffffff", padx=16, pady=10)
        body.pack(fill=tk.BOTH, expand=True)

        months = [calendar.month_abbr[i] for i in range(1, 13)]
        days = [str(i) for i in range(1, 32)]
        today = date.today()

        # From Date Row
        row_from = tk.Frame(body, bg="#ffffff")
        row_from.pack(fill=tk.X, pady=3)
        tk.Label(row_from, text="From:", width=6, anchor="w", font=("Segoe UI", 10), bg="#ffffff").pack(side=tk.LEFT)

        self.tbd_from_m = ttk.Combobox(row_from, values=months, width=5, state="readonly")
        self.tbd_from_m.set(calendar.month_abbr[today.month])
        self.tbd_from_m.pack(side=tk.LEFT, padx=2)

        self.tbd_from_d = ttk.Combobox(row_from, values=days, width=4, state="readonly")
        self.tbd_from_d.set(str(today.day))
        self.tbd_from_d.pack(side=tk.LEFT, padx=2)

        self.tbd_from_y = ttk.Entry(row_from, width=6, justify="center")
        self.tbd_from_y.insert(0, str(today.year))
        self.tbd_from_y.pack(side=tk.LEFT, padx=2)

        cal_icon_from = tk.Button(row_from, text="📅", font=("Segoe UI", 8), bg="#edf2f7", bd=1, relief="solid", command=lambda: self._set_date_today(self.tbd_from_m, self.tbd_from_d, self.tbd_from_y))
        cal_icon_from.pack(side=tk.LEFT, padx=3)

        # To Date Row
        row_to = tk.Frame(body, bg="#ffffff")
        row_to.pack(fill=tk.X, pady=3)
        tk.Label(row_to, text="To:", width=6, anchor="w", font=("Segoe UI", 10), bg="#ffffff").pack(side=tk.LEFT)

        next_month = (today.month % 12) + 1
        next_year = today.year + (1 if today.month == 12 else 0)

        self.tbd_to_m = ttk.Combobox(row_to, values=months, width=5, state="readonly")
        self.tbd_to_m.set(calendar.month_abbr[next_month])
        self.tbd_to_m.pack(side=tk.LEFT, padx=2)

        self.tbd_to_d = ttk.Combobox(row_to, values=days, width=4, state="readonly")
        self.tbd_to_d.set(str(today.day))
        self.tbd_to_d.pack(side=tk.LEFT, padx=2)

        self.tbd_to_y = ttk.Entry(row_to, width=6, justify="center")
        self.tbd_to_y.insert(0, str(next_year))
        self.tbd_to_y.pack(side=tk.LEFT, padx=2)

        cal_icon_to = tk.Button(row_to, text="📅", font=("Segoe UI", 8), bg="#edf2f7", bd=1, relief="solid", command=lambda: self._set_date_today(self.tbd_to_m, self.tbd_to_d, self.tbd_to_y))
        cal_icon_to.pack(side=tk.LEFT, padx=3)

        # Calculate Button
        calc_btn = tk.Button(
            body, text="CALCULATE", font=("Segoe UI", 10, "bold"),
            bg="#9aa0a6", fg="#ffffff", activebackground="#7f858a",
            relief="flat", cursor="hand2", pady=4, command=self.calculate_time_between_dates
        )
        calc_btn.pack(fill=tk.X, pady=(6, 4))

        # Total Display Box
        tot_row = tk.Frame(body, bg="#ffffff")
        tot_row.pack(fill=tk.X, pady=2)
        tk.Label(tot_row, text="Total:", font=("Segoe UI", 10), width=6, anchor="w", bg="#ffffff").pack(side=tk.LEFT)

        self.tbd_total_entry = tk.Label(
            tot_row, text="00.00", font=("Segoe UI", 10, "bold"),
            bg="#ffffff", fg="#2d3748", bd=1, relief="solid", pady=3
        )
        self.tbd_total_entry.pack(side=tk.LEFT, fill=tk.X, expand=True)

        # Clear and More Options Footer
        foot_row = tk.Frame(body, bg="#ffffff")
        foot_row.pack(fill=tk.X, pady=(4, 0))

        clr_link = tk.Button(
            foot_row, text="Clear", font=("Segoe UI", 9, "underline"),
            bg="#ffffff", fg="#4a5568", bd=0, cursor="hand2", command=self.clear_tbd
        )
        clr_link.pack(side=tk.LEFT)

        opt_link = tk.Button(
            foot_row, text="More Options", font=("Segoe UI", 9, "underline"),
            bg="#ffffff", fg="#4a5568", bd=0, cursor="hand2", command=self.tbd_more_options
        )
        opt_link.pack(side=tk.RIGHT)

        self.tbd_hours_per_day = 8.0

    def _set_date_today(self, m_box, d_box, y_box):
        td = date.today()
        m_box.set(calendar.month_abbr[td.month])
        d_box.set(str(td.day))
        y_box.delete(0, tk.END)
        y_box.insert(0, str(td.year))

    def _get_date_from_fields(self, m_cb, d_cb, y_en):
        m_name = m_cb.get()
        d_val = int(d_cb.get())
        y_val = int(y_en.get())
        m_val = list(calendar.month_abbr).index(m_name)
        return date(y_val, m_val, d_val)

    def calculate_time_between_dates(self):
        try:
            d1 = self._get_date_from_fields(self.tbd_from_m, self.tbd_from_d, self.tbd_from_y)
            d2 = self._get_date_from_fields(self.tbd_to_m, self.tbd_to_d, self.tbd_to_y)
        except Exception:
            messagebox.showerror("Invalid Date", "Please ensure valid Month, Day, and Year selections.")
            return

        if d2 < d1:
            diff_days = (d1 - d2).days
        else:
            diff_days = (d2 - d1).days

        cur = min(d1, d2)
        end = max(d1, d2)
        work_days = 0
        while cur < end:
            if cur.weekday() < 5:
                work_days += 1
            cur += timedelta(days=1)

        work_hours = work_days * self.tbd_hours_per_day
        self.tbd_work_hours = work_hours
        self.tbd_total_entry.config(text=f"{diff_days} days ({work_days} work days / {work_hours:.1f} hrs)")

    def clear_tbd(self):
        today = date.today()
        self.tbd_from_m.set(calendar.month_abbr[today.month])
        self.tbd_from_d.set(str(today.day))
        self.tbd_from_y.delete(0, tk.END)
        self.tbd_from_y.insert(0, str(today.year))

        self.tbd_to_m.set(calendar.month_abbr[today.month])
        self.tbd_to_d.set(str(today.day))
        self.tbd_to_y.delete(0, tk.END)
        self.tbd_to_y.insert(0, str(today.year))

        self.tbd_work_hours = 0.0
        self.tbd_total_entry.config(text="00.00")

    def tbd_more_options(self):
        dlg = tk.Toplevel(self)
        dlg.title("More Options - Time Between Dates")
        dlg.geometry("340x190")
        dlg.transient(self)
        dlg.grab_set()

        tk.Label(dlg, text="Hours per Working Day:", font=("Segoe UI", 10)).pack(pady=(20, 5))
        h_var = tk.StringVar(value=str(self.tbd_hours_per_day))
        entry = ttk.Entry(dlg, textvariable=h_var, width=12, justify="center")
        entry.pack(pady=5)

        def apply_opt():
            try:
                self.tbd_hours_per_day = float(h_var.get())
            except ValueError:
                self.tbd_hours_per_day = 8.0
            dlg.destroy()
            self.calculate_time_between_dates()

        ttk.Button(dlg, text="Apply & Recalculate", command=apply_opt).pack(pady=15)

    # =========================================================================
    # TAB 2: FULL BI-WEEKLY PAYROLL TIMESHEET (In & Out Shifts)
    # =========================================================================
    def _build_payroll_tab(self, parent):
        container = ttk.Frame(parent, padding=(16, 12))
        container.pack(fill=tk.BOTH, expand=True)

        container.columnconfigure(0, weight=3)
        container.columnconfigure(1, weight=2)
        container.rowconfigure(0, weight=1)

        # Left: Shifts Table
        left_frame = ttk.Frame(container)
        left_frame.grid(row=0, column=0, sticky="nsew", padx=(0, 10))
        left_frame.rowconfigure(0, weight=1)
        left_frame.columnconfigure(0, weight=1)

        canvas = tk.Canvas(left_frame, bg="#f7fafc", highlightthickness=0)
        scrollbar = ttk.Scrollbar(left_frame, orient="vertical", command=canvas.yview)

        self.scroll_payroll_frame = ttk.Frame(canvas)
        self.scroll_payroll_frame.bind("<Configure>", lambda e: canvas.configure(scrollregion=canvas.bbox("all")))
        canvas_win = canvas.create_window((0, 0), window=self.scroll_payroll_frame, anchor="nw")
        canvas.bind("<Configure>", lambda e: canvas.itemconfig(canvas_win, width=e.width))

        canvas.configure(yscrollcommand=scrollbar.set)
        canvas.grid(row=0, column=0, sticky="nsew")
        scrollbar.grid(row=0, column=1, sticky="ns")

        # Bottom Bar
        bbar = ttk.Frame(left_frame, padding=(0, 10, 0, 0))
        bbar.grid(row=1, column=0, columnspan=2, sticky="ew")

        ttk.Button(bbar, text="➕ Add More Weeks", command=self.add_payroll_week).pack(side=tk.LEFT, padx=(0, 6))
        ttk.Button(bbar, text="⚡ Fill Mon-Fri 9AM-5PM", command=self.quick_fill_payroll).pack(side=tk.LEFT, padx=(0, 6))
        ttk.Button(bbar, text="🗑️ Clear All", command=self.clear_payroll).pack(side=tk.LEFT)

        # Right: Payroll Summary Card
        right_frame = ttk.Frame(container)
        right_frame.grid(row=0, column=1, sticky="nsew", padx=(10, 0))
        self._build_payroll_summary_card(right_frame)

        self.payroll_weeks = []
        self.add_payroll_week()
        self.add_payroll_week()

    def _build_payroll_summary_card(self, parent):
        card = tk.Frame(parent, bg="#ffffff", bd=1, relief="solid")
        card.pack(fill=tk.BOTH, expand=True)

        inner = ttk.Frame(card, padding=16)
        inner.pack(fill=tk.BOTH, expand=True)

        ttk.Label(inner, text="📊 Bi-Weekly Payroll Summary", font=("Segoe UI", 13, "bold")).pack(anchor="w", pady=(0, 10))

        self.payroll_breakdown_frame = ttk.Frame(inner)
        self.payroll_breakdown_frame.pack(fill=tk.X, pady=(0, 10))

        ttk.Separator(inner, orient="horizontal").pack(fill=tk.X, pady=8)

        tbox = tk.Frame(inner, bg="#e6fffa", bd=1, relief="solid")
        tbox.pack(fill=tk.X, pady=(0, 14))
        tk.Label(tbox, text="TOTAL BI-WEEKLY HOURS", font=("Segoe UI", 9, "bold"), fg="#234e52", bg="#e6fffa", padx=12, pady=4).pack(anchor="w")
        self.payroll_grand_total = tk.Label(tbox, text="0.00 hrs", font=("Segoe UI", 24, "bold"), fg="#285e61", bg="#e6fffa", padx=12, pady=4)
        self.payroll_grand_total.pack(anchor="w")

        pbox = ttk.LabelFrame(inner, text=" 💵 Payroll & Overtime Estimator ", padding=12)
        pbox.pack(fill=tk.X, pady=(0, 12))

        r_f = ttk.Frame(pbox)
        r_f.pack(fill=tk.X, pady=2)
        ttk.Label(r_f, text="Hourly Pay Rate ($):").pack(side=tk.LEFT)
        self.pay_rate_var = tk.StringVar(value="25.00")
        self.pay_rate_var.trace_add("write", lambda *args: self.recalculate_payroll())
        ttk.Entry(r_f, textvariable=self.pay_rate_var, width=10, justify="right").pack(side=tk.RIGHT)

        ot_f = ttk.Frame(pbox)
        ot_f.pack(fill=tk.X, pady=2)
        ttk.Label(ot_f, text="Overtime after (hrs/wk):").pack(side=tk.LEFT)
        self.pay_ot_var = tk.StringVar(value="40")
        self.pay_ot_var.trace_add("write", lambda *args: self.recalculate_payroll())
        ttk.Entry(ot_f, textvariable=self.pay_ot_var, width=10, justify="right").pack(side=tk.RIGHT)

        ttk.Separator(pbox, orient="horizontal").pack(fill=tk.X, pady=6)

        reg_f = ttk.Frame(pbox)
        reg_f.pack(fill=tk.X, pady=2)
        ttk.Label(reg_f, text="Regular Hours:").pack(side=tk.LEFT)
        self.pay_reg_lbl = ttk.Label(reg_f, text="0.00 hrs", font=("Segoe UI", 9, "bold"))
        self.pay_reg_lbl.pack(side=tk.RIGHT)

        ot_row = ttk.Frame(pbox)
        ot_row.pack(fill=tk.X, pady=2)
        ttk.Label(ot_row, text="Overtime Hours (1.5x):").pack(side=tk.LEFT)
        self.pay_ot_lbl = ttk.Label(ot_row, text="0.00 hrs", font=("Segoe UI", 9, "bold"), foreground="#c53030")
        self.pay_ot_lbl.pack(side=tk.RIGHT)

        gross_f = ttk.Frame(pbox)
        gross_f.pack(fill=tk.X, pady=(6, 2))
        ttk.Label(gross_f, text="Estimated Gross Pay:", font=("Segoe UI", 10, "bold")).pack(side=tk.LEFT)
        self.pay_gross_lbl = ttk.Label(gross_f, text="$0.00", font=("Segoe UI", 13, "bold"), foreground="#2b6cb0")
        self.pay_gross_lbl.pack(side=tk.RIGHT)

        ttk.Button(inner, text="💾 Export Timesheet to CSV", command=self.export_payroll_csv).pack(fill=tk.X, side=tk.BOTTOM, pady=(8, 0))

    def add_payroll_week(self):
        days = ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday"]
        w_idx = len(self.payroll_weeks) + 1

        w_card = tk.Frame(self.scroll_payroll_frame, bg="#ffffff", bd=1, relief="solid")
        w_card.pack(fill=tk.X, pady=(0, 12))

        inner = ttk.Frame(w_card, padding=10)
        inner.pack(fill=tk.X)

        hdr = ttk.Frame(inner)
        hdr.pack(fill=tk.X, pady=(0, 6))

        tk.Label(hdr, text=f"📅 Week {w_idx}", font=("Segoe UI", 11, "bold"), fg="#2b6cb0", bg="#ffffff").pack(side=tk.LEFT)

        sub_lbl = ttk.Label(hdr, text="Subtotal: 0.00 hrs", font=("Segoe UI", 9, "bold"), foreground="#2b6cb0")
        sub_lbl.pack(side=tk.RIGHT, padx=(8, 0))

        add_s_btn = ttk.Button(hdr, text="➕ Add Shift", command=lambda: self.add_payroll_row(w_data, "Extra Shift"))
        add_s_btn.pack(side=tk.RIGHT)

        cols = ttk.Frame(inner)
        cols.pack(fill=tk.X, pady=(0, 2))
        cols.columnconfigure(0, weight=3)
        cols.columnconfigure(1, weight=3)
        cols.columnconfigure(2, weight=3)
        cols.columnconfigure(3, weight=2)
        cols.columnconfigure(4, weight=2)
        cols.columnconfigure(5, weight=1)

        ttk.Label(cols, text="Day / Shift", font=("Segoe UI", 8, "bold")).grid(row=0, column=0, sticky="w")
        ttk.Label(cols, text="Time In", font=("Segoe UI", 8, "bold")).grid(row=0, column=1, sticky="w")
        ttk.Label(cols, text="Time Out", font=("Segoe UI", 8, "bold")).grid(row=0, column=2, sticky="w")
        ttk.Label(cols, text="Break (min)", font=("Segoe UI", 8, "bold")).grid(row=0, column=3, sticky="w")
        ttk.Label(cols, text="Hours", font=("Segoe UI", 8, "bold")).grid(row=0, column=4, sticky="w")

        rows_f = ttk.Frame(inner)
        rows_f.pack(fill=tk.X)
        rows_f.columnconfigure(0, weight=3)
        rows_f.columnconfigure(1, weight=3)
        rows_f.columnconfigure(2, weight=3)
        rows_f.columnconfigure(3, weight=2)
        rows_f.columnconfigure(4, weight=2)
        rows_f.columnconfigure(5, weight=1)

        w_data = {
            "index": w_idx,
            "subtotal_lbl": sub_lbl,
            "rows_frame": rows_f,
            "rows": []
        }
        self.payroll_weeks.append(w_data)

        for d in days:
            self.add_payroll_row(w_data, d)

        self._refresh_payroll_breakdown()
        self.recalculate_payroll()

    def add_payroll_row(self, w_data, day_label):
        rf = w_data["rows_frame"]
        r_idx = len(w_data["rows"])

        d_var = tk.StringVar(value=day_label)
        in_var = tk.StringVar(value="")
        out_var = tk.StringVar(value="")
        brk_var = tk.StringVar(value="0")
        hrs_var = tk.StringVar(value="0.00")

        in_var.trace_add("write", lambda *args: self.recalculate_payroll())
        out_var.trace_add("write", lambda *args: self.recalculate_payroll())
        brk_var.trace_add("write", lambda *args: self.recalculate_payroll())

        ttk.Entry(rf, textvariable=d_var, width=11).grid(row=r_idx, column=0, sticky="ew", padx=1, pady=2)
        ttk.Entry(rf, textvariable=in_var, width=9).grid(row=r_idx, column=1, sticky="ew", padx=1, pady=2)
        ttk.Entry(rf, textvariable=out_var, width=9).grid(row=r_idx, column=2, sticky="ew", padx=1, pady=2)
        ttk.Entry(rf, textvariable=brk_var, width=6, justify="center").grid(row=r_idx, column=3, sticky="ew", padx=1, pady=2)
        ttk.Label(rf, textvariable=hrs_var, font=("Segoe UI", 9, "bold")).grid(row=r_idx, column=4, sticky="w", padx=4, pady=2)

        clr = tk.Button(rf, text="✕", font=("Segoe UI", 8), bg="#ffffff", fg="#a0aec0", relief="flat", bd=0, cursor="hand2",
                        command=lambda: (in_var.set(""), out_var.set(""), brk_var.set("0")))
        clr.grid(row=r_idx, column=5, padx=1, pady=2)

        w_data["rows"].append({
            "day_var": d_var, "in_var": in_var, "out_var": out_var,
            "brk_var": brk_var, "hrs_var": hrs_var, "hours_float": 0.0
        })

    def _parse_shift_time(self, s):
        raw = s.strip().upper()
        if not raw:
            return None
        import re
        if re.search(r'\d+[AP]$', raw) or re.search(r'\d+\s+[AP]$', raw):
            raw += "M"
        for fmt in ["%I:%M %p", "%I:%M%p", "%I %p", "%I%p", "%H:%M", "%H"]:
            try:
                return datetime.strptime(raw, fmt).time()
            except ValueError:
                pass
        return None

    def recalculate_payroll(self):
        grand = 0.0
        tot_reg = 0.0
        tot_ot = 0.0

        try:
            ot_limit = float(self.pay_ot_var.get())
        except ValueError:
            ot_limit = 40.0

        for w in self.payroll_weeks:
            w_sum = 0.0
            for r in w["rows"]:
                in_s = r["in_var"].get().strip()
                out_s = r["out_var"].get().strip()
                brk_s = r["brk_var"].get().strip()

                if not in_s or not out_s:
                    r["hours_float"] = 0.0
                    r["hrs_var"].set("0.00")
                    continue

                t_in = self._parse_shift_time(in_s)
                t_out = self._parse_shift_time(out_s)

                if not t_in or not t_out:
                    r["hours_float"] = 0.0
                    r["hrs_var"].set("Invalid")
                    continue

                base = datetime(2000, 1, 1)
                dt_in = datetime.combine(base, t_in)
                dt_out = datetime.combine(base, t_out)
                if dt_out <= dt_in:
                    dt_out += timedelta(days=1)

                diff = dt_out - dt_in
                tot_m = diff.total_seconds() / 60.0
                try:
                    b_min = float(brk_s) if brk_s else 0.0
                except ValueError:
                    b_min = 0.0

                net_h = max(0.0, tot_m - b_min) / 60.0
                r["hours_float"] = net_h
                r["hrs_var"].set(f"{net_h:.2f} hrs")
                w_sum += net_h

            w["subtotal_lbl"].config(text=f"Subtotal: {w_sum:.2f} hrs")
            if hasattr(w, "summary_lbl") and w["summary_lbl"]:
                w["summary_lbl"].config(text=f"{w_sum:.2f} hrs")

            grand += w_sum
            if w_sum > ot_limit:
                tot_reg += ot_limit
                tot_ot += (w_sum - ot_limit)
            else:
                tot_reg += w_sum

        self.payroll_grand_total.config(text=f"{grand:.2f} hrs")
        self.pay_reg_lbl.config(text=f"{tot_reg:.2f} hrs")
        self.pay_ot_lbl.config(text=f"{tot_ot:.2f} hrs")

        try:
            rate = float(self.pay_rate_var.get())
            gross = (tot_reg * rate) + (tot_ot * rate * 1.5)
            self.pay_gross_lbl.config(text=f"${gross:,.2f}")
        except ValueError:
            self.pay_gross_lbl.config(text="--")

    def _refresh_payroll_breakdown(self):
        for widget in self.payroll_breakdown_frame.winfo_children():
            widget.destroy()

        for w in self.payroll_weeks:
            rf = ttk.Frame(self.payroll_breakdown_frame)
            rf.pack(fill=tk.X, pady=1)
            ttk.Label(rf, text=f"Week {w['index']} Total:").pack(side=tk.LEFT)
            lbl = ttk.Label(rf, text="0.00 hrs", font=("Segoe UI", 9, "bold"), foreground="#2b6cb0")
            lbl.pack(side=tk.RIGHT)
            w["summary_lbl"] = lbl

    def quick_fill_payroll(self):
        for w in self.payroll_weeks:
            for r in w["rows"]:
                day = r["day_var"].get().lower()
                if any(k in day for k in ["mon", "tue", "wed", "thu", "fri"]):
                    r["in_var"].set("9:00 AM")
                    r["out_var"].set("5:00 PM")
                    r["brk_var"].set("30")
                else:
                    r["in_var"].set("")
                    r["out_var"].set("")
                    r["brk_var"].set("0")
        self.recalculate_payroll()

    def clear_payroll(self):
        if messagebox.askyesno("Clear Payroll", "Clear all entered shift hours?"):
            for w in self.payroll_weeks:
                for r in w["rows"]:
                    r["in_var"].set("")
                    r["out_var"].set("")
                    r["brk_var"].set("0")
            self.recalculate_payroll()

    def export_payroll_csv(self):
        path = filedialog.asksaveasfilename(defaultextension=".csv", filetypes=[("CSV Files", "*.csv"), ("All Files", "*.*")])
        if not path:
            return
        with open(path, "w", newline="", encoding="utf-8") as f:
            wr = csv.writer(f)
            wr.writerow(["Week", "Day/Shift", "Time In", "Time Out", "Break (min)", "Total Hours"])
            for w in self.payroll_weeks:
                for r in w["rows"]:
                    wr.writerow([f"Week {w['index']}", r["day_var"].get(), r["in_var"].get(), r["out_var"].get(), r["brk_var"].get(), f"{r['hours_float']:.2f}"])
            wr.writerow([])
            wr.writerow(["Grand Total Hours", self.payroll_grand_total.cget("text")])
            wr.writerow(["Regular Hours", self.pay_reg_lbl.cget("text")])
            wr.writerow(["Overtime Hours", self.pay_ot_lbl.cget("text")])
            wr.writerow(["Gross Pay", self.pay_gross_lbl.cget("text")])
        messagebox.showinfo("Export Successful", f"Saved to {path}")

if __name__ == "__main__":
    app = MultiTimeCalculatorApp()
    app.mainloop()
