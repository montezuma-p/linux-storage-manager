# 🗺️ ROADMAP:

<div align="center">

<img src="https://media1.giphy.com/media/v1.Y2lkPTc5MGI3NjExMmtpYTcwMDE5ZmpqMnhxNWczMzl5bHU5MHl2bnZyN3dteDcxNHkxdSZlcD12MV9pbnRlcm5hbF9naWZfYnlfaWQmY3Q9Zw/BpGWitbFZflfSUYuZ9/giphy.gif" width="300" alt="future planning"/>

### 📍 Onde estamos e para onde vamos

</div>

---

## 🎯 Situação Atual

Atualmente o projeto está **funcional e sendo usado em produção pessoal**, mas com algumas características que precisam ser melhoradas para torná-lo público e mais acessível:

- ✅ Sistema funciona perfeitamente no ambiente atual
- ⚠️ Caminhos hardcoded no código (específicos do meu setup)
- ⚠️ Configuração requer edição direta dos arquivos `.py`
- ⚠️ Instalação manual necessária

---

## 🚀 Objetivos:

### 1. 📝 Sistema de Configuração Externo

**Prioridade:** 🔴 Alta  
**Status:** 📋 Planejado

Mover todos os caminhos hardcoded para um arquivo de configuração:

```yaml
# cleaning.config.yaml (exemplo)
storage:
  path: "/mnt/storage"
  
paths:
  reports: "~/.bin/data/scripts-data/reports"
  backups: "~/.bin/data/backups/archives"
  home: "~/"

policies:
  reports:
    keep_days: 15
  backups:
    keep_count: 2
  logs:
    keep_days: 7
  node_modules:
    keep_days: 30

compression:
  level: 9
  format: "tar.gz"
```

**Benefícios:**
- ✅ Usuários podem configurar sem mexer no código
- ✅ Múltiplos perfis de configuração (dev, prod, test)
- ✅ Validação automática de configurações
- ✅ Geração de config padrão no primeiro uso

---

### 2. 🐳 Docker Image

**Prioridade:** 🟡 Média  
**Status:** 📋 Planejado

Criar uma imagem Docker para facilitar deployment e uso:

```dockerfile
# Exemplo de uso futuro
docker run -v /seu/storage:/storage \
           -v /seu/home:/data \
           cleaning-system --interactive
```

**Benefícios:**
- ✅ Instalação com um comando
- ✅ Ambiente isolado e reproduzível
- ✅ Não depende de configuração do sistema host
- ✅ Fácil atualização (docker pull)

**Desafios:**
- 🤔 Acesso aos arquivos do host (volumes)
- 🤔 Permissões de arquivos
- 🤔 Performance com grandes quantidades de arquivos

---

### 3. 📦 Publicação no PyPI

**Prioridade:** 🟢 Alta  
**Status:** 📋 Planejado

Disponibilizar o pacote no PyPI para instalação via pip:

```bash
# Instalação futura
pip install cleaning-system

# Uso
cleaning --interactive
cleaning --storage-info
```

**Estrutura do Pacote:**
```
cleaning-system/
├── setup.py
├── pyproject.toml
├── README.md
├── LICENSE
├── cleaning/
│   ├── __init__.py
│   ├── cli.py
│   ├── config.py
│   └── modules/
│       ├── storage_manager.py
│       ├── archive_manager.py
│       ├── trash_manager.py
│       └── restore_manager.py
└── tests/
```

**Benefícios:**
- ✅ Instalação global: `pip install cleaning-system`
- ✅ Versionamento semântico
- ✅ Atualizações automáticas: `pip install --upgrade cleaning-system`
- ✅ Maior alcance e visibilidade


---

## 🤝 Como Contribuir com o Roadmap

Gostou de alguma ideia? Tem sugestões? Quer ajudar a implementar?

1. 🗣️ **Discussões:** Abra uma issue para discutir novas ideias
2. 🎯 **Vote:** Reaja com 👍 nas features que você mais quer
3. 💻 **Implemente:** Escolha um item e mande um PR
4. 📝 **Documente:** Ajude a melhorar a documentação

---

## 📊 Priorização

As prioridades podem mudar baseado em:
- 👥 Feedback da comunidade
- 🐛 Bugs críticos descobertos
- 💡 Novas necessidades identificadas
- ⏰ Tempo disponível para desenvolvimento

---

<div align="center">

<img src="https://media3.giphy.com/media/v1.Y2lkPTc5MGI3NjExMzdkaWV5eTJ4emltdXdzMzBudHA3ZThhNW43NjZtNHQzc3l3a3B5aiZlcD12MV9pbnRlcm5hbF9naWZfYnlfaWQmY3Q9Zw/YQitE4YNQNahy/giphy.gif" width="550" alt="building"/>

### 🚀 **Vamos construir isso juntos!** 🚀

_Este roadmap é vivo e será atualizado conforme o projeto evolui_

**Última atualização:** 5 de novembro de 2025

</div>
