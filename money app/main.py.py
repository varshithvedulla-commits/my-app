import flet as ft
import sqlite3
from datetime import datetime

# ==========================================
# DATABASE MANAGEMENT (SQLite)
# ==========================================
class Database:
    def __init__(self):
        self.conn = sqlite3.connect("money_manager.db", check_same_thread=False)
        self.create_tables()

    def create_tables(self):
        cursor = self.conn.cursor()
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS loans (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id TEXT,
                name TEXT,
                mobile TEXT,
                address TEXT,
                amount REAL,
                rate REAL,
                interest_type TEXT,
                date_given TEXT,
                due_date TEXT,
                notes TEXT,
                status TEXT, -- 'ACTIVE', 'COMPLETED', 'BLACKLISTED'
                amount_returned REAL,
                date_returned TEXT
            )
        """)
        self.conn.commit()

    def add_loan(self, data):
        cursor = self.conn.cursor()
        cursor.execute("""
            INSERT INTO loans (user_id, name, mobile, address, amount, rate, interest_type, date_given, due_date, notes, status)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, 'ACTIVE')
        """, data)
        self.conn.commit()

    def get_loans(self, user_id, status):
        cursor = self.conn.cursor()
        cursor.execute("SELECT * FROM loans WHERE user_id=? AND status=? ORDER BY id DESC", (user_id, status))
        return cursor.fetchall()

    def update_status(self, loan_id, status, amount_returned=0, date_returned=""):
        cursor = self.conn.cursor()
        cursor.execute("UPDATE loans SET status=?, amount_returned=?, date_returned=? WHERE id=?", 
                       (status, amount_returned, date_returned, loan_id))
        self.conn.commit()

    def delete_loan(self, loan_id):
        cursor = self.conn.cursor()
        cursor.execute("DELETE FROM loans WHERE id=?", (loan_id,))
        self.conn.commit()

    def get_dashboard_stats(self, user_id):
        cursor = self.conn.cursor()
        stats = {
            "total_lent": cursor.execute("SELECT SUM(amount) FROM loans WHERE user_id=? AND status='ACTIVE'", (user_id,)).fetchone()[0] or 0,
            "total_returned": cursor.execute("SELECT SUM(amount_returned) FROM loans WHERE user_id=? AND status='COMPLETED'", (user_id,)).fetchone()[0] or 0,
            "lost_money": cursor.execute("SELECT SUM(amount) FROM loans WHERE user_id=? AND status='BLACKLISTED'", (user_id,)).fetchone()[0] or 0,
            "active_count": cursor.execute("SELECT COUNT(*) FROM loans WHERE user_id=? AND status='ACTIVE'", (user_id,)).fetchone()[0],
            "blacklisted_count": cursor.execute("SELECT COUNT(*) FROM loans WHERE user_id=? AND status='BLACKLISTED'", (user_id,)).fetchone()[0],
        }
        return stats

db = Database()

# ==========================================
# MAIN APPLICATION APP STATE & UI
# ==========================================
def main(page: ft.Page):
    page.title = "Money Management App"
    page.theme_mode = ft.ThemeMode.DARK
    page.window_width = 1200
    page.window_height = 800
    page.padding = 20
    
    # State Variables
    app_state = {
        "user_id": None,
        "current_view": "Dashboard"
    }

    # --- UI COMPONENTS ---
    
    def switch_view(e):
        app_state["current_view"] = e.control.selected_index
        render_main_layout()

    def calculate_interest(e):
        try:
            amt = float(amount_input.value) if amount_input.value else 0
            rate = float(rate_input.value) if rate_input.value else 0
            interest = amt * (rate / 100)
            total = amt + interest
            calc_text.value = f"Calculated: Principal: ₹{amt} | Interest/Period: ₹{interest} | Total: ₹{total}"
        except ValueError:
            calc_text.value = "Please enter valid numbers."
        page.update()

    # Form Inputs
    name_input = ft.TextField(label="Full Name (Required)", width=300)
    mobile_input = ft.TextField(label="Mobile Number", width=300)
    address_input = ft.TextField(label="Address", width=300)
    amount_input = ft.TextField(label="Amount Given (₹)", width=300, on_change=calculate_interest)
    rate_input = ft.TextField(label="Interest Rate (%)", width=300, on_change=calculate_interest)
    type_input = ft.Dropdown(label="Interest Type", options=[ft.dropdown.Option("Monthly"), ft.dropdown.Option("Yearly")], width=300, value="Monthly")
    date_input = ft.TextField(label="Date Given (YYYY-MM-DD)", value=datetime.today().strftime('%Y-%m-%d'), width=300)
    due_input = ft.TextField(label="Due Date (YYYY-MM-DD)", width=300)
    notes_input = ft.TextField(label="Notes", multiline=True, width=300)
    calc_text = ft.Text("Enter amount and rate to calculate.", color=ft.colors.GREEN_400, weight="bold")

    def clear_form(e=None):
        name_input.value = ""
        mobile_input.value = ""
        address_input.value = ""
        amount_input.value = ""
        rate_input.value = ""
        date_input.value = datetime.today().strftime('%Y-%m-%d')
        due_input.value = ""
        notes_input.value = ""
        calc_text.value = "Enter amount and rate to calculate."
        page.update()

    def save_loan(e):
        if not name_input.value or not amount_input.value or not rate_input.value:
            page.snack_bar = ft.SnackBar(ft.Text("Please fill required fields!"), bgcolor=ft.colors.RED)
            page.snack_bar.open = True
            page.update()
            return
        
        data = (app_state["user_id"], name_input.value, mobile_input.value, address_input.value,
                float(amount_input.value), float(rate_input.value), type_input.value,
                date_input.value, due_input.value, notes_input.value)
        db.add_loan(data)
        clear_form()
        page.snack_bar = ft.SnackBar(ft.Text("Loan Saved Successfully!"), bgcolor=ft.colors.GREEN)
        page.snack_bar.open = True
        app_state["current_view"] = 0 # Go to Dashboard
        render_main_layout()

    def build_dashboard():
        stats = db.get_dashboard_stats(app_state["user_id"])
        return ft.Column([
            ft.Text(f"Dashboard - {app_state['user_id']}", size=30, weight="bold"),
            ft.Divider(),
            ft.Row([
                ft.Card(content=ft.Container(content=ft.Column([ft.Text("Total Lent", size=16), ft.Text(f"₹{stats['total_lent']}", size=24, weight="bold", color=ft.colors.BLUE_400)]), padding=20)),
                ft.Card(content=ft.Container(content=ft.Column([ft.Text("Total Returned", size=16), ft.Text(f"₹{stats['total_returned']}", size=24, weight="bold", color=ft.colors.GREEN_400)]), padding=20)),
                ft.Card(content=ft.Container(content=ft.Column([ft.Text("Lost Money", size=16), ft.Text(f"₹{stats['lost_money']}", size=24, weight="bold", color=ft.colors.RED_400)]), padding=20)),
            ]),
            ft.Row([
                ft.Card(content=ft.Container(content=ft.Column([ft.Text("Active Loans", size=16), ft.Text(f"{stats['active_count']}", size=24, weight="bold")]), padding=20)),
                ft.Card(content=ft.Container(content=ft.Column([ft.Text("Blacklisted", size=16), ft.Text(f"{stats['blacklisted_count']}", size=24, weight="bold")]), padding=20)),
            ])
        ])

    def build_add_person():
        return ft.Column([
            ft.Text("Add New Loan", size=30, weight="bold"),
            ft.Divider(),
            ft.Row([name_input, mobile_input]),
            ft.Row([address_input, type_input]),
            ft.Row([amount_input, rate_input]),
            calc_text,
            ft.Row([date_input, due_input]),
            notes_input,
            ft.Row([
                ft.ElevatedButton("Save Loan", on_click=save_loan, bgcolor=ft.colors.BLUE_700, color=ft.colors.WHITE),
                ft.OutlinedButton("Clear", on_click=clear_form)
            ])
        ], scroll=ft.ScrollMode.AUTO, expand=True)

    def handle_action(action, loan_id, amount_given=0):
        if action == "DELETE":
            db.delete_loan(loan_id)
        elif action == "BLACKLIST":
            db.update_status(loan_id, "BLACKLISTED")
        elif action == "COMPLETE":
            db.update_status(loan_id, "COMPLETED", amount_returned=amount_given, date_returned=datetime.today().strftime('%Y-%m-%d'))
        elif action == "RESTORE":
            db.update_status(loan_id, "ACTIVE")
        render_main_layout()

    def build_loan_list(status):
        loans = db.get_loans(app_state["user_id"], status)
        list_view = ft.ListView(expand=True, spacing=10)
        list_view.controls.append(ft.Text(f"{status.capitalize()} Loans", size=30, weight="bold"))
        list_view.controls.append(ft.Divider())

        for loan in loans:
            l_id, _, name, mob, addr, amt, rate, i_type, d_given, due, notes, stat, a_ret, d_ret = loan
            
            actions = []
            if status == "ACTIVE":
                actions = [
                    ft.ElevatedButton("Complete", on_click=lambda e, lid=l_id, a=amt: handle_action("COMPLETE", lid, a), bgcolor=ft.colors.GREEN_700),
                    ft.ElevatedButton("Blacklist", on_click=lambda e, lid=l_id: handle_action("BLACKLIST", lid), bgcolor=ft.colors.ORANGE_700),
                    ft.IconButton(ft.icons.DELETE, icon_color=ft.colors.RED_400, on_click=lambda e, lid=l_id: handle_action("DELETE", lid))
                ]
            elif status == "BLACKLISTED":
                actions = [
                    ft.ElevatedButton("Restore", on_click=lambda e, lid=l_id: handle_action("RESTORE", lid)),
                    ft.IconButton(ft.icons.DELETE, icon_color=ft.colors.RED_400, on_click=lambda e, lid=l_id: handle_action("DELETE", lid))
                ]
            else: # COMPLETED
                actions = [ft.IconButton(ft.icons.DELETE, icon_color=ft.colors.RED_400, on_click=lambda e, lid=l_id: handle_action("DELETE", lid))]

            list_view.controls.append(
                ft.Card(
                    content=ft.Container(
                        padding=15,
                        content=ft.Column([
                            ft.Text(f"{name} | {mob}", weight="bold", size=18),
                            ft.Text(f"Amount: ₹{amt} | Rate: {rate}% {i_type} | Given: {d_given}"),
                            ft.Text(f"Notes: {notes}", italic=True, size=12) if notes else ft.Container(),
                            ft.Text(f"Returned: ₹{a_ret} on {d_ret}", color=ft.colors.GREEN_300) if status == "COMPLETED" else ft.Container(),
                            ft.Row(actions, alignment=ft.MainAxisAlignment.END)
                        ])
                    )
                )
            )
        if not loans:
            list_view.controls.append(ft.Text("No records found.", italic=True, color=ft.colors.GREY_500))
        
        return list_view

    # --- LAYOUT MANAGEMENT ---
    
    content_area = ft.Container(expand=True, padding=20)
    
    nav_rail = ft.NavigationRail(
        selected_index=0,
        label_type=ft.NavigationRailLabelType.ALL,
        min_width=100,
        min_extended_width=200,
        on_change=switch_view,
        destinations=[
            ft.NavigationRailDestination(icon=ft.icons.DASHBOARD, label="Dashboard"),
            ft.NavigationRailDestination(icon=ft.icons.PERSON_ADD, label="Add Loan"),
            ft.NavigationRailDestination(icon=ft.icons.ACCOUNT_BALANCE_WALLET, label="Active Loans"),
            ft.NavigationRailDestination(icon=ft.icons.CHECK_CIRCLE, label="Returned"),
            ft.NavigationRailDestination(icon=ft.icons.BLOCK, label="Blacklist"),
        ],
    )

    def render_main_layout():
        page.controls.clear()
        
        # Determine view based on nav rail index
        views = {
            0: build_dashboard,
            1: build_add_person,
            2: lambda: build_loan_list("ACTIVE"),
            3: lambda: build_loan_list("COMPLETED"),
            4: lambda: build_loan_list("BLACKLISTED")
        }
        
        idx = app_state["current_view"]
        if isinstance(idx, str): idx = 0 # Default to dashboard
        content_area.content = views[idx]()

        page.add(
            ft.Row(
                [
                    nav_rail,
                    ft.VerticalDivider(width=1),
                    content_area,
                ],
                expand=True,
            )
        )
        page.update()

    # --- AUTHENTICATION & USER SELECTION ---

    def handle_login(e):
        if user_field.value == "Bhaskar" and pass_field.value == "Satya143":
            page.controls.clear()
            page.add(user_selection_view)
            page.update()
        else:
            page.snack_bar = ft.SnackBar(ft.Text("Invalid Username or Password"), bgcolor=ft.colors.RED)
            page.snack_bar.open = True
            page.update()

    def select_user(name):
        app_state["user_id"] = name
        nav_rail.selected_index = 0
        render_main_layout()

    # Login View Elements
    user_field = ft.TextField(label="Username", width=300)
    pass_field = ft.TextField(label="Password", password=True, can_reveal_password=True, width=300)
    login_btn = ft.ElevatedButton("Login", width=300, on_click=handle_login)
    
    login_view = ft.Container(
        content=ft.Column(
            [
                ft.Icon(ft.icons.ACCOUNT_BALANCE, size=100, color=ft.colors.BLUE_500),
                ft.Text("Money Manager", size=32, weight="bold"),
                user_field,
                pass_field,
                login_btn
            ],
            alignment=ft.MainAxisAlignment.CENTER,
            horizontal_alignment=ft.CrossAxisAlignment.CENTER,
        ),
        alignment=ft.alignment.center,
        expand=True
    )

    # User Selection Elements
    user_selection_view = ft.Container(
        content=ft.Column(
            [
                ft.Text("Select Profile", size=32, weight="bold"),
                ft.ElevatedButton("Varshith Vedulla", width=300, height=60, on_click=lambda _: select_user("Varshith Vedulla")),
                ft.ElevatedButton("Vedulla Vijaya Bhaskar", width=300, height=60, on_click=lambda _: select_user("Vedulla Vijaya Bhaskar")),
            ],
            alignment=ft.MainAxisAlignment.CENTER,
            horizontal_alignment=ft.CrossAxisAlignment.CENTER,
            spacing=20
        ),
        alignment=ft.alignment.center,
        expand=True
    )

    # Start App
    page.add(login_view)
    page.update()

# Run the application
ft.app(target=main)