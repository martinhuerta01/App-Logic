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
    stats_mes: str = ""
    stats_anio: str = "2026"
    stats_resumen: list[dict] = []
    stats_barras_horas: list[dict] = []
    stats_barras_prod: list[dict] = []
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
    mostrar_form_prod: bool = False
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
    servicios: list[dict] = []
    serv_fecha: str = ""
    serv_cliente_tipo: str = ""
    serv_cliente_otro: str = ""
    serv_es_serenisima: bool = False
    serv_tipo: str = "INSTALACION"
    serv_tipo_unidad: str = ""
    serv_alcance: str = ""
    serv_patente: str = ""
    serv_responsable: str = ""
    serv_responsable_tipo: str = ""
    serv_tecnicos: str = ""
    serv_estado: str = "PENDIENTE"
    serv_observaciones: str = ""
    serv_exito: str = ""
    serv_error: str = ""
    serv_filtro_estado: str = ""
    serv_filtro_mes: str = ""
    serv_filtro_anio: str = "2026"
    serv_edit_id: str = ""

    # Reportes
    rep_mes: str = ""
    rep_anio: str = "2026"
    rep_jornadas: list[dict] = []
    rep_por_estado: list[dict] = []
    rep_por_tipo: list[dict] = []
    rep_por_cliente: list[dict] = []
    rep_servicios_total: int = 0

    @rx.var
    def productos_filtrados(self) -> list[dict]:
        if not self.prod_filtro_cat:
            return self.productos
        return [p for p in self.productos if p["categoria"] == self.prod_filtro_cat]

    @rx.var
    def responsables_opciones(self) -> list[str]:
        base = ["EQUIPO 1", "EQUIPO 2", "VITACO", "ZARZA", "TALLER INTERNO"]
        return base + self.nombres_terceros

    def set_serv_cliente_tipo(self, val: str):
        self.serv_cliente_tipo = val
        self.serv_es_serenisima = val == "LA SERENISIMA"

    def set_serv_responsable_tipo(self, val: str):
        self.serv_responsable_tipo = val
        self.serv_responsable = val
        self.serv_tecnicos = ""

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
                resumen[nombre] = {"nombre": nombre, "dias": 0, "horas_total": 0.0, "extras": 0.0, "debe": 0.0, "instalaciones": 0, "desinstalaciones": 0, "revisiones": 0, "ausencias": 0}
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
        self.stats_barras_prod = [
            {"tipo": "Instalaciones", "cantidad": sum(j.get("instalaciones", 0) for j in raw)},
            {"tipo": "Desinstalaciones", "cantidad": sum(j.get("desinstalaciones", 0) for j in raw)},
            {"tipo": "Revisiones", "cantidad": sum(j.get("revisiones", 0) for j in raw)},
        ]

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

    def reset_servicio(self):
        self.serv_fecha = ""
        self.serv_cliente_tipo = ""
        self.serv_cliente_otro = ""
        self.serv_es_serenisima = False
        self.serv_tipo = "INSTALACION"
        self.serv_tipo_unidad = ""
        self.serv_alcance = ""
        self.serv_patente = ""
        self.serv_responsable = ""
        self.serv_responsable_tipo = ""
        self.serv_tecnicos = ""
        self.serv_estado = "PENDIENTE"
        self.serv_observaciones = ""
        self.serv_exito = ""
        self.serv_error = ""
        self.serv_edit_id = ""

    async def cargar_servicios(self):
        params = {}
        if self.serv_filtro_estado:
            params["estado"] = self.serv_filtro_estado
        if self.serv_filtro_mes:
            params["mes"] = self.serv_filtro_mes
        if self.serv_filtro_anio:
            params["anio"] = self.serv_filtro_anio
        try:
            async with httpx.AsyncClient(timeout=30.0) as client:
                r = await client.get(f"{API_URL}/servicios/", params=params)
            raw = r.json()
            if not isinstance(raw, list):
                raw = []
            for s in raw:
                s["estado_color"] = {
                    "PENDIENTE": "orange", "CONFIRMADO": "blue", "REALIZADO": "green",
                    "SUSPENDIDO": "red", "REPROGRAMADO": "purple",
                }.get(s.get("estado", ""), "gray")
            self.servicios = raw
        except Exception:
            self.servicios = []

    async def guardar_servicio(self):
        cliente = self.serv_cliente_otro if self.serv_cliente_tipo == "OTRO" else self.serv_cliente_tipo
        if not self.serv_fecha or not cliente or not self.serv_tipo:
            self.serv_error = "Completá fecha, cliente y tipo"
            return
        responsable_final = self.serv_responsable_tipo
        if self.serv_responsable_tipo in ["EQUIPO 1", "EQUIPO 2"] and self.serv_tecnicos:
            responsable_final = f"{self.serv_responsable_tipo} ({self.serv_tecnicos})"
        payload = {
            "fecha": self.serv_fecha,
            "cliente": cliente,
            "es_serenisima": self.serv_es_serenisima,
            "tipo_servicio": self.serv_tipo,
            "tipo_unidad": self.serv_tipo_unidad or None,
            "alcance": self.serv_alcance or None,
            "patente": self.serv_patente or None,
            "responsable": responsable_final or None,
            "estado": self.serv_estado,
            "observaciones": self.serv_observaciones or None,
            "cargado_por": self.usuario,
        }
        async with httpx.AsyncClient(timeout=30.0) as client:
            if self.serv_edit_id:
                r = await client.put(f"{API_URL}/servicios/{self.serv_edit_id}", json=payload)
            else:
                r = await client.post(f"{API_URL}/servicios/", json=payload)
        if r.status_code == 200:
            self.reset_servicio()
            self.serv_exito = "Servicio guardado correctamente"
            await self.cargar_servicios()
        else:
            self.serv_error = "Error al guardar servicio"

    async def eliminar_servicio(self, serv_id: str):
        async with httpx.AsyncClient(timeout=30.0) as client:
            await client.delete(f"{API_URL}/servicios/{serv_id}")
        await self.cargar_servicios()

    def iniciar_edit_servicio(self, serv_id: str, fecha: str, cliente: str, es_seren: bool, tipo: str, unidad, alcance, patente, responsable, estado: str, obs):
        self.serv_edit_id = serv_id
        self.serv_fecha = fecha
        if es_seren:
            self.serv_cliente_tipo = "LA SERENISIMA"
        else:
            self.serv_cliente_tipo = "OTRO"
            self.serv_cliente_otro = cliente
        self.serv_es_serenisima = es_seren
        self.serv_tipo = tipo
        self.serv_tipo_unidad = unidad or ""
        self.serv_alcance = alcance or ""
        self.serv_patente = patente or ""
        self.serv_responsable_tipo = responsable or ""
        self.serv_responsable = responsable or ""
        self.serv_estado = estado
        self.serv_observaciones = obs or ""
        self.pagina = "serv_cargar"

    async def cargar_reporte(self):
        params = {}
        if self.rep_mes:
            params["mes"] = self.rep_mes
        if self.rep_anio:
            params["anio"] = self.rep_anio
        try:
            async with httpx.AsyncClient(timeout=30.0) as client:
                r = await client.get(f"{API_URL}/jornadas/reporte_cruzado/", params=params)
            data = r.json()
            self.rep_jornadas = data.get("jornadas", [])
            self.rep_servicios_total = data.get("servicios_total", 0)
            self.rep_por_estado = data.get("por_estado", [])
            self.rep_por_tipo = data.get("por_tipo", [])
            self.rep_por_cliente = data.get("por_cliente", [])
        except Exception:
            self.rep_jornadas = []
            self.rep_por_estado = []
            self.rep_por_tipo = []
            self.rep_por_cliente = []


MODULOS = [
    {"id": "horarios", "icon": "clock", "label": "Horarios", "color": "#1e3a8a",
     "subs": [("registro", "Registro"), ("historial", "Historial"), ("estadisticas", "Estadísticas"), ("tecnicos", "Técnicos")]},
    {"id": "servicios", "icon": "wrench", "label": "Servicios", "color": "#0f766e",
     "subs": [("serv_cargar", "Cargar servicio"), ("serv_lista", "Lista")]},
    {"id": "stock", "icon": "package", "label": "Stock", "color": "#b45309",
     "subs": [("stock_actual", "Stock actual"), ("stock_entrada", "Entrada"), ("stock_salida", "Transferencia/Salida"), ("stock_productos", "Productos"), ("stock_proveedores", "Proveedores")]},
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
                rx.vstack(rx.text("Técnico", font_size="12px", font_weight="600", color="gray"), rx.select(State.nombres_empleados, placeholder="Seleccionar técnico", value=State.empleado_sel, on_change=State.set_empleado_sel, width="200px"), spacing="1"),
                rx.vstack(rx.text("Fecha", font_size="12px", font_weight="600", color="gray"), rx.input(type="date", value=State.fecha_jornada, on_change=State.set_fecha_jornada, width="180px"), spacing="1"),
                rx.vstack(rx.text("Tipo", font_size="12px", font_weight="600", color="gray"), rx.select(["ACTIVO", "LLEGADA_TARDE", "AUSENCIA_SJ", "AUSENCIA_J", "VACACIONES", "LICENCIA"], value=State.tipo_asistencia, on_change=State.set_tipo_asistencia, width="200px"), spacing="1"),
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
            rx.cond(State.tipo_asistencia == "AUSENCIA_J", rx.vstack(rx.text("Motivo", font_size="12px", color="gray"), rx.input(value=State.motivo, on_change=State.set_motivo, width="300px"), spacing="1")),
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
                rx.table.header(rx.table.row(
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
                )),
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
                rx.table.header(rx.table.row(
                    rx.table.column_header_cell("Nombre"),
                    rx.table.column_header_cell("Teléfono"),
                    rx.table.column_header_cell("Vehículo"),
                    rx.table.column_header_cell("Patente"),
                    rx.table.column_header_cell(""),
                )),
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
                rx.table.header(rx.table.row(
                    rx.table.column_header_cell("Técnico"),
                    rx.table.column_header_cell("Días trabajados"),
                    rx.table.column_header_cell("Hs totales"),
                    rx.table.column_header_cell("Extras"),
                    rx.table.column_header_cell("Debe"),
                    rx.table.column_header_cell("Inst."),
                    rx.table.column_header_cell("Desins."),
                    rx.table.column_header_cell("Rev."),
                    rx.table.column_header_cell("Ausencias"),
                )),
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
                width="100%", height=300,
            ),
            rx.text("Productividad del período", font_size="14px", font_weight="700", color="#1e3a8a", margin_top="16px"),
            rx.recharts.bar_chart(
                rx.recharts.bar(data_key="cantidad", fill="#0f766e", name="Cantidad"),
                rx.recharts.x_axis(data_key="tipo"),
                rx.recharts.y_axis(),
                rx.recharts.cartesian_grid(stroke_dasharray="3 3"),
                rx.recharts.graphing_tooltip(),
                data=State.stats_barras_prod,
                width="100%", height=250,
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
            rx.button("🗑", size="1", color_scheme="red", on_click=State.eliminar_producto(prod["id"])),
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


def proveedor_row(prov: dict) -> rx.Component:
    return rx.table.row(
        rx.table.cell(prov["nombre"]),
        rx.table.cell(rx.cond(prov["responsable"], prov["responsable"], "-")),
        rx.table.cell(rx.cond(prov["telefono"], prov["telefono"], "-")),
        rx.table.cell(rx.cond(prov["email"], prov["email"], "-")),
        rx.table.cell(rx.cond(prov["productos_que_vende"], prov["productos_que_vende"], "-")),
        rx.table.cell(rx.hstack(
            rx.button("✏️", size="1", color_scheme="blue", on_click=State.iniciar_edit_proveedor(prov["id"], prov["nombre"], prov["responsable"], prov["telefono"], prov["email"], prov["direccion"], prov["productos_que_vende"], prov["observaciones"])),
            rx.button("🗑", size="1", color_scheme="red", on_click=State.eliminar_proveedor(prov["id"])),
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
            rx.button("🗑", size="1", color_scheme="red", on_click=State.eliminar_tercero(terc["id"])),
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


def servicio_row(serv: dict) -> rx.Component:
    return rx.table.row(
        rx.table.cell(serv["fecha"]),
        rx.table.cell(serv["cliente"]),
        rx.table.cell(serv["tipo_servicio"]),
        rx.table.cell(rx.cond(serv["tipo_unidad"], serv["tipo_unidad"], rx.cond(serv["alcance"], serv["alcance"], "-"))),
        rx.table.cell(rx.cond(serv["patente"], serv["patente"], "-")),
        rx.table.cell(rx.cond(serv["responsable"], serv["responsable"], "-")),
        rx.table.cell(rx.text(serv["estado"], color=serv["estado_color"], font_weight="600")),
        rx.table.cell(rx.hstack(
            rx.button("✏️", size="1", color_scheme="blue",
                on_click=State.iniciar_edit_servicio(
                    serv["id"], serv["fecha"], serv["cliente"], serv["es_serenisima"],
                    serv["tipo_servicio"], serv["tipo_unidad"], serv["alcance"],
                    serv["patente"], serv["responsable"], serv["estado"], serv["observaciones"]
                )),
            rx.button("🗑", size="1", color_scheme="red", on_click=State.eliminar_servicio(serv["id"])),
            spacing="2",
        )),
    )


def page_serv_cargar() -> rx.Component:
    return layout(
        rx.vstack(
            rx.heading(rx.cond(State.serv_edit_id != "", "Editar Servicio", "Cargar Servicio"), size="6"),
            rx.divider(),
            rx.hstack(
                rx.vstack(rx.text("Fecha", font_size="12px", color="gray"), rx.input(type="date", value=State.serv_fecha, on_change=State.set_serv_fecha, width="160px"), spacing="1"),
                rx.vstack(rx.text("Cliente", font_size="12px", color="gray"), rx.select(["LA SERENISIMA", "OTRO"], placeholder="Seleccionar", value=State.serv_cliente_tipo, on_change=State.set_serv_cliente_tipo, width="200px"), spacing="1"),
                rx.vstack(rx.text("Tipo de servicio", font_size="12px", color="gray"), rx.select(["INSTALACION", "DESINSTALACION", "REVISION"], value=State.serv_tipo, on_change=State.set_serv_tipo, width="180px"), spacing="1"),
                spacing="4", wrap="wrap",
            ),
            rx.cond(
                State.serv_cliente_tipo == "OTRO",
                rx.vstack(rx.text("Nombre del cliente", font_size="12px", color="gray"), rx.input(placeholder="Ingresá el nombre", value=State.serv_cliente_otro, on_change=State.set_serv_cliente_otro, width="300px"), spacing="1"),
            ),
            rx.cond(
                State.serv_es_serenisima,
                rx.vstack(rx.text("Tipo de unidad", font_size="12px", color="gray"), rx.select(["CHASIS", "SEMI", "TRACTOR"], placeholder="Seleccionar", value=State.serv_tipo_unidad, on_change=State.set_serv_tipo_unidad, width="200px"), spacing="1"),
                rx.vstack(rx.text("Alcance", font_size="12px", color="gray"), rx.select(["GPS", "LECTORA", "GPS Y LECTORA"], placeholder="Seleccionar", value=State.serv_alcance, on_change=State.set_serv_alcance, width="200px"), spacing="1"),
            ),
            rx.hstack(
                rx.vstack(rx.text("Patente / Dominio", font_size="12px", color="gray"), rx.input(value=State.serv_patente, on_change=State.set_serv_patente, width="160px"), spacing="1"),
                rx.vstack(rx.text("Responsable", font_size="12px", color="gray"), rx.select(State.responsables_opciones, placeholder="Seleccionar", value=State.serv_responsable_tipo, on_change=State.set_serv_responsable_tipo, width="220px"), spacing="1"),
                rx.vstack(rx.text("Estado", font_size="12px", color="gray"), rx.select(["PENDIENTE", "CONFIRMADO", "REALIZADO", "SUSPENDIDO", "REPROGRAMADO"], value=State.serv_estado, on_change=State.set_serv_estado, width="180px"), spacing="1"),
                spacing="4", wrap="wrap",
            ),
            rx.cond(
                (State.serv_responsable_tipo == "EQUIPO 1") | (State.serv_responsable_tipo == "EQUIPO 2"),
                rx.vstack(rx.text("Técnicos del equipo", font_size="12px", color="gray"), rx.input(placeholder="Ej: Maxi, Lautaro", value=State.serv_tecnicos, on_change=State.set_serv_tecnicos, width="300px"), spacing="1"),
            ),
            rx.vstack(rx.text("Observaciones", font_size="12px", color="gray"), rx.text_area(value=State.serv_observaciones, on_change=State.set_serv_observaciones, width="500px", rows="3"), spacing="1"),
            rx.cond(State.serv_error != "", rx.callout(State.serv_error, color="red")),
            rx.cond(State.serv_exito != "", rx.callout(State.serv_exito, color="green")),
            rx.hstack(
                rx.button(rx.cond(State.serv_edit_id != "", "Guardar cambios", "Guardar servicio"), on_click=State.guardar_servicio, color_scheme="blue", size="3"),
                rx.cond(State.serv_edit_id != "", rx.button("Cancelar", on_click=State.reset_servicio, color_scheme="gray", size="3")),
                spacing="3",
            ),
            spacing="4", width="100%", max_width="700px",
            on_mount=State.cargar_terceros,
        )
    )


def page_serv_lista() -> rx.Component:
    return layout(
        rx.vstack(
            rx.heading("Lista de Servicios", size="6"),
            rx.divider(),
            rx.hstack(
                rx.vstack(rx.text("Estado", font_size="12px", color="gray"), rx.select(["PENDIENTE", "CONFIRMADO", "REALIZADO", "SUSPENDIDO", "REPROGRAMADO"], placeholder="Todos", value=State.serv_filtro_estado, on_change=State.set_serv_filtro_estado, width="180px"), spacing="1"),
                rx.vstack(rx.text("Mes", font_size="12px", color="gray"), rx.select(["1","2","3","4","5","6","7","8","9","10","11","12"], placeholder="Todos", value=State.serv_filtro_mes, on_change=State.set_serv_filtro_mes, width="100px"), spacing="1"),
                rx.vstack(rx.text("Año", font_size="12px", color="gray"), rx.select(["2025", "2026", "2027"], value=State.serv_filtro_anio, on_change=State.set_serv_filtro_anio, width="100px"), spacing="1"),
                rx.button("Buscar", on_click=State.cargar_servicios, color_scheme="blue"),
                spacing="4", align="end",
            ),
            rx.table.root(
                rx.table.header(rx.table.row(
                    rx.table.column_header_cell("Fecha"),
                    rx.table.column_header_cell("Cliente"),
                    rx.table.column_header_cell("Tipo"),
                    rx.table.column_header_cell("Unidad/Alcance"),
                    rx.table.column_header_cell("Patente"),
                    rx.table.column_header_cell("Responsable"),
                    rx.table.column_header_cell("Estado"),
                    rx.table.column_header_cell(""),
                )),
                rx.table.body(rx.foreach(State.servicios, servicio_row)),
                width="100%",
            ),
            spacing="4", width="100%",
            on_mount=State.cargar_servicios,
        )
    )


def rep_jornada_row(r: dict) -> rx.Component:
    return rx.table.row(
        rx.table.cell(r["nombre"]),
        rx.table.cell(r["dias_trabajados"]),
        rx.table.cell(f"{r['horas_total']}h"),
        rx.table.cell(r["instalaciones"]),
        rx.table.cell(r["desinstalaciones"]),
        rx.table.cell(r["revisiones"]),
    )


def rep_estado_row(r: dict) -> rx.Component:
    return rx.table.row(
        rx.table.cell(r["estado"]),
        rx.table.cell(r["cantidad"]),
    )


def rep_tipo_row(r: dict) -> rx.Component:
    return rx.table.row(
        rx.table.cell(r["tipo"]),
        rx.table.cell(r["cantidad"]),
    )


def rep_cliente_row(r: dict) -> rx.Component:
    return rx.table.row(
        rx.table.cell(r["cliente"]),
        rx.table.cell(r["cantidad"]),
    )


def page_reporte_cruzado() -> rx.Component:
    return layout(
        rx.vstack(
            rx.heading("Reporte Horarios vs Servicios", size="6"),
            rx.divider(),
            rx.hstack(
                rx.vstack(rx.text("Mes", font_size="12px", color="gray"), rx.select(["1","2","3","4","5","6","7","8","9","10","11","12"], placeholder="Todos", value=State.rep_mes, on_change=State.set_rep_mes, width="130px"), spacing="1"),
                rx.vstack(rx.text("Año", font_size="12px", color="gray"), rx.select(["2025", "2026", "2027"], value=State.rep_anio, on_change=State.set_rep_anio, width="100px"), spacing="1"),
                rx.button("Generar reporte", on_click=State.cargar_reporte, color_scheme="red"),
                spacing="4", align="end",
            ),

            # Resumen técnicos
            rx.text("Actividad por técnico", font_size="14px", font_weight="700", color="#1e3a8a", margin_top="8px"),
            rx.table.root(
                rx.table.header(rx.table.row(
                    rx.table.column_header_cell("Técnico"),
                    rx.table.column_header_cell("Días trabajados"),
                    rx.table.column_header_cell("Horas totales"),
                    rx.table.column_header_cell("Instalaciones"),
                    rx.table.column_header_cell("Desinstalaciones"),
                    rx.table.column_header_cell("Revisiones"),
                )),
                rx.table.body(rx.foreach(State.rep_jornadas, rep_jornada_row)),
                width="100%",
            ),

            # Servicios resumen
            rx.hstack(
                rx.box(
                    rx.vstack(
                        rx.text("Total servicios del período", font_size="13px", color="gray"),
                        rx.text(State.rep_servicios_total, font_size="32px", font_weight="700", color="#1e3a8a"),
                        spacing="1", align="center",
                    ),
                    padding="20px", border="1px solid #e2e6ea", border_radius="12px", background="white", width="180px",
                ),
                rx.vstack(
                    rx.text("Por estado", font_size="14px", font_weight="700", color="#1e3a8a"),
                    rx.table.root(
                        rx.table.header(rx.table.row(rx.table.column_header_cell("Estado"), rx.table.column_header_cell("Cant."))),
                        rx.table.body(rx.foreach(State.rep_por_estado, rep_estado_row)),
                    ),
                    spacing="2",
                ),
                rx.vstack(
                    rx.text("Por tipo", font_size="14px", font_weight="700", color="#1e3a8a"),
                    rx.table.root(
                        rx.table.header(rx.table.row(rx.table.column_header_cell("Tipo"), rx.table.column_header_cell("Cant."))),
                        rx.table.body(rx.foreach(State.rep_por_tipo, rep_tipo_row)),
                    ),
                    spacing="2",
                ),
                rx.vstack(
                    rx.text("Por cliente", font_size="14px", font_weight="700", color="#1e3a8a"),
                    rx.table.root(
                        rx.table.header(rx.table.row(rx.table.column_header_cell("Cliente"), rx.table.column_header_cell("Cant."))),
                        rx.table.body(rx.foreach(State.rep_por_cliente, rep_cliente_row)),
                    ),
                    spacing="2",
                ),
                spacing="6", align="start", wrap="wrap", margin_top="8px",
            ),

            # Gráficos
            rx.text("Servicios por tipo", font_size="14px", font_weight="700", color="#1e3a8a", margin_top="16px"),
            rx.recharts.bar_chart(
                rx.recharts.bar(data_key="cantidad", fill="#be123c", name="Servicios"),
                rx.recharts.x_axis(data_key="tipo"),
                rx.recharts.y_axis(),
                rx.recharts.cartesian_grid(stroke_dasharray="3 3"),
                rx.recharts.graphing_tooltip(),
                data=State.rep_por_tipo,
                width="100%", height=250,
            ),

            rx.text("Servicios por cliente", font_size="14px", font_weight="700", color="#1e3a8a", margin_top="8px"),
            rx.recharts.bar_chart(
                rx.recharts.bar(data_key="cantidad", fill="#7c3aed", name="Servicios"),
                rx.recharts.x_axis(data_key="cliente"),
                rx.recharts.y_axis(),
                rx.recharts.cartesian_grid(stroke_dasharray="3 3"),
                rx.recharts.graphing_tooltip(),
                data=State.rep_por_cliente,
                width="100%", height=250,
            ),

            spacing="4", width="100%",
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
        rx.cond(State.pagina == "stock_productos", page_stock_productos(),
        rx.cond(State.pagina == "stock_proveedores", page_proveedores(),
        rx.cond(State.pagina == "terceros_lista", page_terceros_lista(),
        rx.cond(State.pagina == "terceros_stock", page_terceros_stock(),
        rx.cond(State.pagina == "serv_cargar", page_serv_cargar(),
        rx.cond(State.pagina == "serv_lista", page_serv_lista(),
        rx.cond(State.pagina == "reporte_cruzado", page_reporte_cruzado(),
        layout(rx.vstack(
            rx.heading("Bienvenido!", size="7"),
            rx.text("Seleccioná un módulo del sidebar.", color="gray"),
            spacing="4",
        ))))))))))))))))


app = rx.App(theme=rx.theme(accent_color="blue", has_background=True))
app.add_page(login_page, route="/")
app.add_page(dashboard_page, route="/dashboard", on_load=State.cargar_empleados)