#!/usr/bin/env python3
"""
ARCHIVE MANAGER - Gerenciador de Arquivamento
==============================================

Move arquivos antigos do sistema principal para /mnt/storage/archives
(disco exclusivo para esses arquivos) seguindo políticas de retenção definidas. 
Mantém estrutura organizada e gera metadados completos de cada operação.

AUTOR: Pedro Montezuma 
DATA: 3 de novembro de 2025
"""

import os
import shutil
import json
from pathlib import Path
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Tuple
from modules.storage_manager import StorageManager


class ArchiveManager:
    """Gerencia arquivamento de arquivos antigos"""
    
    def __init__(self, storage_manager: StorageManager):
        self.storage = storage_manager
        self.current_operation = None
        self.files_to_move = []
        self.total_size = 0
        
        # Caminhos do meu sistema
        self.reports_path = Path.home() / ".bin/data/scripts-data/reports"
        self.backups_path = Path.home() / ".bin/data/backups/archives"
    
    def scan_old_reports(self, keep_days: int = 15) -> List[Dict]:
        """Escaneia relatórios para limpeza inteligente usando METADADOS DO ARQUIVO
        
        LÓGICA APLICADA (usando st_mtime do sistema de arquivos):
        1. Agrupa arquivos por categoria/subdir/DIA (usando mtime real, não nome)
        2. Para cada dia, mantém apenas o mais RECENTE (maior mtime)
        3. Move duplicados do mesmo dia
        4. Move completamente arquivos com mais de {keep_days} dias
        
        VANTAGEM: Não depende de nomenclatura, usa metadados fixos do filesystem
        """
        files_to_move = []
        cutoff_date = datetime.now() - timedelta(days=keep_days)
        
        print(f"   🔍 Escaneando relatórios (mantendo 1 por dia dos últimos {keep_days} dias)...")
        print(f"   📅 Usando metadados do arquivo (mtime) - independente de nomenclatura")
        
        if not self.reports_path.exists():
            print(f"   ⚠️  Pasta de relatórios não encontrada: {self.reports_path}")
            return files_to_move
        
        # Percorre todas as categorias de relatórios
        for category_dir in self.reports_path.iterdir():
            if not category_dir.is_dir() or category_dir.name == 'index.html':
                continue
            
            category = category_dir.name
            
            # Verifica html e raw
            for subdir in ['html', 'raw']:
                subdir_path = category_dir / subdir
                if not subdir_path.exists():
                    continue
                
                # Coleta TODOS os arquivos com seus metadados
                all_files = []
                
                for file_path in subdir_path.iterdir():
                    if file_path.is_file():
                        mtime = datetime.fromtimestamp(file_path.stat().st_mtime)
                        age_days = (datetime.now() - mtime).days
                        
                        all_files.append({
                            'path': file_path,
                            'category': category,
                            'subdir': subdir,
                            'size': file_path.stat().st_size,
                            'age_days': age_days,
                            'mtime': mtime,
                            'mtime_iso': mtime.isoformat(),
                            'type': 'report'
                        })
                
                # Agrupa por DIA usando o mtime real (YYYY-MM-DD)
                by_date = {}
                
                for file_info in all_files:
                    # Extrai apenas a data (sem hora) do mtime
                    file_date = file_info['mtime'].date()  # Objeto date (YYYY-MM-DD)
                    
                    # Chave única: categoria_subdir_data
                    day_key = f"{category}_{subdir}_{file_date.strftime('%Y%m%d')}"
                    
                    if day_key not in by_date:
                        by_date[day_key] = []
                    
                    by_date[day_key].append(file_info)
                
                # Para cada dia, mantém apenas o MAIS RECENTE (maior mtime)
                for day_key, files_in_day in by_date.items():
                    if len(files_in_day) <= 1:
                        # Só tem 1 arquivo neste dia
                        if files_in_day[0]['mtime'] < cutoff_date:
                            # É muito antigo, move
                            files_in_day[0]['mtime'] = files_in_day[0]['mtime_iso']
                            files_to_move.append(files_in_day[0])
                        continue
                    
                    # Ordena por mtime (mais recente primeiro)
                    files_in_day.sort(key=lambda x: x['mtime'], reverse=True)
                    
                    most_recent = files_in_day[0]
                    duplicates = files_in_day[1:]
                    
                    # Verifica se o dia inteiro é antigo
                    if most_recent['mtime'] < cutoff_date:
                        # Dia completo é antigo, move TODOS
                        print(f"      • {day_key}: dia antigo, movendo todos os {len(files_in_day)} arquivos")
                        for file_info in files_in_day:
                            file_info['mtime'] = file_info['mtime_iso']
                            files_to_move.append(file_info)
                    else:
                        # Dia está dentro do prazo, mantém apenas o mais recente
                        most_recent_time = most_recent['mtime'].strftime('%H:%M:%S')
                        print(f"      • {day_key}: mantendo {most_recent['path'].name} ({most_recent_time}), movendo {len(duplicates)} duplicados")
                        
                        for file_info in duplicates:
                            file_info['mtime'] = file_info['mtime_iso']
                            files_to_move.append(file_info)
        
        print(f"   ✅ Encontrados {len(files_to_move)} relatórios para mover/limpar")
        return files_to_move
    
    def scan_old_backups(self, keep_count: int = 2) -> List[Dict]:
        """Escaneia backups antigos (mantém apenas os 2 mais recentes de cada categoria)"""
        old_backups = []
        
        print(f"   🔍 Escaneando backups (mantendo {keep_count} mais recentes por categoria)...")
        
        if not self.backups_path.exists():
            print(f"   ⚠️  Pasta de backups não encontrada: {self.backups_path}")
            return old_backups
        
        # Agrupa backups por categoria
        backup_groups = {}
        
        for file_path in self.backups_path.iterdir():
            if file_path.is_file() and (file_path.suffix in ['.gz', '.zip', '.tar']):
                # Extrai categoria do nome: backup_[CATEGORIA]_[TIMESTAMP]
                parts = file_path.stem.replace('.tar', '').split('_')
                if len(parts) >= 2:
                    category = parts[1]  # Ex: Projects, scripts-data, Videos
                    
                    if category not in backup_groups:
                        backup_groups[category] = []
                    
                    backup_groups[category].append({
                        'path': file_path,
                        'category': category,
                        'size': file_path.stat().st_size,
                        'mtime': datetime.fromtimestamp(file_path.stat().st_mtime),
                        'type': 'backup'
                    })
        
        # Para cada categoria, mantém apenas os N mais recentes
        for category, backups in backup_groups.items():
            # Ordena por data (mais recente primeiro)
            backups.sort(key=lambda x: x['mtime'], reverse=True)
            
            # Os que excedem keep_count devem ser movidos
            to_move = backups[keep_count:]
            
            for backup in to_move:
                age_days = (datetime.now() - backup['mtime']).days
                backup['age_days'] = age_days
                backup['mtime'] = backup['mtime'].isoformat()
                old_backups.append(backup)
            
            if to_move:
                print(f"      • {category}: {len(to_move)} backups antigos (mantendo {min(len(backups), keep_count)} mais recentes)")
        
        print(f"   ✅ Encontrados {len(old_backups)} backups para mover")
        return old_backups
    
    def scan_by_policy(self, policy_name: str) -> List[Dict]:
        """Escaneia arquivos baseado em uma política"""
        policies = self.storage.get_policies()
        
        if policy_name not in policies:
            print(f"   ❌ Política '{policy_name}' não encontrada")
            return []
        
        policy = policies[policy_name]
        
        if policy_name == "reports":
            return self.scan_old_reports(policy.get("keep_days", 15))
        elif policy_name == "backups":
            return self.scan_old_backups(policy.get("keep_count", 2))
        else:
            print(f"   ⚠️  Política '{policy_name}' ainda não implementada")
            return []
    
    def prepare_move_operation(self, files: List[Dict], operation_name: str = None) -> str:
        """Prepara uma operação de movimentação"""
        if not files:
            print("   ⚠️  Nenhum arquivo para mover")
            return None
        
        # Gera timestamp para a operação
        timestamp = datetime.now().strftime("%Y%m%d-%H%M%S")
        if operation_name:
            operation_id = f"moving-{operation_name}-{timestamp}"
        else:
            operation_id = f"moving-{timestamp}"
        
        self.current_operation = {
            'id': operation_id,
            'timestamp': timestamp,
            'datetime': datetime.now().isoformat(),
            'files': files,
            'total_files': len(files),
            'total_size': sum(f['size'] for f in files),
            'status': 'prepared'
        }
        
        self.files_to_move = files
        self.total_size = self.current_operation['total_size']
        
        return operation_id
    
    def show_move_preview(self):
        """Mostra preview do que será movido"""
        if not self.current_operation:
            print("   ⚠️  Nenhuma operação preparada")
            return
        
        op = self.current_operation
        
        print(f"\n📋 PREVIEW DA OPERAÇÃO: {op['id']}")
        print("=" * 60)
        print(f"📊 Total de arquivos: {op['total_files']}")
        print(f"💾 Tamanho total: {StorageManager.format_size(op['total_size'])}")
        
        # Agrupa por tipo
        by_type = {}
        for f in op['files']:
            ftype = f.get('type', 'unknown')
            if ftype not in by_type:
                by_type[ftype] = []
            by_type[ftype].append(f)
        
        print(f"\n📁 POR CATEGORIA:")
        for ftype, files in by_type.items():
            total_size = sum(f['size'] for f in files)
            print(f"   • {ftype}: {len(files)} arquivos ({StorageManager.format_size(total_size)})")
            
            # Mostra alguns exemplos
            if len(files) <= 5:
                for f in files:
                    print(f"      - {f['path'].name} ({f.get('age_days', '?')} dias)")
            else:
                for f in files[:3]:
                    print(f"      - {f['path'].name} ({f.get('age_days', '?')} dias)")
                print(f"      ... e mais {len(files) - 3} arquivos")
        
        print("=" * 60)
    
    def execute_move(self, confirm: bool = False) -> bool:
        """Executa a movimentação dos arquivos"""
        if not self.current_operation:
            print("   ❌ Nenhuma operação preparada")
            return False
        
        if not confirm:
            print("\n⚠️  ATENÇÃO: Esta operação moverá os arquivos para o storage!")
            resposta = input("   Confirma? (s/n): ").strip().lower()
            if resposta not in ['s', 'sim', 'y', 'yes']:
                print("   ❌ Operação cancelada")
                return False
        
        op = self.current_operation
        operation_dir = self.storage.archives_path / op['id']
        
        try:
            print(f"\n🚀 EXECUTANDO MOVIMENTAÇÃO...")
            print("=" * 60)
            
            # Cria diretório da operação
            operation_dir.mkdir(parents=True, exist_ok=True)
            
            moved_files = []
            errors = []
            
            for file_info in op['files']:
                try:
                    source = file_info['path']
                    
                    # Determina destino mantendo estrutura
                    if file_info['type'] == 'report':
                        category = file_info['category']
                        subdir = file_info['subdir']
                        dest_dir = operation_dir / "reports" / category / subdir
                    elif file_info['type'] == 'backup':
                        dest_dir = operation_dir / "backups"
                    else:
                        dest_dir = operation_dir / "other"
                    
                    dest_dir.mkdir(parents=True, exist_ok=True)
                    destination = dest_dir / source.name
                    
                    # Move o arquivo
                    shutil.move(str(source), str(destination))
                    
                    file_info['destination'] = str(destination)
                    file_info['moved'] = True
                    moved_files.append(file_info)
                    
                    print(f"   ✅ {source.name}")
                    
                except Exception as e:
                    error_msg = f"Erro ao mover {file_info['path']}: {e}"
                    errors.append(error_msg)
                    print(f"   ❌ {error_msg}")
            
            # Cria metadata.json
            metadata = {
                'operation_id': op['id'],
                'timestamp': op['timestamp'],
                'datetime': op['datetime'],
                'total_files': len(moved_files),
                'total_size': sum(f['size'] for f in moved_files),
                'files': moved_files,
                'errors': errors
            }
            
            metadata_file = operation_dir / "metadata.json"
            with open(metadata_file, 'w', encoding='utf-8') as f:
                json.dump(metadata, f, indent=2, ensure_ascii=False, default=str)
            
            # Atualiza índice de archives
            self._update_archives_index(metadata)
            
            # Atualiza estatísticas
            moved_mb = metadata['total_size'] / (1024 * 1024)
            self.storage.increment_usage(moved_mb=moved_mb)
            
            print("=" * 60)
            print(f"✅ MOVIMENTAÇÃO CONCLUÍDA!")
            print(f"   📁 Arquivos movidos: {len(moved_files)}")
            print(f"   💾 Tamanho total: {StorageManager.format_size(metadata['total_size'])}")
            print(f"   📍 Localização: {operation_dir}")
            if errors:
                print(f"   ⚠️  Erros: {len(errors)}")
            
            return True
            
        except Exception as e:
            print(f"❌ Erro durante movimentação: {e}")
            return False
    
    def _update_archives_index(self, metadata: Dict):
        """Atualiza o índice de archives"""
        try:
            index = self.storage._load_json(self.storage.archives_index)
            
            if 'operations' not in index:
                index['operations'] = []
            
            # Adiciona resumo da operação
            index['operations'].append({
                'operation_id': metadata['operation_id'],
                'timestamp': metadata['timestamp'],
                'datetime': metadata['datetime'],
                'total_files': metadata['total_files'],
                'total_size': metadata['total_size'],
                'location': str(self.storage.archives_path / metadata['operation_id'])
            })
            
            index['last_updated'] = datetime.now().isoformat()
            
            self.storage._save_json(self.storage.archives_index, index)
            
        except Exception as e:
            print(f"⚠️  Erro ao atualizar índice: {e}")


def main():
    """Teste do ArchiveManager"""
    storage = StorageManager()
    storage.initialize_storage()
    
    archive = ArchiveManager(storage)
    
    # Escaneia relatórios antigos
    old_reports = archive.scan_old_reports(keep_days=15)
    
    # Escaneia backups antigos
    old_backups = archive.scan_old_backups(keep_count=2)
    
    # Prepara operação
    all_files = old_reports + old_backups
    if all_files:
        archive.prepare_move_operation(all_files)
        archive.show_move_preview()


if __name__ == "__main__":
    main()
