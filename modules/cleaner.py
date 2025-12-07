#!/usr/bin/env python3
"""
CLEANER - Sistema de Limpeza
=============================

Gerencia a limpeza de arquivos desnecessários do sistema de desenvolvimento.

MÓDULO PRINCIPAL:
----------------
Este módulo contém a classe LimpadorSistema, responsável por:
- Escanear o sistema em busca de arquivos/diretórios para limpeza
- Proteger automaticamente diretórios críticos
- Executar limpeza com diferentes modos (interativo, automático, Python-only)

CARACTERÍSTICAS:
---------------
- Limpeza de node_modules antigos (>30 dias de inatividade)
- Remoção de arquivos temporários (.tmp, .bak, .swp, etc)
- Limpeza de caches (.next, .nuxt, dist, build, __pycache__)
- Modo especializado para cache Python (--python-only)
- Proteção automática de diretórios críticos do sistema

AUTOR: Pedro Montezuma
DATA: 6 de dezembro de 2025
"""

import os
import shutil
import sys
from pathlib import Path
import time
from datetime import datetime

# Adiciona o diretório pai ao path para importar utils
sys.path.insert(0, str(Path(__file__).parent.parent))
from utils.file_utils import format_size, get_dir_size, is_old_file, is_old_or_inactive


class LimpadorSistema:
    """
    Sistema de Limpeza de Arquivos Desnecessários
    ==============================================
    
    Escaneia e remove arquivos/diretórios desnecessários do sistema de desenvolvimento,
    com proteção automática para diretórios críticos.
    
    CARACTERÍSTICAS:
    ---------------
    - Limpeza de node_modules antigos (>30 dias de inatividade)
    - Remoção de arquivos temporários (.tmp, .bak, .swp, etc)
    - Limpeza de caches (.next, .nuxt, dist, build, __pycache__)
    - Modo especializado para cache Python (--python-only)
    - Proteção automática de diretórios críticos do sistema
    
    DIRETÓRIOS PROTEGIDOS:
    ---------------------
    O sistema NUNCA limpará arquivos de:
    - .var (dados Flatpak)
    - .config (configurações de apps)
    - .local/share (dados de apps locais)
    - .vscode / .vscode-server (VS Code)
    - .mozilla (Firefox)
    - .ssh (chaves SSH - CRÍTICO!)
    - .gnupg (chaves GPG - CRÍTICO!)
    
    MODOS DE OPERAÇÃO:
    -----------------
    1. Preview (padrão): Mostra o que seria removido sem deletar
    2. Automático (--run): Executa limpeza após confirmação
    3. Interativo (--interactive): Pergunta item por item
    4. Python-only (--python-only): Limpa apenas cache Python
    
    EXEMPLO:
    -------
    >>> limpador = LimpadorSistema()
    >>> limpador.escanear_sistema()  # ou escanear_python_only()
    >>> limpador.mostrar_relatorio()
    >>> limpador.ex_limpeza(only_nodes=False, full=False)
    
    ATRIBUTOS:
    ---------
    protected_dirs : list
        Lista de diretórios que nunca serão limpos
    node_modules_dirs : list
        Diretórios node_modules encontrados
    python_caches : list
        Caches Python encontrados (__pycache__, .pytest_cache, etc)
    temp_files : list
        Arquivos temporários encontrados
    cache_dirs : list
        Diretórios de cache encontrados
    log_files : list
        Arquivos de log antigos encontrados
    total_liberado : int
        Total de bytes liberados após limpeza
    arquivos_removidos : int
        Contador de arquivos removidos
    diretorios_removidos : int
        Contador de diretórios removidos
    """
    def __init__(self):
        # Diretório base (Área de trabalho)
        self.base_dir = Path.home()
        
        # Diretórios protegidos - NUNCA limpar
        self.protected_dirs = [
            '.var',
            '.config',
            '.local/share',
            '.vscode',
            '.vscode-server',
            '.mozilla',
            '.ssh',
            '.gnupg'
        ]
        
        # Contadores para estatísticas
        self.total_liberado = 0
        self.arquivos_removidos = 0
        self.diretorios_removidos = 0
        
        # Lista de diretórios e arquivos para limpeza
        self.node_modules_dirs = []
        self.temp_files = []
        self.cache_dirs = []
        self.log_files = []
        self.python_caches = []
    
    def _is_protected_path(self, path):
        """
        Verifica se um path está dentro de um diretório protegido.
        
        Esta função é chamada em TODOS os métodos de escaneamento (_encontrar_*)
        para garantir que diretórios críticos nunca sejam incluídos na limpeza,
        mesmo em modo --full.
        
        IMPLEMENTAÇÃO:
        -------------
        Compara o path absoluto com cada item em self.protected_dirs.
        Se o path começa com qualquer diretório protegido, retorna True.
        
        PROTEÇÃO EM os.walk():
        ---------------------
        Nos métodos _encontrar_*(), usamos:
        dirs[:] = [d for d in dirs if not self._is_protected_path(Path(root) / d)]
        
        O uso de dirs[:] (slice assignment) modifica a lista IN-PLACE,
        fazendo com que os.walk() pule esses diretórios completamente.
        
        Parameters
        ----------
        path : Path ou str
            Caminho a ser verificado
        
        Returns
        -------
        bool
            True se o path está protegido, False caso contrário
        
        Examples
        --------
        >>> limpador._is_protected_path(Path.home() / '.config' / 'app.conf')
        True
        >>> limpador._is_protected_path(Path.home() / 'Documents' / 'file.txt')
        False
        """
        path_str = str(path)
        for protected in self.protected_dirs:
            protected_full = str(self.base_dir / protected)
            if path_str.startswith(protected_full):
                return True
        return False
        
    def escanear_sistema(self):
        """Escaneia o sistema procurando arquivos para limpeza"""
        print("🔍 Escaneando sistema...")
        print(f"📁 Diretório base: {self.base_dir}")
        
        # Procura por node_modules
        self._encontrar_node_modules()
        
        # Procura por arquivos temporários
        self._encontrar_arquivos_temp()
        
        # Procura por caches
        self._encontrar_caches()
        
        # Procura por logs antigos
        self._encontrar_logs()
        
        print(f"✅ Escaneamento concluído!")
    
    def escanear_python_only(self):
        """
        Escaneia APENAS cache e arquivos compilados Python.
        
        Diferente de escanear_sistema(), este método foca exclusivamente em:
        
        DIRETÓRIOS DE CACHE:
        -------------------
        - __pycache__ (bytecode compilado)
        - .pytest_cache (cache do pytest)
        - .mypy_cache (cache do mypy type checker)
        - .ruff_cache (cache do linter Ruff)
        - .tox (ambientes virtuais de teste)
        - htmlcov (relatórios de cobertura)
        - .coverage (arquivo de cobertura)
        
        ARQUIVOS COMPILADOS:
        -------------------
        - *.pyc (bytecode compilado)
        - *.pyo (bytecode otimizado - Python 2)
        - *.pyd (extensões Python em Windows)
        
        USO RECOMENDADO:
        ---------------
        Use esta flag quando:
        - Estiver trabalhando ativamente em projetos Python
        - Quiser limpar cache sem afetar node_modules ou outros caches
        - Precisar liberar espaço rapidamente sem riscos
        
        SEGURANÇA:
        ---------
        Todos os diretórios protegidos (self.protected_dirs) são respeitados.
        
        Populates
        ---------
        self.python_caches : list
            Lista de dicionários com 'path', 'size', 'tipo'
        
        See Also
        --------
        escanear_sistema : Escaneamento completo do sistema
        _encontrar_python_caches : Implementação da busca
        """
        print("🔍 Escaneando cache Python...")
        print(f"📁 Diretório base: {self.base_dir}")
        
        self._encontrar_python_caches()
        
        print(f"✅ Escaneamento concluído!")
    
    def _encontrar_python_caches(self):
        """Encontra apenas cache Python"""
        print("   🐍 Procurando cache Python...")
        
        python_cache_dirs = [
            '__pycache__',
            '.pytest_cache',
            '.mypy_cache',
            '.ruff_cache',
            '.tox',
            'htmlcov',
            '.coverage'
        ]
        
        python_cache_files = [
            '**/*.pyc',
            '**/*.pyo',
            '**/*.pyd',
            '**/.coverage',
            '**/.coverage.*'
        ]
        
        # Procura diretórios de cache Python
        for root, dirs, files in os.walk(self.base_dir):
            # Pula diretórios protegidos
            dirs[:] = [d for d in dirs if not self._is_protected_path(Path(root) / d)]
            
            for cache_dir in python_cache_dirs:
                if cache_dir in dirs:
                    cache_path = Path(root) / cache_dir
                    if not self._is_protected_path(cache_path):
                        size = get_dir_size(cache_path)
                        self.python_caches.append({
                            'path': cache_path,
                            'size': size,
                            'tipo': cache_dir
                        })
        
        # Procura arquivos de cache Python
        for pattern in python_cache_files:
            for file_path in self.base_dir.rglob(pattern):
                if file_path.is_file() and not self._is_protected_path(file_path):
                    size = file_path.stat().st_size
                    self.python_caches.append({
                        'path': file_path,
                        'size': size,
                        'tipo': 'arquivo'
                    })
        
    def _encontrar_node_modules(self):
        """Encontra todos os diretórios node_modules"""
        print("   📦 Procurando node_modules...")
        
        for root, dirs, files in os.walk(self.base_dir):
            # PROTEÇÃO CRÍTICA: Remove diretórios protegidos da lista IN-PLACE
            # O uso de dirs[:] (slice assignment) faz com que os.walk()
            # pule esses diretórios completamente, economizando tempo e
            # garantindo que nunca tentaremos limpar .config/, .var/, etc.
            dirs[:] = [d for d in dirs if not self._is_protected_path(Path(root) / d)]
            
            if 'node_modules' in dirs:
                node_modules_path = Path(root) / 'node_modules'
                
                # Verifica se tem mais de 30 dias ou se está em projeto inativo
                if is_old_or_inactive(node_modules_path):
                    size = get_dir_size(node_modules_path)
                    self.node_modules_dirs.append({
                        'path': node_modules_path,
                        'size': size,
                        'projeto': Path(root).name
                    })
    
    def _encontrar_arquivos_temp(self):
        """Encontra arquivos temporários"""
        print("   🗂️  Procurando arquivos temporários...")
        
        temp_patterns = [
            '**/*.tmp',
            '**/*.temp',
            '**/.DS_Store',
            '**/Thumbs.db',
            '**/*.log',
            '**/*.bak',
            '**/*.swp',
            '**/*~'
        ]
        
        for pattern in temp_patterns:
            for file_path in self.base_dir.rglob(pattern):
                if file_path.is_file() and not self._is_protected_path(file_path):
                    size = file_path.stat().st_size
                    self.temp_files.append({
                        'path': file_path,
                        'size': size
                    })
    
    def _encontrar_caches(self):
        """Encontra diretórios de cache"""
        print("   💾 Procurando caches...")
        
        cache_dirs = [
            '.next',
            '.nuxt',
            'dist',
            'build',
            '.cache',
            '__pycache__',
            '.pytest_cache'
        ]
        
        for root, dirs, files in os.walk(self.base_dir):
            # Pula diretórios protegidos
            dirs[:] = [d for d in dirs if not self._is_protected_path(Path(root) / d)]
            
            for cache_dir in cache_dirs:
                if cache_dir in dirs:
                    cache_path = Path(root) / cache_dir
                    if not self._is_protected_path(cache_path):
                        size = get_dir_size(cache_path)
                        self.cache_dirs.append({
                            'path': cache_path,
                            'size': size,
                            'tipo': cache_dir
                        })
    
    def _encontrar_logs(self):
        """Encontra arquivos de log antigos"""
        print("   📋 Procurando logs antigos...")
        
        for log_file in self.base_dir.rglob('*.log'):
            if log_file.is_file() and not self._is_protected_path(log_file):
                # Verifica se o log tem mais de 7 dias
                if is_old_file(log_file, days=7):
                    size = log_file.stat().st_size
                    self.log_files.append({
                        'path': log_file,
                        'size': size
                    })
    
    def mostrar_relatorio(self, d=False):
        """Mostra relatório do que será removido"""
        print("\n" + "="*60)
        print("📊 RELATÓRIO DE LIMPEZA")
        print("="*60)
        
        total_estimado = 0
        
        # Node modules
        if self.node_modules_dirs:
            print(f"\n📦 NODE_MODULES ENCONTRADOS ({len(self.node_modules_dirs)}):")
            if d:
                # Mostra todos os d
                for item in self.node_modules_dirs:
                    size_str = format_size(item['size'])
                    print(f"   • {item['path']}")
                    print(f"     Projeto: {item['projeto']} | Tamanho: {size_str}")
                    total_estimado += item['size']
            else:
                # Mostra apenas os 10 maiores
                for item in self.node_modules_dirs[:10]:
                    size_str = format_size(item['size'])
                    print(f"   • {item['projeto']}: {size_str}")
                    total_estimado += item['size']
                
                if len(self.node_modules_dirs) > 10:
                    print(f"   ... e mais {len(self.node_modules_dirs) - 10} diretórios")
                    # Adiciona o tamanho dos restantes
                    for item in self.node_modules_dirs[10:]:
                        total_estimado += item['size']
        
        # Arquivos temporários
        if self.temp_files:
            temp_size = sum(item['size'] for item in self.temp_files)
            print(f"\n🗂️  ARQUIVOS TEMPORÁRIOS: {len(self.temp_files)} arquivos")
            if d:
                print("   Lista completa:")
                for item in self.temp_files:
                    size_str = format_size(item['size'])
                    print(f"   • {item['path']} ({size_str})")
            else:
                print(f"   Tamanho total: {format_size(temp_size)}")
            total_estimado += temp_size
        
        # Caches
        if self.cache_dirs:
            cache_size = sum(item['size'] for item in self.cache_dirs)
            print(f"\n💾 DIRETÓRIOS DE CACHE: {len(self.cache_dirs)} diretórios")
            if d:
                print("   Lista completa:")
                for item in self.cache_dirs:
                    size_str = format_size(item['size'])
                    print(f"   • {item['path']} [{item['tipo']}] ({size_str})")
            else:
                print(f"   Tamanho total: {format_size(cache_size)}")
            total_estimado += cache_size
        
        # Logs
        if self.log_files:
            log_size = sum(item['size'] for item in self.log_files)
            print(f"\n📋 LOGS ANTIGOS: {len(self.log_files)} arquivos")
            if d:
                print("   Lista completa:")
                for item in self.log_files:
                    size_str = format_size(item['size'])
                    mtime = datetime.fromtimestamp(item['path'].stat().st_mtime)
                    print(f"   • {item['path']} ({size_str}) - {mtime.strftime('%d/%m/%Y')}")
            else:
                print(f"   Tamanho total: {format_size(log_size)}")
            total_estimado += log_size
        
        # Cache Python
        if self.python_caches:
            python_cache_size = sum(item['size'] for item in self.python_caches)
            print(f"\n🐍 CACHE PYTHON: {len(self.python_caches)} itens")
            if d:
                print("   Lista completa:")
                for item in self.python_caches:
                    size_str = format_size(item['size'])
                    print(f"   • {item['path']} [{item['tipo']}] ({size_str})")
            else:
                print(f"   Tamanho total: {format_size(python_cache_size)}")
            total_estimado += python_cache_size
        
        print(f"\n💾 ESPAÇO TOTAL A SER LIBERADO: {format_size(total_estimado)}")
        print("="*60)
    
    def ex_limpeza(self, only_nodes=False, only_python=False, full=False):
        """Executa a limpeza dos arquivos"""
        print("\n🧹 INICIANDO LIMPEZA...")
        inicio = time.time()
        
        try:
            # Limpa apenas cache Python
            if only_python:
                self._limpar_python_caches()
            # Limpa node_modules
            elif only_nodes:
                self._limpar_node_modules()
            # Limpeza padrão
            else:
                # Limpa arquivos temporários
                self._limpar_temp_files()
                
                # Limpa caches
                self._limpar_caches()
                
                # Se limpeza completa, limpa logs também
                if full:
                    self._limpar_logs()
            
            # Limpa lixeira do sistema (se possível) - apenas em modo full
            if full and not only_python and not only_nodes:
                self._limpar_lixeira()
            
        except KeyboardInterrupt:
            print("\n⚠️  Limpeza interrompida pelo usuário!")
            return False
        
        fim = time.time()
        tempo_total = fim - inicio
        
        print(f"\n✅ LIMPEZA CONCLUÍDA!")
        print(f"⏱️  Tempo total: {tempo_total:.1f} segundos")
        print(f"💾 Espaço liberado: {format_size(self.total_liberado)}")
        print(f"📁 Diretórios removidos: {self.diretorios_removidos}")
        print(f"📄 Arquivos removidos: {self.arquivos_removidos}")
        
        return True
    
    def _limpar_node_modules(self):
        """Remove diretórios node_modules"""
        print("   📦 Removendo node_modules...")
        
        for item in self.node_modules_dirs:
            try:
                # Verifica se o diretório ainda existe antes de tentar remover
                if item['path'].exists():
                    print(f"      Removendo: {item['projeto']}/node_modules")
                    shutil.rmtree(item['path'])
                    self.total_liberado += item['size']
                    self.diretorios_removidos += 1
                else:
                    # Silenciosamente pula arquivos que já foram removidos
                    pass
            except Exception as e:
                print(f"      ⚠️  Pulando {item['path']}: arquivo não encontrado")
    
    def _limpar_temp_files(self):
        """Remove arquivos temporários"""
        print("   🗂️  Removendo arquivos temporários...")
        
        for item in self.temp_files:
            try:
                if item['path'].exists():
                    item['path'].unlink()
                    self.total_liberado += item['size']
                    self.arquivos_removidos += 1
            except Exception as e:
                # Silenciosamente pula arquivos que já foram removidos
                pass
    
    def _limpar_caches(self):
        """Remove diretórios de cache"""
        print("   💾 Removendo caches...")
        
        for item in self.cache_dirs:
            try:
                if item['path'].exists():
                    shutil.rmtree(item['path'])
                    self.total_liberado += item['size']
                    self.diretorios_removidos += 1
            except Exception as e:
                # Silenciosamente pula diretórios que já foram removidos
                pass
    
    def _limpar_logs(self):
        """Remove logs antigos"""
        print("   📋 Removendo logs antigos...")
        
        for item in self.log_files:
            try:
                if item['path'].exists():
                    item['path'].unlink()
                    self.total_liberado += item['size']
                    self.arquivos_removidos += 1
            except Exception as e:
                # Silenciosamente pula arquivos que já foram removidos
                pass
    
    def _limpar_python_caches(self):
        """Remove cache Python"""
        print("   🐍 Removendo cache Python...")
        
        for item in self.python_caches:
            try:
                if item['path'].exists():
                    if item['path'].is_dir():
                        shutil.rmtree(item['path'])
                        self.diretorios_removidos += 1
                    else:
                        item['path'].unlink()
                        self.arquivos_removidos += 1
                    self.total_liberado += item['size']
            except Exception as e:
                # Silenciosamente pula itens que já foram removidos
                pass
    
    def _limpar_lixeira(self):
        """Limpa a lixeira do sistema"""
        print("   🗑️  Limpando lixeira do sistema...")
        try:
            # Tenta limpar lixeira no Linux
            trash_dir = Path.home() / ".local/share/Trash"
            if trash_dir.exists():
                for item in trash_dir.rglob("*"):
                    if item.is_file():
                        try:
                            item.unlink()
                            self.arquivos_removidos += 1
                        except:
                            pass
        except Exception as e:
            print(f"      ⚠️  Não foi possível limpar lixeira: {e}")
    
    def limpeza_interativa(self):
        """Modo interativo - permite escolher o que limpar"""
        print("\n🎯 MODO INTERATIVO - Escolha o que deseja limpar:")
        print("="*60)
        
        actions_taken = []

        try:
            # Para remover node modules
            if self.node_modules_dirs:
                total_size = sum(item['size'] for item in self.node_modules_dirs)
                print(f"\n📦 Node modules? {len(self.node_modules_dirs)} encontrados ({format_size(total_size)})")
                resposta = input("   Limpar? (s/n): ").strip().lower()
                if resposta in ['s', 'sim', 'y', 'yes']:
                    self._limpar_node_modules()
                    actions_taken.append({
                        'type': 'node_modules',
                        'size': total_size,
                        'count': len(self.node_modules_dirs)
                    })

            # Para arquivos temp
            if self.temp_files:
                temp_size = sum(item['size'] for item in self.temp_files)
                print(f"\n🗂️  Arquivos Temporários: {len(self.temp_files)} arquivos ({format_size(temp_size)})")
                resposta = input("   Limpar? (s/n): ").strip().lower()
                if resposta in ['s', 'sim', 'y', 'yes']:
                    self._limpar_temp_files()
                    actions_taken.append({
                        'type': 'tmp',
                        'size': temp_size,
                        'count': len(self.temp_files)
                    })
        
            # Caches
            if self.cache_dirs:
                cache_size = sum(item['size'] for item in self.cache_dirs)
                print(f"\n💾 Caches: {len(self.cache_dirs)} diretórios ({format_size(cache_size)})")
                resposta = input("   Limpar? (s/n): ").strip().lower()
                if resposta in ['s', 'sim', 'y', 'yes']:
                    self._limpar_caches()
                    actions_taken.append({
                        'type': 'cache',
                        'size': cache_size,
                        'count': len(self.cache_dirs)
                    })
        
            # Cache Python
            if self.python_caches:
                python_size = sum(item['size'] for item in self.python_caches)
                print(f"\n🐍 Cache Python: {len(self.python_caches)} itens ({format_size(python_size)})")
                resposta = input("   Limpar? (s/n): ").strip().lower()
                if resposta in ['s', 'sim', 'y', 'yes']:
                    self._limpar_python_caches()
                    actions_taken.append({
                        'type': 'python',
                        'size': python_size,
                        'count': len(self.python_caches)
                    })
        
            # Logs
            if self.log_files:
                log_size = sum(item['size'] for item in self.log_files)
                print(f"\n📋 Logs: {len(self.log_files)} arquivos ({format_size(log_size)})")
                resposta = input("   Limpar? (s/n): ").strip().lower()
                if resposta in ['s', 'sim', 'y', 'yes']:
                    self._limpar_logs()
                    actions_taken.append({
                        'type': 'logs',
                        'size': log_size,
                        'count': len(self.log_files)
                    })
        
            # Lixeira
            print(f"\n🗑️  Lixeira do Sistema")
            resposta = input("   Limpar? (s/n): ").strip().lower()
            if resposta in ['s', 'sim', 'y', 'yes']:
                self._limpar_lixeira()
                actions_taken.append({'type': 'trash'})
            
            # Retorna True se alguma ação foi tomada
            return len(actions_taken) > 0
        
        except KeyboardInterrupt:
            print("\n⚠️  Limpeza interativa interrompida pelo usuário!")
            return False
