#!/usr/bin/env python3
"""
TRASH MANAGER - Gerenciador do Lixão Compactado
================================================

Compacta e move arquivos/diretórios para o lixão permanente no storage.
Usa nomenclatura com [TAGS] para fácil identificação e compressão máxima
para economizar espaço.

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


class TrashManager:
    """Gerencia o lixão compactado do storage"""
    
    def __init__(self, storage_manager: StorageManager):
        self.storage = storage_manager
        self.compressed_path = self.storage.trash_path / "compressed"
        self.metadata_path = self.storage.trash_path / "metadata"
        self.items_to_trash = []
        self.current_operation = None
        
        # Tags disponíveis
        self.available_tags = [
            "OLD-REPORTS",
            "OLD-BACKUPS", 
            "ARCHIVED",
            "NODE-MODULES",
            "MOVED",
            "LOGS",
            "TEMP",
            "CUSTOM"
        ]
    
    def add_items(self, paths: List[Path], tag: str = "MOVED", description: str = "") -> bool:
        """Adiciona itens para serem enviados ao lixão"""
        if tag not in self.available_tags:
            print(f"⚠️  Tag '{tag}' não reconhecida. Disponíveis: {', '.join(self.available_tags)}")
            tag = "CUSTOM"
        
        added = []
        for path in paths:
            path = Path(path)
            if not path.exists():
                print(f"   ⚠️  Não encontrado: {path}")
                continue
            
            size = self._get_path_size(path)
            
            item = {
                'path': path,
                'name': path.name,
                'is_dir': path.is_dir(),
                'size': size,
                'tag': tag,
                'description': description,
                'added_at': datetime.now().isoformat()
            }
            
            added.append(item)
            self.items_to_trash.append(item)
        
        print(f"   ✅ Adicionados {len(added)} itens para o lixão")
        return len(added) > 0
    
    def add_directory(self, dir_path: Path, tag: str = "ARCHIVED", description: str = "") -> bool:
        """Adiciona um diretório completo ao lixão"""
        return self.add_items([dir_path], tag, description)
    
    def show_trash_preview(self):
        """Mostra preview do que será enviado ao lixão"""
        if not self.items_to_trash:
            print("   ℹ️  Nenhum item adicionado ao lixão")
            return
        
        total_size = sum(item['size'] for item in self.items_to_trash)
        
        print(f"\n🗑️  PREVIEW DO LIXÃO")
        print("=" * 60)
        print(f"📊 Total de itens: {len(self.items_to_trash)}")
        print(f"💾 Tamanho total: {StorageManager.format_size(total_size)}")
        
        # Agrupa por tag
        by_tag = {}
        for item in self.items_to_trash:
            tag = item['tag']
            if tag not in by_tag:
                by_tag[tag] = []
            by_tag[tag].append(item)
        
        print(f"\n🏷️  POR TAG:")
        for tag, items in by_tag.items():
            tag_size = sum(i['size'] for i in items)
            print(f"   [{tag}]: {len(items)} itens ({StorageManager.format_size(tag_size)})")
            
            for item in items[:3]:
                tipo = "📁" if item['is_dir'] else "📄"
                print(f"      {tipo} {item['name']}")
            
            if len(items) > 3:
                print(f"      ... e mais {len(items) - 3} itens")
        
        print("=" * 60)
    
    def compress_and_move(self, custom_name: str = None, confirm: bool = False) -> bool:
        """Compacta itens e move para o lixão"""
        if not self.items_to_trash:
            print("   ❌ Nenhum item para enviar ao lixão")
            return False
        
        if not confirm:
            print("\n⚠️  ATENÇÃO: Itens serão compactados e movidos para o lixão!")
            print("   Compressão máxima será aplicada.")
            resposta = input("   Confirma? (s/n): ").strip().lower()
            if resposta not in ['s', 'sim', 'y', 'yes']:
                print("   ❌ Operação cancelada")
                return False
        
        try:
            print(f"\n🗜️  COMPACTANDO E MOVENDO PARA O LIXÃO...")
            print("=" * 60)
            
            # Determina tag principal (mais comum)
            tag_counts = {}
            for item in self.items_to_trash:
                tag = item['tag']
                tag_counts[tag] = tag_counts.get(tag, 0) + 1
            main_tag = max(tag_counts, key=tag_counts.get)
            
            # Gera nome do arquivo
            timestamp = datetime.now().strftime("%Y%m%d-%H%M%S")
            if custom_name:
                filename = f"[{main_tag}]_{custom_name}_{timestamp}.tar.gz"
            else:
                filename = f"[{main_tag}]_trash_{timestamp}.tar.gz"
            
            output_path = self.compressed_path / filename
            
            # Cria arquivo tar.gz com compressão máxima
            print(f"   🗜️  Compactando com nível máximo...")
            with tarfile.open(output_path, 'w:gz', compresslevel=9) as tar:
                for item in self.items_to_trash:
                    try:
                        # Adiciona ao tar mantendo nome original
                        arcname = item['name']
                        tar.add(str(item['path']), arcname=arcname)
                        print(f"      ✅ {item['name']}")
                    except Exception as e:
                        print(f"      ❌ Erro ao adicionar {item['name']}: {e}")
            
            compressed_size = output_path.stat().st_size
            original_size = sum(item['size'] for item in self.items_to_trash)
            compression_ratio = ((original_size - compressed_size) / original_size * 100) if original_size > 0 else 0
            
            # Cria metadata
            metadata = {
                'filename': filename,
                'created_at': datetime.now().isoformat(),
                'timestamp': timestamp,
                'main_tag': main_tag,
                'total_items': len(self.items_to_trash),
                'original_size': original_size,
                'compressed_size': compressed_size,
                'compression_ratio': compression_ratio,
                'items': [
                    {
                        'name': item['name'],
                        'tag': item['tag'],
                        'size': item['size'],
                        'is_dir': item['is_dir'],
                        'description': item.get('description', '')
                    }
                    for item in self.items_to_trash
                ]
            }
            
            # Salva metadata
            metadata_file = self.metadata_path / f"{filename}.json"
            with open(metadata_file, 'w', encoding='utf-8') as f:
                json.dump(metadata, f, indent=2, ensure_ascii=False)
            
            # Atualiza manifest
            self._update_trash_manifest(metadata)
            
            # Remove arquivos originais
            print(f"\n   🗑️  Removendo arquivos originais...")
            for item in self.items_to_trash:
                try:
                    if item['path'].is_dir():
                        shutil.rmtree(item['path'])
                    else:
                        item['path'].unlink()
                except Exception as e:
                    print(f"      ⚠️  Erro ao remover {item['name']}: {e}")
            
            # Atualiza estatísticas
            trashed_mb = compressed_size / (1024 * 1024)
            self.storage.increment_usage(trashed_mb=trashed_mb)
            
            print("=" * 60)
            print(f"✅ LIXÃO ATUALIZADO!")
            print(f"   📦 Arquivo: {filename}")
            print(f"   📊 Itens compactados: {len(self.items_to_trash)}")
            print(f"   📏 Tamanho original: {StorageManager.format_size(original_size)}")
            print(f"   🗜️  Tamanho compactado: {StorageManager.format_size(compressed_size)}")
            print(f"   📉 Compressão: {compression_ratio:.1f}%")
            print(f"   📍 Localização: {output_path}")
            
            # Limpa lista
            self.items_to_trash = []
            
            return True
            
        except Exception as e:
            print(f"❌ Erro ao processar lixão: {e}")
            return False
    
    def list_trash_contents(self, limit: int = 20):
        """Lista conteúdo do lixão"""
        manifest = self.storage._load_json(self.storage.trash_manifest)
        items = manifest.get('items', [])
        
        if not items:
            print("\n🗑️  Lixão está vazio")
            return
        
        print(f"\n🗑️  CONTEÚDO DO LIXÃO ({len(items)} arquivos)")
        print("=" * 60)
        
        total_compressed = sum(item.get('compressed_size', 0) for item in items)
        print(f"💾 Tamanho total: {StorageManager.format_size(total_compressed)}\n")
        
        # Mostra os mais recentes
        items_sorted = sorted(items, key=lambda x: x.get('created_at', ''), reverse=True)
        
        for i, item in enumerate(items_sorted[:limit], 1):
            filename = item.get('filename', 'unknown')
            created = item.get('created_at', 'unknown')[:10]
            size = StorageManager.format_size(item.get('compressed_size', 0))
            ratio = item.get('compression_ratio', 0)
            
            print(f"{i:2}. {filename}")
            print(f"    📅 {created} | 💾 {size} | 🗜️  {ratio:.1f}% compressão")
        
        if len(items) > limit:
            print(f"\n... e mais {len(items) - limit} arquivos")
        
        print("=" * 60)
    
    def search_in_trash(self, search_term: str):
        """Busca arquivos no lixão"""
        manifest = self.storage._load_json(self.storage.trash_manifest)
        items = manifest.get('items', [])
        
        results = []
        for trash_item in items:
            # Busca no nome do arquivo
            if search_term.lower() in trash_item.get('filename', '').lower():
                results.append(trash_item)
                continue
            
            # Busca nos itens internos
            for internal_item in trash_item.get('items', []):
                if search_term.lower() in internal_item.get('name', '').lower():
                    if trash_item not in results:
                        results.append(trash_item)
                    break
        
        if not results:
            print(f"\n🔍 Nenhum resultado encontrado para '{search_term}'")
            return
        
        print(f"\n🔍 RESULTADOS DA BUSCA: '{search_term}' ({len(results)} arquivos)")
        print("=" * 60)
        
        for item in results:
            print(f"📦 {item.get('filename')}")
            print(f"   📅 {item.get('created_at', 'unknown')[:10]}")
            print(f"   💾 {StorageManager.format_size(item.get('compressed_size', 0))}")
            print(f"   📊 {item.get('total_items', 0)} itens internos\n")
    
    def _update_trash_manifest(self, metadata: Dict):
        """Atualiza o manifesto do lixão"""
        try:
            manifest = self.storage._load_json(self.storage.trash_manifest)
            
            if 'items' not in manifest:
                manifest['items'] = []
            
            manifest['items'].append(metadata)
            manifest['last_updated'] = datetime.now().isoformat()
            
            self.storage._save_json(self.storage.trash_manifest, manifest)
            
        except Exception as e:
            print(f"⚠️  Erro ao atualizar manifest: {e}")
    
    def _get_path_size(self, path: Path) -> int:
        """Calcula tamanho de um arquivo ou diretório"""
        if path.is_file():
            return path.stat().st_size
        
        total = 0
        try:
            for item in path.rglob('*'):
                if item.is_file():
                    try:
                        total += item.stat().st_size
                    except:
                        pass
        except:
            pass
        
        return total


def main():
    """Teste do TrashManager"""
    storage = StorageManager()
    storage.initialize_storage()
    
    trash = TrashManager(storage)
    
    # Lista conteúdo do lixão
    trash.list_trash_contents()


if __name__ == "__main__":
    main()
