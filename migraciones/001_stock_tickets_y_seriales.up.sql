-- Migración 001: importación de tickets de soporte y seguimiento de equipos por número de serie.
-- YA APLICADA en Supabase (reconstruida a partir del plan para dejarla versionada).
-- No volver a ejecutar en la base actual; sirve para crear otro entorno desde cero.

-- Registro de tickets importados (evita descontar dos veces el mismo ticket)
CREATE TABLE IF NOT EXISTS tickets_importados (
  id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
  ticket_numero text NOT NULL,
  distrito text NULL,
  archivo_nombre text NULL,
  fila_excel jsonb NULL,
  importado_por text NULL,
  importado_en timestamptz NOT NULL DEFAULT now(),
  CONSTRAINT uq_ticket_numero UNIQUE (ticket_numero)
);

-- Serial y ticket de origen en cada movimiento
ALTER TABLE movimientos ADD COLUMN IF NOT EXISTS serial text NULL;
ALTER TABLE movimientos ADD COLUMN IF NOT EXISTS ticket_id uuid NULL REFERENCES tickets_importados(id);
CREATE INDEX IF NOT EXISTS idx_movimientos_serial ON movimientos(serial) WHERE serial IS NOT NULL;
CREATE INDEX IF NOT EXISTS idx_movimientos_ticket_id ON movimientos(ticket_id) WHERE ticket_id IS NOT NULL;

-- Palabra clave de localidad o taller -> ubicación de destino
CREATE TABLE IF NOT EXISTS mapeo_talleres (
  id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
  keyword text NOT NULL,
  ubicacion_id uuid NOT NULL REFERENCES ubicaciones(id),
  activo boolean NOT NULL DEFAULT true,
  created_at timestamptz NOT NULL DEFAULT now()
);
CREATE INDEX IF NOT EXISTS idx_mapeo_talleres_activo ON mapeo_talleres(activo);

-- Estado actual de cada equipo identificado por número de serie
CREATE TABLE IF NOT EXISTS equipos_estado (
  id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
  producto_id uuid NOT NULL REFERENCES productos(id),
  serial text NOT NULL,
  estado text NOT NULL DEFAULT 'EN_STOCK'
    CHECK (estado IN ('EN_STOCK','INSTALADO','RETIRADO_PENDIENTE','USADO_OK_CAMPO','USADO_OK_OFICINA','FALLA_RMA','BAJA')),
  ubicacion_id uuid NULL REFERENCES ubicaciones(id),
  patente text NULL,
  sin_control boolean NOT NULL DEFAULT false,
  updated_at timestamptz NOT NULL DEFAULT now(),
  created_at timestamptz NOT NULL DEFAULT now(),
  CONSTRAINT uq_equipos_estado_serial UNIQUE (serial)
);
CREATE INDEX IF NOT EXISTS idx_equipos_estado_estado ON equipos_estado(estado);
CREATE INDEX IF NOT EXISTS idx_equipos_estado_patente ON equipos_estado(patente) WHERE patente IS NOT NULL;

-- Confirma UN ticket de forma atómica: registro de duplicado, movimientos, stock y estado del equipo
CREATE OR REPLACE FUNCTION fn_confirmar_ticket_stock(
  p_ticket_numero text,
  p_distrito text,
  p_archivo_nombre text,
  p_fila_excel jsonb,
  p_cargado_por text,
  p_movimientos jsonb
) RETURNS jsonb
LANGUAGE plpgsql
AS $$
DECLARE
  v_ticket_id uuid;
  v_mov jsonb;
  v_stock_id uuid;
  v_cantidad_actual int;
BEGIN
  INSERT INTO tickets_importados (ticket_numero, distrito, archivo_nombre, fila_excel, importado_por)
  VALUES (p_ticket_numero, p_distrito, p_archivo_nombre, p_fila_excel, p_cargado_por)
  ON CONFLICT (ticket_numero) DO NOTHING
  RETURNING id INTO v_ticket_id;

  IF v_ticket_id IS NULL THEN
    RETURN jsonb_build_object('duplicado', true, 'ticket_numero', p_ticket_numero);
  END IF;

  FOR v_mov IN SELECT * FROM jsonb_array_elements(p_movimientos)
  LOOP
    INSERT INTO movimientos (tipo, producto_id, origen_id, destino_id, cantidad, fecha, cargado_por, observacion, serial, ticket_id)
    VALUES (
      v_mov->>'tipo', (v_mov->>'producto_id')::uuid,
      NULLIF(v_mov->>'origen_id','')::uuid, NULLIF(v_mov->>'destino_id','')::uuid,
      (v_mov->>'cantidad')::int, (v_mov->>'fecha')::date,
      p_cargado_por, v_mov->>'observacion', NULLIF(v_mov->>'serial',''), v_ticket_id
    );

    IF NULLIF(v_mov->>'origen_id','') IS NOT NULL THEN
      SELECT id, cantidad INTO v_stock_id, v_cantidad_actual FROM stock_actual
        WHERE producto_id = (v_mov->>'producto_id')::uuid AND ubicacion_id = (v_mov->>'origen_id')::uuid;
      IF v_stock_id IS NOT NULL THEN
        UPDATE stock_actual SET cantidad = v_cantidad_actual - (v_mov->>'cantidad')::int WHERE id = v_stock_id;
      ELSE
        INSERT INTO stock_actual (producto_id, ubicacion_id, cantidad)
        VALUES ((v_mov->>'producto_id')::uuid, (v_mov->>'origen_id')::uuid, -(v_mov->>'cantidad')::int);
      END IF;
    END IF;
    IF NULLIF(v_mov->>'destino_id','') IS NOT NULL THEN
      SELECT id, cantidad INTO v_stock_id, v_cantidad_actual FROM stock_actual
        WHERE producto_id = (v_mov->>'producto_id')::uuid AND ubicacion_id = (v_mov->>'destino_id')::uuid;
      IF v_stock_id IS NOT NULL THEN
        UPDATE stock_actual SET cantidad = v_cantidad_actual + (v_mov->>'cantidad')::int WHERE id = v_stock_id;
      ELSE
        INSERT INTO stock_actual (producto_id, ubicacion_id, cantidad)
        VALUES ((v_mov->>'producto_id')::uuid, (v_mov->>'destino_id')::uuid, (v_mov->>'cantidad')::int);
      END IF;
    END IF;

    IF NULLIF(v_mov->>'serial','') IS NOT NULL THEN
      INSERT INTO equipos_estado (producto_id, serial, estado, ubicacion_id, patente)
      VALUES (
        (v_mov->>'producto_id')::uuid, v_mov->>'serial',
        CASE v_mov->>'tipo' WHEN 'RETIRO' THEN 'RETIRADO_PENDIENTE' WHEN 'INSTALACION' THEN 'INSTALADO' ELSE 'EN_STOCK' END,
        CASE WHEN v_mov->>'tipo' = 'INSTALACION' THEN NULL ELSE NULLIF(v_mov->>'destino_id','')::uuid END,
        CASE WHEN v_mov->>'tipo' = 'INSTALACION' THEN v_mov->>'patente' ELSE NULL END
      )
      ON CONFLICT (serial) DO UPDATE SET
        estado = EXCLUDED.estado, ubicacion_id = EXCLUDED.ubicacion_id,
        patente = EXCLUDED.patente, updated_at = now();
    END IF;
  END LOOP;

  RETURN jsonb_build_object('duplicado', false, 'ticket_id', v_ticket_id, 'movimientos', jsonb_array_length(p_movimientos));
END;
$$;
