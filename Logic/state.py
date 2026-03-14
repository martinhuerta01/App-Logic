import reflex as rx
from typing import Optional

class State(rx.State):
    usuario: str = ""
    token: str = ""
    pagina: str = "login"

    def logout(self):
        self.usuario = ""
        self.token = ""
        self.pagina = "login"
        return rx.redirect("/")