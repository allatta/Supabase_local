#!/usr/bin/env python3
"""
Script de backup diário do Supabase.

Executa pg_dump do banco PostgreSQL local (já comprimido internamente).
"""

import os
import logging
import sys
import subprocess
from datetime import datetime
from dotenv import load_dotenv

# Configuração de logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('backup.log'),
        logging.StreamHandler(sys.stdout)
    ]
)
logger = logging.getLogger(__name__)

# Carregar variáveis de ambiente
load_dotenv()

# Configurações do PostgreSQL (ajuste conforme seu docker-compose)
DB_HOST = os.getenv('DB_HOST', '11.1.1.79')
DB_PORT = os.getenv('DB_PORT', '5432')  # Porta padrão do Supabase local
DB_NAME = os.getenv('DB_NAME', 'postgres')
DB_USER = os.getenv('DB_USER', 'postgres.supabase_id')
DB_PASSWORD = os.getenv('DB_PASSWORD', 'your_password')

# Diretório de backups
BACKUP_DIR = os.getenv('BACKUP_DIR', './backups')

def create_backup_dir():
    """Cria diretório de backups se não existir."""
    if not os.path.exists(BACKUP_DIR):
        os.makedirs(BACKUP_DIR)
        logger.info(f"Diretório de backup criado: {BACKUP_DIR}")

def run_pg_dump(filename):
    """Executa pg_dump para criar backup."""
    logger.info(f"Iniciando backup: {filename}")

    # Comando pg_dump
    cmd = [
        '/usr/bin/pg_dump',
        f'--host={DB_HOST}',
        f'--port={DB_PORT}',
        f'--username={DB_USER}',
        f'--dbname={DB_NAME}',
        '--format=custom',  # Formato compactado
        '--compress=9',     # Máxima compressão
        '--no-owner',       # Não incluir ownership
        '--no-privileges',  # Não incluir privilégios
        '--file', filename
    ]

    # Variável de ambiente para senha
    env = os.environ.copy()
    env['PGPASSWORD'] = DB_PASSWORD

    try:
        result = subprocess.run(cmd, env=env, capture_output=True, text=True, timeout=1800)  # 30min timeout

        if result.returncode == 0:
            logger.info(f"Backup criado com sucesso: {filename}")
            return True
        else:
            logger.error(f"Falha no pg_dump: {result.stderr}")
            return False

    except subprocess.TimeoutExpired:
        logger.error("Timeout no pg_dump")
        return False
    except Exception as e:
        logger.error(f"Erro ao executar pg_dump: {e}")
        return False



def cleanup_old_backups():
    """Remove backups antigos (mantém últimos 30 dias)."""
    logger.info("Limpando backups antigos...")

    try:
        # Listar arquivos de backup
        import glob
        backup_files = glob.glob(os.path.join(BACKUP_DIR, 'backup_*.sql'))

        # Ordenar por data (mais recente primeiro)
        backup_files.sort(key=os.path.getctime, reverse=True)

        # Manter apenas os 30 mais recentes
        files_to_remove = backup_files[30:]

        for file_path in files_to_remove:
            os.remove(file_path)
            logger.info(f"Backup antigo removido: {os.path.basename(file_path)}")

        logger.info(f"Limpeza concluída. {len(files_to_remove)} arquivos removidos.")

    except Exception as e:
        logger.error(f"Erro na limpeza de backups: {e}")

def get_backup_size(filename):
    """Retorna o tamanho do arquivo de backup em MB."""
    try:
        size_bytes = os.path.getsize(filename)
        size_mb = size_bytes / (1024 * 1024)
        return round(size_mb, 2)
    except Exception:
        return 0

def main():
    """Função principal de backup."""
    logger.info("=== Iniciando backup diário ===")

    # Criar diretório se necessário
    create_backup_dir()

    # Gerar nome do arquivo
    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    backup_file = os.path.join(BACKUP_DIR, f'backup_{timestamp}.sql')

    success = False

    # 1. Executar pg_dump
    if run_pg_dump(backup_file):
        size_mb = get_backup_size(backup_file)
        logger.info(f"Backup concluído: {os.path.basename(backup_file)} ({size_mb} MB)")
        success = True
    else:
        logger.error("Falha na criação do backup")

    # 2. Limpar backups antigos
    cleanup_old_backups()

    logger.info("=== Backup concluído ===")

    return success

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
