# Projeto Sungrow Data Sync

Sistema completo para coleta, processamento e armazenamento automatizado de dados de usinas solares Sungrow.

## 🎯 Visão Geral

Este projeto oferece uma solução completa para monitoramento de usinas solares conectadas ao ecossistema Sungrow, desde a coleta de dados em tempo real até o armazenamento automatizado em banco de dados.

### Principais Componentes:
- **📊 Coleta de Dados**: Scripts para extração de dados da API Sungrow
- **🔄 Automação**: Sistema de sincronização diária com Supabase
- **🔮 Expansões**: Funcionalidades futuras e manutenção avançada

---

## 📖 Documentação

### 🔄 Pipeline Completo (Automação + Supabase)
Para usuários que querem o sistema completo de automação diária com armazenamento em banco:
- **[README_01.md](README_01.md)** - Sistema de automação Supabase, instalação, monitoramento e backup

  > **Nota**: Este README explica as diferenças entre credenciais API vs PostgreSQL para backup

### 📊 Coleta de Dados (API Sungrow)
Para usuários que querem coletar dados da API Sungrow para análise:
- **[README_02.md](README_02.md)** - Scripts de coleta, autenticação e referência completa da API

### 🔮 Manutenção e Expansões Futuras
Para funcionalidades planejadas, manutenção avançada e roadmap:
- **[README_MAINTENANCE_FUTURE.md](README_MAINTENANCE_FUTURE.md)** - Expansões futuras e melhorias do sistema

---

## 🚀 Início Rápido

### Para Coleta de Dados Apenas:
1. Leia **[README_02.md](README_02.md)**
2. Configure credenciais no `.env`
3. Execute scripts de coleta na ordem recomendada

### Para Sistema Completo de Automação:
1. Leia **[README_02.md](README_02.md)** para entender a coleta de dados
2. Leia **[README_01.md](README_01.md)** para configurar automação e Supabase
3. Configure systemd, monitoramento e backup automático

### Para Planejamento de Expansões:
- Consulte **[README_MAINTENANCE_FUTURE.md](README_MAINTENANCE_FUTURE.md)** para funcionalidades futuras

---

## 📋 Arquivos do Projeto

### Documentação:
- `README.md` - Este arquivo (índice principal)
- `README_01.md` - Sistema de automação Supabase
- `README_02.md` - Scripts de coleta Sungrow
- `README_MAINTENANCE_FUTURE.md` - Expansões futuras

### Scripts Python:
- `get_*.py` - Scripts de coleta de dados
- `insert_*.py` - Scripts de inserção independente
- `scheduler.py` - Orquestrador principal
- `db_*.py` - Scripts de manutenção e backup

### Configuração:
- `.env` - Credenciais (não versionar)
- `*.service` / `*.timer` - Arquivos Systemd
- `install.sh` - Script de instalação automatizada

---

## 🔧 Requisitos do Sistema

- **Python**: 3.8 ou superior
- **Banco**: Supabase (local ou cloud)
- **Sistema**: Linux (para automação completa)
- **Credenciais**: Conta válida na plataforma Sungrow

### Dependências Python:
```bash
pip install requests pandas python-dotenv supabase psycopg2-binary httpx[http2]
```

---

## 📞 Suporte

Para dúvidas específicas:

- **Coleta de dados Sungrow**: Consulte [README_02.md](README_02.md)
- **Automação e Supabase**: Consulte [README_01.md](README_01.md)
- **Funcionalidades futuras**: Consulte [README_MAINTENANCE_FUTURE.md](README_MAINTENANCE_FUTURE.md)

---

**Última atualização**: Outubro 2025
**Versão**: 2.1
