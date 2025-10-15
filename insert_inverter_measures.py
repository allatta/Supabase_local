#!/usr/bin/env python3
"""
Script para inserir dados do inverter_measures.csv na tabela inverter_measures do Supabase.

Este script lê o arquivo CSV e insere os dados no Supabase com deduplicação.
"""

import os
import sys
import logging
from dotenv import load_dotenv
import pandas as pd
from supabase import create_client, Client

# Configuração de logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('insert_inverter_measures.log'),
        logging.StreamHandler(sys.stdout)
    ]
)
logger = logging.getLogger(__name__)

# Carregar variáveis de ambiente
load_dotenv()

# Credenciais Supabase
SUPABASE_URL = os.getenv('SUPABASE_URL')
SUPABASE_KEY = os.getenv('SUPABASE_ANON_KEY')

if not SUPABASE_URL or not SUPABASE_KEY:
    logger.error("SUPABASE_URL ou SUPABASE_ANON_KEY não encontradas no .env")
    sys.exit(1)

# Inicializar cliente Supabase
supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY)

def insert_inverter_measures_to_supabase():
    """Insere dados do inverter_measures.csv no Supabase."""
    csv_file = 'inverter_measures.csv'
    table_name = 'inverter_measures'

    logger.info(f"Inserindo dados de {csv_file} em {table_name}...")

    try:
        # Ler CSV
        df = pd.read_csv(csv_file)
        if df.empty:
            logger.info(f"CSV {csv_file} vazio, pulando inserção")
            return True

        # Converter tipos de dados
        if 'timestamp' in df.columns:
            df['timestamp'] = pd.to_datetime(df['timestamp']).dt.strftime('%Y-%m-%d %H:%M:%S')

        # Substituir NaN por None
        df = df.replace({float('nan'): None})

        # Inserir em lotes
        batch_size = 1000
        total_inserted = 0

        for i in range(0, len(df), batch_size):
            batch = df.iloc[i:i+batch_size]
            records = batch.to_dict('records')

            try:
                result = supabase.table(table_name).upsert(records).execute()
                total_inserted += len(records)
                logger.info(f"Inseridos {len(records)} registros em {table_name} (lote {i//batch_size + 1})")
            except Exception as e:
                logger.error(f"Erro ao inserir lote em {table_name}: {e}")
                return False

        logger.info(f"Total inserido em {table_name}: {total_inserted}")
        return True

    except Exception as e:
        logger.error(f"Erro ao processar {csv_file}: {e}")
        return False

def main():
    """Função principal."""
    logger.info("=== Iniciando inserção de inverter_measures ===")

    if insert_inverter_measures_to_supabase():
        logger.info("=== Inserção concluída com sucesso ===")
        return True
    else:
        logger.error("=== Falha na inserção ===")
        return False

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
