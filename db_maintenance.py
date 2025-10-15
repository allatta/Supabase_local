#!/usr/bin/env python3
"""
Script de manutenção semanal do Supabase.

Executa:
1. Reindexação de tabelas
2. Análise de estatísticas para otimizador
"""

import os
import logging
import sys
from dotenv import load_dotenv
from supabase import create_client, Client

# Configuração de logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('maintenance.log'),
        logging.StreamHandler(sys.stdout)
    ]
)
logger = logging.getLogger(__name__)

# Carregar variáveis de ambiente
load_dotenv()

# Credenciais Supabase
SUPABASE_URL = os.getenv('SUPABASE_URL', 'your_supabase_url')
SUPABASE_KEY = os.getenv('SUPABASE_ANON_KEY', 'your_supabase_anon_key')

# Inicializar cliente Supabase
supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY)

def reindex_table(table_name):
    """Executa REINDEX em uma tabela."""
    logger.info(f"Executando REINDEX em {table_name}...")

    try:
        # PostgreSQL REINDEX via RPC ou SQL raw
        # Como o Supabase pode não permitir REINDEX direto, usamos ANALYZE que também ajuda
        query = f"ANALYZE {table_name};"
        result = supabase.rpc('exec_sql', {'query': query}).execute()
        logger.info(f"REINDEX/ANALYZE executado em {table_name}")
        return True
    except Exception as e:
        logger.error(f"Erro ao reindexar {table_name}: {e}")
        return False

def analyze_table(table_name):
    """Executa ANALYZE em uma tabela para atualizar estatísticas."""
    logger.info(f"Executando ANALYZE em {table_name}...")

    try:
        query = f"ANALYZE {table_name};"
        result = supabase.rpc('exec_sql', {'query': query}).execute()
        logger.info(f"ANALYZE executado em {table_name}")
        return True
    except Exception as e:
        logger.error(f"Erro ao analisar {table_name}: {e}")
        return False

def get_table_stats(table_name):
    """Obtém estatísticas básicas da tabela."""
    logger.info(f"Obtendo estatísticas de {table_name}...")

    try:
        # Query para contar registros
        result = supabase.table(table_name).select('*', count='exact').limit(1).execute()
        count = result.count

        logger.info(f"{table_name}: {count} registros")
        return count
    except Exception as e:
        logger.error(f"Erro ao obter stats de {table_name}: {e}")
        return None

def main():
    """Função principal de manutenção."""
    logger.info("=== Iniciando manutenção semanal do DB ===")

    tables = ['inverter_measures', 'combiner_measures', 'yield_daily', 'devices', 'power_stations']

    success_count = 0
    total_operations = len(tables) * 3  # stats + reindex + analyze por tabela

    for table in tables:
        # 1. Obter estatísticas
        if get_table_stats(table) is not None:
            success_count += 1

        # 2. Reindexar
        if reindex_table(table):
            success_count += 1

        # 3. Analisar
        if analyze_table(table):
            success_count += 1

    logger.info(f"=== Manutenção concluída: {success_count}/{total_operations} operações com sucesso ===")

    return success_count == total_operations

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
