-- Migración 003: stock mínimo por vista, plazo de entrega por producto y enlace de ubicación con equipo.
-- PENDIENTE DE APLICAR en Supabase (ejecutar completa, una sola vez).

-- Plazo de entrega del proveedor, en días. Reemplaza los 3 días fijos de la fecha de pedido sugerida.
ALTER TABLE productos ADD COLUMN IF NOT EXISTS plazo_entrega_dias integer NULL
  CHECK (plazo_entrega_dias IS NULL OR plazo_entrega_dias >= 0);

-- Stock mínimo por producto y por ámbito (la vista del Dashboard de Stock: oficina, serenisima, camioneta1, camioneta2).
-- Para "serenisima" el mínimo es del total de todos los centros de distribución juntos.
CREATE TABLE IF NOT EXISTS stock_minimo (
  id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
  producto_id uuid NOT NULL REFERENCES productos(id) ON DELETE CASCADE,
  ambito text NOT NULL,
  cantidad_minima integer NOT NULL CHECK (cantidad_minima >= 0),
  updated_at timestamptz NOT NULL DEFAULT now(),
  CONSTRAINT uq_stock_minimo UNIQUE (producto_id, ambito)
);
CREATE INDEX IF NOT EXISTS idx_stock_minimo_ambito ON stock_minimo(ambito);

-- Enlace opcional de una ubicación (por ejemplo Camioneta 1) con el equipo de Personal (Equipo 1).
ALTER TABLE ubicaciones ADD COLUMN IF NOT EXISTS equipo_id uuid NULL REFERENCES equipos(id) ON DELETE SET NULL;
