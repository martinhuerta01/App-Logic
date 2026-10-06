-- Migración 007: retirados (equipos desinstalados), recepción en la Oficina y faltantes.
-- PENDIENTE DE APLICAR en Supabase (ejecutar completa, una sola vez). Requiere la 006 ya aplicada.
--
-- Un equipo retirado queda en equipos_estado con estado RETIRADO_PENDIENTE y la ubicación donde está
-- (camioneta, taller o centro). Al recibirlo en la Oficina se anota la fecha y quién lo recibió;
-- las piezas que no llegaron quedan como faltantes. Recibir un equipo NO suma stock disponible.

ALTER TABLE equipos_estado ADD COLUMN IF NOT EXISTS recibido_en timestamptz NULL;
ALTER TABLE equipos_estado ADD COLUMN IF NOT EXISTS recibido_por text NULL;

CREATE TABLE IF NOT EXISTS configuracion_stock (
  clave text PRIMARY KEY,
  valor text NOT NULL,
  updated_at timestamptz NOT NULL DEFAULT now()
);
INSERT INTO configuracion_stock (clave, valor) VALUES ('dias_alerta_retirados', '15') ON CONFLICT (clave) DO NOTHING;

CREATE TABLE IF NOT EXISTS recepciones (
  id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
  serial text NOT NULL,
  producto_id uuid NULL REFERENCES productos(id),
  ubicacion_origen_id uuid NULL REFERENCES ubicaciones(id),
  ticket_numero text NULL,
  recibido_por text NULL,
  recibido_en timestamptz NOT NULL DEFAULT now()
);
CREATE INDEX IF NOT EXISTS idx_recepciones_serial ON recepciones(serial);

CREATE TABLE IF NOT EXISTS faltantes (
  id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
  recepcion_id uuid NULL REFERENCES recepciones(id) ON DELETE CASCADE,
  serial text NOT NULL,
  ticket_numero text NULL,
  ubicacion_id uuid NULL REFERENCES ubicaciones(id),
  pieza text NOT NULL,
  resuelto boolean NOT NULL DEFAULT false,
  creado_en timestamptz NOT NULL DEFAULT now()
);
CREATE INDEX IF NOT EXISTS idx_faltantes_pendientes ON faltantes(resuelto) WHERE resuelto = false;

-- Recibe un retirado en la Oficina. p_piezas: [{pieza: "Lectora", llego: true|false}]
CREATE OR REPLACE FUNCTION fn_recibir_retirado(
  p_serial text, p_oficina uuid, p_recibido_por text, p_ticket text, p_piezas jsonb
) RETURNS jsonb LANGUAGE plpgsql AS $$
DECLARE
  v_eq record;
  v_recepcion uuid := gen_random_uuid();
  v_pieza jsonb;
  v_faltantes int := 0;
BEGIN
  SELECT * INTO v_eq FROM equipos_estado WHERE serial = p_serial FOR UPDATE;
  IF NOT FOUND THEN RAISE EXCEPTION 'No existe el equipo %', p_serial; END IF;
  IF v_eq.estado <> 'RETIRADO_PENDIENTE' THEN RAISE EXCEPTION 'El equipo % no figura como retirado pendiente', p_serial; END IF;
  IF v_eq.recibido_en IS NOT NULL THEN RAISE EXCEPTION 'El equipo % ya fue recibido en la Oficina', p_serial; END IF;

  INSERT INTO recepciones (id, serial, producto_id, ubicacion_origen_id, ticket_numero, recibido_por)
  VALUES (v_recepcion, p_serial, v_eq.producto_id, v_eq.ubicacion_id, p_ticket, p_recibido_por);

  FOR v_pieza IN SELECT * FROM jsonb_array_elements(coalesce(p_piezas, '[]'::jsonb))
  LOOP
    IF coalesce((v_pieza->>'llego')::boolean, true) = false THEN
      INSERT INTO faltantes (recepcion_id, serial, ticket_numero, ubicacion_id, pieza)
      VALUES (v_recepcion, p_serial, p_ticket, v_eq.ubicacion_id, v_pieza->>'pieza');
      v_faltantes := v_faltantes + 1;
    END IF;
  END LOOP;

  UPDATE equipos_estado
     SET ubicacion_id = p_oficina, recibido_en = now(), recibido_por = p_recibido_por, updated_at = now()
   WHERE id = v_eq.id;

  RETURN jsonb_build_object('recepcion_id', v_recepcion, 'faltantes', v_faltantes);
END;
$$;
