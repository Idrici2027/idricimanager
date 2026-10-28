
import json
import hashlib
from pathlib import Path
from datetime import date, datetime

import flet as ft

APP_NAME = "IDRICI MANAGER"
DATA_DIR = Path.home() / ".idricimanager"
DATA_FILE = DATA_DIR / "finance.json"


def load_data():
    DATA_DIR.mkdir(parents=True, exist_ok=True)
    if DATA_FILE.exists():
        try:
            return json.loads(DATA_FILE.read_text(encoding="utf-8"))
        except (json.JSONDecodeError, OSError):
            pass
    return {
        "password_hash": "",
        "transactions": []
    }


data = load_data()


def save_data():
    DATA_DIR.mkdir(parents=True, exist_ok=True)
    DATA_FILE.write_text(
        json.dumps(data, ensure_ascii=False, indent=2),
        encoding="utf-8"
    )


def hash_password(password):
    return hashlib.sha256(password.encode("utf-8")).hexdigest()


def main(page: ft.Page):
    page.title = APP_NAME
    page.theme_mode = ft.ThemeMode.LIGHT
    page.padding = 16
    page.scroll = ft.ScrollMode.AUTO
    page.rtl = True
    page.bgcolor = "#F4F6FA"
    page.theme = ft.Theme(color_scheme_seed="#5B3CC4")

    def notify(message):
        page.snack_bar = ft.SnackBar(content=ft.Text(message))
        page.snack_bar.open = True
        page.update()

    def field(label, password=False, value=""):
        return ft.TextField(
            label=label,
            password=password,
            can_reveal_password=password,
            value=value,
            text_align=ft.TextAlign.RIGHT,
            border_radius=12,
        )

    def show_login():
        page.controls.clear()
        password = field("كلمة المرور", True)
        title = ft.Text(APP_NAME, size=28, weight=ft.FontWeight.BOLD,
                        color="#5B3CC4")
        message = ft.Text(
            "أنشئ كلمة مرور لحماية حسابك"
            if not data["password_hash"]
            else "أدخل كلمة المرور للدخول"
        )

        def enter(e):
            value = password.value or ""
            if len(value) < 4:
                notify("كلمة المرور يجب أن تتكون من 4 أحرف على الأقل")
                return

            if not data["password_hash"]:
                data["password_hash"] = hash_password(value)
                save_data()
                show_dashboard()
            elif hash_password(value) == data["password_hash"]:
                show_dashboard()
            else:
                notify("كلمة المرور غير صحيحة")

        page.add(
            ft.Container(
                content=ft.Column(
                    [
                        ft.Text("💰", size=52),
                        title,
                        ft.Text("إدارة أموالك بسهولة"),
                        ft.Divider(),
                        message,
                        password,
                        ft.Button("دخول", icon=ft.Icons.LOCK_OPEN,
                                  on_click=enter, width=300),
                    ],
                    horizontal_alignment=ft.CrossAxisAlignment.CENTER,
                    spacing=18,
                ),
                alignment=ft.Alignment.CENTER,
                padding=24,
                border_radius=20,
                bgcolor="white",
            )
        )
        page.update()

    def show_dashboard():
        page.controls.clear()

        income_field = field("المبلغ بالدينار الجزائري")
        note_field = field("الوصف")
        kind = ft.Dropdown(
            label="نوع العملية",
            value="expense",
            options=[
                ft.dropdown.Option("income", "مدخول"),
                ft.dropdown.Option("expense", "مصروف"),
            ],
        )
        category = ft.Dropdown(
            label="التصنيف",
            value="أخرى",
            options=[
                ft.dropdown.Option(x)
                for x in [
                    "الراتب", "منحة", "مداخيل أخرى",
                    "التسوق والأكل", "النقل", "الترفيه",
                    "الفواتير", "الصحة والرياضة",
                    "السكن", "أخرى"
                ]
            ],
        )
        transaction_date = ft.TextField(
            label="التاريخ (YYYY-MM-DD)",
            value=date.today().isoformat(),
            text_align=ft.TextAlign.RIGHT,
        )
        month_filter = ft.Dropdown(
            label="الشهر",
            value=date.today().strftime("%Y-%m"),
            options=[
                ft.dropdown.Option(
                    date.today().replace(day=1).isoformat()[:7],
                    "الشهر الحالي"
                ),
                ft.dropdown.Option("all", "كل الأشهر"),
            ],
        )

        summary = ft.Column(spacing=8)
        history = ft.Column(spacing=8)

        def refresh():
            transactions = data["transactions"]
            selected_month = month_filter.value

            visible = [
                t for t in transactions
                if selected_month == "all"
                or t["date"].startswith(selected_month)
            ]

            income = sum(
                t["amount"] for t in visible if t["kind"] == "income"
            )
            expenses = sum(
                t["amount"] for t in visible if t["kind"] == "expense"
            )

            summary.controls.clear()
            for label, amount, color in [
                ("إجمالي المداخيل", income, "#16845B"),
                ("إجمالي المصاريف", expenses, "#C0392B"),
                ("الرصيد", income - expenses, "#5B3CC4"),
            ]:
                summary.controls.append(
                    ft.Container(
                        content=ft.Column(
                            [
                                ft.Text(label, color="#555555"),
                                ft.Text(
                                    f"{amount:,.2f} دج",
                                    size=23,
                                    weight=ft.FontWeight.BOLD,
                                    color=color,
                                ),
                            ],
                            spacing=5,
                        ),
                        padding=16,
                        bgcolor="white",
                        border_radius=14,
                    )
                )

            history.controls.clear()
            for t in reversed(visible):
                color = "#16845B" if t["kind"] == "income" else "#C0392B"
                sign = "+" if t["kind"] == "income" else "-"
                history.controls.append(
                    ft.Container(
                        content=ft.Row(
                            [
                                ft.Column(
                                    [
                                        ft.Text(
                                            t.get("note") or t["category"],
                                            weight=ft.FontWeight.BOLD,
                                        ),
                                        ft.Text(
                                            f'{t["category"]} • {t["date"]}',
                                            size=12,
                                            color="#777777",
                                        ),
                                    ],
                                    expand=True,
                                    spacing=4,
                                ),
                                ft.Text(
                                    f'{sign}{t["amount"]:,.2f} دج',
                                    color=color,
                                    weight=ft.FontWeight.BOLD,
                                ),
                                ft.IconButton(
                                    icon=ft.Icons.DELETE_OUTLINE,
                                    tooltip="حذف العملية",
                                    on_click=lambda e, item=t: delete_transaction(item),
                                ),
                            ],
                            vertical_alignment=ft.CrossAxisAlignment.CENTER,
                        ),
                        bgcolor="white",
                        padding=12,
                        border_radius=12,
                    )
                )

            if not visible:
                history.controls.append(ft.Text("لا توجد عمليات لهذا الشهر"))

            page.update()

        def delete_transaction(item):
            data["transactions"].remove(item)
            save_data()
            refresh()
            notify("تم حذف العملية")

        def add_transaction(e):
            try:
                amount = float((income_field.value or "").replace(",", "."))
                if amount <= 0:
                    raise ValueError
                datetime.strptime(
                    transaction_date.value, "%Y-%m-%d"
                )
            except (ValueError, TypeError):
                notify("تحقق من المبلغ والتاريخ")
                return

            data["transactions"].append({
                "kind": kind.value,
                "category": category.value or "أخرى",
                "amount": amount,
                "note": note_field.value or "",
                "date": transaction_date.value,
            })
            save_data()
            income_field.value = ""
            note_field.value = ""
            refresh()
            notify("تم حفظ العملية بنجاح")

        def logout(e):
            show_login()

        page.add(
            ft.Row(
                [
                    ft.Column(
                        [
                            ft.Text(APP_NAME, size=22,
                                    weight=ft.FontWeight.BOLD,
                                    color="#5B3CC4"),
                            ft.Text("إدارة مالية شخصية"),
                        ],
                        expand=True,
                        spacing=3,
                    ),
                    ft.IconButton(
                        icon=ft.Icons.LOGOUT,
                        tooltip="تسجيل الخروج",
                        on_click=logout,
                    ),
                ]
            ),
            ft.Divider(),
            month_filter,
            summary,
            ft.Text("إضافة عملية", size=20, weight=ft.FontWeight.BOLD),
            kind,
            category,
            income_field,
            note_field,
            transaction_date,
            ft.Button(
                "حفظ العملية",
                icon=ft.Icons.ADD_CIRCLE,
                on_click=add_transaction,
            ),
            ft.Text("سجل العمليات", size=20, weight=ft.FontWeight.BOLD),
            history,
        )
        month_filter.on_select = lambda e: refresh()
        refresh()

    show_login()


ft.run(main)
