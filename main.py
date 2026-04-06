import flet as ft

def main(page: ft.Page):
    page.title = "Chat App"

    chat = ft.ListView(expand=True)
    message_input = ft.TextField(
        hint_text="Escreve uma mensagem...",
        expand=True
    )

    def send_message(e):
        if message_input.value.strip() == "":
            return

        chat.controls.append(
            ft.Text(message_input.value)
        )
        message_input.value = ""
        page.update()

    page.add(
        ft.Column(
            expand=True,
            controls=[
                chat,
                ft.Row(
                    controls=[
                        message_input,
                        ft.IconButton(
                            icon=ft.Icons.SEND,
                            on_click=send_message
                        )
                    ]
                )
            ]
        )
    )

ft.app(target=main)