import reflex as rx
from App_Logic.state import State

def page() -> rx.Component:
    return rx.center(
        rx.vstack(
            rx.heading("⚙️ App-Logic", size="8", color="blue"),
            rx.text("Ingresá para continuar", color="gray"),
            rx.input(placeholder="Usuario", id="usuario"),
            rx.input(placeholder="Contraseña", type="password", id="password"),
            rx.button("Ingresar", width="100%", color_scheme="blue"),
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