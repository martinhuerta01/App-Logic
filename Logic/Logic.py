import reflex as rx
import httpx

API_URL = "http://127.0.0.1:8001"

class State(rx.State):
    usuario: str = ""
    password: str = ""
    token: str = ""
    error: str = ""
    cargando: bool = False
    pagina: str = "registro"
    empleados: list[dict] = []
    nombres_empleados: list[str] = []
    empleado_sel: str = ""
    fecha_jornada: str = ""
    tipo_asistencia: str = "ACTIVO"
    hora_entrada: str = ""
    hora_salida: str = ""
    instalaciones: str = "0"
    desinstalaciones: str = "0"
    revisiones: str = "0"
    detalle: str = ""
    motivo: str = ""
    tipo_licencia: str = ""
    fecha_desde: str = ""
    fecha_hasta: str = ""
    exito: str = ""
    jornadas: list[dict] = []
    filtro_empleado: str = ""
    filtro_mes: str = ""
    filtro_anio: str = "2026"
    nuevo_empleado: str = ""

    # Estadísticas
    stats_mes: str = ""
    stats_anio: str = "2026"
    stats_resumen: list[dict] = []
    stats_barras_horas: list[dict] = []
    stats_barras_prod: list[dict] = []

    # Stock
    productos: list[dict] = []
    nombres_productos: list[str] = []
    ubicaciones: list[dict] = []
    nombres_ubicaciones: list[str] = []
    stock_actual: list[dict] = []
    stock_ubicacion_filtro: str = ""
    nombres_ubicaciones_internas: list[str] = []

    # Entrada
    entrada_producto: str = ""
    entrada_cantidad: str = "1"
    entrada_fecha: str = ""
    entrada_origen: str = "Proveedor"
    entrada_observacion: str = ""
    entrada_exito: str = ""
    entrada_error: str = ""

    # Transferencia / Salida
    mov_producto: str = ""
    mov_cantidad: str = "1"
    mov_fecha: str = ""
    mov_origen: str = ""
    mov_destino: str = ""
    mov_observacion: str = ""
    mov_tipo: str = "TRANSFERENCIA"
    mov_exito: str = ""
    mov_error: str = ""

    async def login(self):
        self.cargando = True
        self.error = ""
        yield
        try:
            async with httpx.AsyncClient(timeout=30.0) as client:
                response = await client.post(
                    f"{API_URL}/auth/login",
                    json={"usuario": self.usuario, "password": self.password}
                )
            if response.status_code == 200:
                data = response.json()
                self.token = data["access_token"]
                self.usuario = data["usuario"]
                yield rx.redirect("/dashboard")
            else:
                self.error = "Usuario o contraseña incorrectos"
        except Exception:
            self.error = "Error conectando al servidor"
        self.cargando = False

    def logout(self):
        self.usuario = ""
        self.token = ""
        self.pagina = "registro"
        return rx.redirect("/")

    def set_pagina(self, pagina: str):
        self.pagina = pagina

    async def cargar_empleados(self):
        async with httpx.AsyncClient(timeout=30.0) as client:
            r = await client.get(f"{API_URL}/empleados/")
        self.empleados = r.json()
        self.nombres_empleados = [e["nombre"] for e in self.empleados]

    def reset_formulario(self):
        self.empleado_sel = ""
        self.fecha_jornada = ""
        self.tipo_asistencia = "ACTIVO"
        self.hora_entrada = ""
        self.hora_salida = ""
        self.instalaciones = "0"
        self.desinstalaciones = "0"
        self.revisiones = "0"
        self.detalle = ""
        self.motivo = ""
        self.tipo_licencia = ""
        self.fecha_desde = ""
        self.fecha_hasta = ""
        self.error = ""
        self.exito = ""

    async def guardar_jornada(self):
        if not self.empleado_sel or not self.fecha_jornada:
            self.error = "Completá empleado y fecha"
            return
        emp = next((e for e in self.empleados if e["nombre"] == self.empleado_sel), None)
        if not emp:
            return
        payload = {
            "empleado_id": emp["id"],
            "nombre": emp["nombre"],
            "fecha": self.fecha_jornada,
            "tipo_asistencia": self.tipo_asistencia,
            "hora_entrada": self.hora_entrada or None,
            "hora_salida": self.hora_salida or None,
            "instalaciones": int(self.instalaciones),
            "desinstalaciones": int(self.desinstalaciones),
            "revisiones": int(self.revisiones),
            "detalle": self.detalle or None,
            "motivo": self.motivo or None,
            "tipo_licencia": self.tipo_licencia or None,
            "fecha_desde": self.fecha_desde or None,
            "fecha_hasta": self.fecha_hasta or None,
            "cargado_por": self.usuario,
        }
        async with httpx.AsyncClient(timeout=30.0) as client:
            r = await client.post(f"{API_URL}/jornadas/", json=payload)
        if r.status_code == 200:
            self.reset_formulario()
            self.exito = "Jornada guardada correctamente"
        else:
            self.error = r.json().get("detail", "Error al guardar")
            self.exito = ""

    def _calcular_horas(self, jornadas):
        from datetime import datetime
        for j in jornadas:
            if j.get("hora_entrada") and j.get("hora_salida"):
                try:
                    ent = datetime.strptime(j["hora_entrada"], "%H:%M")
                    sal = datetime.strptime(j["hora_salida"], "%H:%M")
                    diff = (sal - ent).seconds / 3600
                    j["horas"] = round(diff, 2)
                    extra = round(diff - 8, 2)
                    j["diferencia"] = extra
                    j["dif_str"] = f"+{extra}h" if extra >= 0 else f"{extra}h"
                    j["dif_color"] = "green" if extra >= 0 else "red"
                except:
                    j["horas"] = 0
                    j["diferencia"] = 0
                    j["dif_str"] = "-"
                    j["dif_color"] = "gray"
            else:
                j["horas"] = 0
                j["diferencia"] = 0
                j["dif_str"] = "-"
                j["dif_color"] = "gray"
        return jornadas

    async def cargar_historial(self):
        params = {}
        if self.filtro_mes:
            params["mes"] = self.filtro_mes
        if self.filtro_anio:
            params["anio"] = self.filtro_anio
        if self.filtro_empleado:
            emp = next((e for e in self.empleados if e["nombre"] == self.filtro_empleado), None)
            if emp:
                params["empleado_id"] = emp["id"]
        async with httpx.AsyncClient(timeout=30.0) as client:
            r = await client.get(f"{API_URL}/jornadas/", params=params)
        self.jornadas = self._calcular_horas(r.json())

    async def eliminar_jornada(self, jornada_id: str):
        async with httpx.AsyncClient(timeout=30.0) as client:
            await client.delete(f"{API_URL}/jornadas/{jornada_id}")
        await self.cargar_historial()

    async def agregar_empleado(self):
        if not self.nuevo_empleado:
            return
        async with httpx.AsyncClient(timeout=30.0) as client:
            await client.post(f"{API_URL}/empleados/", json={"nombre": self.nuevo_empleado})
        self.nuevo_empleado = ""
        await self.cargar_empleados()

    async def desactivar_empleado(self, empleado_id: str):
        async with httpx.AsyncClient(timeout=30.0) as client:
            await client.delete(f"{API_URL}/empleados/{empleado_id}")
        await self.cargar_empleados()

    async def cargar_estadisticas(self):
        params = {}
        if self.stats_mes:
            params["mes"] = self.stats_mes
        if self.stats_anio:
            params["anio"] = self.stats_anio
        async with httpx.AsyncClient(timeout=30.0) as client:
            r = await client.get(f"{API_URL}/jornadas/", params=params)
        raw = self._calcular_horas(r.json())
        resumen = {}
        for j in raw:
            nombre = j["nombre"]
            if nombre not in resumen:
                resumen[nombre] = {
                    "nombre": nombre, "dias": 0, "horas_total": 0.0,
                    "extras": 0.0, "debe": 0.0,
                    "instalaciones": 0, "desinstalaciones": 0, "revisiones": 0, "ausencias": 0,
                }
            r2 = resumen[nombre]
            if j["tipo_asistencia"] in ["ACTIVO", "LLEGADA_TARDE"]:
                r2["dias"] += 1
                r2["horas_total"] = round(r2["horas_total"] + j["horas"], 2)
                if j["diferencia"] > 0:
                    r2["extras"] = round(r2["extras"] + j["diferencia"], 2)
                else:
                    r2["debe"] = round(r2["debe"] + abs(j["diferencia"]), 2)
                r2["instalaciones"] += j.get("instalaciones", 0)
                r2["desinstalaciones"] += j.get("desinstalaciones", 0)
                r2["revisiones"] += j.get("revisiones", 0)
            elif j["tipo_asistencia"] in ["AUSENCIA_SJ", "AUSENCIA_J"]:
                r2["ausencias"] += 1
        for v in resumen.values():
            v["extras_str"] = f"+{v['extras']}h"
            v["debe_str"] = f"-{v['debe']}h"
        self.stats_resumen = list(resumen.values())
        dias = {}
        for j in raw:
            if j["tipo_asistencia"] in ["ACTIVO", "LLEGADA_TARDE"]:
                dia = j["fecha"][-2:]
                if dia not in dias:
                    dias[dia] = {"dia": dia, "horas": 0.0}
                dias[dia]["horas"] = round(dias[dia]["horas"] + j["horas"], 2)
        self.stats_barras_horas = sorted(dias.values(), key=lambda x: x["dia"])
        total_inst = sum(j.get("instalaciones", 0) for j in raw)
        total_desins = sum(j.get("desinstalaciones", 0) for j in raw)
        total_rev = sum(j.get("revisiones", 0) for j in raw)
        self.stats_barras_prod = [
            {"tipo": "Instalaciones", "cantidad": total_inst},
            {"tipo": "Desinstalaciones", "cantidad": total_desins},
            {"tipo": "Revisiones", "cantidad": total_rev},
        ]

    # ── STOCK ──────────────────────────────────────────
    async def cargar_productos_y_ubicaciones(self):
        async with httpx.AsyncClient(timeout=30.0) as client:
            rp = await client.get(f"{API_URL}/stock/productos/")
            ru = await client.get(f"{API_URL}/stock/ubicaciones/")
        self.productos = rp.json()
        self.nombres_productos = [f"{p['codigo']} - {p['descripcion']}" for p in self.productos]
        self.ubicaciones = ru.json()
        self.nombres_ubicaciones = [u["nombre"] for u in self.ubicaciones]
        self.nombres_ubicaciones_internas = [u["nombre"] for u in self.ubicaciones if u["tipo"] == "INTERNO"]

    async def cargar_stock_actual(self):
        await self.cargar_productos_y_ubicaciones()
        params = {}
        if self.stock_ubicacion_filtro:
            ub = next((u for u in self.ubicaciones if u["nombre"] == self.stock_ubicacion_filtro), None)
            if ub:
                params["ubicacion_id"] = ub["id"]
        async with httpx.AsyncClient(timeout=30.0) as client:
            r = await client.get(f"{API_URL}/stock/actual/", params=params)
        raw = r.json()
        for item in raw:
            item["prod_codigo"] = item.get("productos", {}).get("codigo", "")
            item["prod_desc"] = item.get("productos", {}).get("descripcion", "")
            item["prod_cat"] = item.get("productos", {}).get("categoria", "")
            item["ubic_nombre"] = item.get("ubicaciones", {}).get("nombre", "")
            item["stock_color"] = "red" if item["cantidad"] <= 0 else "green" if item["cantidad"] > 5 else "orange"
        self.stock_actual = raw

    async def registrar_entrada(self):
        if not self.entrada_producto or not self.entrada_fecha:
            self.entrada_error = "Completá producto y fecha"
            return
        prod = next((p for p in self.productos if f"{p['codigo']} - {p['descripcion']}" == self.entrada_producto), None)
        if not prod:
            return
        ub_oficina = next((u for u in self.ubicaciones if u["nombre"] == "Oficina"), None)
        if not ub_oficina:
            self.entrada_error = "No se encontró la ubicación Oficina"
            return
        payload = {
            "tipo": "ENTRADA",
            "producto_id": prod["id"],
            "destino_id": ub_oficina["id"],
            "cantidad": int(self.entrada_cantidad),
            "fecha": self.entrada_fecha,
            "cargado_por": self.usuario,
            "observacion": self.entrada_observacion or None,
        }
        async with httpx.AsyncClient(timeout=30.0) as client:
            r = await client.post(f"{API_URL}/stock/movimiento/", json=payload)
        if r.status_code == 200:
            self.entrada_producto = ""
            self.entrada_cantidad = "1"
            self.entrada_fecha = ""
            self.entrada_observacion = ""
            self.entrada_exito = "Entrada registrada correctamente"
            self.entrada_error = ""
        else:
            self.entrada_error = "Error al registrar entrada"
            self.entrada_exito = ""

    async def registrar_transferencia(self):
        if not self.mov_producto or not self.mov_fecha or not self.mov_origen or not self.mov_destino:
            self.mov_error = "Completá todos los campos"
            return
        prod = next((p for p in self.productos if f"{p['codigo']} - {p['descripcion']}" == self.mov_producto), None)
        orig = next((u for u in self.ubicaciones if u["nombre"] == self.mov_origen), None)
        dest = next((u for u in self.ubicaciones if u["nombre"] == self.mov_destino), None)
        if not prod or not orig or not dest:
            self.mov_error = "Datos inválidos"
            return
        payload = {
            "tipo": self.mov_tipo,
            "producto_id": prod["id"],
            "origen_id": orig["id"],
            "destino_id": dest["id"],
            "cantidad": int(self.mov_cantidad),
            "fecha": self.mov_fecha,
            "cargado_por": self.usuario,
            "observacion": self.mov_observacion or None,
        }
        async with httpx.AsyncClient(timeout=30.0) as client:
            r = await client.post(f"{API_URL}/stock/movimiento/", json=payload)
        if r.status_code == 200:
            self.mov_producto = ""
            self.mov_cantidad = "1"
            self.mov_fecha = ""
            self.mov_origen = ""
            self.mov_destino = ""
            self.mov_observacion = ""
            self.mov_exito = "Movimiento registrado correctamente"
            self.mov_error = ""
        else:
            detail = r.json().get("detail", "Error al registrar")
            self.mov_error = detail
            self.mov_exito = ""


MODULOS = [
    {"id": "horarios", "icon": "clock", "label": "Horarios", "color": "#1e3a8a",
     "subs": [("registro", "Registro"), ("historial", "Historial"), ("estadisticas", "Estadísticas"), ("tecnicos", "Técnicos")]},
    {"id": "servicios", "icon": "wrench", "label": "Servicios", "color": "#0f766e",
     "subs": [("serv_cargar", "Cargar servicio"), ("serv_lista", "Lista")]},
    {"id": "stock", "icon": "package", "label": "Stock", "color": "#b45309",
     "subs": [("stock_actual", "Stock actual"), ("stock_entrada", "Entrada"), ("stock_salida", "Transferencia/Salida"), ("stock_productos", "Productos")]},
    {"id": "terceros", "icon": "users", "label": "Terceros", "color": "#7c3aed",
     "subs": [("terceros_lista", "Lista"), ("terceros_stock", "Stock")]},
    {"id": "reportes", "icon": "chart-bar", "label": "Reportes", "color": "#be123c",
     "subs": [("reporte_cruzado", "Horarios vs Servicios")]},
]


def sidebar() -> rx.Component:
    return rx.box(
        rx.vstack(
            rx.box(
                rx.hstack(
                    rx.icon("settings", size=20, color="white"),
                    rx.text("App-Logic", font_weight="700", color="white", font_size="16px"),
                    spacing="2", align="center",
                ),
                rx.text(State.usuario, font_size="11px", color="#93c5fd", margin_top="2px"),
                padding="16px",
                border_bottom="1px solid #1e40af",
                width="100%",
            ),
            rx.vstack(
                *[
                    rx.vstack(
                        rx.hstack(
                            rx.icon(mod["icon"], size=16, color="white"),
                            rx.text(mod["label"], color="white", font_size="13px", font_weight="600"),
                            spacing="2", align="center", width="100%",
                            padding="8px 12px",
                        ),
                        *[
                            rx.box(
                                rx.text(sub_label, font_size="12px", color="#bfdbfe",
                                       _hover={"color": "white"}, cursor="pointer",
                                       padding="5px 12px 5px 32px"),
                                on_click=State.set_pagina(sub_key),
                                width="100%",
                            )
                            for sub_key, sub_label in mod["subs"]
                        ],
                        width="100%", spacing="0",
                    )
                    for mod in MODULOS
                ],
                width="100%", spacing="1", padding_top="8px",
            ),
            rx.spacer(),
            rx.box(
                rx.hstack(
                    rx.icon("log-out", size=14, color="#93c5fd"),
                    rx.text("Cerrar sesión", font_size="12px", color="#93c5fd"),
                    spacing="2", cursor="pointer",
                    on_click=State.logout,
                ),
                padding="12px 16px",
                border_top="1px solid #1e40af",
                width="100%",
            ),
            height="100vh", width="220px", spacing="0",
        ),
        background="#1e3a8a",
        height="100vh",
        position="fixed",
        left="0", top="0",
        width="220px",
    )


def layout(content: rx.Component) -> rx.Component:
    return rx.hstack(
        sidebar(),
        rx.box(
            content,
            margin_left="220px",
            padding="24px",
            width="100%",
            min_height="100vh",
            background="#f1f3f6",
        ),
        spacing="0", width="100%",
    )


def login_page() -> rx.Component:
    return rx.center(
        rx.vstack(
            rx.heading("⚙️ App-Logic", size="8", color="blue"),
            rx.text("Ingresá para continuar", color="gray"),
            rx.input(placeholder="Usuario", value=State.usuario, on_change=State.set_usuario),
            rx.input(placeholder="Contraseña", type="password", value=State.password, on_change=State.set_password),
            rx.cond(State.error != "", rx.text(State.error, color="red")),
            rx.button(
                rx.cond(State.cargando, "Ingresando...", "Ingresar"),
                on_click=State.login, width="100%", color_scheme="blue", disabled=State.cargando,
            ),
            width="360px", spacing="4", padding="40px",
            border="1px solid #e2e6ea", border_radius="12px", background="white",
        ),
        min_height="100vh", background="#f1f3f6",
    )


def page_registro() -> rx.Component:
    return layout(
        rx.vstack(
            rx.heading("Registro de Jornada", size="6"),
            rx.divider(),
            rx.hstack(
                rx.vstack(
                    rx.text("Técnico", font_size="12px", font_weight="600", color="gray"),
                    rx.select(State.nombres_empleados, placeholder="Seleccionar técnico", value=State.empleado_sel, on_change=State.set_empleado_sel, width="200px"),
                    spacing="1",
                ),
                rx.vstack(
                    rx.text("Fecha", font_size="12px", font_weight="600", color="gray"),
                    rx.input(type="date", value=State.fecha_jornada, on_change=State.set_fecha_jornada, width="180px"),
                    spacing="1",
                ),
                rx.vstack(
                    rx.text("Tipo", font_size="12px", font_weight="600", color="gray"),
                    rx.select(["ACTIVO", "LLEGADA_TARDE", "AUSENCIA_SJ", "AUSENCIA_J", "VACACIONES", "LICENCIA"], value=State.tipo_asistencia, on_change=State.set_tipo_asistencia, width="200px"),
                    spacing="1",
                ),
                spacing="4", wrap="wrap",
            ),
            rx.cond(
                (State.tipo_asistencia == "ACTIVO") | (State.tipo_asistencia == "LLEGADA_TARDE"),
                rx.vstack(
                    rx.hstack(
                        rx.vstack(rx.text("Entrada", font_size="12px", color="gray"), rx.input(type="time", value=State.hora_entrada, on_change=State.set_hora_entrada), spacing="1"),
                        rx.vstack(rx.text("Salida", font_size="12px", color="gray"), rx.input(type="time", value=State.hora_salida, on_change=State.set_hora_salida), spacing="1"),
                        spacing="4",
                    ),
                    rx.hstack(
                        rx.vstack(rx.text("Instalaciones", font_size="12px", color="gray"), rx.input(type="number", value=State.instalaciones, on_change=State.set_instalaciones, width="120px"), spacing="1"),
                        rx.vstack(rx.text("Desinstalaciones", font_size="12px", color="gray"), rx.input(type="number", value=State.desinstalaciones, on_change=State.set_desinstalaciones, width="120px"), spacing="1"),
                        rx.vstack(rx.text("Revisiones", font_size="12px", color="gray"), rx.input(type="number", value=State.revisiones, on_change=State.set_revisiones, width="120px"), spacing="1"),
                        spacing="4",
                    ),
                    rx.vstack(rx.text("Detalle", font_size="12px", color="gray"), rx.text_area(value=State.detalle, on_change=State.set_detalle, width="500px", rows="3"), spacing="1"),
                    spacing="4",
                ),
            ),
            rx.cond(State.tipo_asistencia == "AUSENCIA_J",
                rx.vstack(rx.text("Motivo", font_size="12px", color="gray"), rx.input(value=State.motivo, on_change=State.set_motivo, width="300px"), spacing="1")),
            rx.cond(State.tipo_asistencia == "LICENCIA",
                rx.hstack(
                    rx.vstack(rx.text("Tipo licencia", font_size="12px", color="gray"), rx.input(value=State.tipo_licencia, on_change=State.set_tipo_licencia, width="200px"), spacing="1"),
                    rx.vstack(rx.text("Desde", font_size="12px", color="gray"), rx.input(type="date", value=State.fecha_desde, on_change=State.set_fecha_desde), spacing="1"),
                    rx.vstack(rx.text("Hasta", font_size="12px", color="gray"), rx.input(type="date", value=State.fecha_hasta, on_change=State.set_fecha_hasta), spacing="1"),
                    spacing="4",
                )),
            rx.cond(State.tipo_asistencia == "VACACIONES",
                rx.hstack(
                    rx.vstack(rx.text("Desde", font_size="12px", color="gray"), rx.input(type="date", value=State.fecha_desde, on_change=State.set_fecha_desde), spacing="1"),
                    rx.vstack(rx.text("Hasta", font_size="12px", color="gray"), rx.input(type="date", value=State.fecha_hasta, on_change=State.set_fecha_hasta), spacing="1"),
                    spacing="4",
                )),
            rx.cond(State.error != "", rx.callout(State.error, color="red")),
            rx.cond(State.exito != "", rx.callout(State.exito, color="green")),
            rx.button("Guardar jornada", on_click=State.guardar_jornada, color_scheme="blue", size="3"),
            spacing="4", width="100%", max_width="700px",
        )
    )


def jornada_row(jornada: dict) -> rx.Component:
    return rx.table.row(
        rx.table.cell(jornada["fecha"]),
        rx.table.cell(jornada["nombre"]),
        rx.table.cell(jornada["tipo_asistencia"]),
        rx.table.cell(rx.cond(jornada["hora_entrada"], jornada["hora_entrada"], "-")),
        rx.table.cell(rx.cond(jornada["hora_salida"], jornada["hora_salida"], "-")),
        rx.table.cell(rx.cond(jornada["horas"], jornada["horas"], "-")),
        rx.table.cell(rx.text(jornada["dif_str"], color=jornada["dif_color"], font_weight="600")),
        rx.table.cell(jornada["instalaciones"]),
        rx.table.cell(jornada["desinstalaciones"]),
        rx.table.cell(jornada["revisiones"]),
        rx.table.cell(rx.button("🗑", size="1", color_scheme="red", on_click=State.eliminar_jornada(jornada["id"]))),
    )


def page_historial() -> rx.Component:
    return layout(
        rx.vstack(
            rx.heading("Historial de Jornadas", size="6"),
            rx.divider(),
            rx.hstack(
                rx.vstack(rx.text("Técnico", font_size="12px", color="gray"), rx.select(State.nombres_empleados, placeholder="Todos", value=State.filtro_empleado, on_change=State.set_filtro_empleado, width="160px"), spacing="1"),
                rx.vstack(rx.text("Mes", font_size="12px", color="gray"), rx.select(["1","2","3","4","5","6","7","8","9","10","11","12"], placeholder="Todos", value=State.filtro_mes, on_change=State.set_filtro_mes, width="100px"), spacing="1"),
                rx.vstack(rx.text("Año", font_size="12px", color="gray"), rx.select(["2025", "2026", "2027"], value=State.filtro_anio, on_change=State.set_filtro_anio, width="100px"), spacing="1"),
                rx.button("Buscar", on_click=State.cargar_historial, color_scheme="blue"),
                spacing="4", align="end",
            ),
            rx.table.root(
                rx.table.header(
                    rx.table.row(
                        rx.table.column_header_cell("Fecha"),
                        rx.table.column_header_cell("Técnico"),
                        rx.table.column_header_cell("Tipo"),
                        rx.table.column_header_cell("Entrada"),
                        rx.table.column_header_cell("Salida"),
                        rx.table.column_header_cell("Hs trabajadas"),
                        rx.table.column_header_cell("Diferencia"),
                        rx.table.column_header_cell("Inst."),
                        rx.table.column_header_cell("Desins."),
                        rx.table.column_header_cell("Rev."),
                        rx.table.column_header_cell(""),
                    )
                ),
                rx.table.body(rx.foreach(State.jornadas, jornada_row)),
                width="100%",
            ),
            spacing="4", width="100%",
            on_mount=State.cargar_historial,
        )
    )


def empleado_row(emp: dict) -> rx.Component:
    return rx.table.row(
        rx.table.cell(emp["nombre"]),
        rx.table.cell(rx.cond(emp["telefono"], emp["telefono"], "-")),
        rx.table.cell(rx.cond(emp["vehiculo"], emp["vehiculo"], "-")),
        rx.table.cell(rx.cond(emp["patente"], emp["patente"], "-")),
        rx.table.cell(rx.button("🗑", size="1", color_scheme="red", on_click=State.desactivar_empleado(emp["id"]))),
    )


def page_tecnicos() -> rx.Component:
    return layout(
        rx.vstack(
            rx.heading("Técnicos", size="6"),
            rx.divider(),
            rx.hstack(
                rx.input(placeholder="Nombre del técnico", value=State.nuevo_empleado, on_change=State.set_nuevo_empleado, width="250px"),
                rx.button("Agregar", on_click=State.agregar_empleado, color_scheme="blue"),
                spacing="3", align="center",
            ),
            rx.table.root(
                rx.table.header(
                    rx.table.row(
                        rx.table.column_header_cell("Nombre"),
                        rx.table.column_header_cell("Teléfono"),
                        rx.table.column_header_cell("Vehículo"),
                        rx.table.column_header_cell("Patente"),
                        rx.table.column_header_cell(""),
                    )
                ),
                rx.table.body(rx.foreach(State.empleados, empleado_row)),
                width="100%",
            ),
            spacing="4", width="100%",
            on_mount=State.cargar_empleados,
        )
    )


def stats_resumen_row(r: dict) -> rx.Component:
    return rx.table.row(
        rx.table.cell(r["nombre"]),
        rx.table.cell(r["dias"]),
        rx.table.cell(f"{r['horas_total']}h"),
        rx.table.cell(rx.text(r["extras_str"], color="green", font_weight="600")),
        rx.table.cell(rx.text(r["debe_str"], color="red", font_weight="600")),
        rx.table.cell(r["instalaciones"]),
        rx.table.cell(r["desinstalaciones"]),
        rx.table.cell(r["revisiones"]),
        rx.table.cell(r["ausencias"]),
    )


def page_estadisticas() -> rx.Component:
    return layout(
        rx.vstack(
            rx.heading("Estadísticas", size="6"),
            rx.divider(),
            rx.hstack(
                rx.vstack(rx.text("Mes", font_size="12px", color="gray"), rx.select(["1","2","3","4","5","6","7","8","9","10","11","12"], placeholder="Seleccionar", value=State.stats_mes, on_change=State.set_stats_mes, width="130px"), spacing="1"),
                rx.vstack(rx.text("Año", font_size="12px", color="gray"), rx.select(["2025", "2026", "2027"], value=State.stats_anio, on_change=State.set_stats_anio, width="100px"), spacing="1"),
                rx.button("Calcular", on_click=State.cargar_estadisticas, color_scheme="blue"),
                spacing="4", align="end",
            ),
            rx.text("Resumen por técnico", font_size="14px", font_weight="700", color="#1e3a8a"),
            rx.table.root(
                rx.table.header(
                    rx.table.row(
                        rx.table.column_header_cell("Técnico"),
                        rx.table.column_header_cell("Días trabajados"),
                        rx.table.column_header_cell("Hs totales"),
                        rx.table.column_header_cell("Extras"),
                        rx.table.column_header_cell("Debe"),
                        rx.table.column_header_cell("Inst."),
                        rx.table.column_header_cell("Desins."),
                        rx.table.column_header_cell("Rev."),
                        rx.table.column_header_cell("Ausencias"),
                    )
                ),
                rx.table.body(rx.foreach(State.stats_resumen, stats_resumen_row)),
                width="100%",
            ),
            rx.text("Horas trabajadas por día", font_size="14px", font_weight="700", color="#1e3a8a", margin_top="16px"),
            rx.recharts.bar_chart(
                rx.recharts.bar(data_key="horas", fill="#1e3a8a", name="Horas"),
                rx.recharts.reference_line(y=8, stroke="red", stroke_dasharray="3 3", label="8h"),
                rx.recharts.x_axis(data_key="dia"),
                rx.recharts.y_axis(),
                rx.recharts.cartesian_grid(stroke_dasharray="3 3"),
                rx.recharts.graphing_tooltip(),
                data=State.stats_barras_horas,
                width="100%",
                height=300,
            ),
            rx.text("Productividad del período", font_size="14px", font_weight="700", color="#1e3a8a", margin_top="16px"),
            rx.recharts.bar_chart(
                rx.recharts.bar(data_key="cantidad", fill="#0f766e", name="Cantidad"),
                rx.recharts.x_axis(data_key="tipo"),
                rx.recharts.y_axis(),
                rx.recharts.cartesian_grid(stroke_dasharray="3 3"),
                rx.recharts.graphing_tooltip(),
                data=State.stats_barras_prod,
                width="100%",
                height=250,
            ),
            spacing="4", width="100%",
        )
    )


def stock_row(item: dict) -> rx.Component:
    return rx.table.row(
        rx.table.cell(item["prod_codigo"]),
        rx.table.cell(item["prod_desc"]),
        rx.table.cell(item["prod_cat"]),
        rx.table.cell(item["ubic_nombre"]),
        rx.table.cell(
            rx.text(item["cantidad"], color=item["stock_color"], font_weight="700")
        ),
    )


def page_stock_actual() -> rx.Component:
    return layout(
        rx.vstack(
            rx.heading("Stock Actual", size="6"),
            rx.divider(),
            rx.hstack(
                rx.vstack(
                    rx.text("Ubicación", font_size="12px", color="gray"),
                    rx.select(
                        State.nombres_ubicaciones,
                        placeholder="Todas",
                        value=State.stock_ubicacion_filtro,
                        on_change=State.set_stock_ubicacion_filtro,
                        width="200px",
                    ),
                    spacing="1",
                ),
                rx.button("Filtrar", on_click=State.cargar_stock_actual, color_scheme="blue"),
                spacing="4", align="end",
            ),
            rx.table.root(
                rx.table.header(
                    rx.table.row(
                        rx.table.column_header_cell("Código"),
                        rx.table.column_header_cell("Descripción"),
                        rx.table.column_header_cell("Categoría"),
                        rx.table.column_header_cell("Ubicación"),
                        rx.table.column_header_cell("Cantidad"),
                    )
                ),
                rx.table.body(rx.foreach(State.stock_actual, stock_row)),
                width="100%",
            ),
            spacing="4", width="100%",
            on_mount=State.cargar_stock_actual,
        )
    )


def page_stock_entrada() -> rx.Component:
    return layout(
        rx.vstack(
            rx.heading("Entrada de Stock", size="6"),
            rx.divider(),
            rx.hstack(
                rx.vstack(
                    rx.text("Producto", font_size="12px", color="gray"),
                    rx.select(State.nombres_productos, placeholder="Seleccionar producto", value=State.entrada_producto, on_change=State.set_entrada_producto, width="300px"),
                    spacing="1",
                ),
                rx.vstack(
                    rx.text("Cantidad", font_size="12px", color="gray"),
                    rx.input(type="number", value=State.entrada_cantidad, on_change=State.set_entrada_cantidad, width="100px"),
                    spacing="1",
                ),
                rx.vstack(
                    rx.text("Fecha", font_size="12px", color="gray"),
                    rx.input(type="date", value=State.entrada_fecha, on_change=State.set_entrada_fecha, width="160px"),
                    spacing="1",
                ),
                spacing="4", wrap="wrap",
            ),
            rx.vstack(
                rx.text("Origen / Observación", font_size="12px", color="gray"),
                rx.input(placeholder="Proveedor o motivo", value=State.entrada_observacion, on_change=State.set_entrada_observacion, width="400px"),
                spacing="1",
            ),
            rx.cond(State.entrada_error != "", rx.callout(State.entrada_error, color="red")),
            rx.cond(State.entrada_exito != "", rx.callout(State.entrada_exito, color="green")),
            rx.button("Registrar entrada", on_click=State.registrar_entrada, color_scheme="blue", size="3"),
            spacing="4", width="100%", max_width="700px",
            on_mount=State.cargar_productos_y_ubicaciones,
        )
    )


def page_stock_salida() -> rx.Component:
    return layout(
        rx.vstack(
            rx.heading("Transferencia / Salida", size="6"),
            rx.divider(),
            rx.hstack(
                rx.vstack(
                    rx.text("Tipo", font_size="12px", color="gray"),
                    rx.select(
                        ["TRANSFERENCIA", "SALIDA", "DESCARTE"],
                        value=State.mov_tipo,
                        on_change=State.set_mov_tipo,
                        width="160px",
                    ),
                    spacing="1",
                ),
                rx.vstack(
                    rx.text("Producto", font_size="12px", color="gray"),
                    rx.select(State.nombres_productos, placeholder="Seleccionar", value=State.mov_producto, on_change=State.set_mov_producto, width="300px"),
                    spacing="1",
                ),
                rx.vstack(
                    rx.text("Cantidad", font_size="12px", color="gray"),
                    rx.input(type="number", value=State.mov_cantidad, on_change=State.set_mov_cantidad, width="100px"),
                    spacing="1",
                ),
                spacing="4", wrap="wrap",
            ),
            rx.hstack(
                rx.vstack(
                    rx.text("Origen", font_size="12px", color="gray"),
                    rx.select(State.nombres_ubicaciones, placeholder="Origen", value=State.mov_origen, on_change=State.set_mov_origen, width="200px"),
                    spacing="1",
                ),
                rx.vstack(
                    rx.text("Destino", font_size="12px", color="gray"),
                    rx.select(State.nombres_ubicaciones, placeholder="Destino", value=State.mov_destino, on_change=State.set_mov_destino, width="200px"),
                    spacing="1",
                ),
                rx.vstack(
                    rx.text("Fecha", font_size="12px", color="gray"),
                    rx.input(type="date", value=State.mov_fecha, on_change=State.set_mov_fecha, width="160px"),
                    spacing="1",
                ),
                spacing="4", wrap="wrap",
            ),
            rx.vstack(
                rx.text("Observación", font_size="12px", color="gray"),
                rx.input(value=State.mov_observacion, on_change=State.set_mov_observacion, width="400px"),
                spacing="1",
            ),
            rx.cond(State.mov_error != "", rx.callout(State.mov_error, color="red")),
            rx.cond(State.mov_exito != "", rx.callout(State.mov_exito, color="green")),
            rx.button("Registrar movimiento", on_click=State.registrar_transferencia, color_scheme="blue", size="3"),
            spacing="4", width="100%", max_width="700px",
            on_mount=State.cargar_productos_y_ubicaciones,
        )
    )


def dashboard_page() -> rx.Component:
    return rx.cond(
        State.pagina == "registro", page_registro(),
        rx.cond(State.pagina == "historial", page_historial(),
        rx.cond(State.pagina == "tecnicos", page_tecnicos(),
        rx.cond(State.pagina == "estadisticas", page_estadisticas(),
        rx.cond(State.pagina == "stock_actual", page_stock_actual(),
        rx.cond(State.pagina == "stock_entrada", page_stock_entrada(),
        rx.cond(State.pagina == "stock_salida", page_stock_salida(),
        layout(rx.vstack(
            rx.heading("Bienvenido!", size="7"),
            rx.text("Seleccioná un módulo del sidebar.", color="gray"),
            spacing="4",
        )))))))))


app = rx.App(theme=rx.theme(accent_color="blue", has_background=True))
app.add_page(login_page, route="/")
app.add_page(dashboard_page, route="/dashboard", on_load=State.cargar_empleados)