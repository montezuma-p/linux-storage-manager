<div align="center">

# 🧹 Sistema de Limpeza Inteligente 🧹

<img src="https://media1.giphy.com/media/v1.Y2lkPTc5MGI3NjExeDhzYjBzMXg0ZHh5YWdyZWEybnBycTNqcGc2dmIzcjhpajFhenJ1ZSZlcD12MV9pbnRlcm5hbF9naWZfYnlfaWQmY3Q9Zw/Qvpxb0bju1rEp9Nipy/giphy.gif" width="400" alt="rick and morty cleaning"/>

### 🚀 Libere espaço, organize arquivos e mantenha seu sistema limpo como nunca

[![Python](https://img.shields.io/badge/Python-3776AB?style=for-the-badge&logo=python&logoColor=white)](https://www.python.org/)
[![Linux](https://img.shields.io/badge/Linux-FCC624?style=for-the-badge&logo=linux&logoColor=black)](https://www.linux.org/)
[![License](https://img.shields.io/badge/License-MIT-green.svg?style=for-the-badge)](LICENSE)

</div>

---

## 📖 Índice

- [🤔 O que é isso?](#-o-que-é-isso)
- [✨ Funcionalidades](#-funcionalidades)
- [🏗️ Arquitetura](#️-arquitetura)
- [📦 Instalação](#-instalação)
- [🎯 Como Usar](#-como-usar)
  - [Modo Limpeza Tradicional](#modo-limpeza-tradicional)
  - [Modo Arquivamento Inteligente](#modo-arquivamento-inteligente)
  - [Lixão Compactado](#lixão-compactado)
  - [Sistema de Restauração](#sistema-de-restauração)
- [⚙️ Estrutura do Storage](#️-estrutura-do-storage)
- [🎨 Exemplos de Uso](#-exemplos-de-uso)
- [🔧 Configuração](#-configuração)
- [🤝 Contribuindo](#-contribuindo)
- [📜 Licença](#-licença)

---

## 🤔 O que é isso?

Sabe aquele momento que você olha pro seu disco e tá **92% cheio** de `node_modules`, caches e arquivos temporários que você nem lembra que existem? **Pois é.**

Este é um sistema completo de gerenciamento de arquivos para ambientes de desenvolvimento Linux. Ele não só **limpa** seu sistema, mas também:

- 🗄️ **Arquiva** arquivos antigos de forma inteligente
- 🗑️ **Move** para um "lixão" compactado (com tags bonitinhas)
- 🔄 **Restaura** tudo quando você precisar
- 📊 **Organiza** com políticas de retenção automatizadas
- 💾 **Economiza espaço** com compressão máxima

<div align="center">
<img src="https://media3.giphy.com/media/v1.Y2lkPTc5MGI3NjExOWJjZ2hvcnlvOTh2NzRlajZsMnlodjl6OXFsbWU4cWhhbDVpYTd4ZyZlcD12MV9pbnRlcm5hbF9naWZfYnlfaWQmY3Q9Zw/rBA9YKPPA4v7DXPdvg/giphy.gif" width="350" alt="explaning"/>
</div>

---

## ✨ Funcionalidades

### 🧹 Limpeza Tradicional

- 📦 **Node Modules**: Detecta e remove `node_modules` antigos ou inativos (>30 dias)
- 🗂️ **Arquivos Temporários**: `.tmp`, `.temp`, `.bak`, `.swp`, `~`, etc.
- 💾 **Caches**: `.next`, `.nuxt`, `dist`, `build`, `.cache`, `__pycache__`, `.pytest_cache`
- 📋 **Logs Antigos**: Arquivos `.log` com mais de 7 dias
- 🗑️ **Lixeira do Sistema**: Limpa `~/.local/share/Trash`

### 🗄️ Arquivamento Inteligente

O sistema implementa **políticas de retenção automáticas** que movem arquivos antigos para um storage dedicado:

| Categoria | Política | Descrição |
|-----------|----------|-----------|
| 📊 **Reports** | 15 dias | Mantém apenas 1 relatório por dia dos últimos 15 dias |
| 💾 **Backups** | Top 2 | Mantém apenas os 2 backups mais recentes por categoria |
| 📋 **Logs** | 7 dias | Move logs com mais de 7 dias |
| 📦 **Node Modules** | 30 dias | Arquiva projetos inativos há mais de 30 dias |

**Diferencial:** Usa **metadados do sistema de arquivos** (mtime) em vez de nomenclatura, garantindo confiabilidade independente de como você nomeou seus arquivos.

### 🗑️ Lixão Compactado

Move arquivos para um "lixão" no storage com:
- ✅ **Compressão máxima** (nível 9)
- 🏷️ **Tags organizadas**: `[OLD-REPORTS]`, `[ARCHIVED]`, `[NODE-MODULES]`, etc.
- 📊 **Metadados completos** de cada operação
- 🔍 **Busca rápida** sem precisar descompactar tudo

### 🔄 Sistema de Restauração

- 📋 Lista todos os archives e itens do lixão
- 🔍 Busca inteligente por arquivo específico
- 📂 Extração seletiva (não precisa restaurar tudo)
- 🎯 Destino personalizável

---

## 🏗️ Arquitetura

```
cleaning/
│
├── cleaning.py              # Script principal
│
└── modules/
    ├── __init__.py
    ├── storage_manager.py   # Gerencia estrutura do storage
    ├── archive_manager.py   # Políticas de arquivamento
    ├── trash_manager.py     # Lixão compactado
    └── restore_manager.py   # Sistema de restauração
```

### 📁 Estrutura do Storage

O sistema cria e gerencia a seguinte estrutura em um disco de armazenamento:

```
/mnt/storage/                    # ← Pode ser configurado
│
├── archives/                    # Arquivos movidos com metadados
│   ├── moving-20241103-143022/
│   │   ├── reports/
│   │   └── backups/
│   └── index_archives.json      # Índice de todas operações
│
├── trash/                       # Lixão compactado
│   ├── compressed/              # .tar.gz files
│   │   └── [TAG]_nome_timestamp.tar.gz
│   ├── metadata/                # Metadados das compressões
│   └── manifest_trash.json      # Manifest do lixão
│
├── recovery/                    # Área temporária de restauração
│
└── .storage-config/             # Configurações e políticas
    ├── config.json
    ├── policies.json
    └── usage.json
```

---

## 📦 Instalação

### Pré-requisitos

- 🐍 Python 3.6+
- 🐧 Sistema Linux
- 💾 Espaço em disco para o storage (recomendado: disco dedicado)

### Instalação Rápida

```bash
# Clone o repositório
git clone https://github.com/montezuma-p/linux-storage-manager
cd linux-storage-manager

# Torna o script executável
chmod +x cleaning.py

# (Opcional) Cria link simbólico para usar globalmente
sudo ln -s $(pwd)/cleaning.py /usr/local/bin/cleaning
```

### Configuração Inicial do Storage

```bash
# O sistema cria a estrutura automaticamente na primeira execução
# Por padrão usa /mnt/storage, mas pode ser configurado

# Teste a inicialização
python3 cleaning.py --storage-info
```

---

## 🎯 Como Usar

### Modo Limpeza Tradicional

#### 1️⃣ Preview (Modo Seguro)

Mostra o que **seria** removido sem remover nada:

```bash
python3 cleaning.py
```

#### 2️⃣ Preview Detalhado

Mostra **todos** os arquivos (não só os 10 primeiros):

```bash
python3 cleaning.py --details
```

#### 3️⃣ Modo Interativo ⭐

Escolhe **item por item** o que limpar:

```bash
python3 cleaning.py --interactive
```

Você verá algo assim:

```
🎯 MODO INTERATIVO - Escolha o que deseja limpar:
============================================================

📦 Node modules? 15 encontrados (2.3 GB)
   Limpar? (s/n): s

🗂️  Arquivos Temporários: 234 arquivos (45.2 MB)
   Limpar? (s/n): s

💾 Caches: 8 diretórios (567.8 MB)
   Limpar? (s/n): n

...
```

#### 4️⃣ Execução Automática

Remove **tudo** de uma vez (cuidado! ⚠️):

```bash
python3 cleaning.py --run
```

#### 5️⃣ Limpeza de Node Modules Apenas

```bash
python3 cleaning.py --only-nodes
```

#### 6️⃣ Limpeza Completa (inclui logs do sistema)

```bash
python3 cleaning.py --run --full
```

---

### Modo Arquivamento Inteligente

#### 📊 Arquivamento Interativo

```bash
python3 cleaning.py --move --interactive
```

Você escolhe quais categorias escanear:
```
📋 Escolha quais categorias escanear:
   [1] Relatórios (mantém últimos 15 dias)
   [2] Backups (mantém 2 mais recentes)
   [3] Ambos
   [0] Cancelar
```

#### 📋 Política Específica

```bash
# Move apenas relatórios antigos
python3 cleaning.py --move --policy reports

# Move apenas backups antigos
python3 cleaning.py --move --policy backups
```

#### 🔄 Modo Sinérgico (Aplica Todas as Políticas)

```bash
python3 cleaning.py --move --synergic
```

---

### Lixão Compactado

#### 🗑️ Enviar para o Lixão

```bash
# Sintaxe básica
python3 cleaning.py --trash /caminho/do/diretorio --tag NOME-DA-TAG

# Exemplos
python3 cleaning.py --trash ~/old-project --tag OLD-PROJECTS
python3 cleaning.py --trash ~/logs/antigos --tag OLD-LOGS
```

**Tags disponíveis:**
- `OLD-REPORTS`
- `OLD-BACKUPS`
- `ARCHIVED`
- `NODE-MODULES`
- `MOVED`
- `LOGS`
- `TEMP`
- `CUSTOM`

#### 📋 Listar Conteúdo do Lixão

```bash
python3 cleaning.py --list-trash
```

Saída:
```
🗑️  LIXÃO (12 arquivos compactados)
============================================================
 1. [OLD-REPORTS]_reports_20241103.tar.gz
    📅 2024-11-03 14:30 | 📊 145 itens | 💾 23.4 MB | 🗜️  87.3%
 2. [NODE-MODULES]_old-project_20241102.tar.gz
    📅 2024-11-02 10:15 | 📊 3421 itens | 💾 89.2 MB | 🗜️  94.1%
...
```

#### 🔍 Buscar no Lixão

```bash
python3 cleaning.py --search-trash "report_20241020"
```

---

### Sistema de Restauração

#### 📦 Listar Archives Disponíveis

```bash
python3 cleaning.py --list-archives
```

#### 🔄 Restaurar Archive Completo

```bash
python3 cleaning.py --restore moving-20241103-143022
```

#### 📄 Restaurar Arquivo Específico do Archive

```bash
python3 cleaning.py --restore moving-20241103-143022 --item report.html
```

#### 🗑️ Restaurar do Lixão

```bash
# Restaura tudo
python3 cleaning.py --restore-trash "[OLD-REPORTS]_file.tar.gz"

# Restaura item específico
python3 cleaning.py --restore-trash "[OLD-REPORTS]_file.tar.gz" --item report.html
```

#### 🔍 Buscar nos Archives

```bash
python3 cleaning.py --search "relatorio" --in-archives
```

#### 🎯 Especificar Destino de Restauração

```bash
python3 cleaning.py --restore moving-20241103 --to /home/user/restored/
```

---

## ⚙️ Estrutura do Storage

### 📊 Visualizar Informações do Storage

```bash
python3 cleaning.py --storage-info
```

Mostra:
- 💾 Espaço usado/disponível
- 📦 Total de archives
- 🗑️ Total no lixão
- 📈 Estatísticas de uso
- ⚙️ Configurações ativas

### 🔧 Políticas de Retenção

As políticas estão definidas no código (`modules/storage_manager.py`):

```python
self.default_policies = {
    "reports": {
        "keep_days": 15,
        "description": "Relatórios - mantém últimos 15 dias no sistema principal"
    },
    "backups": {
        "keep_count": 2,
        "description": "Backups - mantém apenas os 2 mais recentes de cada categoria"
    },
    "logs": {
        "keep_days": 7,
        "description": "Logs do sistema - mantém últimos 7 dias"
    },
    "node_modules": {
        "keep_days": 30,
        "description": "Node modules - move projetos inativos há mais de 30 dias"
    },
    "caches": {
        "action": "delete",
        "description": "Caches - deleta sempre (não arquiva)"
    }
}
```

---

## 🎨 Exemplos de Uso

### 🔥 Workflow Completo Semanal

```bash
# 1. Preview do que será limpo
python3 cleaning.py --details

# 2. Limpa interativamente (você escolhe)
python3 cleaning.py --interactive

# 3. Arquiva relatórios e backups antigos
python3 cleaning.py --move --synergic

# 4. Verifica o storage
python3 cleaning.py --storage-info
```

### 🚀 Limpeza de Emergência (Disco Cheio!)

```bash
# Remove node_modules imediatamente
python3 cleaning.py --run --only-nodes

# Depois faz limpeza completa
python3 cleaning.py --run --full
```

### 🗂️ Organização de Projeto Antigo

```bash
# Move projeto velho pro lixão
python3 cleaning.py --trash ~/Projetos/projeto-antigo --tag OLD-PROJECTS

# Se precisar depois, restaura
python3 cleaning.py --list-trash
python3 cleaning.py --restore-trash "[OLD-PROJECTS]_projeto-antigo_20241103.tar.gz"
```

### 🔍 Procurar Aquele Arquivo que Você Arquivou

```bash
# Busca nos archives
python3 cleaning.py --search "relatorio_importante" --in-archives

# Restaura quando encontrar
python3 cleaning.py --restore archive-20241020 --item relatorio_importante.html
```

---

## 🔧 Configuração

### Mudar Caminho do Storage

Edite `storage_manager.py`:

```python
def __init__(self, storage_path: str = "/seu/caminho/personalizado"):
    self.storage_path = Path(storage_path)
    # ...
```

### Ajustar Políticas de Retenção

Edite `modules/storage_manager.py`:

```python
# Exemplo: Manter relatórios por 30 dias em vez de 15
self.default_policies = {
    "reports": {
        "keep_days": 30,  # ← Mudou aqui
        "description": "Relatórios - mantém últimos 30 dias no sistema principal"
    },
    # ... resto das políticas
}
```

### Nível de Compressão

Para ajustar o nível de compressão (0-9), edite `trash_manager.py`:

```python
# Na função _compress_path()
tar.add(path, arcname=path.name, compresslevel=9)  # ← Padrão: 9 (máxima)
```

**Trade-off:**
- `9` = Máxima compressão, mais lento
- `6` = Balanceado
- `1` = Rápido, menos compressão

---

## 🤝 Contribuindo

Contribuições são super bem-vindas! 🎉

1. Fork o projeto
2. Crie uma branch para sua feature (`git checkout -b feature/MinhaFeature`)
3. Commit suas mudanças (`git commit -m 'Adiciona MinhaFeature'`)
4. Push para a branch (`git push origin feature/MinhaFeature`)
5. Abra um Pull Request

### 💡 Ideias para Contribuir

- 🔌 Adicionar mais políticas de retenção
- 📊 Dashboard web para visualizar estatísticas
- 🔔 Sistema de notificações quando disco está cheio
- 🗜️ Suporte para outros formatos de compressão (zstd, xz)
- 🐳 Dockerfile para rodar em container
- 📱 Integração com Telegram/Discord para alertas

---

## 📜 Licença

Este projeto está sob a licença MIT. Veja o arquivo [LICENSE](LICENSE) para mais detalhes.

---

<div align="center">

## 🙏 Agradecimentos

Feito com ☕ e 💻 por desenvolvedores cansados de disco cheio

<img src="https://media.giphy.com/media/v1.Y2lkPTc5MGI3NjExeXZpZGNjeG9kOG92amhqZnFkaDRqcGtqcmI2YThyM2Jidmw1cTY3biZlcD12MV9pbnRlcm5hbF9naWZfYnlfaWQmY3Q9Zw/hvRJCLFzcasrR4ia7z/giphy.gif" width="100"/>

### ⭐ Se este projeto te ajudou, deixa uma estrela! ⭐

</div>
