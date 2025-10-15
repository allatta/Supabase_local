# Sungrow Data Sync - Automação Diária

Este projeto automatiza a sincronização diária de dados da API Sungrow com um banco Supabase local, incluindo manutenção e backup.

## Mudanças Recentes (v2.1)

### Novos Scripts de Inserção Independentes
- **Scripts standalone para inserção**: Criados `insert_combiner_measures.py` e `insert_yield_daily.py` para inserção independente de dados
- **Separação de responsabilidades**: Scripts de inserção isolados da lógica de coleta e automação
- **Flexibilidade de uso**: Permite inserção manual de CSVs existentes sem executar todo o pipeline de coleta

### Melhorias Estruturais (v2.0)
- **Chaves primárias compostas**: Removida coluna `id` auto-incrementada, implementadas chaves primárias compostas:
  - `yield_daily`: `(date, device)`
  - `inverter_measures`: `(timestamp, device)`
  - `combiner_measures`: `(timestamp, device)`
- **Upsert simplificado**: Removido parâmetro `on_conflict` do scheduler, utilizando upsert automático baseado nas chaves primárias
- **Proteção contra duplicatas**: Adicionado `drop_duplicates()` em todos os scripts de coleta para tratar dados duplicados da API

### Melhorias de Instalação
- **Script de instalação automatizada** (`install.sh`): Detecta usuário automaticamente, configura permissões e instala tudo
- **Instalação independente do usuário**: Sistema funciona com qualquer nome de usuário Linux
- **Ambiente virtual integrado**: Criação e configuração automática do venv

### Scripts de Teste e Manutenção
- **Limpeza de tabelas**: Comando direto para limpar dados de teste
- **Verificação de duplicatas**: Scripts para diagnosticar problemas de dados

## Arquitetura

```
Sungrow API → Scripts Python → Supabase DB → CSV Backup Anual
```

## Componentes

### Scripts de Coleta de Dados
- `get_inverter_measures.py`: Coleta dados de inversores (5min)
- `get_combiner_measures.py`: Coleta dados de combiners (5min)
- `get_yield_daily.py`: Coleta dados de produção diária

### Scripts de Inserção
- `insert_inverter_measures.py`: Inserção independente de dados de inversores
- `insert_combiner_measures.py`: Inserção independente de dados de combiners
- `insert_yield_daily.py`: Inserção independente de dados de yield diário

### Scripts de Automação
- `scheduler.py`: Orquestrador diário principal
- `db_maintenance.py`: Manutenção semanal (reindexação/estatísticas)
- `db_backup.py`: Backup diário com pg_dump

### Unidades Systemd
- `scheduler.timer/service`: Sync diário às 02:00
- `db_maintenance.timer/service`: Manutenção semanal (domingos 03:00)
- `db_backup.timer/service`: Backup diário às 04:00

## Instalação

### Instalação Automática (Recomendado)

Para uma instalação simplificada e independente do usuário, use o script de instalação automatizada:

#### No Servidor Linux:
```bash
# 1. Copie todos os arquivos do projeto para o servidor Linux
# (use scp, rsync, git clone, etc.)

# 2. Navegue para o diretório do projeto
cd /path/to/sungrow-project

# 3. Torne o script executável e execute
chmod +x install.sh
./install.sh
```

O script irá:
- Detectar automaticamente o usuário atual
- Criar o diretório `/opt/sungrow-sync`
- Configurar permissões corretas
- Criar ambiente virtual e instalar dependências
- Configurar arquivos Systemd com o usuário correto
- Instalar serviços automaticamente

### Instalação Manual no Servidor Linux

Se preferir instalação manual, siga estes passos:

#### 1. Criar Diretório do Projeto
```bash
# Criar diretório padrão para aplicações
sudo mkdir -p /opt/sungrow-sync

# Ajustar permissões (substitua 'your_user' pelo seu usuário atual)
sudo chown your_user:your_user /opt/sungrow-sync
```

#### 2. Copiar Arquivos para o Servidor
Copie todos os arquivos do projeto para `/opt/sungrow-sync/`:

**Arquivos obrigatórios:**
- Scripts Python: `scheduler.py`, `get_*.py`, `insert_*.py`, `db_*.py`, `login_script.py`
- Arquivos de configuração: `.env`
- Arquivos de dados: `devices.csv`, `power_stations.csv`
- Arquivos SQL: `sql estrutura DB.txt`
- Arquivos Systemd: `*.service`, `*.timer`
- Script de instalação: `install.sh`
- Documentação: `README.md`, `README_MAINTENANCE_FUTURE.md`

#### 3. Criar Ambiente Virtual
```bash
# Navegar para o diretório do projeto
cd /opt/sungrow-sync

# Criar ambiente virtual
python3 -m venv venv

# Ativar ambiente virtual
source venv/bin/activate
```

#### 4. Instalar Dependências Python
```bash
# Com ambiente virtual ativado
pip install requests python-dotenv pandas supabase psycopg2-binary httpx[http2]
```

**Nota:** O `httpx[http2]` é necessário porque a biblioteca Supabase usa HTTP/2 por padrão para conexões mais eficientes.

#### 5. Configuração do Ambiente
Edite o arquivo `.env`:

```bash
# Credenciais Sungrow
APPKEY=your_appkey
X_ACCESS_KEY=your_x_access_key
TOKEN=your_token
USER_ACCOUNT=your_account
USER_PASSWORD=your_password
ENDPOINT=https://gateway.isolarcloud.com.hk/openapi/login

# Credenciais Supabase - API (para scripts Python)
SUPABASE_URL=http://localhost:8000
SUPABASE_ANON_KEY=your_anon_key

# Credenciais Supabase - PostgreSQL (para backup via pg_dump)
DB_HOST=11.1.1.79
DB_PORT=5432
DB_NAME=postgres
DB_USER=postgres.supabase_id
DB_PASSWORD=teste
BACKUP_DIR=./backups
```

### Diferenças nas Credenciais do Supabase

O projeto utiliza **duas formas distintas** de conectar ao Supabase:

#### **API Supabase (Porta 8000)**
- **Usado por**: Scripts Python (`insert_*.py`, `scheduler.py`)
- **Propósito**: Inserção e consulta de dados via API REST
- **Credenciais**:
  - `SUPABASE_URL`: URL da API (localhost:8000)
  - `SUPABASE_ANON_KEY`: Chave anônima para autenticação

#### **PostgreSQL Direto (Porta 5432)**
- **Usado por**: Script de backup (`db_backup.py`)
- **Propósito**: Backup completo do banco via `pg_dump`
- **Credenciais**:
  - `DB_HOST`: IP do servidor (11.1.1.79)
  - `DB_USER`: `postgres.supabase_id` (username específico do pooler)
  - `DB_PASSWORD`: `teste`

#### 6. Arquivos de Dispositivos
Certifique-se de que `devices.csv` e `power_stations.csv` existem (gerados por `get_device_list_multi.py` e `get_power_station_list.py`).

#### 7. Instalação Systemd
```bash
# Copiar unidades para systemd
sudo cp /opt/sungrow-sync/*.timer /opt/sungrow-sync/*.service /etc/systemd/system/

# Recarregar systemd
sudo systemctl daemon-reload

# Ajustar usuário nos arquivos .service (substitua 'your_user' pelo seu usuário)
# sed -i 's/User=.*/User=your_user/' /etc/systemd/system/*.service
# sed -i 's/Group=.*/Group=your_user/' /etc/systemd/system/*.service

# Habilitar timers
sudo systemctl enable scheduler.timer
sudo systemctl enable db_maintenance.timer
sudo systemctl enable db_backup.timer

# Iniciar timers
sudo systemctl start scheduler.timer
sudo systemctl start db_maintenance.timer
sudo systemctl start db_backup.timer
```

## Uso Manual

**Nota:** Todos os comandos devem ser executados no diretório `/opt/sungrow-sync` com o ambiente virtual ativado:

```bash
cd /opt/sungrow-sync
source venv/bin/activate
```

### Executar Sync Diário
```bash
python3 scheduler.py
```

### Executar Manutenção
```bash
python3 db_maintenance.py
```

### Executar Backup
```bash
python3 db_backup.py
```

### Scripts de Inserção Independentes
```bash
# Inserir dados de CSVs existentes no Supabase
python3 insert_inverter_measures.py
python3 insert_combiner_measures.py
python3 insert_yield_daily.py
```

### Scripts Individuais com Datas Específicas
```bash
# Inverters
python3 get_inverter_measures.py --start 20241201000000 --end 20241201235500 #Linux
python get_inverter_measures.py --start 20241201000000 --end 20241201235500  #Windows
# Combiners
python3 get_combiner_measures.py --start 20241201000000 --end 20241201235500 #Linux
python get_combiner_measures.py --start 20241201000000 --end 20241201235500 #Windows
# Yield
python3 get_yield_daily.py --start 20241201 --end 20241201 #Linux
python get_yield_daily.py --start 20241201 --end 20241201 #Windows
```

### Limpar Tabelas para Testes
```bash
# Limpar todas as tabelas de dados (para testes)
python3 -c "
from supabase import create_client
import os
from dotenv import load_dotenv
load_dotenv()
supabase = create_client(os.getenv('SUPABASE_URL'), os.getenv('SUPABASE_ANON_KEY'))
tables = ['inverter_measures', 'combiner_measures', 'yield_daily']
for table in tables:
    supabase.table(table).delete().neq('device', '').execute()
    print(f'Tabela {table} limpa')
"
```

## Monitoramento

### Logs Systemd
```bash
# Ver status dos timers
systemctl list-timers

# Logs do scheduler
journalctl -u scheduler.service -f

# Logs de manutenção
journalctl -u db_maintenance.service -f

# Logs de backup
journalctl -u db_backup.service -f
```

### Arquivos de Log
- `scheduler.log`: Logs do sync diário
- `insert_inverter_measures.log`: Logs de inserção de dados de inversores
- `insert_combiner_measures.log`: Logs de inserção de dados de combiners
- `insert_yield_daily.log`: Logs de inserção de dados de yield diário
- `maintenance.log`: Logs de manutenção
- `backup.log`: Logs de backup

## Estrutura de Dados

### Tabelas Supabase
- `power_stations`: Estações de energia
- `devices`: Dispositivos (inversores/combiners)
- `inverter_measures`: Medidas de inversores (timestamp, device, métricas)
- `combiner_measures`: Medidas de combiners (timestamp, device, métricas)
- `yield_daily`: Produção diária (date, device, yield_today)

### Backups CSV Anuais
- `inverter_measures_2024.csv`
- `combiner_measures_2024.csv`
- `yield_daily_2024.csv`

### Backups PostgreSQL
- `./backups/backup_YYYYMMDD_HHMMSS.sql.gz`

## Segurança

- Credenciais armazenadas em `.env` (não versionado)
- Backups comprimidos automaticamente
- Limpeza automática de backups antigos (>30 dias)
- Logs detalhados para auditoria

## Troubleshooting

### Timer não executa
```bash
# Ver status
systemctl status scheduler.timer

# Ver logs
journalctl -u scheduler.service
```

### Falha de conexão Supabase
- Verificar se Docker do Supabase está rodando
- Verificar credenciais no `.env`
- Verificar conectividade de rede

### Falha no pg_dump
- Verificar se PostgreSQL está acessível
- Verificar credenciais DB no `.env`
- Verificar espaço em disco

## Expansões Futuras

Ver `README_MAINTENANCE_FUTURE.md` para funcionalidades planejadas:
- Limpeza de dados antigos
- Agregação histórica
- Monitoramento avançado
- Recuperação de desastres

## Suporte

Para issues ou dúvidas, verificar logs e documentação dos scripts individuais.
