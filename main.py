#!/usr/bin/env python3
"""
SCRIPT DE LIMPEZA DO SISTEMA
============================

Entry point principal para o Sistema de Limpeza Inteligente.

Este módulo gerencia:
- Parsing de argumentos da linha de comando (argparse)
- Roteamento para subsistemas (storage, archive, trash, restore)
- Execução de operações de limpeza através do LimpadorSistema

ARQUITETURA:
-----------
- Imports absolutos (from modules.xxx) para melhor manutenção
- Lazy loading de managers (só importa se necessário)
- Separação clara entre limpeza tradicional e gerenciamento de storage

FLAGS PRINCIPAIS:
----------------
--run: Executa limpeza real (padrão é apenas preview)
--python-only: Limpa APENAS cache Python (__pycache__, .pytest_cache, etc)
--full: Limpeza completa incluindo logs (com proteção de dirs críticos)
--interactive: Modo interativo com confirmação item por item

PROTEÇÃO:
---------
Diretórios críticos são SEMPRE protegidos, mesmo em --full mode:
.var, .config, .local/share, .vscode, .vscode-server, .mozilla, .ssh, .gnupg

AUTOR: Pedro Montezuma
DATA: 5 de setembro de 2025
REFATORAÇÃO: 6 de dezembro de 2025
"""

import os
import argparse
import sys
from pathlib import Path
import time
from datetime import datetime

# Importa o LimpadorSistema do módulo cleaner
from modules.cleaner import LimpadorSistema


def main():
    # Configuração dos argumentos da linha de comando
    parser = argparse.ArgumentParser(
        description="Script de limpeza inteligente do sistema para desenvolvedores",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
EXEMPLOS DE USO - LIMPEZA TRADICIONAL:
   main.py                         # Modo preview (não remove nada)
   main.py --details               # Mostra lista detalhada dos arquivos
   main.py --run                   # Executa limpeza real
   main.py --only-nodes            # Remove apenas node_modules
   main.py --python-only           # Remove apenas cache Python (__pycache__, .pyc, etc)
   main.py --interactive           # Modo interativo (escolha o que limpar)
   main.py --run --full            # Limpeza completa (CUIDADO: inclui logs)

EXEMPLOS DE USO - ARQUIVAMENTO INTELIGENTE:
   main.py --move --interactive              # Move arquivos antigos (interativo)
   main.py --move --policy reports           # Move relatórios antigos (15 dias)
   main.py --move --policy backups           # Move backups antigos (mantém 2)
   main.py --move --synergic                 # Aplica todas as políticas

EXEMPLOS DE USO - LIXÃO:
   main.py --trash /path/to/dir --tag OLD-REPORTS    # Compacta e move para lixão
   main.py --list-trash                              # Lista conteúdo do lixão
   main.py --search-trash "report_20241020"          # Busca no lixão

EXEMPLOS DE USO - RESTAURAÇÃO:
   main.py --list-archives                           # Lista archives disponíveis
   main.py --restore moving-20241103 --item report.html  # Restaura arquivo específico
   main.py --restore-trash "[OLD-REPORTS]_file.tar.gz"   # Restaura do lixão
   main.py --search "report" --in-archives           # Busca nos archives

INFORMAÇÕES:
   main.py --storage-info                            # Mostra info do storage
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
        '--python-only',
        action='store_true',
        help='Remove apenas cache Python (__pycache__, .pytest_cache, .pyc, etc)'
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

    # Escaneia o sistema (Python-only ou completo)
    if args.python_only:
        limpador.escanear_python_only()
    else:
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
        print(f"💾 Espaço liberado: {limpador.total_liberado}")
        print(f"📁 Diretórios removidos: {limpador.diretorios_removidos}")
        print(f"📄 Arquivos removidos: {limpador.arquivos_removidos}")
        return
    
    # MODO AUTOMÁTICO (original)
    # Se não for para ex, apenas mostra o preview
    if not args.run:
        print(f"\n⚠️  MODO PREVIEW ATIVO!")
        print("   Para executar a limpeza real, use: --run")
        print("   Exemplo: python3 main.py --run")
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
        only_python=args.python_only,
        full=args.full,
    )
    
    if sucesso:
        print("\n🎉 Script executado com sucesso!")
        print("💡 Dica: Execute este script semanalmente para manter o sistema otimizado")
    else:
        print("\n❌ Script interrompido ou falhou!")


if __name__ == "__main__":
    main()
