import flet as ft
from datetime import datetime

def main(page: ft.Page):
    page.title = "Chat App"
    page.window.width = 400
    page.window.height = 700
    page.padding = 20
    page.theme_mode = ft.ThemeMode.DARK

    username = ""

    chat = ft.ListView(
        expand=True,
        spacing=10,
        auto_scroll=True,
    )

    message_input = ft.TextField(
        hint_text="Escreve uma mensagem...",
        expand=True,
    )

    username_text = ft.Text(
        value="",
        size=16,
        weight=ft.FontWeight.BOLD,
    )

    def send_message(e):
        if message_input.value.strip() == "":
            return

        chat.controls.append(
            create_message(username, message_input.value)
        )
        message_input.value = ""
        page.update()

    def create_message(user, text):
        time_now = datetime.now().strftime("%H:%M")

        return ft.Container(
            padding=10,
            border_radius=10,
            bgcolor=ft.Colors.BLUE_GREY_800,
            content=ft.Column(
                spacing=2,
                controls=[
                    ft.Text(
                        f"{user} · {time_now}",
                        size=10,
                        color=ft.Colors.WHITE54,
                    ),
                    ft.Text(text, size=14),
                ],
            ),
        )

    def join_chat(e):
        nonlocal username

        entered_name = name_input.value.strip()

        if entered_name == "":
            name_input.error_text = "Introduz o teu nome."
            page.update()
            return

        name_input.error_text = None
        username = entered_name
        username_text.value = f"Entraste como: {username}"

        page.controls.clear()
        page.add(chat_view)
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
    )

    login_view = ft.Column(
        expand=True,
        alignment=ft.MainAxisAlignment.CENTER,
        horizontal_alignment=ft.CrossAxisAlignment.CENTER,
        controls=[
            ft.Text("Chat em Tempo Real", size=28, weight=ft.FontWeight.BOLD),
            ft.Text("Introduz o teu nome para entrar", size=14),
            name_input,
            join_button,
        ],
    )

    chat_view = ft.Column(
        expand=True,
        controls=[
            username_text,
            ft.Divider(),
            chat,
            ft.Row(
                controls=[
                    message_input,
                    ft.IconButton(
                        icon=ft.Icons.SEND,
                        on_click=send_message,
                    ),
                ]
            ),
        ],
    )

    page.add(login_view)


ft.app(target=main)