import reflex as rx
import httpx
import os

API_URL = os.environ.get("API_URL", "http://127.0.0.1:8001")

class State(rx.State):
    usuario: str = ""
    login_input: str = ""
    password: str = ""
    token: str = ""
    error: str = ""
    cargando: bool = False
    pagina: str = "carga_dia"
    confirm_id: str = ""
    confirm_tipo: str = ""
    mostrar_confirm: bool = False

    # Stock
    productos: list[dict] = []
    nombres_productos: list[str] = []
    ubicaciones: list[dict] = []
    nombres_ubicaciones: list[str] = []
    stock_actual: list[dict] = []
    stock_ubicacion_filtro: str = ""
    entrada_producto: str = ""
    entrada_cantidad: str = "1"
    entrada_fecha: str = ""
    entrada_observacion: str = ""
    entrada_exito: str = ""
    entrada_error: str = ""
    mov_producto: str = ""
    mov_cantidad: str = "1"
    mov_fecha: str = ""
    mov_origen: str = ""
    mov_destino: str = ""
    mov_observacion: str = ""
    mov_tipo: str = "TRANSFERENCIA"
    mov_exito: str = ""
    mov_error: str = ""
    prod_codigo: str = ""
    prod_descripcion: str = ""
    prod_categoria: str = "DISPOSITIVOS"
    prod_filtro_cat: str = ""
    prod_edit_id: str = ""
    prod_edit_desc: str = ""
    prod_edit_cat: str = ""
    prod_exito: str = ""
    prod_error: str = ""
    mostrar_form_prod: bool = False

    # Proveedores
    proveedores: list[dict] = []
    prov_nombre: str = ""
    prov_responsable: str = ""
    prov_telefono: str = ""
    prov_email: str = ""
    prov_direccion: str = ""
    prov_productos: str = ""
    prov_observaciones: str = ""
    prov_edit_id: str = ""
    prov_exito: str = ""
    prov_error: str = ""
    mostrar_form_prov: bool = False

    # Terceros (se usan para stock)
    terceros: list[dict] = []
    nombres_terceros: list[str] = []
    terc_nombre: str = ""
    terc_ciudad: str = ""
    terc_telefono: str = ""
    terc_email: str = ""
    terc_empresa: str = ""
    terc_observaciones: str = ""
    terc_edit_id: str = ""
    terc_exito: str = ""
    terc_error: str = ""
    mostrar_form_terc: bool = False
    terc_sel_id: str = ""
    terc_sel_nombre: str = ""
    terc_stock: list[dict] = []

    # Equipos
    equipos: list[dict] = []
    equipos_nombres: list[str] = []

    # Carga del día
    carga_fecha: str = ""
    carga_equipo_id: str = ""
    carga_equipo_nombre: str = ""
    carga_cliente_sel: str = ""
    carga_cliente_ref: str = ""
    carga_hora: str = ""
    carga_tipo: str = "INSTALACION"
    carga_dispositivo: str = "GPS"
    carga_patente: str = ""
    carga_estado: str = "PENDIENTE"
    carga_obs_serv: str = ""
    carga_servicios: list[dict] = []
    carga_punto_inicio: str = ""
    carga_hora_salida: str = ""
    carga_punto_fin: str = ""
    carga_hora_llegada: str = ""
    carga_obs_mov: str = ""
    carga_tecnicos_presencia: list[dict] = []
    carga_exito: str = ""
    carga_error: str = ""

    # Vista del día
    vista_fecha: str = ""
    vista_servicios_equipo1: list[dict] = []
    vista_servicios_equipo2: list[dict] = []
    vista_mov_equipo1: dict = {}
    vista_mov_equipo2: dict = {}
    vista_edit_mov1_salida: str = ""
    vista_edit_mov1_llegada: str = ""
    vista_edit_mov1_inicio: str = ""
    vista_edit_mov1_fin: str = ""
    vista_edit_mov2_salida: str = ""
    vista_edit_mov2_llegada: str = ""
    vista_edit_mov2_inicio: str = ""
    vista_edit_mov2_fin: str = ""
    vista_exito: str = ""

    # Historial servicios
    hist_servicios: list[dict] = []
    hist_filtro_estado: str = ""
    hist_filtro_mes: str = ""
    hist_filtro_anio: str = "2026"
    hist_filtro_equipo: str = ""
    hist_edit_id: str = ""
    hist_edit_fecha: str = ""
    hist_edit_hora: str = ""
    hist_edit_cliente: str = ""
    hist_edit_tipo: str = ""
    hist_edit_dispositivo: str = ""
    hist_edit_patente: str = ""
    hist_edit_estado: str = ""
    hist_edit_obs: str = ""
    hist_edit_equipo_id: str = ""
    mostrar_edit_hist: bool = False

    # Directorio
    dir_tipo: str = "interno"
    dir_nombre: str = ""
    dir_telefono: str = ""
    dir_email: str = ""
    dir_equipo_id: str = ""
    dir_ciudad: str = ""
    dir_contacto: str = ""
    dir_observaciones: str = ""
    dir_exito: str = ""
    dir_error: str = ""
    dir_personal: list[dict] = []
    dir_filtro_personal: str = ""
    dir_clientes_list: list[dict] = []
    dir_clientes_nombres: list[str] = []
    dir_edit_id: str = ""

    # Estadísticas horas
    stats2_mes: str = ""
    stats2_anio: str = "2026"
    stats2_tecnicos: list[dict] = []
    stats2_movimientos: list[dict] = []
    stats2_tecnico_sel: str = ""
    stats2_detalle: list[dict] = []

    # Estadísticas servicios por cliente
    stats_cli_mes: str = ""
    stats_cli_anio: str = "2026"
    stats_cli_cliente_id: str = ""
    stats_cli_cliente_ref: str = ""
    stats_cli_resumen: dict = {}
    stats_cli_servicios: list[dict] = []

    # Reporte cruzado
    stats_cruz_mes: str = ""
    stats_cruz_anio: str = "2026"
    stats_cruz_tecnicos: list[dict] = []

    # ─── computed vars ───────────────────────────────────────────────────────

    @rx.var
    def productos_filtrados(self) -> list[dict]:
        if not self.prod_filtro_cat:
            return self.productos
        return [p for p in self.productos if p["categoria"] == self.prod_filtro_cat]

    # ─── auth ────────────────────────────────────────────────────────────────

    async def login(self):
        self.cargando = True
        self.error = ""
        yield
        try:
            async with httpx.AsyncClient(timeout=30.0) as client:
                response = await client.post(
                    f"{API_URL}/auth/login",
                    json={"usuario": self.login_input, "password": self.password}
                )
            if response.status_code == 200:
                data = response.json()
                self.token = data["access_token"]
                self.usuario = data["usuario"]
                self.login_input = ""
                self.password = ""
                yield rx.redirect("/dashboard")
            else:
                self.error = "Usuario o contraseña incorrectos"
        except Exception:
            self.error = "Error conectando al servidor"
        self.cargando = False

    def logout(self):
        self.usuario = ""
        self.token = ""
        self.pagina = "carga_dia"
        return rx.redirect("/")

    def set_pagina(self, pagina: str):
        self.pagina = pagina

    # ─── stock ───────────────────────────────────────────────────────────────

    async def cargar_productos_y_ubicaciones(self):
        async with httpx.AsyncClient(timeout=30.0) as client:
            rp = await client.get(f"{API_URL}/stock/productos/")
            ru = await client.get(f"{API_URL}/stock/ubicaciones/")
        self.productos = rp.json()
        self.nombres_productos = [f"{p['codigo']} - {p['descripcion']}" for p in self.productos]
        self.ubicaciones = ru.json()
        self.nombres_ubicaciones = [u["nombre"] for u in self.ubicaciones]

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
        result = []
        for item in raw:
            prod = item.get("productos") or {}
            ubic = item.get("ubicaciones") or {}
            item["prod_codigo"] = prod.get("codigo", "")
            item["prod_desc"] = prod.get("descripcion", "")
            item["prod_cat"] = prod.get("categoria", "")
            item["ubic_nombre"] = ubic.get("nombre", "")
            if item["prod_codigo"] and item["ubic_nombre"]:
                cantidad = item.get("cantidad", 0)
                item["stock_color"] = "red" if cantidad <= 0 else "green" if cantidad > 5 else "orange"
                result.append(item)
        self.stock_actual = result

    async def registrar_entrada(self):
        if not self.entrada_producto or not self.entrada_fecha:
            self.entrada_error = "Completá producto y fecha"
            return
        prod = next((p for p in self.productos if f"{p['codigo']} - {p['descripcion']}" == self.entrada_producto), None)
        ub_oficina = next((u for u in self.ubicaciones if u["nombre"] == "Oficina"), None)
        if not prod or not ub_oficina:
            self.entrada_error = "Error con producto o ubicación"
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
            self.mov_error = r.json().get("detail", "Error al registrar")
            self.mov_exito = ""

    async def cargar_productos(self):
        async with httpx.AsyncClient(timeout=30.0) as client:
            r = await client.get(f"{API_URL}/stock/productos/")
        self.productos = r.json()
        self.nombres_productos = [f"{p['codigo']} - {p['descripcion']}" for p in self.productos]

    async def agregar_producto(self):
        if not self.prod_codigo or not self.prod_descripcion:
            self.prod_error = "Completá código y descripción"
            return
        payload = {"codigo": self.prod_codigo, "descripcion": self.prod_descripcion, "categoria": self.prod_categoria}
        async with httpx.AsyncClient(timeout=30.0) as client:
            r = await client.post(f"{API_URL}/stock/productos/", json=payload)
        if r.status_code == 200:
            self.prod_codigo = ""
            self.prod_descripcion = ""
            self.prod_exito = "Producto agregado"
            self.prod_error = ""
            self.mostrar_form_prod = False
            await self.cargar_productos()
        else:
            self.prod_error = "Error al agregar producto"

    async def eliminar_producto(self, producto_id: str):
        async with httpx.AsyncClient(timeout=30.0) as client:
            await client.delete(f"{API_URL}/stock/productos/{producto_id}")
        await self.cargar_productos()

    def iniciar_edit_producto(self, prod_id: str, desc: str, cat: str):
        self.prod_edit_id = prod_id
        self.prod_edit_desc = desc
        self.prod_edit_cat = cat

    async def guardar_edit_producto(self):
        async with httpx.AsyncClient(timeout=30.0) as client:
            await client.put(f"{API_URL}/stock/productos/{self.prod_edit_id}", json={"descripcion": self.prod_edit_desc, "categoria": self.prod_edit_cat})
        self.prod_edit_id = ""
        await self.cargar_productos()

    # ─── proveedores ─────────────────────────────────────────────────────────

    async def cargar_proveedores(self):
        async with httpx.AsyncClient(timeout=30.0) as client:
            r = await client.get(f"{API_URL}/proveedores/")
        self.proveedores = r.json()

    async def agregar_proveedor(self):
        if not self.prov_nombre:
            self.prov_error = "El nombre es obligatorio"
            return
        payload = {
            "nombre": self.prov_nombre,
            "responsable": self.prov_responsable or None,
            "telefono": self.prov_telefono or None,
            "email": self.prov_email or None,
            "direccion": self.prov_direccion or None,
            "productos_que_vende": self.prov_productos or None,
            "observaciones": self.prov_observaciones or None,
        }
        async with httpx.AsyncClient(timeout=30.0) as client:
            r = await client.post(f"{API_URL}/proveedores/", json=payload)
        if r.status_code == 200:
            self.prov_nombre = ""
            self.prov_responsable = ""
            self.prov_telefono = ""
            self.prov_email = ""
            self.prov_direccion = ""
            self.prov_productos = ""
            self.prov_observaciones = ""
            self.prov_exito = "Proveedor agregado"
            self.prov_error = ""
            self.mostrar_form_prov = False
            await self.cargar_proveedores()
        else:
            self.prov_error = "Error al agregar proveedor"

    async def eliminar_proveedor(self, prov_id: str):
        async with httpx.AsyncClient(timeout=30.0) as client:
            await client.delete(f"{API_URL}/proveedores/{prov_id}")
        await self.cargar_proveedores()

    def iniciar_edit_proveedor(self, prov_id: str, nombre: str, responsable, telefono, email, direccion, productos, obs):
        self.prov_edit_id = prov_id
        self.prov_nombre = nombre or ""
        self.prov_responsable = responsable or ""
        self.prov_telefono = telefono or ""
        self.prov_email = email or ""
        self.prov_direccion = direccion or ""
        self.prov_productos = productos or ""
        self.prov_observaciones = obs or ""
        self.mostrar_form_prov = True

    async def guardar_edit_proveedor(self):
        payload = {
            "nombre": self.prov_nombre,
            "responsable": self.prov_responsable or None,
            "telefono": self.prov_telefono or None,
            "email": self.prov_email or None,
            "direccion": self.prov_direccion or None,
            "productos_que_vende": self.prov_productos or None,
            "observaciones": self.prov_observaciones or None,
        }
        async with httpx.AsyncClient(timeout=30.0) as client:
            await client.put(f"{API_URL}/proveedores/{self.prov_edit_id}", json=payload)
        self.prov_edit_id = ""
        self.mostrar_form_prov = False
        await self.cargar_proveedores()

    # ─── terceros ────────────────────────────────────────────────────────────

    async def cargar_terceros(self):
        try:
            async with httpx.AsyncClient(timeout=30.0) as client:
                r = await client.get(f"{API_URL}/terceros/")
            data = r.json()
            self.terceros = data if isinstance(data, list) else []
            self.nombres_terceros = [t["nombre"] for t in self.terceros]
        except Exception:
            self.terceros = []
            self.nombres_terceros = []

    async def agregar_tercero(self):
        if not self.terc_nombre or not self.terc_ciudad:
            self.terc_error = "Nombre y ciudad son obligatorios"
            return
        payload = {
            "nombre": self.terc_nombre,
            "ciudad": self.terc_ciudad,
            "telefono": self.terc_telefono or None,
            "email": self.terc_email or None,
            "empresa": self.terc_empresa or None,
            "observaciones": self.terc_observaciones or None,
        }
        async with httpx.AsyncClient(timeout=30.0) as client:
            r = await client.post(f"{API_URL}/terceros/", json=payload)
        if r.status_code == 200:
            self.terc_nombre = ""
            self.terc_ciudad = ""
            self.terc_telefono = ""
            self.terc_email = ""
            self.terc_empresa = ""
            self.terc_observaciones = ""
            self.terc_exito = "Tercero agregado"
            self.terc_error = ""
            self.mostrar_form_terc = False
            await self.cargar_terceros()
        else:
            self.terc_error = "Error al agregar tercero"

    async def eliminar_tercero(self, terc_id: str):
        async with httpx.AsyncClient(timeout=30.0) as client:
            await client.delete(f"{API_URL}/terceros/{terc_id}")
        await self.cargar_terceros()

    def iniciar_edit_tercero(self, terc_id: str, nombre: str, ciudad: str, telefono, email, empresa, obs):
        self.terc_edit_id = terc_id
        self.terc_nombre = nombre or ""
        self.terc_ciudad = ciudad or ""
        self.terc_telefono = telefono or ""
        self.terc_email = email or ""
        self.terc_empresa = empresa or ""
        self.terc_observaciones = obs or ""
        self.mostrar_form_terc = True

    async def guardar_edit_tercero(self):
        payload = {
            "nombre": self.terc_nombre,
            "ciudad": self.terc_ciudad,
            "telefono": self.terc_telefono or None,
            "email": self.terc_email or None,
            "empresa": self.terc_empresa or None,
            "observaciones": self.terc_observaciones or None,
        }
        async with httpx.AsyncClient(timeout=30.0) as client:
            await client.put(f"{API_URL}/terceros/{self.terc_edit_id}", json=payload)
        self.terc_edit_id = ""
        self.mostrar_form_terc = False
        await self.cargar_terceros()

    async def ver_stock_tercero(self, terc_id: str, terc_nombre: str):
        self.terc_sel_id = terc_id
        self.terc_sel_nombre = terc_nombre
        async with httpx.AsyncClient(timeout=30.0) as client:
            r = await client.get(f"{API_URL}/terceros/{terc_id}/stock")
        raw = r.json()
        for item in raw:
            item["prod_codigo"] = item.get("productos", {}).get("codigo", "")
            item["prod_desc"] = item.get("productos", {}).get("descripcion", "")
            item["prod_cat"] = item.get("productos", {}).get("categoria", "")
            item["stock_color"] = "red" if item["cantidad"] <= 0 else "green" if item["cantidad"] > 5 else "orange"
        self.terc_stock = raw
        self.pagina = "terceros_stock"

    # ─── equipos ─────────────────────────────────────────────────────────────

    async def cargar_equipos(self):
        async with httpx.AsyncClient(timeout=30.0) as client:
            r = await client.get(f"{API_URL}/equipos/")
        self.equipos = r.json()
        self.equipos_nombres = [e["nombre"] for e in self.equipos]

    def set_carga_equipo(self, nombre: str):
        self.carga_equipo_nombre = nombre
        eq = next((e for e in self.equipos if e["nombre"] == nombre), None)
        if eq:
            self.carga_equipo_id = eq["id"]
            tecnicos_equipo = [t for t in self.dir_personal if t.get("equipo_id") == eq["id"] and t.get("tipo") == "interno"]
            self.carga_tecnicos_presencia = [
                {"tecnico_id": t["id"], "nombre": t["nombre"], "presente": True, "motivo_ausencia": ""}
                for t in tecnicos_equipo
            ]

    def toggle_tecnico_presencia(self, tecnico_id: str):
        self.carga_tecnicos_presencia = [
            {**t, "presente": not t["presente"]} if t["tecnico_id"] == tecnico_id else t
            for t in self.carga_tecnicos_presencia
        ]

    def set_motivo_ausencia(self, tecnico_id: str, motivo: str):
        self.carga_tecnicos_presencia = [
            {**t, "motivo_ausencia": motivo} if t["tecnico_id"] == tecnico_id else t
            for t in self.carga_tecnicos_presencia
        ]

    def agregar_servicio_a_lista(self):
        if not self.carga_cliente_sel or not self.carga_tipo:
            self.carga_error = "Completá cliente y tipo"
            return
        import uuid
        nuevo = {
            "temp_id": str(uuid.uuid4())[:8],
            "cliente": self.carga_cliente_sel,
            "cliente_ref": self.carga_cliente_ref,
            "hora": self.carga_hora,
            "tipo_servicio": self.carga_tipo,
            "dispositivo": self.carga_dispositivo,
            "patente": self.carga_patente,
            "estado": self.carga_estado,
            "observaciones": self.carga_obs_serv,
        }
        self.carga_servicios = self.carga_servicios + [nuevo]
        self.carga_patente = ""
        self.carga_obs_serv = ""
        self.carga_error = ""

    def quitar_servicio_de_lista(self, temp_id: str):
        self.carga_servicios = [s for s in self.carga_servicios if s["temp_id"] != temp_id]

    async def guardar_carga_dia(self):
        if not self.carga_fecha or not self.carga_equipo_id:
            self.carga_error = "Completá fecha y equipo"
            return
        if not self.carga_servicios:
            self.carga_error = "Agregá al menos un servicio"
            return
        async with httpx.AsyncClient(timeout=30.0) as client:
            for s in self.carga_servicios:
                payload = {
                    "fecha": self.carga_fecha,
                    "hora_programada": s["hora"] or None,
                    "equipo_id": self.carga_equipo_id,
                    "cliente": s["cliente"],
                    "cliente_ref": s["cliente_ref"] or None,
                    "tipo_servicio": s["tipo_servicio"],
                    "dispositivo": s["dispositivo"] or None,
                    "patente": s["patente"] or None,
                    "estado": s["estado"],
                    "observaciones": s["observaciones"] or None,
                    "cargado_por": self.usuario,
                }
                await client.post(f"{API_URL}/servicios/", json=payload)
            if self.carga_hora_salida or self.carga_hora_llegada:
                mov_payload = {
                    "equipo_id": self.carga_equipo_id,
                    "fecha": self.carga_fecha,
                    "hora_salida": self.carga_hora_salida or None,
                    "hora_llegada": self.carga_hora_llegada or None,
                    "punto_inicio": self.carga_punto_inicio or None,
                    "punto_fin": self.carga_punto_fin or None,
                    "observaciones": self.carga_obs_mov or None,
                    "cargado_por": self.usuario,
                    "tecnicos": self.carga_tecnicos_presencia,
                }
                await client.post(f"{API_URL}/movimientos-camioneta/", json=mov_payload)
        self.carga_servicios = []
        self.carga_fecha = ""
        self.carga_equipo_id = ""
        self.carga_equipo_nombre = ""
        self.carga_cliente_sel = ""
        self.carga_hora = ""
        self.carga_tipo = "INSTALACION"
        self.carga_dispositivo = "GPS"
        self.carga_patente = ""
        self.carga_estado = "PENDIENTE"
        self.carga_punto_inicio = ""
        self.carga_hora_salida = ""
        self.carga_punto_fin = ""
        self.carga_hora_llegada = ""
        self.carga_obs_mov = ""
        self.carga_tecnicos_presencia = []
        self.carga_exito = "Carga del día guardada correctamente"
        self.carga_error = ""

    async def cargar_vista_dia(self):
        if not self.vista_fecha:
            return
        async with httpx.AsyncClient(timeout=30.0) as client:
            r = await client.get(f"{API_URL}/servicios/", params={"fecha": self.vista_fecha})
            r_mov = await client.get(f"{API_URL}/movimientos-camioneta/")
        servicios = r.json() if isinstance(r.json(), list) else []
        for s in servicios:
            s["estado_color"] = {"PENDIENTE": "orange", "CONFIRMADO": "blue", "REALIZADO": "green"}.get(s.get("estado", ""), "gray")
        eq1 = next((e for e in self.equipos if "1" in e["nombre"]), None)
        eq2 = next((e for e in self.equipos if "2" in e["nombre"]), None)
        self.vista_servicios_equipo1 = [s for s in servicios if s.get("equipo_id") == (eq1["id"] if eq1 else "")]
        self.vista_servicios_equipo2 = [s for s in servicios if s.get("equipo_id") == (eq2["id"] if eq2 else "")]
        movs = r_mov.json() if isinstance(r_mov.json(), list) else []
        self.vista_mov_equipo1 = {}
        self.vista_mov_equipo2 = {}
        for mov in movs:
            if mov.get("fecha") == self.vista_fecha:
                if eq1 and mov.get("equipo_id") == eq1["id"]:
                    self.vista_mov_equipo1 = mov
                elif eq2 and mov.get("equipo_id") == eq2["id"]:
                    self.vista_mov_equipo2 = mov
        # Poblar campos editables de movimientos
        m1 = self.vista_mov_equipo1
        self.vista_edit_mov1_salida = m1.get("hora_salida", "") or "" if m1 else ""
        self.vista_edit_mov1_llegada = m1.get("hora_llegada", "") or "" if m1 else ""
        self.vista_edit_mov1_inicio = m1.get("punto_inicio", "") or "" if m1 else ""
        self.vista_edit_mov1_fin = m1.get("punto_fin", "") or "" if m1 else ""
        m2 = self.vista_mov_equipo2
        self.vista_edit_mov2_salida = m2.get("hora_salida", "") or "" if m2 else ""
        self.vista_edit_mov2_llegada = m2.get("hora_llegada", "") or "" if m2 else ""
        self.vista_edit_mov2_inicio = m2.get("punto_inicio", "") or "" if m2 else ""
        self.vista_edit_mov2_fin = m2.get("punto_fin", "") or "" if m2 else ""

    async def guardar_movimiento_vista(self, equipo_num: str):
        if equipo_num == "1":
            mov = self.vista_mov_equipo1
            payload = {"hora_salida": self.vista_edit_mov1_salida or None, "hora_llegada": self.vista_edit_mov1_llegada or None, "punto_inicio": self.vista_edit_mov1_inicio or None, "punto_fin": self.vista_edit_mov1_fin or None}
        else:
            mov = self.vista_mov_equipo2
            payload = {"hora_salida": self.vista_edit_mov2_salida or None, "hora_llegada": self.vista_edit_mov2_llegada or None, "punto_inicio": self.vista_edit_mov2_inicio or None, "punto_fin": self.vista_edit_mov2_fin or None}
        if not mov or not mov.get("id"):
            return
        async with httpx.AsyncClient(timeout=30.0) as client:
            await client.put(f"{API_URL}/movimientos-camioneta/{mov['id']}", json=payload)
        self.vista_exito = f"Datos de camioneta Equipo {equipo_num} guardados"
        await self.cargar_vista_dia()

    async def actualizar_estado_vista(self, serv_id: str, nuevo_estado: str):
        async with httpx.AsyncClient(timeout=30.0) as client:
            await client.put(f"{API_URL}/servicios/{serv_id}", json={"estado": nuevo_estado})
        await self.cargar_vista_dia()

    async def cargar_historial_svc(self):
        params = {}
        if self.hist_filtro_estado:
            params["estado"] = self.hist_filtro_estado
        if self.hist_filtro_mes:
            params["mes"] = self.hist_filtro_mes
        if self.hist_filtro_anio:
            params["anio"] = self.hist_filtro_anio
        async with httpx.AsyncClient(timeout=30.0) as client:
            r = await client.get(f"{API_URL}/servicios/", params=params)
        raw = r.json()
        if not isinstance(raw, list):
            raw = []
        for s in raw:
            s["estado_color"] = {"PENDIENTE": "orange", "CONFIRMADO": "blue", "REALIZADO": "green"}.get(s.get("estado", ""), "gray")
            eq = next((e for e in self.equipos if e["id"] == s.get("equipo_id")), None)
            s["equipo_nombre"] = eq["nombre"] if eq else "-"
        self.hist_servicios = raw

    async def actualizar_estado_servicio(self, serv_id: str, nuevo_estado: str):
        async with httpx.AsyncClient(timeout=30.0) as client:
            await client.put(f"{API_URL}/servicios/{serv_id}", json={"estado": nuevo_estado})
        await self.cargar_historial_svc()

    hist_edit_equipo_nombre: str = ""

    def abrir_edit_hist(self, serv: dict):
        self.hist_edit_id = serv.get("id", "")
        self.hist_edit_fecha = serv.get("fecha", "")
        self.hist_edit_hora = serv.get("hora_programada", "") or ""
        self.hist_edit_cliente = serv.get("cliente", "")
        self.hist_edit_tipo = serv.get("tipo_servicio", "INSTALACION")
        self.hist_edit_dispositivo = serv.get("dispositivo", "") or ""
        self.hist_edit_patente = serv.get("patente", "") or ""
        self.hist_edit_estado = serv.get("estado", "PENDIENTE")
        self.hist_edit_obs = serv.get("observaciones", "") or ""
        self.hist_edit_equipo_id = serv.get("equipo_id", "") or ""
        eq = next((e for e in self.equipos if e["id"] == self.hist_edit_equipo_id), None)
        self.hist_edit_equipo_nombre = eq["nombre"] if eq else ""
        self.mostrar_edit_hist = True

    def set_hist_edit_equipo_sel(self, nombre: str):
        self.hist_edit_equipo_nombre = nombre
        eq = next((e for e in self.equipos if e["nombre"] == nombre), None)
        if eq:
            self.hist_edit_equipo_id = eq["id"]

    def cerrar_edit_hist(self):
        self.mostrar_edit_hist = False
        self.hist_edit_id = ""

    async def guardar_edit_hist(self):
        payload = {
            "fecha": self.hist_edit_fecha,
            "hora_programada": self.hist_edit_hora or None,
            "cliente": self.hist_edit_cliente,
            "tipo_servicio": self.hist_edit_tipo,
            "dispositivo": self.hist_edit_dispositivo or None,
            "patente": self.hist_edit_patente or None,
            "estado": self.hist_edit_estado,
            "observaciones": self.hist_edit_obs or None,
            "equipo_id": self.hist_edit_equipo_id or None,
        }
        async with httpx.AsyncClient(timeout=30.0) as client:
            await client.put(f"{API_URL}/servicios/{self.hist_edit_id}", json=payload)
        self.mostrar_edit_hist = False
        self.hist_edit_id = ""
        await self.cargar_historial_svc()

    async def eliminar_servicio_hist(self, serv_id: str):
        async with httpx.AsyncClient(timeout=30.0) as client:
            await client.delete(f"{API_URL}/servicios/{serv_id}")
        await self.cargar_historial_svc()

    # ─── directorio ──────────────────────────────────────────────────────────

    async def cargar_directorio_personal(self):
        async with httpx.AsyncClient(timeout=30.0) as client:
            r = await client.get(f"{API_URL}/directorio/")
        self.dir_personal = r.json()

    async def cargar_directorio_clientes(self):
        async with httpx.AsyncClient(timeout=30.0) as client:
            r = await client.get(f"{API_URL}/terceros/")
        data = r.json()
        self.dir_clientes_list = data if isinstance(data, list) else []
        self.dir_clientes_nombres = [c["nombre"] for c in self.dir_clientes_list]

    async def guardar_directorio(self):
        if not self.dir_nombre:
            self.dir_error = "El nombre es obligatorio"
            return
        payload = {
            "nombre": self.dir_nombre,
            "tipo": self.dir_tipo,
            "telefono": self.dir_telefono or None,
            "email": self.dir_email or None,
            "equipo_id": self.dir_equipo_id or None,
            "ciudad": self.dir_ciudad or None,
            "contacto": self.dir_contacto or None,
            "observaciones": self.dir_observaciones or None,
        }
        async with httpx.AsyncClient(timeout=30.0) as client:
            if self.dir_edit_id:
                await client.put(f"{API_URL}/directorio/{self.dir_edit_id}", json=payload)
            else:
                await client.post(f"{API_URL}/directorio/", json=payload)
        self.dir_nombre = ""
        self.dir_telefono = ""
        self.dir_email = ""
        self.dir_equipo_id = ""
        self.dir_ciudad = ""
        self.dir_contacto = ""
        self.dir_observaciones = ""
        self.dir_edit_id = ""
        self.dir_exito = "Guardado correctamente"
        self.dir_error = ""
        await self.cargar_directorio_personal()

    async def guardar_cliente(self):
        if not self.dir_nombre:
            self.dir_error = "El nombre es obligatorio"
            return
        payload = {
            "nombre": self.dir_nombre,
            "ciudad": self.dir_ciudad or "",
            "telefono": self.dir_telefono or None,
            "email": self.dir_email or None,
            "empresa": None,
            "observaciones": self.dir_observaciones or None,
        }
        async with httpx.AsyncClient(timeout=30.0) as client:
            if self.dir_edit_id:
                await client.put(f"{API_URL}/terceros/{self.dir_edit_id}", json=payload)
            else:
                await client.post(f"{API_URL}/terceros/", json=payload)
        self.dir_nombre = ""
        self.dir_ciudad = ""
        self.dir_telefono = ""
        self.dir_email = ""
        self.dir_observaciones = ""
        self.dir_edit_id = ""
        self.dir_exito = "Cliente guardado"
        self.dir_error = ""
        await self.cargar_directorio_clientes()

    def iniciar_edit_dir(self, entry_id: str, nombre: str, tipo: str, telefono, email, equipo_id, ciudad, contacto, obs):
        self.dir_edit_id = entry_id
        self.dir_nombre = nombre or ""
        self.dir_tipo = tipo or "interno"
        self.dir_telefono = telefono or ""
        self.dir_email = email or ""
        self.dir_equipo_id = equipo_id or ""
        self.dir_ciudad = ciudad or ""
        self.dir_contacto = contacto or ""
        self.dir_observaciones = obs or ""

    def iniciar_edit_cliente_dir(self, entry_id: str, nombre: str, ciudad, telefono, email, obs):
        self.dir_edit_id = entry_id
        self.dir_nombre = nombre or ""
        self.dir_ciudad = ciudad or ""
        self.dir_telefono = telefono or ""
        self.dir_email = email or ""
        self.dir_observaciones = obs or ""

    # ─── estadísticas ────────────────────────────────────────────────────────

    async def cargar_stats_horas(self):
        params = {}
        if self.stats2_mes:
            params["mes"] = self.stats2_mes
        if self.stats2_anio:
            params["anio"] = self.stats2_anio
        async with httpx.AsyncClient(timeout=30.0) as client:
            r = await client.get(f"{API_URL}/estadisticas/horas", params=params)
        data = r.json()
        self.stats2_tecnicos = data.get("tecnicos", [])
        self.stats2_movimientos = data.get("movimientos", [])
        for t in self.stats2_tecnicos:
            mins = t.get("diferencia_minutos", 0)
            horas = abs(mins) // 60
            minutos = abs(mins) % 60
            signo = "+" if mins >= 0 else "\u2212"
            t["diferencia_str"] = f"{signo}{horas}h {minutos:02d}m"
            t["diferencia_color"] = "green" if mins >= 0 else "red"
            t_mins = t.get("minutos_trabajados", 0)
            t["horas_str"] = f"{t_mins // 60}h {t_mins % 60:02d}m"

    def set_stats_cli_cliente_nombre(self, nombre: str):
        self.stats_cli_cliente_id = nombre
        # Buscar el id del tercero por nombre
        cli = next((c for c in self.dir_clientes_list if c["nombre"] == nombre), None)
        if cli:
            self.stats_cli_cliente_ref = cli["id"]
        else:
            self.stats_cli_cliente_ref = ""

    async def cargar_stats_clientes(self):
        params = {}
        if self.stats_cli_mes:
            params["mes"] = self.stats_cli_mes
        if self.stats_cli_anio:
            params["anio"] = self.stats_cli_anio
        if hasattr(self, 'stats_cli_cliente_ref') and self.stats_cli_cliente_ref:
            params["cliente_id"] = self.stats_cli_cliente_ref
        async with httpx.AsyncClient(timeout=30.0) as client:
            r = await client.get(f"{API_URL}/estadisticas/servicios-cliente", params=params)
        data = r.json() if isinstance(r.json(), dict) else {}
        resumen = data.get("resumen", {})
        self.stats_cli_resumen = {
            "total": resumen.get("total", 0),
            "instalaciones": resumen.get("INSTALACION", 0),
            "revisiones": resumen.get("REVISION", 0),
            "desinstalaciones": resumen.get("DESINSTALACION", 0),
        }
        raw = data.get("servicios", [])
        for s in raw:
            s["estado_color"] = {"PENDIENTE": "orange", "CONFIRMADO": "blue", "REALIZADO": "green"}.get(s.get("estado", ""), "gray")
        self.stats_cli_servicios = raw

    async def cargar_stats_cruzado(self):
        params = {}
        if self.stats_cruz_mes:
            params["mes"] = self.stats_cruz_mes
        if self.stats_cruz_anio:
            params["anio"] = self.stats_cruz_anio
        async with httpx.AsyncClient(timeout=30.0) as client:
            r = await client.get(f"{API_URL}/estadisticas/reporte-cruzado", params=params)
        data = r.json()
        tecnicos = data.get("tecnicos", [])
        for t in tecnicos:
            mins = t.get("diferencia_minutos", 0)
            t["balance_str"] = f"{'+'if mins>=0 else chr(8722)}{abs(mins)//60}h {abs(mins)%60:02d}m"
            t["balance_color"] = "green" if mins >= 0 else "red"
        self.stats_cruz_tecnicos = tecnicos

    # ─── confirm / eliminar ──────────────────────────────────────────────────

    def iniciar_confirm(self, tipo: str, id: str):
        self.confirm_tipo = tipo
        self.confirm_id = id
        self.mostrar_confirm = True

    def cancelar_confirm(self):
        self.mostrar_confirm = False
        self.confirm_id = ""
        self.confirm_tipo = ""

    async def confirmar_eliminar(self):
        tipo = self.confirm_tipo
        id_ = self.confirm_id
        self.mostrar_confirm = False
        self.confirm_id = ""
        self.confirm_tipo = ""
        async with httpx.AsyncClient(timeout=30.0) as client:
            if tipo == "producto":
                await client.delete(f"{API_URL}/stock/productos/{id_}")
                await self.cargar_productos()
            elif tipo == "proveedor":
                await client.delete(f"{API_URL}/proveedores/{id_}")
                await self.cargar_proveedores()
            elif tipo == "tercero":
                await client.delete(f"{API_URL}/terceros/{id_}")
                await self.cargar_terceros()
            elif tipo == "servicio_hist":
                await client.delete(f"{API_URL}/servicios/{id_}")
                await self.cargar_historial_svc()
            elif tipo == "dir_personal":
                await client.delete(f"{API_URL}/directorio/{id_}")
                await self.cargar_directorio_personal()
            elif tipo == "dir_cliente":
                await client.delete(f"{API_URL}/terceros/{id_}")
                await self.cargar_directorio_clientes()


# ─── MODULOS ─────────────────────────────────────────────────────────────────

MODULOS = [
    {"id": "servicios", "icon": "wrench", "label": "Servicios",
     "subs": [("carga_dia", "Carga del día"), ("vista_dia", "Vista del día"), ("historial_svc", "Historial")]},
    {"id": "directorio", "icon": "book-user", "label": "Directorio",
     "subs": [("dir_carga", "Carga"), ("dir_personal", "Personal"), ("dir_clientes", "Clientes"), ("dir_proveedores", "Proveedores")]},
    {"id": "estadisticas", "icon": "chart-bar", "label": "Estadísticas",
     "subs": [("stats_horas", "Horas trabajadas"), ("stats_clientes", "Servicios por cliente"), ("stats_cruzado", "Reporte cruzado")]},
    {"id": "stock", "icon": "package", "label": "Stock",
     "subs": [("stock_actual", "Stock actual"), ("stock_entrada", "Entrada"), ("stock_salida", "Transferencia/Salida"), ("stock_productos", "Productos"), ("stock_proveedores", "Proveedores")]},
]


# ─── SIDEBAR ─────────────────────────────────────────────────────────────────

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


def confirm_dialog() -> rx.Component:
    return rx.alert_dialog.root(
        rx.alert_dialog.content(
            rx.alert_dialog.title("Confirmar eliminación"),
            rx.alert_dialog.description("¿Seguro que querés eliminar este registro? Esta acción no se puede deshacer."),
            rx.flex(
                rx.button("Cancelar", on_click=State.cancelar_confirm, color_scheme="gray", variant="soft"),
                rx.button("Eliminar", on_click=State.confirmar_eliminar, color_scheme="red"),
                spacing="3", justify="end", margin_top="16px",
            ),
        ),
        open=State.mostrar_confirm,
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
        confirm_dialog(),
        spacing="0", width="100%",
    )


# ─── LOGIN ───────────────────────────────────────────────────────────────────

def login_page() -> rx.Component:
    return rx.center(
        rx.vstack(
            rx.heading("⚙️ App-Logic", size="8", color="blue"),
            rx.text("Ingresá para continuar", color="gray"),
            rx.input(placeholder="Usuario", value=State.login_input, on_change=State.set_login_input),
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


# ─── STOCK PAGES ─────────────────────────────────────────────────────────────

def stock_row(item: dict) -> rx.Component:
    return rx.table.row(
        rx.table.cell(item["prod_codigo"]),
        rx.table.cell(item["prod_desc"]),
        rx.table.cell(item["prod_cat"]),
        rx.table.cell(item["ubic_nombre"]),
        rx.table.cell(rx.text(item["cantidad"], color=item["stock_color"], font_weight="700")),
    )


def page_stock_actual() -> rx.Component:
    return layout(
        rx.vstack(
            rx.heading("Stock Actual", size="6"),
            rx.divider(),
            rx.hstack(
                rx.vstack(rx.text("Ubicación", font_size="12px", color="gray"), rx.select(State.nombres_ubicaciones, placeholder="Todas", value=State.stock_ubicacion_filtro, on_change=State.set_stock_ubicacion_filtro, width="200px"), spacing="1"),
                rx.button("Filtrar", on_click=State.cargar_stock_actual, color_scheme="blue"),
                spacing="4", align="end",
            ),
            rx.table.root(
                rx.table.header(rx.table.row(
                    rx.table.column_header_cell("Código"),
                    rx.table.column_header_cell("Descripción"),
                    rx.table.column_header_cell("Categoría"),
                    rx.table.column_header_cell("Ubicación"),
                    rx.table.column_header_cell("Cantidad"),
                )),
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
                rx.vstack(rx.text("Producto", font_size="12px", color="gray"), rx.select(State.nombres_productos, placeholder="Seleccionar producto", value=State.entrada_producto, on_change=State.set_entrada_producto, width="300px"), spacing="1"),
                rx.vstack(rx.text("Cantidad", font_size="12px", color="gray"), rx.input(type="number", value=State.entrada_cantidad, on_change=State.set_entrada_cantidad, width="100px"), spacing="1"),
                rx.vstack(rx.text("Fecha", font_size="12px", color="gray"), rx.input(type="date", value=State.entrada_fecha, on_change=State.set_entrada_fecha, width="160px"), spacing="1"),
                spacing="4", wrap="wrap",
            ),
            rx.vstack(rx.text("Origen / Observación", font_size="12px", color="gray"), rx.input(placeholder="Proveedor o motivo", value=State.entrada_observacion, on_change=State.set_entrada_observacion, width="400px"), spacing="1"),
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
                rx.vstack(rx.text("Tipo", font_size="12px", color="gray"), rx.select(["TRANSFERENCIA", "SALIDA", "DESCARTE"], value=State.mov_tipo, on_change=State.set_mov_tipo, width="160px"), spacing="1"),
                rx.vstack(rx.text("Producto", font_size="12px", color="gray"), rx.select(State.nombres_productos, placeholder="Seleccionar", value=State.mov_producto, on_change=State.set_mov_producto, width="300px"), spacing="1"),
                rx.vstack(rx.text("Cantidad", font_size="12px", color="gray"), rx.input(type="number", value=State.mov_cantidad, on_change=State.set_mov_cantidad, width="100px"), spacing="1"),
                spacing="4", wrap="wrap",
            ),
            rx.hstack(
                rx.vstack(rx.text("Origen", font_size="12px", color="gray"), rx.select(State.nombres_ubicaciones, placeholder="Origen", value=State.mov_origen, on_change=State.set_mov_origen, width="200px"), spacing="1"),
                rx.vstack(rx.text("Destino", font_size="12px", color="gray"), rx.select(State.nombres_ubicaciones, placeholder="Destino", value=State.mov_destino, on_change=State.set_mov_destino, width="200px"), spacing="1"),
                rx.vstack(rx.text("Fecha", font_size="12px", color="gray"), rx.input(type="date", value=State.mov_fecha, on_change=State.set_mov_fecha, width="160px"), spacing="1"),
                spacing="4", wrap="wrap",
            ),
            rx.vstack(rx.text("Observación", font_size="12px", color="gray"), rx.input(value=State.mov_observacion, on_change=State.set_mov_observacion, width="400px"), spacing="1"),
            rx.cond(State.mov_error != "", rx.callout(State.mov_error, color="red")),
            rx.cond(State.mov_exito != "", rx.callout(State.mov_exito, color="green")),
            rx.button("Registrar movimiento", on_click=State.registrar_transferencia, color_scheme="blue", size="3"),
            spacing="4", width="100%", max_width="700px",
            on_mount=State.cargar_productos_y_ubicaciones,
        )
    )


def producto_row(prod: dict) -> rx.Component:
    return rx.table.row(
        rx.table.cell(prod["codigo"]),
        rx.table.cell(prod["descripcion"]),
        rx.table.cell(prod["categoria"]),
        rx.table.cell(rx.hstack(
            rx.button("✏️", size="1", color_scheme="blue", on_click=State.iniciar_edit_producto(prod["id"], prod["descripcion"], prod["categoria"])),
            rx.button("🗑", size="1", color_scheme="red", on_click=State.iniciar_confirm("producto", prod["id"])),
            spacing="2",
        )),
    )


def page_stock_productos() -> rx.Component:
    return layout(
        rx.vstack(
            rx.heading("Productos", size="6"),
            rx.divider(),
            rx.hstack(
                rx.button("+ Agregar producto", on_click=State.set_mostrar_form_prod(True), color_scheme="blue"),
                rx.vstack(rx.text("Filtrar por categoría", font_size="12px", color="gray"), rx.select(["DISPOSITIVOS", "CABLES", "ACCESORIOS", "INSUMOS", "HERRAMIENTAS"], placeholder="Todas", value=State.prod_filtro_cat, on_change=State.set_prod_filtro_cat, width="180px"), spacing="1"),
                spacing="4", align="end",
            ),
            rx.cond(State.mostrar_form_prod,
                rx.box(rx.vstack(
                    rx.hstack(
                        rx.vstack(rx.text("Código", font_size="12px", color="gray"), rx.input(value=State.prod_codigo, on_change=State.set_prod_codigo, width="120px"), spacing="1"),
                        rx.vstack(rx.text("Descripción", font_size="12px", color="gray"), rx.input(value=State.prod_descripcion, on_change=State.set_prod_descripcion, width="300px"), spacing="1"),
                        rx.vstack(rx.text("Categoría", font_size="12px", color="gray"), rx.select(["DISPOSITIVOS", "CABLES", "ACCESORIOS", "INSUMOS", "HERRAMIENTAS"], value=State.prod_categoria, on_change=State.set_prod_categoria, width="160px"), spacing="1"),
                        spacing="4",
                    ),
                    rx.cond(State.prod_error != "", rx.callout(State.prod_error, color="red")),
                    rx.hstack(rx.button("Guardar", on_click=State.agregar_producto, color_scheme="blue"), rx.button("Cancelar", on_click=State.set_mostrar_form_prod(False), color_scheme="gray"), spacing="3"),
                    spacing="3"),
                    padding="16px", border="1px solid #e2e6ea", border_radius="8px", background="white", width="100%"),
            ),
            rx.cond(State.prod_edit_id != "",
                rx.box(rx.vstack(
                    rx.text("Editando producto", font_weight="600"),
                    rx.hstack(
                        rx.vstack(rx.text("Descripción", font_size="12px", color="gray"), rx.input(value=State.prod_edit_desc, on_change=State.set_prod_edit_desc, width="300px"), spacing="1"),
                        rx.vstack(rx.text("Categoría", font_size="12px", color="gray"), rx.select(["DISPOSITIVOS", "CABLES", "ACCESORIOS", "INSUMOS", "HERRAMIENTAS"], value=State.prod_edit_cat, on_change=State.set_prod_edit_cat, width="160px"), spacing="1"),
                        spacing="4",
                    ),
                    rx.hstack(rx.button("Guardar cambios", on_click=State.guardar_edit_producto, color_scheme="blue"), rx.button("Cancelar", on_click=State.set_prod_edit_id(""), color_scheme="gray"), spacing="3"),
                    spacing="3"),
                    padding="16px", border="1px solid #bfdbfe", border_radius="8px", background="white", width="100%"),
            ),
            rx.cond(State.prod_exito != "", rx.callout(State.prod_exito, color="green")),
            rx.table.root(
                rx.table.header(rx.table.row(rx.table.column_header_cell("Código"), rx.table.column_header_cell("Descripción"), rx.table.column_header_cell("Categoría"), rx.table.column_header_cell(""))),
                rx.table.body(rx.foreach(State.productos_filtrados, producto_row)),
                width="100%",
            ),
            spacing="4", width="100%",
            on_mount=State.cargar_productos,
        )
    )


# ─── PROVEEDORES PAGE ────────────────────────────────────────────────────────

def proveedor_row(prov: dict) -> rx.Component:
    return rx.table.row(
        rx.table.cell(prov["nombre"]),
        rx.table.cell(rx.cond(prov["responsable"], prov["responsable"], "-")),
        rx.table.cell(rx.cond(prov["telefono"], prov["telefono"], "-")),
        rx.table.cell(rx.cond(prov["email"], prov["email"], "-")),
        rx.table.cell(rx.cond(prov["productos_que_vende"], prov["productos_que_vende"], "-")),
        rx.table.cell(rx.hstack(
            rx.button("✏️", size="1", color_scheme="blue", on_click=State.iniciar_edit_proveedor(prov["id"], prov["nombre"], prov["responsable"], prov["telefono"], prov["email"], prov["direccion"], prov["productos_que_vende"], prov["observaciones"])),
            rx.button("🗑", size="1", color_scheme="red", on_click=State.iniciar_confirm("proveedor", prov["id"])),
            spacing="2",
        )),
    )


def page_proveedores() -> rx.Component:
    return layout(
        rx.vstack(
            rx.heading("Proveedores", size="6"),
            rx.divider(),
            rx.button("+ Agregar proveedor", on_click=State.set_mostrar_form_prov(True), color_scheme="blue"),
            rx.cond(State.mostrar_form_prov,
                rx.box(rx.vstack(
                    rx.text(rx.cond(State.prov_edit_id != "", "Editar proveedor", "Nuevo proveedor"), font_weight="600", font_size="14px"),
                    rx.hstack(
                        rx.vstack(rx.text("Nombre", font_size="12px", color="gray"), rx.input(value=State.prov_nombre, on_change=State.set_prov_nombre, width="200px"), spacing="1"),
                        rx.vstack(rx.text("Responsable", font_size="12px", color="gray"), rx.input(value=State.prov_responsable, on_change=State.set_prov_responsable, width="200px"), spacing="1"),
                        rx.vstack(rx.text("Teléfono", font_size="12px", color="gray"), rx.input(value=State.prov_telefono, on_change=State.set_prov_telefono, width="150px"), spacing="1"),
                        spacing="4", wrap="wrap",
                    ),
                    rx.hstack(
                        rx.vstack(rx.text("Email", font_size="12px", color="gray"), rx.input(value=State.prov_email, on_change=State.set_prov_email, width="220px"), spacing="1"),
                        rx.vstack(rx.text("Dirección", font_size="12px", color="gray"), rx.input(value=State.prov_direccion, on_change=State.set_prov_direccion, width="220px"), spacing="1"),
                        spacing="4", wrap="wrap",
                    ),
                    rx.vstack(rx.text("Productos que vende", font_size="12px", color="gray"), rx.input(value=State.prov_productos, on_change=State.set_prov_productos, width="450px"), spacing="1"),
                    rx.vstack(rx.text("Observaciones", font_size="12px", color="gray"), rx.text_area(value=State.prov_observaciones, on_change=State.set_prov_observaciones, width="450px", rows="2"), spacing="1"),
                    rx.cond(State.prov_error != "", rx.callout(State.prov_error, color="red")),
                    rx.hstack(
                        rx.button(rx.cond(State.prov_edit_id != "", "Guardar cambios", "Guardar"), on_click=rx.cond(State.prov_edit_id != "", State.guardar_edit_proveedor, State.agregar_proveedor), color_scheme="blue"),
                        rx.button("Cancelar", on_click=State.set_mostrar_form_prov(False), color_scheme="gray"),
                        spacing="3",
                    ),
                    spacing="3"),
                    padding="16px", border="1px solid #e2e6ea", border_radius="8px", background="white", width="100%"),
            ),
            rx.cond(State.prov_exito != "", rx.callout(State.prov_exito, color="green")),
            rx.table.root(
                rx.table.header(rx.table.row(rx.table.column_header_cell("Nombre"), rx.table.column_header_cell("Responsable"), rx.table.column_header_cell("Teléfono"), rx.table.column_header_cell("Email"), rx.table.column_header_cell("Productos"), rx.table.column_header_cell(""))),
                rx.table.body(rx.foreach(State.proveedores, proveedor_row)),
                width="100%",
            ),
            spacing="4", width="100%",
            on_mount=State.cargar_proveedores,
        )
    )


# ─── TERCEROS PAGES ──────────────────────────────────────────────────────────

def tercero_row(terc: dict) -> rx.Component:
    return rx.table.row(
        rx.table.cell(terc["nombre"]),
        rx.table.cell(terc["ciudad"]),
        rx.table.cell(rx.cond(terc["empresa"], terc["empresa"], "-")),
        rx.table.cell(rx.cond(terc["telefono"], terc["telefono"], "-")),
        rx.table.cell(rx.cond(terc["email"], terc["email"], "-")),
        rx.table.cell(rx.hstack(
            rx.button("📦", size="1", color_scheme="orange", on_click=State.ver_stock_tercero(terc["id"], terc["nombre"])),
            rx.button("✏️", size="1", color_scheme="blue", on_click=State.iniciar_edit_tercero(terc["id"], terc["nombre"], terc["ciudad"], terc["telefono"], terc["email"], terc["empresa"], terc["observaciones"])),
            rx.button("🗑", size="1", color_scheme="red", on_click=State.iniciar_confirm("tercero", terc["id"])),
            spacing="2",
        )),
    )


def terc_stock_row(item: dict) -> rx.Component:
    return rx.table.row(
        rx.table.cell(item["prod_codigo"]),
        rx.table.cell(item["prod_desc"]),
        rx.table.cell(item["prod_cat"]),
        rx.table.cell(rx.text(item["cantidad"], color=item["stock_color"], font_weight="700")),
    )


def page_terceros_lista() -> rx.Component:
    return layout(
        rx.vstack(
            rx.heading("Terceros", size="6"),
            rx.divider(),
            rx.button("+ Agregar tercero", on_click=State.set_mostrar_form_terc(True), color_scheme="blue"),
            rx.cond(State.mostrar_form_terc,
                rx.box(rx.vstack(
                    rx.text(rx.cond(State.terc_edit_id != "", "Editar tercero", "Nuevo tercero"), font_weight="600", font_size="14px"),
                    rx.hstack(
                        rx.vstack(rx.text("Nombre", font_size="12px", color="gray"), rx.input(value=State.terc_nombre, on_change=State.set_terc_nombre, width="200px"), spacing="1"),
                        rx.vstack(rx.text("Ciudad", font_size="12px", color="gray"), rx.input(value=State.terc_ciudad, on_change=State.set_terc_ciudad, width="160px"), spacing="1"),
                        rx.vstack(rx.text("Empresa", font_size="12px", color="gray"), rx.input(value=State.terc_empresa, on_change=State.set_terc_empresa, width="180px"), spacing="1"),
                        spacing="4", wrap="wrap",
                    ),
                    rx.hstack(
                        rx.vstack(rx.text("Teléfono", font_size="12px", color="gray"), rx.input(value=State.terc_telefono, on_change=State.set_terc_telefono, width="160px"), spacing="1"),
                        rx.vstack(rx.text("Email", font_size="12px", color="gray"), rx.input(value=State.terc_email, on_change=State.set_terc_email, width="220px"), spacing="1"),
                        spacing="4", wrap="wrap",
                    ),
                    rx.vstack(rx.text("Observaciones", font_size="12px", color="gray"), rx.text_area(value=State.terc_observaciones, on_change=State.set_terc_observaciones, width="450px", rows="2"), spacing="1"),
                    rx.cond(State.terc_error != "", rx.callout(State.terc_error, color="red")),
                    rx.hstack(
                        rx.button(rx.cond(State.terc_edit_id != "", "Guardar cambios", "Guardar"), on_click=rx.cond(State.terc_edit_id != "", State.guardar_edit_tercero, State.agregar_tercero), color_scheme="blue"),
                        rx.button("Cancelar", on_click=State.set_mostrar_form_terc(False), color_scheme="gray"),
                        spacing="3",
                    ),
                    spacing="3"),
                    padding="16px", border="1px solid #e2e6ea", border_radius="8px", background="white", width="100%"),
            ),
            rx.cond(State.terc_exito != "", rx.callout(State.terc_exito, color="green")),
            rx.table.root(
                rx.table.header(rx.table.row(rx.table.column_header_cell("Nombre"), rx.table.column_header_cell("Ciudad"), rx.table.column_header_cell("Empresa"), rx.table.column_header_cell("Teléfono"), rx.table.column_header_cell("Email"), rx.table.column_header_cell(""))),
                rx.table.body(rx.foreach(State.terceros, tercero_row)),
                width="100%",
            ),
            spacing="4", width="100%",
            on_mount=State.cargar_terceros,
        )
    )


def page_terceros_stock() -> rx.Component:
    return layout(
        rx.vstack(
            rx.hstack(
                rx.button("← Volver", on_click=State.set_pagina("terceros_lista"), color_scheme="gray", size="2"),
                rx.heading(f"Stock de {State.terc_sel_nombre}", size="6"),
                spacing="4", align="center",
            ),
            rx.divider(),
            rx.cond(
                State.terc_stock,
                rx.table.root(
                    rx.table.header(rx.table.row(rx.table.column_header_cell("Código"), rx.table.column_header_cell("Descripción"), rx.table.column_header_cell("Categoría"), rx.table.column_header_cell("Cantidad"))),
                    rx.table.body(rx.foreach(State.terc_stock, terc_stock_row)),
                    width="100%",
                ),
                rx.text("Sin stock registrado para este tercero.", color="gray"),
            ),
            spacing="4", width="100%",
        )
    )


# ─── SERVICIOS: CARGA DEL DÍA ────────────────────────────────────────────────

def servicio_en_lista_row(s: dict) -> rx.Component:
    return rx.table.row(
        rx.table.cell(s["cliente"]),
        rx.table.cell(s["tipo_servicio"]),
        rx.table.cell(s["dispositivo"]),
        rx.table.cell(rx.cond(s["patente"], s["patente"], "-")),
        rx.table.cell(rx.cond(s["hora"], s["hora"], "-")),
        rx.table.cell(s["estado"]),
        rx.table.cell(rx.button("✕", size="1", color_scheme="red", on_click=State.quitar_servicio_de_lista(s["temp_id"]))),
    )


def tecnico_presencia_row(t: dict) -> rx.Component:
    return rx.hstack(
        rx.checkbox(
            checked=t["presente"],
            on_change=lambda _: State.toggle_tecnico_presencia(t["tecnico_id"]),
        ),
        rx.text(t["nombre"], font_size="13px"),
        rx.cond(
            ~t["presente"],
            rx.select(
                ["Licencia", "Vacaciones", "Enfermedad", "Otro"],
                placeholder="Motivo",
                value=t["motivo_ausencia"],
                on_change=lambda v: State.set_motivo_ausencia(t["tecnico_id"], v),
                width="160px",
            ),
        ),
        spacing="3", align="center",
    )


def page_carga_dia() -> rx.Component:
    return layout(
        rx.vstack(
            rx.heading("Carga del Día", size="6"),
            rx.divider(),

            # Header: fecha + equipo
            rx.hstack(
                rx.vstack(rx.text("Fecha", font_size="12px", font_weight="600", color="gray"), rx.input(type="date", value=State.carga_fecha, on_change=State.set_carga_fecha, width="180px"), spacing="1"),
                rx.vstack(rx.text("Equipo", font_size="12px", font_weight="600", color="gray"), rx.select(State.equipos_nombres, placeholder="Seleccionar equipo", value=State.carga_equipo_nombre, on_change=State.set_carga_equipo, width="200px"), spacing="1"),
                spacing="4", align="end",
            ),

            # Sección agregar servicio
            rx.box(
                rx.vstack(
                    rx.text("Agregar servicio", font_size="14px", font_weight="700", color="#1e3a8a"),
                    rx.hstack(
                        rx.vstack(rx.text("Cliente", font_size="12px", color="gray"), rx.select(State.dir_clientes_nombres, placeholder="Seleccionar cliente", value=State.carga_cliente_sel, on_change=State.set_carga_cliente_sel, width="200px"), spacing="1"),
                        rx.vstack(rx.text("Ref cliente", font_size="12px", color="gray"), rx.input(placeholder="Referencia interna", value=State.carga_cliente_ref, on_change=State.set_carga_cliente_ref, width="160px"), spacing="1"),
                        rx.vstack(rx.text("Hora", font_size="12px", color="gray"), rx.input(type="time", value=State.carga_hora, on_change=State.set_carga_hora, width="120px"), spacing="1"),
                        spacing="4", wrap="wrap",
                    ),
                    rx.hstack(
                        rx.vstack(rx.text("Tipo", font_size="12px", color="gray"), rx.select(["INSTALACION", "REVISION", "DESINSTALACION"], value=State.carga_tipo, on_change=State.set_carga_tipo, width="160px"), spacing="1"),
                        rx.vstack(rx.text("Dispositivo", font_size="12px", color="gray"), rx.select(["GPS", "LECTORA", "GPS y LECTORA"], value=State.carga_dispositivo, on_change=State.set_carga_dispositivo, width="160px"), spacing="1"),
                        rx.vstack(rx.text("Patente", font_size="12px", color="gray"), rx.input(value=State.carga_patente, on_change=State.set_carga_patente, width="140px"), spacing="1"),
                        rx.vstack(rx.text("Estado", font_size="12px", color="gray"), rx.select(["PENDIENTE", "CONFIRMADO", "REALIZADO"], value=State.carga_estado, on_change=State.set_carga_estado, width="150px"), spacing="1"),
                        spacing="4", wrap="wrap",
                    ),
                    rx.vstack(rx.text("Observaciones", font_size="12px", color="gray"), rx.input(value=State.carga_obs_serv, on_change=State.set_carga_obs_serv, width="500px"), spacing="1"),
                    rx.cond(State.carga_error != "", rx.callout(State.carga_error, color="red")),
                    rx.button("+ Agregar servicio a lista", on_click=State.agregar_servicio_a_lista, color_scheme="blue"),
                    spacing="3",
                ),
                padding="16px", border="1px solid #bfdbfe", border_radius="8px", background="white", width="100%",
            ),

            # Lista servicios preparados
            rx.cond(
                State.carga_servicios,
                rx.vstack(
                    rx.text("Servicios a guardar", font_size="13px", font_weight="600", color="#374151"),
                    rx.table.root(
                        rx.table.header(rx.table.row(
                            rx.table.column_header_cell("Cliente"),
                            rx.table.column_header_cell("Tipo"),
                            rx.table.column_header_cell("Dispositivo"),
                            rx.table.column_header_cell("Patente"),
                            rx.table.column_header_cell("Hora"),
                            rx.table.column_header_cell("Estado"),
                            rx.table.column_header_cell(""),
                        )),
                        rx.table.body(rx.foreach(State.carga_servicios, servicio_en_lista_row)),
                        width="100%",
                    ),
                    spacing="2", width="100%",
                ),
            ),

            # Movimiento camioneta
            rx.box(
                rx.vstack(
                    rx.text("Movimiento de camioneta", font_size="14px", font_weight="700", color="#1e3a8a"),
                    rx.hstack(
                        rx.vstack(rx.text("Punto inicio", font_size="12px", color="gray"), rx.select(["Oficina", "Casa Maxi", "Casa Lautaro", "Casa Hugo", "Casa Sergio", "Otro"], placeholder="Seleccionar", value=State.carga_punto_inicio, on_change=State.set_carga_punto_inicio, width="180px"), spacing="1"),
                        rx.vstack(rx.text("Hora salida", font_size="12px", color="gray"), rx.input(type="time", value=State.carga_hora_salida, on_change=State.set_carga_hora_salida, width="120px"), spacing="1"),
                        rx.vstack(rx.text("Punto fin", font_size="12px", color="gray"), rx.select(["Oficina", "Casa Maxi", "Casa Lautaro", "Casa Hugo", "Casa Sergio", "Otro"], placeholder="Seleccionar", value=State.carga_punto_fin, on_change=State.set_carga_punto_fin, width="180px"), spacing="1"),
                        rx.vstack(rx.text("Hora llegada", font_size="12px", color="gray"), rx.input(type="time", value=State.carga_hora_llegada, on_change=State.set_carga_hora_llegada, width="120px"), spacing="1"),
                        spacing="4", wrap="wrap",
                    ),
                    rx.vstack(rx.text("Observaciones", font_size="12px", color="gray"), rx.input(value=State.carga_obs_mov, on_change=State.set_carga_obs_mov, width="500px"), spacing="1"),
                    spacing="3",
                ),
                padding="16px", border="1px solid #d1fae5", border_radius="8px", background="white", width="100%",
            ),

            # Técnicos presentes
            rx.cond(
                State.carga_tecnicos_presencia,
                rx.box(
                    rx.vstack(
                        rx.text("Técnicos presentes", font_size="14px", font_weight="700", color="#1e3a8a"),
                        rx.foreach(State.carga_tecnicos_presencia, tecnico_presencia_row),
                        spacing="2",
                    ),
                    padding="16px", border="1px solid #fde68a", border_radius="8px", background="white", width="100%",
                ),
            ),

            rx.cond(State.carga_exito != "", rx.callout(State.carga_exito, color="green")),
            rx.button("Guardar todo", on_click=State.guardar_carga_dia, color_scheme="green", size="3"),
            spacing="4", width="100%",
            on_mount=[State.cargar_equipos, State.cargar_directorio_clientes, State.cargar_directorio_personal],
        )
    )


# ─── SERVICIOS: VISTA DEL DÍA ─────────────────────────────────────────────────

def vista_servicio_row(s: dict) -> rx.Component:
    return rx.table.row(
        rx.table.cell(rx.cond(s["hora_programada"], s["hora_programada"], "-")),
        rx.table.cell(s["cliente"]),
        rx.table.cell(s["tipo_servicio"]),
        rx.table.cell(rx.cond(s["dispositivo"], s["dispositivo"], "-")),
        rx.table.cell(rx.cond(s["patente"], s["patente"], "-")),
        rx.table.cell(
            rx.select(
                ["PENDIENTE", "CONFIRMADO", "REALIZADO"],
                value=s["estado"],
                on_change=lambda v: State.actualizar_estado_vista(s["id"], v),
                width="140px", size="1",
            )
        ),
    )


def vista_mov_editable(equipo_num: str, color: str, bg: str, salida_val, llegada_val, inicio_val, fin_val, set_salida, set_llegada, set_inicio, set_fin) -> rx.Component:
    return rx.box(
        rx.vstack(
            rx.hstack(
                rx.vstack(rx.text("Hora salida", font_size="11px", color="gray"), rx.input(type="time", value=salida_val, on_change=set_salida, width="130px", size="1"), spacing="0"),
                rx.vstack(rx.text("Hora llegada", font_size="11px", color="gray"), rx.input(type="time", value=llegada_val, on_change=set_llegada, width="130px", size="1"), spacing="0"),
                spacing="3",
            ),
            rx.hstack(
                rx.vstack(rx.text("Punto inicio", font_size="11px", color="gray"), rx.input(value=inicio_val, on_change=set_inicio, width="130px", size="1", placeholder="Inicio"), spacing="0"),
                rx.vstack(rx.text("Punto fin", font_size="11px", color="gray"), rx.input(value=fin_val, on_change=set_fin, width="130px", size="1", placeholder="Fin"), spacing="0"),
                spacing="3",
            ),
            rx.button("Guardar camioneta", on_click=State.guardar_movimiento_vista(equipo_num), size="1", color_scheme="green", variant="soft"),
            spacing="2",
        ),
        padding="10px", background=bg, border_radius="6px",
    )


def page_vista_dia() -> rx.Component:
    return layout(
        rx.vstack(
            rx.heading("Vista del Dia", size="6"),
            rx.divider(),
            rx.cond(State.vista_exito, rx.callout(State.vista_exito, icon="check", color_scheme="green")),
            rx.hstack(
                rx.vstack(rx.text("Fecha", font_size="12px", color="gray"), rx.input(type="date", value=State.vista_fecha, on_change=State.set_vista_fecha, width="180px"), spacing="1"),
                rx.button("Buscar", on_click=State.cargar_vista_dia, color_scheme="blue"),
                spacing="4", align="end",
            ),
            rx.hstack(
                # Equipo 1
                rx.vstack(
                    rx.text("Equipo 1", font_size="14px", font_weight="700", color="#1e3a8a"),
                    rx.cond(
                        State.vista_mov_equipo1,
                        vista_mov_editable(
                            "1", "#1e3a8a", "#eff6ff",
                            State.vista_edit_mov1_salida, State.vista_edit_mov1_llegada,
                            State.vista_edit_mov1_inicio, State.vista_edit_mov1_fin,
                            State.set_vista_edit_mov1_salida, State.set_vista_edit_mov1_llegada,
                            State.set_vista_edit_mov1_inicio, State.set_vista_edit_mov1_fin,
                        ),
                        rx.text("Sin movimiento cargado", font_size="12px", color="gray"),
                    ),
                    rx.table.root(
                        rx.table.header(rx.table.row(
                            rx.table.column_header_cell("Hora"),
                            rx.table.column_header_cell("Cliente"),
                            rx.table.column_header_cell("Tipo"),
                            rx.table.column_header_cell("Dispositivo"),
                            rx.table.column_header_cell("Patente"),
                            rx.table.column_header_cell("Estado"),
                        )),
                        rx.table.body(rx.foreach(State.vista_servicios_equipo1, vista_servicio_row)),
                        width="100%",
                    ),
                    spacing="2", width="50%",
                ),
                # Equipo 2
                rx.vstack(
                    rx.text("Equipo 2", font_size="14px", font_weight="700", color="#0f766e"),
                    rx.cond(
                        State.vista_mov_equipo2,
                        vista_mov_editable(
                            "2", "#0f766e", "#f0fdf4",
                            State.vista_edit_mov2_salida, State.vista_edit_mov2_llegada,
                            State.vista_edit_mov2_inicio, State.vista_edit_mov2_fin,
                            State.set_vista_edit_mov2_salida, State.set_vista_edit_mov2_llegada,
                            State.set_vista_edit_mov2_inicio, State.set_vista_edit_mov2_fin,
                        ),
                        rx.text("Sin movimiento cargado", font_size="12px", color="gray"),
                    ),
                    rx.table.root(
                        rx.table.header(rx.table.row(
                            rx.table.column_header_cell("Hora"),
                            rx.table.column_header_cell("Cliente"),
                            rx.table.column_header_cell("Tipo"),
                            rx.table.column_header_cell("Dispositivo"),
                            rx.table.column_header_cell("Patente"),
                            rx.table.column_header_cell("Estado"),
                        )),
                        rx.table.body(rx.foreach(State.vista_servicios_equipo2, vista_servicio_row)),
                        width="100%",
                    ),
                    spacing="2", width="50%",
                ),
                spacing="6", width="100%", align="start",
            ),
            spacing="4", width="100%",
            on_mount=State.cargar_equipos,
        )
    )


# ─── SERVICIOS: HISTORIAL ────────────────────────────────────────────────────

def hist_servicio_row(s: dict) -> rx.Component:
    return rx.table.row(
        rx.table.cell(s["fecha"]),
        rx.table.cell(s["cliente"]),
        rx.table.cell(s["tipo_servicio"]),
        rx.table.cell(rx.cond(s["dispositivo"], s["dispositivo"], "-")),
        rx.table.cell(rx.cond(s["patente"], s["patente"], "-")),
        rx.table.cell(s["equipo_nombre"]),
        rx.table.cell(
            rx.select(
                ["PENDIENTE", "CONFIRMADO", "REALIZADO"],
                value=s["estado"],
                on_change=lambda v: State.actualizar_estado_servicio(s["id"], v),
                width="140px",
            )
        ),
        rx.table.cell(
            rx.hstack(
                rx.button("Editar", size="1", color_scheme="blue", variant="soft", on_click=State.abrir_edit_hist(s)),
                rx.button("Eliminar", size="1", color_scheme="red", variant="soft", on_click=State.iniciar_confirm("servicio_hist", s["id"])),
                spacing="1",
            )
        ),
    )


def hist_edit_dialog() -> rx.Component:
    return rx.dialog.root(
        rx.dialog.content(
            rx.dialog.title("Editar Servicio"),
            rx.vstack(
                rx.hstack(
                    rx.vstack(rx.text("Fecha", font_size="12px", color="gray"), rx.input(type="date", value=State.hist_edit_fecha, on_change=State.set_hist_edit_fecha, width="160px"), spacing="1"),
                    rx.vstack(rx.text("Hora", font_size="12px", color="gray"), rx.input(type="time", value=State.hist_edit_hora, on_change=State.set_hist_edit_hora, width="130px"), spacing="1"),
                    spacing="3",
                ),
                rx.vstack(rx.text("Cliente", font_size="12px", color="gray"), rx.input(value=State.hist_edit_cliente, on_change=State.set_hist_edit_cliente, width="100%"), spacing="1"),
                rx.hstack(
                    rx.vstack(rx.text("Tipo", font_size="12px", color="gray"), rx.select(["INSTALACION", "REVISION", "DESINSTALACION"], value=State.hist_edit_tipo, on_change=State.set_hist_edit_tipo, width="180px"), spacing="1"),
                    rx.vstack(rx.text("Dispositivo", font_size="12px", color="gray"), rx.select(["GPS", "LECTORA", "GPS y LECTORA"], value=State.hist_edit_dispositivo, on_change=State.set_hist_edit_dispositivo, width="180px"), spacing="1"),
                    spacing="3",
                ),
                rx.hstack(
                    rx.vstack(rx.text("Patente", font_size="12px", color="gray"), rx.input(value=State.hist_edit_patente, on_change=State.set_hist_edit_patente, width="160px"), spacing="1"),
                    rx.vstack(rx.text("Estado", font_size="12px", color="gray"), rx.select(["PENDIENTE", "CONFIRMADO", "REALIZADO"], value=State.hist_edit_estado, on_change=State.set_hist_edit_estado, width="160px"), spacing="1"),
                    spacing="3",
                ),
                rx.vstack(rx.text("Equipo", font_size="12px", color="gray"), rx.select(State.equipos_nombres, value=State.hist_edit_equipo_nombre, on_change=State.set_hist_edit_equipo_sel, width="200px"), spacing="1"),
                rx.vstack(rx.text("Observaciones", font_size="12px", color="gray"), rx.text_area(value=State.hist_edit_obs, on_change=State.set_hist_edit_obs, width="100%"), spacing="1"),
                rx.hstack(
                    rx.button("Cancelar", on_click=State.cerrar_edit_hist, variant="soft", color_scheme="gray"),
                    rx.button("Guardar", on_click=State.guardar_edit_hist, color_scheme="blue"),
                    spacing="3", justify="end", width="100%",
                ),
                spacing="3", width="100%",
            ),
            max_width="500px",
        ),
        open=State.mostrar_edit_hist,
    )


def page_historial_svc() -> rx.Component:
    return layout(
        rx.vstack(
            rx.heading("Historial de Servicios", size="6"),
            rx.divider(),
            rx.hstack(
                rx.vstack(rx.text("Estado", font_size="12px", color="gray"), rx.select(["PENDIENTE", "CONFIRMADO", "REALIZADO"], placeholder="Todos", value=State.hist_filtro_estado, on_change=State.set_hist_filtro_estado, width="160px"), spacing="1"),
                rx.vstack(rx.text("Mes", font_size="12px", color="gray"), rx.select(["1","2","3","4","5","6","7","8","9","10","11","12"], placeholder="Todos", value=State.hist_filtro_mes, on_change=State.set_hist_filtro_mes, width="100px"), spacing="1"),
                rx.vstack(rx.text("Ano", font_size="12px", color="gray"), rx.select(["2025", "2026", "2027"], value=State.hist_filtro_anio, on_change=State.set_hist_filtro_anio, width="100px"), spacing="1"),
                rx.button("Buscar", on_click=State.cargar_historial_svc, color_scheme="blue"),
                spacing="4", align="end",
            ),
            rx.table.root(
                rx.table.header(rx.table.row(
                    rx.table.column_header_cell("Fecha"),
                    rx.table.column_header_cell("Cliente"),
                    rx.table.column_header_cell("Tipo"),
                    rx.table.column_header_cell("Dispositivo"),
                    rx.table.column_header_cell("Patente"),
                    rx.table.column_header_cell("Equipo"),
                    rx.table.column_header_cell("Estado"),
                    rx.table.column_header_cell("Acciones"),
                )),
                rx.table.body(rx.foreach(State.hist_servicios, hist_servicio_row)),
                width="100%",
            ),
            hist_edit_dialog(),
            spacing="4", width="100%",
            on_mount=[State.cargar_historial_svc, State.cargar_equipos],
        )
    )


# ─── DIRECTORIO: CARGA ───────────────────────────────────────────────────────

def page_dir_carga() -> rx.Component:
    return layout(
        rx.vstack(
            rx.heading("Directorio — Carga", size="6"),
            rx.divider(),
            rx.hstack(
                rx.button("Técnico / Interno", on_click=State.set_dir_tipo("interno"), color_scheme=rx.cond(State.dir_tipo == "interno", "blue", "gray"), variant=rx.cond(State.dir_tipo == "interno", "solid", "soft")),
                rx.button("Contacto exterior", on_click=State.set_dir_tipo("interior"), color_scheme=rx.cond(State.dir_tipo == "interior", "blue", "gray"), variant=rx.cond(State.dir_tipo == "interior", "solid", "soft")),
                rx.button("Cliente", on_click=State.set_dir_tipo("cliente"), color_scheme=rx.cond(State.dir_tipo == "cliente", "blue", "gray"), variant=rx.cond(State.dir_tipo == "cliente", "solid", "soft")),
                spacing="3",
            ),
            rx.cond(
                State.dir_tipo == "cliente",
                # Formulario cliente
                rx.vstack(
                    rx.hstack(
                        rx.vstack(rx.text("Nombre", font_size="12px", color="gray"), rx.input(value=State.dir_nombre, on_change=State.set_dir_nombre, width="220px"), spacing="1"),
                        rx.vstack(rx.text("Contacto", font_size="12px", color="gray"), rx.input(value=State.dir_contacto, on_change=State.set_dir_contacto, width="180px"), spacing="1"),
                        rx.vstack(rx.text("Teléfono", font_size="12px", color="gray"), rx.input(value=State.dir_telefono, on_change=State.set_dir_telefono, width="160px"), spacing="1"),
                        spacing="4", wrap="wrap",
                    ),
                    rx.vstack(rx.text("Email", font_size="12px", color="gray"), rx.input(value=State.dir_email, on_change=State.set_dir_email, width="300px"), spacing="1"),
                    rx.vstack(rx.text("Observaciones", font_size="12px", color="gray"), rx.text_area(value=State.dir_observaciones, on_change=State.set_dir_observaciones, width="500px", rows="2"), spacing="1"),
                    rx.cond(State.dir_error != "", rx.callout(State.dir_error, color="red")),
                    rx.cond(State.dir_exito != "", rx.callout(State.dir_exito, color="green")),
                    rx.button("Guardar cliente", on_click=State.guardar_cliente, color_scheme="blue", size="3"),
                    spacing="3",
                ),
                # Formulario personal/contacto
                rx.vstack(
                    rx.hstack(
                        rx.vstack(rx.text("Nombre", font_size="12px", color="gray"), rx.input(value=State.dir_nombre, on_change=State.set_dir_nombre, width="220px"), spacing="1"),
                        rx.cond(
                            State.dir_tipo == "interno",
                            rx.vstack(rx.text("Equipo", font_size="12px", color="gray"), rx.select(State.equipos_nombres, placeholder="Seleccionar equipo", value=State.dir_equipo_id, on_change=State.set_dir_equipo_id, width="180px"), spacing="1"),
                            rx.vstack(rx.text("Ciudad / Zona", font_size="12px", color="gray"), rx.input(value=State.dir_ciudad, on_change=State.set_dir_ciudad, width="180px"), spacing="1"),
                        ),
                        rx.vstack(rx.text("Teléfono", font_size="12px", color="gray"), rx.input(value=State.dir_telefono, on_change=State.set_dir_telefono, width="160px"), spacing="1"),
                        spacing="4", wrap="wrap",
                    ),
                    rx.cond(
                        State.dir_tipo == "interior",
                        rx.hstack(
                            rx.vstack(rx.text("Contacto", font_size="12px", color="gray"), rx.input(value=State.dir_contacto, on_change=State.set_dir_contacto, width="200px"), spacing="1"),
                            rx.vstack(rx.text("Email", font_size="12px", color="gray"), rx.input(value=State.dir_email, on_change=State.set_dir_email, width="240px"), spacing="1"),
                            spacing="4",
                        ),
                    ),
                    rx.vstack(rx.text("Observaciones", font_size="12px", color="gray"), rx.text_area(value=State.dir_observaciones, on_change=State.set_dir_observaciones, width="500px", rows="2"), spacing="1"),
                    rx.cond(State.dir_error != "", rx.callout(State.dir_error, color="red")),
                    rx.cond(State.dir_exito != "", rx.callout(State.dir_exito, color="green")),
                    rx.button("Guardar", on_click=State.guardar_directorio, color_scheme="blue", size="3"),
                    spacing="3",
                ),
            ),
            spacing="4", width="100%", max_width="700px",
            on_mount=[State.cargar_equipos, State.cargar_directorio_personal],
        )
    )


# ─── DIRECTORIO: PERSONAL ────────────────────────────────────────────────────

def dir_personal_row(t: dict) -> rx.Component:
    return rx.table.row(
        rx.table.cell(t["nombre"]),
        rx.table.cell(
            rx.badge(t["tipo"], color_scheme=rx.cond(t["tipo"] == "interno", "blue", "gray"))
        ),
        rx.table.cell(rx.cond(t["equipo_id"], t["equipo_id"], rx.cond(t["ciudad"], t["ciudad"], "-"))),
        rx.table.cell(rx.cond(t["telefono"], t["telefono"], "-")),
        rx.table.cell(rx.cond(t["observaciones"], t["observaciones"], "-")),
        rx.table.cell(rx.button("🗑", size="1", color_scheme="red", on_click=State.iniciar_confirm("dir_personal", t["id"]))),
    )


def page_dir_personal() -> rx.Component:
    return layout(
        rx.vstack(
            rx.heading("Personal y Contactos", size="6"),
            rx.divider(),
            rx.table.root(
                rx.table.header(rx.table.row(
                    rx.table.column_header_cell("Nombre"),
                    rx.table.column_header_cell("Tipo"),
                    rx.table.column_header_cell("Equipo / Zona"),
                    rx.table.column_header_cell("Teléfono"),
                    rx.table.column_header_cell("Observaciones"),
                    rx.table.column_header_cell(""),
                )),
                rx.table.body(rx.foreach(State.dir_personal, dir_personal_row)),
                width="100%",
            ),
            spacing="4", width="100%",
            on_mount=[State.cargar_directorio_personal, State.cargar_equipos],
        )
    )


# ─── DIRECTORIO: CLIENTES ────────────────────────────────────────────────────

def dir_cliente_row(c: dict) -> rx.Component:
    return rx.table.row(
        rx.table.cell(c["nombre"]),
        rx.table.cell(rx.cond(c["ciudad"], c["ciudad"], "-")),
        rx.table.cell(rx.cond(c["telefono"], c["telefono"], "-")),
        rx.table.cell(rx.cond(c["email"], c["email"], "-")),
        rx.table.cell(rx.hstack(
            rx.button("✏️", size="1", color_scheme="blue",
                on_click=State.iniciar_edit_cliente_dir(c["id"], c["nombre"], c["ciudad"], c["telefono"], c["email"], c["observaciones"])),
            rx.button("🗑", size="1", color_scheme="red", on_click=State.iniciar_confirm("dir_cliente", c["id"])),
            spacing="2",
        )),
    )


def page_dir_clientes() -> rx.Component:
    return layout(
        rx.vstack(
            rx.heading("Clientes", size="6"),
            rx.divider(),
            rx.button("+ Agregar cliente", on_click=[State.set_dir_tipo("cliente"), State.set_pagina("dir_carga")], color_scheme="blue"),
            rx.cond(State.dir_exito != "", rx.callout(State.dir_exito, color="green")),
            rx.table.root(
                rx.table.header(rx.table.row(
                    rx.table.column_header_cell("Nombre"),
                    rx.table.column_header_cell("Ciudad"),
                    rx.table.column_header_cell("Teléfono"),
                    rx.table.column_header_cell("Email"),
                    rx.table.column_header_cell(""),
                )),
                rx.table.body(rx.foreach(State.dir_clientes_list, dir_cliente_row)),
                width="100%",
            ),
            spacing="4", width="100%",
            on_mount=State.cargar_directorio_clientes,
        )
    )


# ─── DIRECTORIO: PROVEEDORES (alias) ─────────────────────────────────────────

def page_dir_proveedores() -> rx.Component:
    return page_proveedores()


# ─── ESTADÍSTICAS: HORAS ─────────────────────────────────────────────────────

def stats_horas_row(t: dict) -> rx.Component:
    return rx.table.row(
        rx.table.cell(t["nombre"]),
        rx.table.cell(rx.cond(t["equipo"], t["equipo"], "-")),
        rx.table.cell(t["dias_presentes"]),
        rx.table.cell(t["horas_str"]),
        rx.table.cell(rx.text(t["diferencia_str"], color=t["diferencia_color"], font_weight="600")),
    )


def page_stats_horas() -> rx.Component:
    return layout(
        rx.vstack(
            rx.heading("Horas Trabajadas", size="6"),
            rx.divider(),
            rx.hstack(
                rx.vstack(rx.text("Mes", font_size="12px", color="gray"), rx.select(["1","2","3","4","5","6","7","8","9","10","11","12"], placeholder="Seleccionar", value=State.stats2_mes, on_change=State.set_stats2_mes, width="130px"), spacing="1"),
                rx.vstack(rx.text("Año", font_size="12px", color="gray"), rx.select(["2025", "2026", "2027"], value=State.stats2_anio, on_change=State.set_stats2_anio, width="100px"), spacing="1"),
                rx.button("Calcular", on_click=State.cargar_stats_horas, color_scheme="blue"),
                spacing="4", align="end",
            ),
            rx.table.root(
                rx.table.header(rx.table.row(
                    rx.table.column_header_cell("Técnico"),
                    rx.table.column_header_cell("Equipo"),
                    rx.table.column_header_cell("Días presentes"),
                    rx.table.column_header_cell("Horas trabajadas"),
                    rx.table.column_header_cell("Balance"),
                )),
                rx.table.body(rx.foreach(State.stats2_tecnicos, stats_horas_row)),
                width="100%",
            ),
            spacing="4", width="100%",
        )
    )


# ─── ESTADÍSTICAS: CLIENTES ──────────────────────────────────────────────────

def stats_cli_serv_row(s: dict) -> rx.Component:
    return rx.table.row(
        rx.table.cell(s["fecha"]),
        rx.table.cell(s["tipo_servicio"]),
        rx.table.cell(rx.cond(s["dispositivo"], s["dispositivo"], "-")),
        rx.table.cell(rx.cond(s["patente"], s["patente"], "-")),
        rx.table.cell(rx.text(s["estado"], color=s["estado_color"], font_weight="600")),
    )


def page_stats_clientes() -> rx.Component:
    return layout(
        rx.vstack(
            rx.heading("Servicios por Cliente", size="6"),
            rx.divider(),
            rx.hstack(
                rx.vstack(rx.text("Cliente", font_size="12px", color="gray"), rx.select(State.dir_clientes_nombres, placeholder="Todos", value=State.stats_cli_cliente_id, on_change=State.set_stats_cli_cliente_nombre, width="200px"), spacing="1"),
                rx.vstack(rx.text("Mes", font_size="12px", color="gray"), rx.select(["1","2","3","4","5","6","7","8","9","10","11","12"], placeholder="Todos", value=State.stats_cli_mes, on_change=State.set_stats_cli_mes, width="100px"), spacing="1"),
                rx.vstack(rx.text("Año", font_size="12px", color="gray"), rx.select(["2025", "2026", "2027"], value=State.stats_cli_anio, on_change=State.set_stats_cli_anio, width="100px"), spacing="1"),
                rx.button("Buscar", on_click=State.cargar_stats_clientes, color_scheme="blue"),
                spacing="4", align="end",
            ),
            rx.cond(
                State.stats_cli_resumen,
                rx.hstack(
                    rx.box(rx.vstack(rx.text("Total", font_size="12px", color="gray"), rx.text(State.stats_cli_resumen["total"], font_size="28px", font_weight="700", color="#1e3a8a"), spacing="1", align="center"), padding="16px 20px", border="1px solid #e2e6ea", border_radius="12px", background="white"),
                    rx.box(rx.vstack(rx.text("Instalaciones", font_size="12px", color="gray"), rx.text(State.stats_cli_resumen["instalaciones"], font_size="28px", font_weight="700", color="#0f766e"), spacing="1", align="center"), padding="16px 20px", border="1px solid #e2e6ea", border_radius="12px", background="white"),
                    rx.box(rx.vstack(rx.text("Revisiones", font_size="12px", color="gray"), rx.text(State.stats_cli_resumen["revisiones"], font_size="28px", font_weight="700", color="#b45309"), spacing="1", align="center"), padding="16px 20px", border="1px solid #e2e6ea", border_radius="12px", background="white"),
                    rx.box(rx.vstack(rx.text("Desinstalaciones", font_size="12px", color="gray"), rx.text(State.stats_cli_resumen["desinstalaciones"], font_size="28px", font_weight="700", color="#7c3aed"), spacing="1", align="center"), padding="16px 20px", border="1px solid #e2e6ea", border_radius="12px", background="white"),
                    spacing="4", wrap="wrap",
                ),
            ),
            rx.table.root(
                rx.table.header(rx.table.row(
                    rx.table.column_header_cell("Fecha"),
                    rx.table.column_header_cell("Tipo"),
                    rx.table.column_header_cell("Dispositivo"),
                    rx.table.column_header_cell("Patente"),
                    rx.table.column_header_cell("Estado"),
                )),
                rx.table.body(rx.foreach(State.stats_cli_servicios, stats_cli_serv_row)),
                width="100%",
            ),
            spacing="4", width="100%",
            on_mount=State.cargar_directorio_clientes,
        )
    )


# ─── ESTADÍSTICAS: REPORTE CRUZADO ───────────────────────────────────────────

def stats_cruzado_row(t: dict) -> rx.Component:
    return rx.table.row(
        rx.table.cell(t["nombre"]),
        rx.table.cell(rx.cond(t["equipo"], t["equipo"], "-")),
        rx.table.cell(t["dias_presentes"]),
        rx.table.cell(t["servicios_realizados"]),
        rx.table.cell(t["servicios_por_dia"]),
        rx.table.cell(t["horas_str"]),
        rx.table.cell(rx.text(t["balance_str"], color=t["balance_color"], font_weight="600")),
    )


def page_stats_cruzado() -> rx.Component:
    return layout(
        rx.vstack(
            rx.heading("Reporte Cruzado", size="6"),
            rx.divider(),
            rx.hstack(
                rx.vstack(rx.text("Mes", font_size="12px", color="gray"), rx.select(["1","2","3","4","5","6","7","8","9","10","11","12"], placeholder="Seleccionar", value=State.stats_cruz_mes, on_change=State.set_stats_cruz_mes, width="130px"), spacing="1"),
                rx.vstack(rx.text("Año", font_size="12px", color="gray"), rx.select(["2025", "2026", "2027"], value=State.stats_cruz_anio, on_change=State.set_stats_cruz_anio, width="100px"), spacing="1"),
                rx.button("Calcular", on_click=State.cargar_stats_cruzado, color_scheme="blue"),
                spacing="4", align="end",
            ),
            rx.table.root(
                rx.table.header(rx.table.row(
                    rx.table.column_header_cell("Técnico"),
                    rx.table.column_header_cell("Equipo"),
                    rx.table.column_header_cell("Días presentes"),
                    rx.table.column_header_cell("Servicios realizados"),
                    rx.table.column_header_cell("Servicios/día"),
                    rx.table.column_header_cell("Horas trabajadas"),
                    rx.table.column_header_cell("Balance"),
                )),
                rx.table.body(rx.foreach(State.stats_cruz_tecnicos, stats_cruzado_row)),
                width="100%",
            ),
            spacing="4", width="100%",
        )
    )


# ─── DASHBOARD ───────────────────────────────────────────────────────────────

def dashboard_page() -> rx.Component:
    return rx.cond(
        State.pagina == "carga_dia", page_carga_dia(),
    rx.cond(State.pagina == "vista_dia", page_vista_dia(),
    rx.cond(State.pagina == "historial_svc", page_historial_svc(),
    rx.cond(State.pagina == "dir_carga", page_dir_carga(),
    rx.cond(State.pagina == "dir_personal", page_dir_personal(),
    rx.cond(State.pagina == "dir_clientes", page_dir_clientes(),
    rx.cond(State.pagina == "dir_proveedores", page_dir_proveedores(),
    rx.cond(State.pagina == "stats_horas", page_stats_horas(),
    rx.cond(State.pagina == "stats_clientes", page_stats_clientes(),
    rx.cond(State.pagina == "stats_cruzado", page_stats_cruzado(),
    rx.cond(State.pagina == "stock_actual", page_stock_actual(),
    rx.cond(State.pagina == "stock_entrada", page_stock_entrada(),
    rx.cond(State.pagina == "stock_salida", page_stock_salida(),
    rx.cond(State.pagina == "stock_productos", page_stock_productos(),
    rx.cond(State.pagina == "stock_proveedores", page_proveedores(),
    rx.cond(State.pagina == "terceros_lista", page_terceros_lista(),
    rx.cond(State.pagina == "terceros_stock", page_terceros_stock(),
    layout(rx.vstack(
        rx.heading("Bienvenido!", size="7"),
        rx.text("Seleccioná un módulo del sidebar.", color="gray"),
        spacing="4",
    )))))))))))))))))))


app = rx.App(theme=rx.theme(accent_color="blue", has_background=True))
app.add_page(login_page, route="/")
app.add_page(dashboard_page, route="/dashboard", on_load=State.cargar_equipos)
