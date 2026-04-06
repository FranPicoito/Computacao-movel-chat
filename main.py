import flet as ft
from datetime import datetime


def main(page: ft.Page):
    page.title = "Chat App"
    page.window.width = 400
    page.window.height = 700
    page.padding = 0
    page.theme_mode = ft.ThemeMode.DARK
    page.bgcolor = "#0f172a"

    username = ""

    chat = ft.ListView(
        expand=True,
        spacing=10,
        auto_scroll=True,
        padding=15,
    )

    message_input = ft.TextField(
        hint_text="Escreve uma mensagem...",
        expand=True,
        border_radius=20,
        filled=True,
        on_submit=lambda e: send_message(e),
    )

    username_text = ft.Text(
        value="",
        size=16,
        weight=ft.FontWeight.BOLD,
        color=ft.Colors.WHITE,
    )

    def create_message(user, text, timestamp=None, system=False):
        time_now = timestamp if timestamp else datetime.now().strftime("%H:%M")

        if system:
            return ft.Row(
                alignment=ft.MainAxisAlignment.CENTER,
                controls=[
                    ft.Text(
                        f"[{time_now}] {text}",
                        size=12,
                        italic=True,
                        color=ft.Colors.WHITE54,
                    )
                ],
            )

        is_me = user == username

        return ft.Row(
            alignment=ft.MainAxisAlignment.END if is_me else ft.MainAxisAlignment.START,
            controls=[
                ft.Container(
                    padding=12,
                    border_radius=12,
                    bgcolor="#2563eb" if is_me else "#1e293b",
                    content=ft.Column(
                        tight=True,
                        spacing=4,
                        controls=[
                            ft.Text(
                                f"{user} · {time_now}",
                                size=10,
                                color="#cbd5e1",
                            ),
                            ft.Text(
                                text,
                                size=14,
                                color=ft.Colors.WHITE,
                            ),
                        ],
                    ),
                )
            ],
        )

    def on_message(message_data: dict):
        msg_type = message_data.get("type")
        timestamp = message_data.get("timestamp")

        if msg_type == "system":
            chat.controls.append(
                create_message(
                    user="",
                    text=message_data.get("text", ""),
                    timestamp=timestamp,
                    system=True,
                )
            )
        elif msg_type == "chat":
            chat.controls.append(
                create_message(
                    user=message_data.get("user", "Unknown"),
                    text=message_data.get("text", ""),
                    timestamp=timestamp,
                    system=False,
                )
            )

        page.update()

    def send_message(e):
        if message_input.value.strip() == "":
            return

        page.pubsub.send_all(
            {
                "type": "chat",
                "user": username,
                "text": message_input.value.strip(),
                "timestamp": datetime.now().strftime("%H:%M"),
            }
        )

        message_input.value = ""
        message_input.focus()
        page.update()

    def join_chat(e):
        nonlocal username

        entered_name = name_input.value.strip()

        if entered_name == "":
            name_input.error_text = "Introduz o teu nome."
            page.update()
            return

        name_input.error_text = None
        username = entered_name
        username_text.value = f"Olá, {username}"

        page.pubsub.subscribe(on_message)

        page.controls.clear()
        page.add(chat_view)

        page.pubsub.send_all(
            {
                "type": "system",
                "text": f"{username} entrou no chat.",
                "timestamp": datetime.now().strftime("%H:%M"),
            }
        )

        message_input.focus()
        page.update()

    name_input = ft.TextField(
        label="Nome de utilizador",
        width=300,
        autofocus=True,
        on_submit=join_chat,
    )

    join_button = ft.ElevatedButton(
        "Entrar no chat",
        on_click=join_chat,
        width=300,
        height=45,
    )

    login_view = ft.Container(
        expand=True,
        padding=20,
        content=ft.Column(
            expand=True,
            alignment=ft.MainAxisAlignment.CENTER,
            horizontal_alignment=ft.CrossAxisAlignment.CENTER,
            controls=[
                ft.Text("Chat em Tempo Real", size=28, weight=ft.FontWeight.BOLD),
                ft.Text(
                    "Introduz o teu nome para entrar",
                    size=14,
                    color=ft.Colors.WHITE70,
                ),
                name_input,
                join_button,
            ],
        ),
    )

    header = ft.Container(
        padding=ft.padding.symmetric(horizontal=16, vertical=14),
        bgcolor="#1e293b",
        content=ft.Row(
            alignment=ft.MainAxisAlignment.SPACE_BETWEEN,
            controls=[
                ft.Text(
                    "Flet Chat",
                    size=20,
                    weight=ft.FontWeight.BOLD,
                    color=ft.Colors.WHITE,
                ),
                username_text,
            ],
        ),
    )

    input_bar = ft.Container(
        padding=ft.padding.all(12),
        bgcolor="#1e293b",
        content=ft.Row(
            vertical_alignment=ft.CrossAxisAlignment.CENTER,
            controls=[
                message_input,
                ft.IconButton(
                    icon=ft.Icons.SEND,
                    icon_color=ft.Colors.BLUE_200,
                    on_click=send_message,
                ),
            ],
        ),
    )

    chat_view = ft.Column(
        expand=True,
        spacing=0,
        controls=[
            header,
            ft.Container(
                expand=True,
                content=chat,
            ),
            input_bar,
        ],
    )

    page.add(login_view)


ft.app(target=main)