#!/usr/bin/env python3
"""
RESTORE MANAGER - Gerenciador de Restauração
=============================================

Gerencia restauração de arquivos do storage (archives e trash).
Permite listar, buscar e extrair arquivos específicos sem descompactar tudo.

AUTOR: Pedro Montezuma
DATA: 3 de novembro de 2025
"""

import os
import shutil
import json
import tarfile
from pathlib import Path
from datetime import datetime
from typing import Dict, List, Optional
from modules.storage_manager import StorageManager


class RestoreManager:
    """Gerencia restauração de arquivos do storage"""
    
    def __init__(self, storage_manager: StorageManager):
        self.storage = storage_manager
        self.recovery_path = self.storage.recovery_path
    
    def list_archives(self, limit: int = 20):
        """Lista operações de archive disponíveis"""
        index = self.storage._load_json(self.storage.archives_index)
        operations = index.get('operations', [])
        
        if not operations:
            print("\n📦 Nenhum archive encontrado")
            return
        
        print(f"\n📦 ARCHIVES DISPONÍVEIS ({len(operations)} operações)")
        print("=" * 60)
        
        # Ordena por data (mais recente primeiro)
        operations_sorted = sorted(operations, key=lambda x: x.get('datetime', ''), reverse=True)
        
        for i, op in enumerate(operations_sorted[:limit], 1):
            op_id = op.get('operation_id', 'unknown')
            date = op.get('datetime', 'unknown')[:19].replace('T', ' ')
            files = op.get('total_files', 0)
            size = StorageManager.format_size(op.get('total_size', 0))
            
            print(f"{i:2}. {op_id}")
            print(f"    📅 {date} | 📊 {files} arquivos | 💾 {size}")
        
        if len(operations) > limit:
            print(f"\n... e mais {len(operations) - limit} operações")
        
        print("=" * 60)
        print("💡 Use: main.py --restore <operation_id> --item <arquivo>")
    
    def list_trash(self, limit: int = 20):
        """Lista arquivos no lixão"""
        manifest = self.storage._load_json(self.storage.trash_manifest)
        items = manifest.get('items', [])
        
        if not items:
            print("\n🗑️  Lixão está vazio")
            return
        
        print(f"\n🗑️  LIXÃO ({len(items)} arquivos compactados)")
        print("=" * 60)
        
        # Ordena por data (mais recente primeiro)
        items_sorted = sorted(items, key=lambda x: x.get('created_at', ''), reverse=True)
        
        for i, item in enumerate(items_sorted[:limit], 1):
            filename = item.get('filename', 'unknown')
            date = item.get('created_at', 'unknown')[:19].replace('T', ' ')
            count = item.get('total_items', 0)
            size = StorageManager.format_size(item.get('compressed_size', 0))
            ratio = item.get('compression_ratio', 0)
            
            print(f"{i:2}. {filename}")
            print(f"    📅 {date} | 📊 {count} itens | 💾 {size} | 🗜️  {ratio:.1f}%")
        
        if len(items) > limit:
            print(f"\n... e mais {len(items) - limit} arquivos")
        
        print("=" * 60)
        print("💡 Use: main.py --restore-trash <filename>")
    
    def search_in_archives(self, search_term: str):
        """Busca arquivos nos archives"""
        print(f"\n🔍 Buscando '{search_term}' nos archives...")
        print("=" * 60)
        
        found = []
        
        # Percorre todos os archives
        for archive_dir in self.storage.archives_path.iterdir():
            if not archive_dir.is_dir() or archive_dir.name.startswith('.'):
                continue
            
            # Lê metadata
            metadata_file = archive_dir / "metadata.json"
            if not metadata_file.exists():
                continue
            
            with open(metadata_file, 'r', encoding='utf-8') as f:
                metadata = json.load(f)
            
            # Busca nos arquivos
            for file_info in metadata.get('files', []):
                path = Path(file_info.get('destination', ''))
                if search_term.lower() in path.name.lower():
                    found.append({
                        'archive': archive_dir.name,
                        'file': path.name,
                        'path': str(path),
                        'size': file_info.get('size', 0),
                        'age_days': file_info.get('age_days', 0)
                    })
        
        if not found:
            print(f"   ❌ Nenhum arquivo encontrado")
            return
        
        print(f"   ✅ Encontrados {len(found)} resultados:\n")
        
        for item in found[:20]:
            print(f"📄 {item['file']}")
            print(f"   📦 Archive: {item['archive']}")
            print(f"   💾 Tamanho: {StorageManager.format_size(item['size'])}")
            print(f"   📍 Path: {item['path']}\n")
        
        if len(found) > 20:
            print(f"... e mais {len(found) - 20} resultados")
        
        print("=" * 60)
    
    def search_in_trash(self, search_term: str):
        """Busca arquivos no lixão"""
        print(f"\n🔍 Buscando '{search_term}' no lixão...")
        print("=" * 60)
        
        manifest = self.storage._load_json(self.storage.trash_manifest)
        items = manifest.get('items', [])
        
        found = []
        
        for trash_item in items:
            filename = trash_item.get('filename', '')
            
            # Busca nos itens internos
            for internal_item in trash_item.get('items', []):
                if search_term.lower() in internal_item.get('name', '').lower():
                    found.append({
                        'trash_file': filename,
                        'item_name': internal_item.get('name'),
                        'tag': internal_item.get('tag'),
                        'size': internal_item.get('size', 0)
                    })
        
        if not found:
            print(f"   ❌ Nenhum arquivo encontrado")
            return
        
        print(f"   ✅ Encontrados {len(found)} resultados:\n")
        
        for item in found[:20]:
            print(f"📄 {item['item_name']}")
            print(f"   🗑️  Trash: {item['trash_file']}")
            print(f"   🏷️  Tag: [{item['tag']}]")
            print(f"   💾 Tamanho: {StorageManager.format_size(item['size'])}\n")
        
        if len(found) > 20:
            print(f"... e mais {len(found) - 20} resultados")
        
        print("=" * 60)
    
    def restore_from_archive(self, operation_id: str, item_name: str = None, destination: str = None) -> bool:
        """Restaura arquivo(s) de um archive"""
        archive_dir = self.storage.archives_path / operation_id
        
        if not archive_dir.exists():
            print(f"❌ Archive '{operation_id}' não encontrado")
            return False
        
        # Define destino
        if destination:
            dest_path = Path(destination).expanduser()
        else:
            # Cria pasta temporária em recovery
            timestamp = datetime.now().strftime("%Y%m%d-%H%M%S")
            dest_path = self.recovery_path / f"restore-{timestamp}"
        
        dest_path.mkdir(parents=True, exist_ok=True)
        
        try:
            print(f"\n♻️  RESTAURANDO DO ARCHIVE: {operation_id}")
            print("=" * 60)
            
            if item_name:
                # Restaura item específico
                print(f"   🔍 Procurando '{item_name}'...")
                
                found = False
                for root, dirs, files in os.walk(archive_dir):
                    for file in files:
                        if item_name.lower() in file.lower():
                            source = Path(root) / file
                            dest = dest_path / file
                            shutil.copy2(source, dest)
                            print(f"   ✅ Restaurado: {file}")
                            print(f"   📍 Para: {dest}")
                            found = True
                
                if not found:
                    print(f"   ❌ Item '{item_name}' não encontrado")
                    return False
            else:
                # Restaura tudo
                print(f"   📦 Restaurando todo o archive...")
                
                count = 0
                for root, dirs, files in os.walk(archive_dir):
                    for file in files:
                        if file == 'metadata.json':
                            continue
                        
                        source = Path(root) / file
                        rel_path = source.relative_to(archive_dir)
                        dest = dest_path / rel_path
                        
                        dest.parent.mkdir(parents=True, exist_ok=True)
                        shutil.copy2(source, dest)
                        count += 1
                
                print(f"   ✅ Restaurados {count} arquivos")
                print(f"   📍 Para: {dest_path}")
            
            print("=" * 60)
            print("✅ RESTAURAÇÃO CONCLUÍDA!")
            
            return True
            
        except Exception as e:
            print(f"❌ Erro ao restaurar: {e}")
            return False
    
    def restore_from_trash(self, trash_filename: str, destination: str = None) -> bool:
        """Restaura arquivo do lixão (descompacta)"""
        trash_file = self.storage.trash_path / "compressed" / trash_filename
        
        if not trash_file.exists():
            print(f"❌ Arquivo '{trash_filename}' não encontrado no lixão")
            return False
        
        # Define destino
        if destination:
            dest_path = Path(destination).expanduser()
        else:
            # Cria pasta temporária em recovery
            timestamp = datetime.now().strftime("%Y%m%d-%H%M%S")
            dest_path = self.recovery_path / f"restore-trash-{timestamp}"
        
        dest_path.mkdir(parents=True, exist_ok=True)
        
        try:
            print(f"\n♻️  RESTAURANDO DO LIXÃO: {trash_filename}")
            print("=" * 60)
            print(f"   🗜️  Descompactando...")
            
            # Extrai arquivo
            with tarfile.open(trash_file, 'r:gz') as tar:
                tar.extractall(path=dest_path)
                members = tar.getmembers()
                print(f"   ✅ Extraídos {len(members)} itens")
            
            print(f"   📍 Para: {dest_path}")
            print("=" * 60)
            print("✅ RESTAURAÇÃO CONCLUÍDA!")
            print("⚠️  ATENÇÃO: Arquivo original permanece no lixão")
            
            return True
            
        except Exception as e:
            print(f"❌ Erro ao restaurar do lixão: {e}")
            return False
    
    def extract_item_from_trash(self, trash_filename: str, item_name: str, destination: str = None) -> bool:
        """Extrai um item específico do lixão sem descompactar tudo"""
        trash_file = self.storage.trash_path / "compressed" / trash_filename
        
        if not trash_file.exists():
            print(f"❌ Arquivo '{trash_filename}' não encontrado no lixão")
            return False
        
        # Define destino
        if destination:
            dest_path = Path(destination).expanduser()
        else:
            timestamp = datetime.now().strftime("%Y%m%d-%H%M%S")
            dest_path = self.recovery_path / f"restore-item-{timestamp}"
        
        dest_path.mkdir(parents=True, exist_ok=True)
        
        try:
            print(f"\n♻️  EXTRAINDO DE: {trash_filename}")
            print("=" * 60)
            print(f"   🔍 Procurando '{item_name}'...")
            
            # Extrai apenas o item específico
            with tarfile.open(trash_file, 'r:gz') as tar:
                found = False
                for member in tar.getmembers():
                    if item_name.lower() in member.name.lower():
                        tar.extract(member, path=dest_path)
                        print(f"   ✅ Extraído: {member.name}")
                        print(f"   📍 Para: {dest_path / member.name}")
                        found = True
                
                if not found:
                    print(f"   ❌ Item '{item_name}' não encontrado no arquivo")
                    return False
            
            print("=" * 60)
            print("✅ EXTRAÇÃO CONCLUÍDA!")
            
            return True
            
        except Exception as e:
            print(f"❌ Erro ao extrair: {e}")
            return False
    
    def list_archive_contents(self, operation_id: str):
        """Lista conteúdo de um archive específico"""
        archive_dir = self.storage.archives_path / operation_id
        
        if not archive_dir.exists():
            print(f"❌ Archive '{operation_id}' não encontrado")
            return
        
        metadata_file = archive_dir / "metadata.json"
        if not metadata_file.exists():
            print(f"❌ Metadata não encontrado")
            return
        
        with open(metadata_file, 'r', encoding='utf-8') as f:
            metadata = json.load(f)
        
        print(f"\n📦 CONTEÚDO DO ARCHIVE: {operation_id}")
        print("=" * 60)
        print(f"📅 Data: {metadata.get('datetime', 'unknown')[:19]}")
        print(f"📊 Total: {metadata.get('total_files', 0)} arquivos")
        print(f"💾 Tamanho: {StorageManager.format_size(metadata.get('total_size', 0))}\n")
        
        for i, file_info in enumerate(metadata.get('files', [])[:50], 1):
            path = Path(file_info.get('destination', ''))
            size = StorageManager.format_size(file_info.get('size', 0))
            print(f"{i:2}. {path.name} ({size})")
        
        total = len(metadata.get('files', []))
        if total > 50:
            print(f"\n... e mais {total - 50} arquivos")
        
        print("=" * 60)
    
    def list_trash_file_contents(self, trash_filename: str):
        """Lista conteúdo de um arquivo do lixão"""
        trash_file = self.storage.trash_path / "compressed" / trash_filename
        
        if not trash_file.exists():
            print(f"❌ Arquivo '{trash_filename}' não encontrado")
            return
        
        try:
            print(f"\n🗑️  CONTEÚDO DE: {trash_filename}")
            print("=" * 60)
            
            with tarfile.open(trash_file, 'r:gz') as tar:
                members = tar.getmembers()
                
                print(f"📊 Total: {len(members)} itens\n")
                
                for i, member in enumerate(members[:50], 1):
                    size = StorageManager.format_size(member.size)
                    tipo = "📁" if member.isdir() else "📄"
                    print(f"{i:2}. {tipo} {member.name} ({size})")
                
                if len(members) > 50:
                    print(f"\n... e mais {len(members) - 50} itens")
            
            print("=" * 60)
            
        except Exception as e:
            print(f"❌ Erro ao ler arquivo: {e}")


def main():
    """Teste do RestoreManager"""
    storage = StorageManager()
    storage.initialize_storage()
    
    restore = RestoreManager(storage)
    
    # Lista archives disponíveis
    restore.list_archives()
    
    print("\n")
    
    # Lista lixão
    restore.list_trash()


if __name__ == "__main__":
    main()
