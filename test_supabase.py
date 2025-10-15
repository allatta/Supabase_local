#!/usr/bin/env python3
"""
Script para testar conexão com Supabase local
"""

import os
from dotenv import load_dotenv
from supabase import create_client, Client

# Carregar variáveis de ambiente
load_dotenv()

SUPABASE_URL = os.getenv('SUPABASE_URL', 'http://localhost:8000')
SUPABASE_KEY = os.getenv('SUPABASE_ANON_KEY')

def test_connection():
    """Testa conexão básica com Supabase"""
    try:
        print(f"Testando conexão com: {SUPABASE_URL}")
        
        supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY)
        
        # Teste básico - tentar listar tabelas
        result = supabase.table('power_stations').select('*').limit(1).execute()
        
        print("✅ Conexão com Supabase estabelecida!")
        print(f"Registros encontrados na tabela power_stations: {len(result.data)}")
        
        return True
        
    except Exception as e:
        print(f"❌ Erro de conexão: {e}")
        return False

def test_tables():
    """Testa se as tabelas existem e têm a estrutura correta"""
    try:
        supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY)
        
        tables = ['power_stations', 'devices', 'inverter_measures', 'combiner_measures', 'yield_daily']
        
        for table in tables:
            try:
                # Tentar fazer uma consulta simples
                result = supabase.table(table).select('*').limit(1).execute()
                print(f"✅ Tabela '{table}' acessível")
            except Exception as e:
                print(f"❌ Erro na tabela '{table}': {e}")
                
    except Exception as e:
        print(f"❌ Erro geral: {e}")

if __name__ == "__main__":
    print("=== Teste de Conexão Supabase ===\n")
    
    if test_connection():
        print("\n=== Teste de Tabelas ===\n")
        test_tables()
    else:
        print("\n=== Instruções para resolver ===\n")
        print("1. Verificar se o Docker está rodando:")
        print("   docker ps")
        print()
        print("2. Verificar containers Supabase:")
        print("   docker ps | grep supabase")
        print()
        print("3. Se não estiver rodando, iniciar Supabase:")
        print("   # Navegar para o diretório do Supabase")
        print("   cd /path/to/supabase-project")
        print("   supabase start")
        print()
        print("4. Verificar portas:")
        print("   netstat -tlnp | grep 54321")
        print("   curl http://localhost:54321/rest/v1/")
        print()
        print("5. Verificar arquivo .env:")
        print("   cat /opt/sungrow-sync/.env")
        print("   # SUPABASE_URL deve ser http://localhost:54321")
