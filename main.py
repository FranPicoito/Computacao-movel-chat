import flet as ft
from datetime import datetime
import uuid


async def main(page: ft.Page):
    client_id = str(uuid.uuid4())

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
    room_messages = {"Geral": []}
    unread_counts = {"Geral": 0}
    editing_message_id = None
    search_query = ""

    pending_uploads = {}
    current_picker = None

    sidebar_open = False
    MOBILE_BREAKPOINT = 768

    chat = ft.ListView(
        expand=True,
        spacing=10,
        auto_scroll=True,
        padding=15,
    )

    room_list = ft.Column(
        spacing=8,
        scroll=ft.ScrollMode.AUTO,
    )

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
        on_submit=lambda e: add_room(e),
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

    upload_status_text = ft.Text(
        value="",
        size=12,
        color=ft.Colors.WHITE70,
    )

    def is_mobile():
        return (page.width or 0) < MOBILE_BREAKPOINT

    def open_sidebar(e=None):
        nonlocal sidebar_open
        if is_mobile():
            sidebar_open = True
            update_layout()

    def close_sidebar(e=None):
        nonlocal sidebar_open
        sidebar_open = False
        update_layout()

    def update_layout():
        mobile = is_mobile()

        menu_button.visible = mobile
        sidebar_close_button.visible = mobile

        desktop_sidebar.visible = not mobile

        mobile_sidebar.visible = mobile and sidebar_open
        sidebar_overlay.visible = mobile and sidebar_open

        if mobile:
            username_text.size = 13
            recipient_dropdown.width = page.width - 40 if page.width and page.width < 500 else 220
        else:
            username_text.size = 16
            recipient_dropdown.width = 220

        page.update()

    def on_page_resize(e):
        nonlocal sidebar_open
        if not is_mobile():
            sidebar_open = False
        update_layout()

    page.on_resized = on_page_resize

    def open_file_url(url: str):
        page.launch_url(url, web_popup_window=True)

    def get_file_icon(file_name: str):
        lower = file_name.lower()
        if lower.endswith((".png", ".jpg", ".jpeg", ".gif", ".webp")):
            return ft.Icons.IMAGE
        if lower.endswith(".pdf"):
            return ft.Icons.PICTURE_AS_PDF
        if lower.endswith((".doc", ".docx")):
            return ft.Icons.DESCRIPTION
        if lower.endswith((".xls", ".xlsx", ".csv")):
            return ft.Icons.TABLE_CHART
        if lower.endswith((".zip", ".rar", ".7z")):
            return ft.Icons.FOLDER_ZIP
        return ft.Icons.ATTACH_FILE

    def on_search_change(e):
        nonlocal search_query
        search_query = (e.control.value or "").strip().lower()
        render_current_room_messages()

    def clear_search(e=None):
        nonlocal search_query
        search_query = ""
        search_input.value = ""
        render_current_room_messages()
        page.update()

    search_input = ft.TextField(
        hint_text="Pesquisar mensagens nesta sala...",
        prefix_icon=ft.Icons.SEARCH,
        dense=True,
        filled=True,
        expand=True,
        on_change=on_search_change,
    )

    def message_exists(message_id):
        if not message_id:
            return False
        for messages in room_messages.values():
            for msg in messages:
                if msg.get("id") == message_id:
                    return True
        return False

    def find_message_by_id(message_id):
        for _, messages in room_messages.items():
            for msg in messages:
                if msg.get("id") == message_id:
                    return msg
        return None

    def add_message_locally(message_data):
        room = message_data.get("room", "Geral")
        if room not in room_messages:
            room_messages[room] = []

        msg_id = message_data.get("id")
        if msg_id and message_exists(msg_id):
            return

        room_messages[room].append(message_data)

    def apply_local_edit(message_id, new_text):
        updated = False

        for messages in room_messages.values():
            for msg in messages:
                if msg.get("id") == message_id:
                    msg["text"] = new_text
                    msg["edited"] = True
                    updated = True
                    break
            if updated:
                break

        if updated:
            render_current_room_messages()
            page.update()

        return updated

    def start_edit_message(message_id):
        nonlocal editing_message_id

        msg = find_message_by_id(message_id)
        if not msg or msg.get("deleted"):
            return
        if msg.get("user") != username:
            return
        if msg.get("type") != "chat":
            return

        editing_message_id = message_id
        message_input.value = msg.get("text", "")
        message_input.hint_text = "Editar mensagem..."
        message_input.focus()
        page.update()

    def cancel_edit():
        nonlocal editing_message_id
        editing_message_id = None
        message_input.value = ""
        message_input.hint_text = "Escreve uma mensagem..."
        message_input.focus()
        page.update()

    def delete_message(message_id):
        msg = find_message_by_id(message_id)
        if not msg:
            return
        if msg.get("user") != username:
            return

        msg["deleted"] = True
        render_current_room_messages()
        page.update()

        page.pubsub.send_all(
            {
                "type": "message_deleted",
                "id": message_id,
                "room": msg.get("room"),
                "sender_session": client_id,
            }
        )

    def toggle_reaction(message_id, emoji):
        msg = find_message_by_id(message_id)
        if not msg or msg.get("deleted"):
            return

        reactions = msg.setdefault("reactions", {})
        users = reactions.setdefault(emoji, [])

        if username in users:
            users.remove(username)
            if not users:
                del reactions[emoji]
        else:
            users.append(username)

        msg["reactions"] = {k: list(v) for k, v in reactions.items()}

        render_current_room_messages()
        page.update()

        page.pubsub.send_all(
            {
                "type": "reaction_updated",
                "id": message_id,
                "reactions": {k: list(v) for k, v in msg["reactions"].items()},
                "sender_session": client_id,
            }
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

    def build_reaction_bar(message_data):
        message_id = message_data.get("id")
        reactions = message_data.get("reactions", {})
        available_emojis = ["👍", "❤️", "😂", "😮"]

        chips = []
        for emoji in available_emojis:
            count = len(reactions.get(emoji, []))
            label = f"{emoji} {count}" if count > 0 else emoji

            chips.append(
                ft.OutlinedButton(
                    content=ft.Text(label, size=13, color=ft.Colors.WHITE),
                    height=28,
                    width=58,
                    style=ft.ButtonStyle(
                        padding=ft.Padding(0, 0, 0, 0),
                        side={ft.ControlState.DEFAULT: ft.BorderSide(1, ft.Colors.WHITE24)},
                        shape=ft.RoundedRectangleBorder(radius=8),
                    ),
                    on_click=lambda e, em=emoji, msg_id=message_id: toggle_reaction(msg_id, em),
                )
            )

        return ft.Row(spacing=4, wrap=True, controls=chips)

    def create_file_content(message_data):
        file_name = message_data.get("file_name", "Ficheiro")
        file_url = message_data.get("file_url", "")
        file_size = message_data.get("file_size", 0)

        size_text = ""
        if isinstance(file_size, (int, float)) and file_size > 0:
            if file_size >= 1024 * 1024:
                size_text = f"{file_size / (1024 * 1024):.1f} MB"
            elif file_size >= 1024:
                size_text = f"{file_size / 1024:.1f} KB"
            else:
                size_text = f"{int(file_size)} B"

        controls = [
            ft.Row(
                spacing=10,
                vertical_alignment=ft.CrossAxisAlignment.CENTER,
                controls=[
                    ft.Icon(get_file_icon(file_name), color=ft.Colors.WHITE, size=22),
                    ft.Column(
                        spacing=2,
                        controls=[
                            ft.Text(file_name, color=ft.Colors.WHITE, weight=ft.FontWeight.BOLD),
                            ft.Text(
                                size_text if size_text else "Ficheiro enviado",
                                color=ft.Colors.WHITE70,
                                size=11,
                            ),
                        ],
                    ),
                ],
            )
        ]

        if file_url:
            controls.append(
                ft.Row(
                    spacing=10,
                    wrap=True,
                    controls=[
                        ft.TextButton(
                            "Abrir ficheiro",
                            on_click=lambda e, url=file_url: page.launch_url(
                                url,
                                web_popup_window=True,
                            ),
                        ),
                        ft.TextButton(
                            "Download",
                            on_click=lambda e, url=file_url: page.launch_url(
                                url,
                                web_popup_window=True,
                            ),
                        ),
                    ]
                )
            )

        if file_name.lower().endswith((".png", ".jpg", ".jpeg", ".gif", ".webp")) and file_url:
            controls.append(
                ft.Container(
                    margin=ft.margin.only(top=6),
                    content=ft.Image(
                        src=file_url,
                        width=220,
                        height=160,
                        fit="contain",
                        border_radius=10,
                    ),
                )
            )

        return ft.Column(spacing=6, controls=controls)

    def create_message(message_data):
        sender = message_data.get("user", "Sistema")
        text = message_data.get("text", "")
        timestamp = message_data.get("timestamp", "")
        private = message_data.get("private", False)
        recipient = message_data.get("recipient")
        edited = message_data.get("edited", False)
        deleted = message_data.get("deleted", False)
        message_id = message_data.get("id")
        msg_type = message_data.get("type", "chat")

        if deleted:
            text = "Mensagem apagada"

        meta_text = sender
        if private and recipient:
            meta_text += f" → {recipient} (privada)"
        if edited and not deleted and msg_type == "chat":
            meta_text += " · editada"

        bubble_color = "#1d4ed8" if sender == username else "#1e293b"
        if msg_type == "system":
            bubble_color = "#334155"

        action_buttons = []
        if msg_type in ["chat", "file"] and not deleted and sender == username:
            action_buttons = [
                ft.IconButton(
                    icon=ft.Icons.DELETE,
                    tooltip="Apagar",
                    icon_size=16,
                    icon_color=ft.Colors.WHITE70,
                    on_click=lambda e, msg_id=message_id: delete_message(msg_id),
                ),
            ]

        if msg_type == "chat" and not deleted and sender == username:
            action_buttons.insert(
                0,
                ft.IconButton(
                    icon=ft.Icons.EDIT,
                    tooltip="Editar",
                    icon_size=16,
                    icon_color=ft.Colors.WHITE70,
                    on_click=lambda e, msg_id=message_id: start_edit_message(msg_id),
                ),
            )

        bottom_row_controls = []
        if msg_type in ["chat", "file"] and not deleted:
            bottom_row_controls.append(
                ft.Container(expand=True, content=build_reaction_bar(message_data))
            )

        if action_buttons:
            bottom_row_controls.append(ft.Row(spacing=0, tight=True, controls=action_buttons))

        content_controls = [
            ft.Row(
                alignment=ft.MainAxisAlignment.SPACE_BETWEEN,
                controls=[
                    ft.Text(meta_text, size=12, color=ft.Colors.WHITE70),
                    ft.Text(timestamp, size=11, color=ft.Colors.WHITE54),
                ],
            )
        ]

        if msg_type == "file" and not deleted:
            content_controls.append(create_file_content(message_data))
        else:
            content_controls.append(
                ft.Text(
                    text,
                    size=15,
                    color=ft.Colors.WHITE if not deleted else ft.Colors.WHITE54,
                    italic=deleted,
                    selectable=True,
                )
            )

        if bottom_row_controls:
            content_controls.append(
                ft.Row(
                    alignment=ft.MainAxisAlignment.SPACE_BETWEEN,
                    vertical_alignment=ft.CrossAxisAlignment.CENTER,
                    controls=bottom_row_controls,
                )
            )

        max_bubble_width = 430
        if page.width:
            if is_mobile():
                max_bubble_width = max(220, page.width - 40)
            else:
                max_bubble_width = min(430, max(280, int(page.width * 0.5)))

        message_card = ft.Container(
            bgcolor=bubble_color,
            border_radius=14,
            padding=10,
            content=ft.Column(spacing=6, tight=True, controls=content_controls),
        )

        return ft.Row(
            alignment=ft.MainAxisAlignment.END if sender == username else ft.MainAxisAlignment.START,
            controls=[ft.Container(width=max_bubble_width, content=message_card)],
        )

    def refresh_room_list():
        room_list.controls.clear()

        for room in rooms:
            selected = room == current_room
            unread = unread_counts.get(room, 0)

            room_button = ft.Container(
                bgcolor="#2563eb" if selected else "#1e293b",
                border_radius=10,
                padding=10,
                on_click=lambda e, r=room: change_room(r),
                content=ft.Row(
                    alignment=ft.MainAxisAlignment.SPACE_BETWEEN,
                    vertical_alignment=ft.CrossAxisAlignment.CENTER,
                    controls=[
                        ft.Text(room, color=ft.Colors.WHITE, expand=True),
                        ft.Container(
                            visible=unread > 0,
                            bgcolor="#ef4444",
                            border_radius=999,
                            padding=ft.padding.symmetric(horizontal=8, vertical=2),
                            content=ft.Text(
                                str(unread),
                                color=ft.Colors.WHITE,
                                size=11,
                                weight=ft.FontWeight.BOLD,
                            ),
                        ),
                    ],
                ),
            )

            room_list.controls.append(room_button)

    def render_current_room_messages():
        chat.controls.clear()

        query = search_query.strip().lower()

        for message_data in room_messages.get(current_room, []):
            sender = message_data.get("user", "Unknown")
            recipient = message_data.get("recipient")
            private = message_data.get("private", False)

            if private and username not in [sender, recipient]:
                continue

            if query:
                text = str(message_data.get("text", "")).lower()
                file_name = str(message_data.get("file_name", "")).lower()
                sender_name = str(sender).lower()

                searchable_content = f"{text} {file_name} {sender_name}"

                if query not in searchable_content:
                    continue

            chat.controls.append(create_message(message_data))

        page.update()

    def change_room(room_name):
        nonlocal current_room, search_query
        current_room = room_name
        unread_counts[room_name] = 0
        search_query = ""
        search_input.value = ""
        room_title.value = f"Sala: {current_room}"
        refresh_room_list()
        render_current_room_messages()

        if is_mobile():
            close_sidebar()

        page.update()

    def add_room(e):
        room_name = new_room_input.value.strip()
        if not room_name:
            return

        if room_name not in rooms:
            rooms.append(room_name)

        if room_name not in room_messages:
            room_messages[room_name] = []

        if room_name not in unread_counts:
            unread_counts[room_name] = 0

        refresh_room_list()
        page.update()

        page.pubsub.send_all(
            {
                "type": "room_created",
                "room_name": room_name,
                "created_by": username,
                "sender_session": client_id,
            }
        )

        new_room_input.value = ""
        page.update()

    def on_message(message_data: dict):
        msg_type = message_data.get("type")
        sender_session = message_data.get("sender_session")

        if sender_session == client_id:
            return

        if msg_type == "room_created":
            room_name = message_data.get("room_name", "").strip()

            if room_name and room_name not in rooms:
                rooms.append(room_name)

            if room_name and room_name not in room_messages:
                room_messages[room_name] = []

            if room_name and room_name not in unread_counts:
                unread_counts[room_name] = 0

            refresh_room_list()
            page.update()
            return

        if msg_type == "presence":
            joined_user = message_data.get("user", "").strip()
            if joined_user:
                add_online_user(joined_user)

                if username and joined_user != username:
                    page.pubsub.send_all(
                        {
                            "type": "presence_ack",
                            "user": username,
                            "target": joined_user,
                            "sender_session": client_id,
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

        if msg_type == "message_edited":
            message_id = message_data.get("id")
            new_text = message_data.get("text", "").strip()
            apply_local_edit(message_id, new_text)
            return

        if msg_type == "reaction_updated":
            message_id = message_data.get("id")
            new_reactions = message_data.get("reactions", {})

            msg = find_message_by_id(message_id)
            if not msg or msg.get("deleted"):
                return

            msg["reactions"] = new_reactions
            render_current_room_messages()
            page.update()
            return

        if msg_type == "message_deleted":
            message_id = message_data.get("id")

            for messages in room_messages.values():
                for msg in messages:
                    if msg.get("id") == message_id:
                        msg["deleted"] = True
                        break

            render_current_room_messages()
            page.update()
            return

        if msg_type in ["system", "chat", "file"]:
            msg_id = message_data.get("id")
            if msg_id and message_exists(msg_id):
                return

            room = message_data.get("room", "Geral")
            private = message_data.get("private", False)
            sender = message_data.get("user", "Unknown")
            recipient = message_data.get("recipient")

            if room not in room_messages:
                room_messages[room] = []

            if room not in unread_counts:
                unread_counts[room] = 0

            room_messages[room].append(message_data)

            if private and username not in [sender, recipient]:
                return

            if room != current_room:
                unread_counts[room] += 1
                refresh_room_list()
                page.update()
                return

            chat.controls.append(create_message(message_data))
            page.update()

    def send_message(e):
        nonlocal editing_message_id

        text = message_input.value.strip()
        if not text or not username:
            return

        if editing_message_id is not None:
            apply_local_edit(editing_message_id, text)

            msg = find_message_by_id(editing_message_id)
            if msg:
                page.pubsub.send_all(
                    {
                        "type": "message_edited",
                        "id": editing_message_id,
                        "text": text,
                        "room": msg.get("room"),
                        "edited": True,
                        "editor": username,
                        "sender_session": client_id,
                    }
                )

            editing_message_id = None
            message_input.value = ""
            message_input.hint_text = "Escreve uma mensagem..."
            message_input.focus()
            page.update()
            return

        selected_recipient = recipient_dropdown.value or "Todos"
        is_private = selected_recipient != "Todos"

        new_message = {
            "type": "chat",
            "id": str(uuid.uuid4()),
            "user": username,
            "text": text,
            "room": current_room,
            "timestamp": datetime.now().strftime("%H:%M"),
            "private": is_private,
            "recipient": selected_recipient if is_private else None,
            "edited": False,
            "deleted": False,
            "reactions": {},
            "sender_session": client_id,
        }

        add_message_locally(new_message)

        if current_room == new_message["room"]:
            if not new_message["private"] or username in [new_message["user"], new_message["recipient"]]:
                chat.controls.append(create_message(new_message))

        message_input.value = ""
        message_input.focus()
        page.update()

        page.pubsub.send_all(new_message)

    def on_file_upload(e: ft.FilePickerUploadEvent):
        file_name = e.file_name

        if e.error:
            upload_status_text.value = f"Erro no upload de {file_name}: {e.error}"
            page.update()
            return

        if e.progress is not None and e.progress < 1:
            upload_status_text.value = f"A enviar {file_name}: {int(e.progress * 100)}%"
            page.update()
            return

        info = pending_uploads.get(file_name)
        if not info:
            if not pending_uploads:
                upload_status_text.value = ""
                page.update()
            return

        file_message = {
            "type": "file",
            "id": str(uuid.uuid4()),
            "user": username,
            "room": info["room"],
            "timestamp": datetime.now().strftime("%H:%M"),
            "private": info["private"],
            "recipient": info["recipient"],
            "edited": False,
            "deleted": False,
            "reactions": {},
            "file_name": info["original_name"],
            "file_url": info["public_url"],
            "file_size": info["size"],
            "sender_session": client_id,
        }

        add_message_locally(file_message)

        if current_room == file_message["room"]:
            if not file_message["private"] or username in [file_message["user"], file_message["recipient"]]:
                chat.controls.append(create_message(file_message))

        page.pubsub.send_all(file_message)

        pending_uploads.pop(file_name, None)
        upload_status_text.value = "Upload concluído." if not pending_uploads else "A terminar uploads..."
        page.update()

    async def send_file(e):
        nonlocal current_picker

        if not username:
            return

        selected_recipient = recipient_dropdown.value or "Todos"
        is_private = selected_recipient != "Todos"

        current_picker = ft.FilePicker(on_upload=on_file_upload)

        files = await current_picker.pick_files(
            allow_multiple=True,
            dialog_title="Escolher ficheiros",
        )

        if not files:
            upload_status_text.value = ""
            page.update()
            return

        pending_uploads.clear()
        upload_list = []

        for f in files:
            safe_name = f"{uuid.uuid4()}_{f.name}"
            relative_path = f"{client_id}/{safe_name}"
            public_url = f"/uploads/{relative_path}"
            upload_url = page.get_upload_url(relative_path, 600)

            pending_uploads[f.name] = {
                "original_name": f.name,
                "public_url": public_url,
                "room": current_room,
                "private": is_private,
                "recipient": selected_recipient if is_private else None,
                "size": getattr(f, "size", 0),
            }

            upload_list.append(
                ft.FilePickerUploadFile(
                    name=f.name,
                    upload_url=upload_url,
                )
            )

        upload_status_text.value = "A enviar ficheiro(s)..."
        page.update()

        await current_picker.upload(upload_list)

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
        render_current_room_messages()
        update_layout()

        page.pubsub.send_all(
            {
                "type": "presence",
                "user": username,
                "sender_session": client_id,
            }
        )

        system_message = {
            "type": "system",
            "id": str(uuid.uuid4()),
            "user": "Sistema",
            "text": f"{username} entrou na sala {current_room}.",
            "room": current_room,
            "timestamp": datetime.now().strftime("%H:%M"),
            "sender_session": client_id,
        }

        add_message_locally(system_message)
        if current_room == system_message["room"]:
            chat.controls.append(create_message(system_message))

        page.pubsub.send_all(system_message)

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
                ft.Text(
                    "Chat em Tempo Real",
                    size=28,
                    weight=ft.FontWeight.BOLD,
                    color=ft.Colors.WHITE,
                ),
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

    sidebar_close_button = ft.IconButton(
        icon=ft.Icons.CLOSE,
        icon_color=ft.Colors.WHITE,
        tooltip="Fechar menu",
        visible=False,
        on_click=close_sidebar,
    )

    def build_sidebar_content():
        return ft.Column(
            expand=True,
            controls=[
                ft.Row(
                    alignment=ft.MainAxisAlignment.SPACE_BETWEEN,
                    controls=[
                        ft.Text("Salas", size=20, weight=ft.FontWeight.BOLD, color=ft.Colors.WHITE),
                        sidebar_close_button,
                    ],
                ),
                ft.Row(
                    controls=[
                        new_room_input,
                        ft.IconButton(
                            icon=ft.Icons.ADD,
                            on_click=add_room,
                            icon_color=ft.Colors.WHITE,
                        ),
                    ]
                ),
                ft.Divider(),
                room_list,
            ],
        )

    desktop_sidebar = ft.Container(
        width=240,
        bgcolor="#111827",
        padding=12,
        visible=True,
        content=build_sidebar_content(),
    )

    mobile_sidebar = ft.Container(
        width=260,
        left=0,
        top=0,
        bottom=0,
        bgcolor="#111827",
        padding=12,
        visible=False,
        content=ft.SafeArea(content=build_sidebar_content()),
    )

    sidebar_overlay = ft.Container(
        expand=True,
        bgcolor="#00000088",
        visible=False,
        on_click=close_sidebar,
    )

    menu_button = ft.IconButton(
        icon=ft.Icons.MENU,
        icon_color=ft.Colors.WHITE,
        tooltip="Abrir menu",
        visible=False,
        on_click=open_sidebar,
    )

    header = ft.Container(
        padding=ft.padding.symmetric(horizontal=16, vertical=14),
        bgcolor="#1e293b",
        content=ft.Column(
            spacing=8,
            controls=[
                ft.Row(
                    alignment=ft.MainAxisAlignment.SPACE_BETWEEN,
                    vertical_alignment=ft.CrossAxisAlignment.CENTER,
                    controls=[
                        ft.Row(
                            spacing=8,
                            vertical_alignment=ft.CrossAxisAlignment.CENTER,
                            controls=[
                                menu_button,
                                room_title,
                            ],
                        ),
                        username_text,
                    ],
                ),
                online_users_text,
                ft.Row(
                    controls=[
                        search_input,
                        ft.IconButton(
                            icon=ft.Icons.CLOSE,
                            tooltip="Limpar pesquisa",
                            icon_color=ft.Colors.WHITE70,
                            on_click=clear_search,
                        ),
                    ],
                ),
            ],
        ),
    )

    input_bar = ft.Container(
        padding=ft.padding.all(12),
        bgcolor="#1e293b",
        content=ft.Column(
            spacing=10,
            controls=[
                ft.Row(controls=[recipient_dropdown]),
                upload_status_text,
                ft.Row(
                    vertical_alignment=ft.CrossAxisAlignment.CENTER,
                    controls=[
                        message_input,
                        ft.IconButton(
                            icon=ft.Icons.ATTACH_FILE,
                            tooltip="Enviar ficheiro",
                            icon_color=ft.Colors.WHITE,
                            on_click=send_file,
                        ),
                        ft.IconButton(
                            icon=ft.Icons.CLOSE,
                            tooltip="Cancelar edição",
                            icon_color=ft.Colors.RED_200,
                            on_click=lambda e: cancel_edit(),
                        ),
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

    main_content = ft.Row(
        expand=True,
        spacing=0,
        controls=[
            desktop_sidebar,
            chat_area,
        ],
    )

    chat_view = ft.Stack(
        expand=True,
        controls=[
            main_content,
            sidebar_overlay,
            mobile_sidebar,
        ],
    )

    page.add(login_view)


ft.app(
    target=main,
    assets_dir="assets",
    upload_dir="assets/uploads",
)