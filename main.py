import flet as ft
from datetime import datetime


def main(page: ft.Page):
    page.title = "Chat App"
    page.window.width = 950
    page.window.height = 700
    page.padding = 0
    page.theme_mode = ft.ThemeMode.DARK
    page.bgcolor = "#0f172a"

    username = ""
    rooms = ["Geral"]
    current_room = "Geral"
    online_users = []

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

    recipient_dropdown = ft.Dropdown(
        label="Destinatário",
        value="Todos",
        width=220,
        options=[ft.dropdown.Option("Todos")],
    )

    online_users_text = ft.Text(
        value="Online: -",
        size=12,
        color=ft.Colors.WHITE70,
    )

    def add_online_user(user):
        if user and user not in online_users:
            online_users.append(user)

    def refresh_recipient_dropdown():
        current_value = recipient_dropdown.value or "Todos"
        user_values = sorted(set(u for u in online_users if u and u != username))

        recipient_dropdown.options = [ft.dropdown.Option("Todos")] + [
            ft.dropdown.Option(user) for user in user_values
        ]

        valid_values = ["Todos"] + user_values
        recipient_dropdown.value = current_value if current_value in valid_values else "Todos"

    def refresh_online_users_text():
        visible_users = sorted(set(u for u in online_users if u))
        online_users_text.value = (
            f"Online: {', '.join(visible_users)}" if visible_users else "Online: -"
        )

    def refresh_presence_ui():
        refresh_recipient_dropdown()
        refresh_online_users_text()
        page.update()

    def create_message(
        user,
        text,
        room,
        timestamp=None,
        system=False,
        private=False,
        recipient=None,
    ):
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

        privacy_label = ""
        if private:
            privacy_label = (
                f"Privada para {recipient}" if is_me else f"Privada de {user}"
            )

        return ft.Row(
            alignment=ft.MainAxisAlignment.END if is_me else ft.MainAxisAlignment.START,
            controls=[
                ft.Container(
                    padding=12,
                    border_radius=12,
                    bgcolor="#7c3aed" if private else ("#2563eb" if is_me else "#1e293b"),
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
                            ft.Text(
                                privacy_label,
                                size=10,
                                italic=True,
                                color="#e2e8f0",
                                visible=private,
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

    def change_room(room_name):
        nonlocal current_room
        current_room = room_name
        room_title.value = f"Sala: {current_room}"
        chat.controls.clear()
        refresh_room_list()
        page.update()

    def add_room(e):
        room_name = new_room_input.value.strip()
        if not room_name:
            return

        page.pubsub.send_all(
            {
                "type": "room_created",
                "room_name": room_name,
                "created_by": username,
            }
        )

        new_room_input.value = ""
        page.update()

    def on_message(message_data: dict):
        msg_type = message_data.get("type")

        if msg_type == "room_created":
            room_name = message_data.get("room_name", "").strip()

            if room_name and room_name not in rooms:
                rooms.append(room_name)
                refresh_room_list()
                page.update()
            return

        if msg_type == "presence":
            joined_user = message_data.get("user", "").strip()
            if joined_user:
                add_online_user(joined_user)

                # responder ao utilizador novo com a nossa presença
                if username and joined_user != username:
                    page.pubsub.send_all(
                        {
                            "type": "presence_ack",
                            "user": username,
                            "target": joined_user,
                        }
                    )

                refresh_presence_ui()
            return

        if msg_type == "presence_ack":
            ack_user = message_data.get("user", "").strip()
            target = message_data.get("target", "").strip()

            if target == username and ack_user:
                add_online_user(ack_user)
                refresh_presence_ui()
            return

        timestamp = message_data.get("timestamp")
        room = message_data.get("room", "Geral")
        private = message_data.get("private", False)
        sender = message_data.get("user", "Unknown")
        recipient = message_data.get("recipient")

        if room != current_room:
            return

        if private and username not in [sender, recipient]:
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
                    user=sender,
                    text=message_data.get("text", ""),
                    room=room,
                    timestamp=timestamp,
                    system=False,
                    private=private,
                    recipient=recipient,
                )
            )

        page.update()

    def send_message(e):
        text = message_input.value.strip()
        if not text or not username:
            return

        selected_recipient = recipient_dropdown.value or "Todos"
        is_private = selected_recipient != "Todos"

        page.pubsub.send_all(
            {
                "type": "chat",
                "user": username,
                "text": text,
                "room": current_room,
                "timestamp": datetime.now().strftime("%H:%M"),
                "private": is_private,
                "recipient": selected_recipient if is_private else None,
            }
        )

        message_input.value = ""
        message_input.focus()
        page.update()

    def join_chat(e):
        nonlocal username

        entered_name = name_input.value.strip()
        if not entered_name:
            name_input.error_text = "Introduz o teu nome."
            page.update()
            return

        name_input.error_text = None
        username = entered_name
        username_text.value = f"Olá, {username}"

        add_online_user(username)

        page.pubsub.subscribe(on_message)

        page.controls.clear()
        page.add(chat_view)

        refresh_room_list()
        refresh_presence_ui()

        # anuncia que entrou
        page.pubsub.send_all(
            {
                "type": "presence",
                "user": username,
            }
        )

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
        width=240,
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
        content=ft.Column(
            spacing=4,
            controls=[
                ft.Row(
                    alignment=ft.MainAxisAlignment.SPACE_BETWEEN,
                    controls=[
                        room_title,
                        username_text,
                    ],
                ),
                online_users_text,
            ],
        ),
    )

    input_bar = ft.Container(
        padding=ft.padding.all(12),
        bgcolor="#1e293b",
        content=ft.Column(
            spacing=10,
            controls=[
                ft.Row(
                    controls=[recipient_dropdown]
                ),
                ft.Row(
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


ft.app(target=main, view=ft.AppView.WEB_BROWSER)