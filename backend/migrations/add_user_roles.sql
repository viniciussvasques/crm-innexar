-- Migration para adicionar novos valores ao enum userrole
-- Execute apenas se os valores não existirem

DO $$ 
BEGIN
    -- Adicionar 'planejamento' se não existir
    IF NOT EXISTS (
        SELECT 1 FROM pg_enum 
        WHERE enumlabel = 'planejamento' 
        AND enumtypid = 'userrole'::regtype
    ) THEN
        ALTER TYPE userrole ADD VALUE 'planejamento';
    END IF;

    -- Adicionar 'dev' se não existir
    IF NOT EXISTS (
        SELECT 1 FROM pg_enum 
        WHERE enumlabel = 'dev' 
        AND enumtypid = 'userrole'::regtype
    ) THEN
        ALTER TYPE userrole ADD VALUE 'dev';
    END IF;
END $$;

-- Verificar valores do enum
SELECT unnest(enum_range(NULL::userrole)) AS role_value;

