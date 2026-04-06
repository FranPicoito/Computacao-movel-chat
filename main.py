import flet as ft
from datetime import datetime


def main(page: ft.Page):
    page.title = "Chat App"
    page.window.width = 900
    page.window.height = 700
    page.padding = 0
    page.theme_mode = ft.ThemeMode.DARK
    page.bgcolor = "#0f172a"

    username = ""
    rooms = ["Geral"]
    current_room = "Geral"

    chat = ft.ListView(
        expand=True,
        spacing=10,
        auto_scroll=True,
        padding=15,
    )

    room_list = ft.Column(spacing=8, scroll=ft.ScrollMode.AUTO)
    room_title = ft.Text(
        value="Sala: Geral",
        size=18,
        weight=ft.FontWeight.BOLD,
        color=ft.Colors.WHITE,
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

    new_room_input = ft.TextField(
        hint_text="Nova sala...",
        dense=True,
        expand=True,
    )

    def create_message(user, text, room, timestamp=None, system=False):
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

    def refresh_room_list():
        room_list.controls.clear()

        for room in rooms:
            selected = room == current_room

            room_button = ft.Container(
                bgcolor="#2563eb" if selected else "#1e293b",
                border_radius=10,
                padding=10,
                content=ft.Text(room, color=ft.Colors.WHITE),
                on_click=lambda e, r=room: change_room(r),
            )
            room_list.controls.append(room_button)

        page.update()

    def change_room(room_name):
        nonlocal current_room
        current_room = room_name
        room_title.value = f"Sala: {current_room}"
        chat.controls.clear()
        refresh_room_list()
        page.update()

    def add_room(e):
        room_name = new_room_input.value.strip()

        if room_name == "":
            return

        if room_name not in rooms:
            rooms.append(room_name)

        new_room_input.value = ""
        refresh_room_list()

    def on_message(message_data: dict):
        msg_type = message_data.get("type")
        timestamp = message_data.get("timestamp")
        room = message_data.get("room", "Geral")

        if room != current_room:
            return

        if msg_type == "system":
            chat.controls.append(
                create_message(
                    user="",
                    text=message_data.get("text", ""),
                    room=room,
                    timestamp=timestamp,
                    system=True,
                )
            )
        elif msg_type == "chat":
            chat.controls.append(
                create_message(
                    user=message_data.get("user", "Unknown"),
                    text=message_data.get("text", ""),
                    room=room,
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
                "room": current_room,
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

        refresh_room_list()

        page.pubsub.send_all(
            {
                "type": "system",
                "text": f"{username} entrou na sala {current_room}.",
                "room": current_room,
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

    sidebar = ft.Container(
        width=220,
        bgcolor="#111827",
        padding=12,
        content=ft.Column(
            expand=True,
            controls=[
                ft.Text("Salas", size=20, weight=ft.FontWeight.BOLD),
                ft.Row(
                    controls=[
                        new_room_input,
                        ft.IconButton(
                            icon=ft.Icons.ADD,
                            on_click=add_room,
                        ),
                    ]
                ),
                ft.Divider(),
                room_list,
            ],
        ),
    )

    header = ft.Container(
        padding=ft.padding.symmetric(horizontal=16, vertical=14),
        bgcolor="#1e293b",
        content=ft.Row(
            alignment=ft.MainAxisAlignment.SPACE_BETWEEN,
            controls=[
                room_title,
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

    chat_area = ft.Column(
        expand=True,
        spacing=0,
        controls=[
            header,
            ft.Container(expand=True, content=chat),
            input_bar,
        ],
    )

    chat_view = ft.Row(
        expand=True,
        spacing=0,
        controls=[
            sidebar,
            chat_area,
        ],
    )

    page.add(login_view)


ft.app(target=main)