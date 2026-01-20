#!/usr/bin/env python3
"""Script para adicionar coluna project_id à tabela activities"""
import asyncio
from sqlalchemy import text
from app.core.database import engine

async def add_project_id_column():
    """Adiciona coluna project_id se não existir"""
    async with engine.begin() as conn:
        # Verificar se a coluna já existe
        check_result = await conn.execute(
            text("""
                SELECT column_name 
                FROM information_schema.columns 
                WHERE table_name='activities' AND column_name='project_id'
            """)
        )
        exists = check_result.fetchone()
        
        if not exists:
            # Adicionar coluna
            await conn.execute(
                text("""
                    ALTER TABLE activities 
                    ADD COLUMN project_id INTEGER REFERENCES projects(id)
                """)
            )
            print("✅ Coluna project_id adicionada à tabela activities")
        else:
            print("✅ Coluna project_id já existe")

if __name__ == "__main__":
    asyncio.run(add_project_id_column())


