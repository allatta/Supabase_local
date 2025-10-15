#!/usr/bin/env python3
"""
Scheduler principal para sincronização diária de dados Sungrow com Supabase.

Este script executa diariamente:
1. Renovação do token Sungrow
2. Download de dados do dia anterior (inverters, combiners, yield, fault logs)
3. Inserção no Supabase com deduplicação
4. Geração de CSVs anuais como backup
"""

import os
import sys
import subprocess
import logging
from datetime import datetime, timedelta
from dotenv import load_dotenv
import pandas as pd
from supabase import create_client, Client

# Configuração de logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('scheduler.log'),
        logging.StreamHandler(sys.stdout)
    ]
)
logger = logging.getLogger(__name__)

# Carregar variáveis de ambiente
load_dotenv()

# Credenciais Supabase (ajuste conforme necessário)
SUPABASE_URL = os.getenv('SUPABASE_URL', 'your_supabase_url')
SUPABASE_KEY = os.getenv('SUPABASE_ANON_KEY', 'your_supabase_anon_key')

# Inicializar cliente Supabase
supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY)

def renew_token():
    """Renova o token Sungrow se necessário."""
    logger.info("Renovando token Sungrow...")
    try:
        result = subprocess.run([sys.executable, 'login_script.py'],
                              capture_output=True, text=True, timeout=60)
        if result.returncode == 0:
            logger.info("Token renovado com sucesso")
            return True
        else:
            logger.error(f"Falha ao renovar token: {result.stderr}")
            return False
    except Exception as e:
        logger.error(f"Erro ao executar login_script.py: {e}")
        return False

def run_script_with_date(script_name, start_date, end_date, date_format='timestamp'):
    """Executa um script com datas específicas."""
    logger.info(f"Executando {script_name} de {start_date} até {end_date}")

    cmd = [sys.executable, script_name, '--start', start_date, '--end', end_date]

    try:
        result = subprocess.run(cmd, capture_output=True, text=True, timeout=3600)  # 1h timeout
        if result.returncode == 0:
            logger.info(f"{script_name} executado com sucesso")
            return True
        else:
            logger.error(f"Falha em {script_name}: {result.stderr}")
            return False
    except subprocess.TimeoutExpired:
        logger.error(f"Timeout em {script_name}")
        return False
    except Exception as e:
        logger.error(f"Erro ao executar {script_name}: {e}")
        return False

def insert_to_supabase(table_name, csv_file, unique_columns):
    """Insere dados no Supabase com deduplicação."""
    logger.info(f"Inserindo dados em {table_name}...")

    try:
        # Ler CSV
        df = pd.read_csv(csv_file)
        if df.empty:
            logger.info(f"CSV {csv_file} vazio, pulando inserção")
            return True

        # Converter tipos de dados conforme necessário e para strings JSON-serializáveis
        if 'timestamp' in df.columns:
            df['timestamp'] = pd.to_datetime(df['timestamp']).dt.strftime('%Y-%m-%d %H:%M:%S')
        if 'date' in df.columns:
            df['date'] = pd.to_datetime(df['date']).dt.strftime('%Y-%m-%d')

        # Substituir NaN por None (null em JSON)
        df = df.replace({float('nan'): None})

        # Inserir em lotes para evitar timeout
        batch_size = 1000
        total_inserted = 0

        for i in range(0, len(df), batch_size):
            batch = df.iloc[i:i+batch_size]

            # Converter para dict e inserir
            records = batch.to_dict('records')

            # Usar upsert para evitar duplicatas (usa chave primária composta automaticamente)
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

def generate_yearly_backup(table_name, year):
    """Gera CSV anual consultando o Supabase."""
    logger.info(f"Gerando backup anual {table_name}_{year}.csv")

    try:
        # Query para dados do ano
        if table_name in ['inverter_measures', 'combiner_measures', 'fault_alarms']:
            query = supabase.table(table_name).select('*').gte('timestamp', f'{year}-01-01').lt('timestamp', f'{year+1}-01-01').execute()
        elif table_name == 'yield_daily':
            query = supabase.table(table_name).select('*').gte('date', f'{year}-01-01').lt('date', f'{year+1}-01-01').execute()
        else:
            logger.error(f"Tabela desconhecida: {table_name}")
            return False

        if not query.data:
            logger.info(f"Nenhum dado encontrado para {table_name} {year}")
            return True

        # Criar DataFrame e salvar
        df = pd.DataFrame(query.data)
        filename = f"{table_name}_{year}.csv"
        df.to_csv(filename, index=False)
        logger.info(f"Backup salvo: {filename} ({len(df)} registros)")
        return True

    except Exception as e:
        logger.error(f"Erro ao gerar backup {table_name}_{year}: {e}")
        return False

def main():
    """Função principal do scheduler."""
    logger.info("=== Iniciando scheduler diário ===")

    # Calcular datas do dia anterior
    yesterday = datetime.now() - timedelta(days=2) #dois dis antes do dia atual para não conflitar com o POSTREQUEST do Sungrow
    yesterday_str = yesterday.strftime('%Y%m%d')
    yesterday_start = yesterday.strftime('%Y%m%d') + '000000'  # 00:00:00
    yesterday_end = yesterday.strftime('%Y%m%d') + '235500'    # 23:55:00

    success_count = 0
    total_steps = 10

    # 1. Renovar token
    if renew_token():
        success_count += 1
        logger.info("✓ Token renovado")
    else:
        logger.error("✗ Falha na renovação do token")
        return False

    # 2. Baixar dados de inverters
    if run_script_with_date('get_inverter_measures.py', yesterday_start, yesterday_end):
        success_count += 1
        logger.info("✓ Dados de inverters baixados")
    else:
        logger.error("✗ Falha no download de inverters")

    # 3. Baixar dados de combiners
    if run_script_with_date('get_combiner_measures.py', yesterday_start, yesterday_end):
        success_count += 1
        logger.info("✓ Dados de combiners baixados")
    else:
        logger.error("✗ Falha no download de combiners")

    # 4. Baixar dados de yield
    if run_script_with_date('get_yield_daily.py', yesterday_str, yesterday_str):
        success_count += 1
        logger.info("✓ Dados de yield baixados")
    else:
        logger.error("✗ Falha no download de yield")

    # 5. Baixar dados de fault alarms
    if run_script_with_date('get_fault_alarms.py', yesterday_start, yesterday_end):
        success_count += 1
        logger.info("✓ Dados de fault alarms baixados")
    else:
        logger.error("✗ Falha no download de fault alarms")

    # 6. Inserir inverters no Supabase
    if insert_to_supabase('inverter_measures', 'inverter_measures.csv', ['timestamp', 'device']):
        success_count += 1
        logger.info("✓ Dados de inverters inseridos no Supabase")
    else:
        logger.error("✗ Falha na inserção de inverters")

    # 7. Inserir combiners no Supabase
    if insert_to_supabase('combiner_measures', 'combiner_measures.csv', ['timestamp', 'device']):
        success_count += 1
        logger.info("✓ Dados de combiners inseridos no Supabase")
    else:
        logger.error("✗ Falha na inserção de combiners")

    # 8. Inserir yield no Supabase
    if insert_to_supabase('yield_daily', 'yield_daily.csv', ['date', 'device']):
        success_count += 1
        logger.info("✓ Dados de yield inseridos no Supabase")
    else:
        logger.error("✗ Falha na inserção de yield")

    # 9. Inserir fault alarms no Supabase
    if insert_to_supabase('fault_alarms', 'fault_alarms.csv', ['timestamp', 'device']):
        success_count += 1
        logger.info("✓ Dados de fault alarms inseridos no Supabase")
    else:
        logger.error("✗ Falha na inserção de fault alarms")

    # 10. Gerar backups anuais (opcional, executado apenas se todos os passos anteriores passaram)
    if success_count == total_steps:
        current_year = datetime.now().year
        generate_yearly_backup('inverter_measures', current_year)
        generate_yearly_backup('combiner_measures', current_year)
        generate_yearly_backup('yield_daily', current_year)
        generate_yearly_backup('fault_alarms', current_year)
        logger.info("✓ Backups anuais gerados")

    logger.info(f"=== Scheduler concluído: {success_count}/{total_steps} passos com sucesso ===")

    return success_count == total_steps

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
