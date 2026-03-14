import reflex as rx
import httpx

API_URL = "http://127.0.0.1:8001"

class State(rx.State):
    usuario: str = ""
    password: str = ""
    token: str = ""
    error: str = ""
    cargando: bool = False

    async def login(self):
        self.cargando = True
        self.error = ""
        yield
        try:
            async with httpx.AsyncClient() as client:
                response = await client.post(
                    f"{API_URL}/auth/login",
                    json={
                        "usuario": self.usuario,
                        "password": self.password,
                    }
                )
            if response.status_code == 200:
                data = response.json()
                self.token = data["access_token"]
                yield rx.redirect("/dashboard")
            else:
                self.error = "Usuario o contraseña incorrectos"
        except Exception:
            self.error = "Error conectando al servidor"
        self.cargando = False

def login_page() -> rx.Component:
    return rx.center(
        rx.vstack(
            rx.heading("⚙️ App-Logic", size="8", color="blue"),
            rx.text("Ingresá para continuar", color="gray"),
            rx.input(
                placeholder="Usuario",
                value=State.usuario,
                on_change=State.set_usuario,
            ),
            rx.input(
                placeholder="Contraseña",
                type="password",
                value=State.password,
                on_change=State.set_password,
            ),
            rx.cond(
                State.error != "",
                rx.text(State.error, color="red"),
            ),
            rx.button(
                rx.cond(State.cargando, "Ingresando...", "Ingresar"),
                on_click=State.login,
                width="100%",
                color_scheme="blue",
                disabled=State.cargando,
            ),
            width="360px",
            spacing="4",
            padding="40px",
            border="1px solid #e2e6ea",
            border_radius="12px",
            background="white",
        ),
        min_height="100vh",
        background="#f1f3f6",
    )

def dashboard_page() -> rx.Component:
    return rx.center(
        rx.heading(f"Bienvenido!", size="7"),
        min_height="100vh",
    )

app = rx.App(
    theme=rx.theme(
        accent_color="blue",
        has_background=True,
    )
)

app.add_page(login_page, route="/")
app.add_page(dashboard_page, route="/dashboard")