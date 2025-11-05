#!/usr/bin/env python3
"""
SCRIPT DE LIMPEZA DO SISTEMA
============================

Este script limpa arquivos desnecessários do sistema, node_modules antigos,
caches e arquivos temporários para liberar espaço em disco.

COMO USAR:
----------
1. Execução básica (modo seguro - apenas mostra o que seria removido):
   python3 cleaning.py

2. Execução com limpeza real:
   python3 cleaning.py --ex

3. Limpeza apenas de node_modules:
   python3 cleaning.py --a-n

4. Limpeza completa (inclui logs e caches do sistema):
   python3 cleaning.py --ex --c

5. Ver ajuda:
   python3 cleaning.py --help

AUTOR: Script criado para otimização do ambiente de desenvolvimento
DATA: 5 de setembro de 2025
"""

import os
import shutil
import argparse
import subprocess
import sys
from pathlib import Path
import time
from datetime import datetime

class LimpadorSistema:
    def __init__(self):
        # Diretório base (Área de trabalho)
        self.base_dir = Path.home()
        
        # Contadores para estatísticas
        self.total_liberado = 0
        self.arquivos_removidos = 0
        self.diretorios_removidos = 0
        
        # Lista de diretórios e arquivos para limpeza
        self.node_modules_dirs = []
        self.temp_files = []
        self.cache_dirs = []
        self.log_files = []
        
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
        
    def _encontrar_node_modules(self):
        """Encontra todos os diretórios node_modules"""
        print("   📦 Procurando node_modules...")
        
        for root, dirs, files in os.walk(self.base_dir):
            if 'node_modules' in dirs:
                node_modules_path = Path(root) / 'node_modules'
                
                # Verifica se tem mais de 30 dias ou se está em projeto inativo
                if self._is_old_or_inactive(node_modules_path):
                    size = self._get_dir_size(node_modules_path)
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
                if file_path.is_file():
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
            for cache_dir in cache_dirs:
                if cache_dir in dirs:
                    cache_path = Path(root) / cache_dir
                    size = self._get_dir_size(cache_path)
                    self.cache_dirs.append({
                        'path': cache_path,
                        'size': size,
                        'tipo': cache_dir
                    })
    
    def _encontrar_logs(self):
        """Encontra arquivos de log antigos"""
        print("   📋 Procurando logs antigos...")
        
        for log_file in self.base_dir.rglob('*.log'):
            if log_file.is_file():
                # Verifica se o log tem mais de 7 dias
                if self._is_old_file(log_file, days=7):
                    size = log_file.stat().st_size
                    self.log_files.append({
                        'path': log_file,
                        'size': size
                    })
    
    def _is_old_or_inactive(self, path, days=30):
        """Verifica se um diretório é antigo ou inativo"""
        try:
            # Verifica a data de modificação mais recente
            mtime = path.stat().st_mtime
            age_days = (time.time() - mtime) / (24 * 3600)
            return age_days > days
        except:
            return False
    
    def _is_old_file(self, file_path, days=7):
        """Verifica se um arquivo é antigo"""
        try:
            mtime = file_path.stat().st_mtime
            age_days = (time.time() - mtime) / (24 * 3600)
            return age_days > days
        except:
            return False
    
    def _get_dir_size(self, path):
        """Calcula o tamanho de um diretório"""
        try:
            total_size = 0
            for dirpath, dirnames, filenames in os.walk(path):
                for filename in filenames:
                    filepath = os.path.join(dirpath, filename)
                    try:
                        total_size += os.path.getsize(filepath)
                    except (OSError, FileNotFoundError):
                        pass
            return total_size
        except:
            return 0
    
    def _format_size(self, size_bytes):
        """Formata tamanho em bytes para formato legível"""
        for unit in ['B', 'KB', 'MB', 'GB']:
            if size_bytes < 1024.0:
                return f"{size_bytes:.1f} {unit}"
            size_bytes /= 1024.0
        return f"{size_bytes:.1f} TB"
    
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
                    size_str = self._format_size(item['size'])
                    print(f"   • {item['path']}")
                    print(f"     Projeto: {item['projeto']} | Tamanho: {size_str}")
                    total_estimado += item['size']
            else:
                # Mostra apenas os 10 maiores
                for item in self.node_modules_dirs[:10]:
                    size_str = self._format_size(item['size'])
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
                    size_str = self._format_size(item['size'])
                    print(f"   • {item['path']} ({size_str})")
            else:
                print(f"   Tamanho total: {self._format_size(temp_size)}")
            total_estimado += temp_size
        
        # Caches
        if self.cache_dirs:
            cache_size = sum(item['size'] for item in self.cache_dirs)
            print(f"\n💾 DIRETÓRIOS DE CACHE: {len(self.cache_dirs)} diretórios")
            if d:
                print("   Lista completa:")
                for item in self.cache_dirs:
                    size_str = self._format_size(item['size'])
                    print(f"   • {item['path']} [{item['tipo']}] ({size_str})")
            else:
                print(f"   Tamanho total: {self._format_size(cache_size)}")
            total_estimado += cache_size
        
        # Logs
        if self.log_files:
            log_size = sum(item['size'] for item in self.log_files)
            print(f"\n📋 LOGS ANTIGOS: {len(self.log_files)} arquivos")
            if d:
                print("   Lista completa:")
                for item in self.log_files:
                    size_str = self._format_size(item['size'])
                    mtime = datetime.fromtimestamp(item['path'].stat().st_mtime)
                    print(f"   • {item['path']} ({size_str}) - {mtime.strftime('%d/%m/%Y')}")
            else:
                print(f"   Tamanho total: {self._format_size(log_size)}")
            total_estimado += log_size
        
        print(f"\n💾 ESPAÇO TOTAL A SER LIBERADO: {self._format_size(total_estimado)}")
        print("="*60)
    
    def ex_limpeza(self, only_nodes=False, full=False):
        """Executa a limpeza dos arquivos"""
        print("\n🧹 INICIANDO LIMPEZA...")
        inicio = time.time()
        
        try:
            # Limpa node_modules
            if only_nodes:
            
                self._limpar_node_modules()
            
            if not only_nodes:
                # Limpa arquivos temporários
                self._limpar_temp_files()
                
                # Limpa caches
                self._limpar_caches()
                
                # Se limpeza completa, limpa logs também
                if full:
                    self._limpar_logs()
            
            # Limpa lixeira do sistema (se possível)
            self._limpar_lixeira()
            
        except KeyboardInterrupt:
            print("\n⚠️  Limpeza interrompida pelo usuário!")
            return False
        
        fim = time.time()
        tempo_total = fim - inicio
        
        print(f"\n✅ LIMPEZA CONCLUÍDA!")
        print(f"⏱️  Tempo total: {tempo_total:.1f} segundos")
        print(f"💾 Espaço liberado: {self._format_size(self.total_liberado)}")
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
                print(f"\n📦 Node modules? {len(self.node_modules_dirs)} encontrados ({self._format_size(total_size)})")
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
                print(f"\n🗂️  Arquivos Temporários: {len(self.temp_files)} arquivos ({self._format_size(temp_size)})")
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
                print(f"\n💾 Caches: {len(self.cache_dirs)} diretórios ({self._format_size(cache_size)})")
                resposta = input("   Limpar? (s/n): ").strip().lower()
                if resposta in ['s', 'sim', 'y', 'yes']:
                    self._limpar_caches()
                    actions_taken.append({
                        'type': 'cache',
                        'size': cache_size,
                        'count': len(self.cache_dirs)
                    })
        
            # Logs
            if self.log_files:
                log_size = sum(item['size'] for item in self.log_files)
                print(f"\n📋 Logs: {len(self.log_files)} arquivos ({self._format_size(log_size)})")
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


def main():
    # Configuração dos argumentos da linha de comando
    parser = argparse.ArgumentParser(
        description="Script de limpeza inteligente do sistema para desenvolvedores",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
EXEMPLOS DE USO - LIMPEZA TRADICIONAL:
   cleaning.py                     # Modo preview (não remove nada)
   cleaning.py --details                 # Mostra lista detalhada dos arquivos
   cleaning.py --run                # Executa limpeza real
   cleaning.py --only-nodes               # Remove apenas node_modules
   cleaning.py --interactive       # Modo interativo (escolha o que limpar)
   cleaning.py --run --full            # Limpeza completa

EXEMPLOS DE USO - ARQUIVAMENTO INTELIGENTE:
   cleaning.py --move --interactive              # Move arquivos antigos (interativo)
   cleaning.py --move --policy reports           # Move relatórios antigos (15 dias)
   cleaning.py --move --policy backups           # Move backups antigos (mantém 2)
   cleaning.py --move --synergic                 # Aplica todas as políticas

EXEMPLOS DE USO - LIXÃO:
   cleaning.py --trash /path/to/dir --tag OLD-REPORTS    # Compacta e move para lixão
   cleaning.py --list-trash                              # Lista conteúdo do lixão
   cleaning.py --search-trash "report_20241020"          # Busca no lixão

EXEMPLOS DE USO - RESTAURAÇÃO:
   cleaning.py --list-archives                           # Lista archives disponíveis
   cleaning.py --restore moving-20241103 --item report.html  # Restaura arquivo específico
   cleaning.py --restore-trash "[OLD-REPORTS]_file.tar.gz"   # Restaura do lixão
   cleaning.py --search "report" --in-archives           # Busca nos archives

INFORMAÇÕES:
   cleaning.py --storage-info                            # Mostra info do storage
        """
    )
    
    parser.add_argument(
        '--run',
        action='store_true',
        help='Executa a limpeza real (sem esta opção apenas mostra o que seria removido)'
    )
    
    parser.add_argument(
        '--only-nodes',
        action='store_true',
        help='Remove apenas diretórios node_modules'
    )
    
    parser.add_argument(
        '--full',
        action='store_true',
        help='Executa limpeza completa (inclui logs do sistema)'
    )
    
    parser.add_argument(
        '--details',
        action='store_true',
        help='Mostra lista detalhada de todos os arquivos que serão removidos'
    )
    
    parser.add_argument(
        '--interactive',
        action='store_true',
        help='Modo interativo - escolha o que limpar item por item'
    )

    parser.add_argument(
        '--move',
        action='store_true',
        help='Ativa modo de arquivamento (move arquivos antigos para storage)'
    )
    
    parser.add_argument(
        '--policy',
        type=str,
        choices=['reports', 'backups', 'logs', 'node_modules'],
        help='Aplica política específica de arquivamento'
    )
    
    parser.add_argument(
        '--synergic',
        action='store_true',
        help='Aplica todas as políticas de arquivamento automaticamente'
    )
    
    # Lixão
    parser.add_argument(
        '--trash',
        type=str,
        help='Move diretório/arquivo para o lixão compactado'
    )
    
    parser.add_argument(
        '--tag',
        type=str,
        default='MOVED',
        help='Tag para o item no lixão (ex: OLD-REPORTS, ARCHIVED, etc)'
    )
    
    parser.add_argument(
        '--list-trash',
        action='store_true',
        help='Lista conteúdo do lixão'
    )
    
    parser.add_argument(
        '--search-trash',
        type=str,
        help='Busca arquivo no lixão'
    )
    
    # Restauração
    parser.add_argument(
        '--restore',
        type=str,
        help='Restaura archive (operation_id)'
    )
    
    parser.add_argument(
        '--restore-trash',
        type=str,
        help='Restaura arquivo do lixão'
    )
    
    parser.add_argument(
        '--item',
        type=str,
        help='Item específico para restaurar'
    )
    
    parser.add_argument(
        '--to',
        type=str,
        help='Destino para restauração (padrão: recovery/)'
    )
    
    parser.add_argument(
        '--list-archives',
        action='store_true',
        help='Lista archives disponíveis'
    )
    
    parser.add_argument(
        '--search',
        type=str,
        help='Termo de busca'
    )
    
    parser.add_argument(
        '--in-archives',
        action='store_true',
        help='Busca nos archives'
    )
    
    # Informações
    parser.add_argument(
        '--storage-info',
        action='store_true',
        help='Mostra informações do storage'
    )
    
    args = parser.parse_args()
    

# Comandos para gerenciamento de diretorios (move/trash/restore [...])
    
    # Importa managers apenas se necessário
    storage_manager = None
    archive_manager = None
    trash_manager = None
    restore_manager = None
    
    if any([args.move, args.trash, args.list_trash, args.search_trash, 
            args.restore, args.restore_trash, args.list_archives, 
            args.storage_info, args.in_archives]):
        try:
            sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
            from modules.storage_manager import StorageManager
            from modules.archive_manager import ArchiveManager
            from modules.trash_manager import TrashManager
            from modules.restore_manager import RestoreManager
            
            storage_manager = StorageManager()
            storage_manager.initialize_storage(verbose=False)
            archive_manager = ArchiveManager(storage_manager)
            trash_manager = TrashManager(storage_manager)
            restore_manager = RestoreManager(storage_manager)
        except Exception as e:
            print(f"❌ Erro ao carregar sistema de storage: {e}")
            return
    
    # Comandos de informação
    if args.storage_info:
        storage_manager.show_storage_info()
        return
    
    if args.list_archives:
        restore_manager.list_archives()
        return
    
    if args.list_trash:
        trash_manager.list_trash_contents()
        return
    
    # Comandos de busca
    if args.search:
        if args.in_archives:
            restore_manager.search_in_archives(args.search)
        else:
            restore_manager.search_in_trash(args.search)
        return
    
    if args.search_trash:
        trash_manager.search_in_trash(args.search_trash)
        return
    
    # Comandos de restauração
    if args.restore:
        success = restore_manager.restore_from_archive(
            args.restore, 
            item_name=args.item,
            destination=args.to
        )
        return
    
    if args.restore_trash:
        if args.item:
            success = restore_manager.extract_item_from_trash(
                args.restore_trash,
                args.item,
                destination=args.to
            )
        else:
            success = restore_manager.restore_from_trash(
                args.restore_trash,
                destination=args.to
            )
        return
    
    # Comando de lixão
    if args.trash:
        trash_path = Path(args.trash).expanduser()
        if not trash_path.exists():
            print(f"❌ Path não encontrado: {trash_path}")
            return
        
        trash_manager.add_items([trash_path], tag=args.tag)
        trash_manager.show_trash_preview()
        trash_manager.compress_and_move()
        return
    
    # Comando de movimentação (arquivamento)
    if args.move:
        if args.synergic:
            # Modo sinérgico: aplica todas as políticas
            print("\n🔄 MODO SINÉRGICO - Aplicando todas as políticas")
            print("=" * 60)
            
            all_files = []
            all_files.extend(archive_manager.scan_old_reports(keep_days=15))
            all_files.extend(archive_manager.scan_old_backups(keep_count=2))
            
            if all_files:
                archive_manager.prepare_move_operation(all_files, operation_name="synergic")
                archive_manager.show_move_preview()
                archive_manager.execute_move()
            else:
                print("   ✅ Nenhum arquivo para mover")
            return
            
        elif args.policy:
            # Aplica política específica
            print(f"\n📋 Aplicando política: {args.policy}")
            print("=" * 60)
            
            files = archive_manager.scan_by_policy(args.policy)
            
            if files:
                archive_manager.prepare_move_operation(files, operation_name=args.policy)
                archive_manager.show_move_preview()
                archive_manager.execute_move()
            else:
                print("   ✅ Nenhum arquivo para mover")
            return
            
        elif args.interactive:
            # Modo interativo
            print("\n🎯 MODO INTERATIVO - ARQUIVAMENTO")
            print("=" * 60)
            
            print("\n📋 Escolha quais categorias escanear:")
            print("   [1] Relatórios (mantém últimos 15 dias)")
            print("   [2] Backups (mantém 2 mais recentes)")
            print("   [3] Ambos")
            print("   [0] Cancelar")
            
            escolha = input("\n   Digite sua escolha: ").strip()
            
            files = []
            if escolha in ['1', '3']:
                files.extend(archive_manager.scan_old_reports(keep_days=15))
            if escolha in ['2', '3']:
                files.extend(archive_manager.scan_old_backups(keep_count=2))
            
            if files:
                archive_manager.prepare_move_operation(files)
                archive_manager.show_move_preview()
                archive_manager.execute_move()
            else:
                print("   ✅ Nenhum arquivo para mover")
            return
        else:
            print("❌ Use --interactive, --policy ou --synergic com --move")
            return
    
    # === MODO LIMPEZA TRADICIONAL ===
    
    # Banner do script
    print("🧹" + "="*58 + "🧹")
    print("   SCRIPT DE LIMPEZA DO SISTEMA - AMBIENTE DE DEV")
    print("🧹" + "="*58 + "🧹")
    print(f"📅 Executado em: {datetime.now().strftime('%d/%m/%Y às %H:%M:%S')}")
  
    # Cria instância do limpador
    limpador = LimpadorSistema()

    # Escaneia o sistema
    limpador.escanear_sistema()
    
    # Mostra relatório
    limpador.mostrar_relatorio(d=args.details)
    
    # MODO INTERATIVO
    if args.interactive:
        print(f"\n🎯 MODO INTERATIVO ATIVADO!")
        inicio = time.time()
        
        sucesso = limpador.limpeza_interativa()
        
        fim = time.time()
        tempo_total = fim - inicio
        
        print(f"\n✅ LIMPEZA INTERATIVA CONCLUÍDA!")
        print(f"⏱️  Tempo total: {tempo_total:.1f} segundos")
        print(f"💾 Espaço liberado: {limpador._format_size(limpador.total_liberado)}")
        print(f"📁 Diretórios removidos: {limpador.diretorios_removidos}")
        print(f"📄 Arquivos removidos: {limpador.arquivos_removidos}")
        return
    
    # MODO AUTOMÁTICO (original)
    # Se não for para ex, apenas mostra o preview
    if not args.run:
        print(f"\n⚠️  MODO PREVIEW ATIVO!")
        print("   Para ex a limpeza real, use: --run")
        print("   Exemplo: python3 cleaning.py --run")
        print("   Ou use: --interactive para escolher o que limpar")
        return
    
    # Confirma antes de ex
    print(f"\n⚠️  ATENÇÃO: Esta operação é IRREVERSÍVEL!")
    resposta = input("🤔 Tem certeza que deseja continuar? (sim/não): ")
    
    if resposta.lower() not in ['sim', 's', 'yes', 'y']:
        print("❌ Operação cancelada pelo usuário.")
        return
    
    # Executa a limpeza
    sucesso = limpador.ex_limpeza(
        only_nodes=args.only_nodes,
        full=args.full,
    )
    
    if sucesso:
        print("\n🎉 Script executado com sucesso!")
        print("💡 Dica: Execute este script semanalmente para manter o sistema otimizado")
    else:
        print("\n❌ Script interrompido ou falhou!")


if __name__ == "__main__":
    main()
