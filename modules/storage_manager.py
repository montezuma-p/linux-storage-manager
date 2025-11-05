#!/usr/bin/env python3
"""
STORAGE MANAGER - Gerenciador do /mnt/storage
==============================================

Gerencia a estrutura, configurações e estatísticas do disco de armazenamento.
Cria automaticamente toda a estrutura necessária na primeira execução.

AUTOR: Sistema de Limpeza Inteligente
DATA: 3 de novembro de 2025
"""

import os
import json
import shutil
from pathlib import Path
from datetime import datetime
from typing import Dict, List, Optional, Tuple


class StorageManager:
    """Gerencia o disco de storage (/mnt/storage)"""
    
    def __init__(self, storage_path: str = "/mnt/storage"):
        self.storage_path = Path(storage_path)
        self.archives_path = self.storage_path / "archives"
        self.trash_path = self.storage_path / "trash"
        self.recovery_path = self.storage_path / "recovery"
        self.config_path = self.storage_path / ".storage-config"
        
        # Arquivos de índice
        self.config_file = self.config_path / "config.json"
        self.policies_file = self.config_path / "policies.json"
        self.usage_file = self.config_path / "usage.json"
        self.archives_index = self.archives_path / "index_archives.json"
        self.trash_manifest = self.trash_path / "manifest_trash.json"
        
        # Políticas padrão
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
        
        # Configurações padrão
        self.default_config = {
            "storage_path": str(self.storage_path),
            "initialized_at": datetime.now().isoformat(),
            "version": "1.0.0",
            "auto_cleanup_archives_days": 90,
            "auto_cleanup_trash_days": 180,
            "compression_level": 9
        }
    
    def initialize_storage(self, verbose: bool = True) -> bool:
        """
        Inicializa a estrutura completa do storage
        Cria todos os diretórios e arquivos necessários
        """
        try:
            if verbose:
                print("\n🔧 INICIALIZANDO ESTRUTURA DO STORAGE")
                print("=" * 60)
            
            # Verifica se storage está montado
            if not self.storage_path.exists():
                print(f"❌ Erro: {self.storage_path} não existe ou não está montado!")
                return False
            
            # Cria diretórios principais
            directories = [
                (self.archives_path, "archives - Arquivos movidos"),
                (self.trash_path / "compressed", "trash/compressed - Lixão compactado"),
                (self.trash_path / "metadata", "trash/metadata - Metadados do lixão"),
                (self.recovery_path, "recovery - Área temporária de restore"),
                (self.config_path, ".storage-config - Configurações")
            ]
            
            for dir_path, description in directories:
                if not dir_path.exists():
                    dir_path.mkdir(parents=True, exist_ok=True)
                    if verbose:
                        print(f"   ✅ Criado: {description}")
                else:
                    if verbose:
                        print(f"   ✓  Existe: {description}")
            
            # Cria arquivos de configuração se não existirem
            if not self.config_file.exists():
                self._save_json(self.config_file, self.default_config)
                if verbose:
                    print(f"   ✅ Criado: config.json")
            
            if not self.policies_file.exists():
                self._save_json(self.policies_file, self.default_policies)
                if verbose:
                    print(f"   ✅ Criado: policies.json")
            
            if not self.usage_file.exists():
                self._save_json(self.usage_file, {
                    "last_updated": datetime.now().isoformat(),
                    "total_operations": 0,
                    "total_moved_mb": 0,
                    "total_trashed_mb": 0
                })
                if verbose:
                    print(f"   ✅ Criado: usage.json")
            
            if not self.archives_index.exists():
                self._save_json(self.archives_index, {
                    "operations": [],
                    "last_updated": datetime.now().isoformat()
                })
                if verbose:
                    print(f"   ✅ Criado: index_archives.json")
            
            if not self.trash_manifest.exists():
                self._save_json(self.trash_manifest, {
                    "items": [],
                    "last_updated": datetime.now().isoformat()
                })
                if verbose:
                    print(f"   ✅ Criado: manifest_trash.json")
            
            if verbose:
                print("=" * 60)
                print("✅ Storage inicializado com sucesso!\n")
            
            return True
            
        except Exception as e:
            print(f"❌ Erro ao inicializar storage: {e}")
            return False
    
    def get_storage_stats(self) -> Dict:
        """Retorna estatísticas do storage"""
        try:
            # Calcula espaço em disco
            stat = shutil.disk_usage(self.storage_path)
            
            # Conta operações
            archives_index = self._load_json(self.archives_index)
            trash_manifest = self._load_json(self.trash_manifest)
            usage_data = self._load_json(self.usage_file)
            
            stats = {
                "disk": {
                    "total_gb": stat.total / (1024**3),
                    "used_gb": stat.used / (1024**3),
                    "free_gb": stat.free / (1024**3),
                    "percent_used": (stat.used / stat.total) * 100
                },
                "operations": {
                    "total_archives": len(archives_index.get("operations", [])),
                    "total_trash_items": len(trash_manifest.get("items", [])),
                    "total_operations": usage_data.get("total_operations", 0),
                    "total_moved_mb": usage_data.get("total_moved_mb", 0),
                    "total_trashed_mb": usage_data.get("total_trashed_mb", 0)
                }
            }
            
            return stats
            
        except Exception as e:
            print(f"⚠️  Erro ao obter estatísticas: {e}")
            return {}
    
    def show_storage_info(self):
        """Exibe informações do storage"""
        stats = self.get_storage_stats()
        
        if not stats:
            print("❌ Não foi possível obter informações do storage")
            return
        
        print("\n📊 INFORMAÇÕES DO STORAGE")
        print("=" * 60)
        print(f"📍 Local: {self.storage_path}")
        print(f"\n💾 DISCO:")
        print(f"   Total: {stats['disk']['total_gb']:.1f} GB")
        print(f"   Usado: {stats['disk']['used_gb']:.1f} GB ({stats['disk']['percent_used']:.1f}%)")
        print(f"   Livre: {stats['disk']['free_gb']:.1f} GB")
        print(f"\n📦 OPERAÇÕES:")
        print(f"   Archives criados: {stats['operations']['total_archives']}")
        print(f"   Itens no lixão: {stats['operations']['total_trash_items']}")
        print(f"   Total de operações: {stats['operations']['total_operations']}")
        print(f"   Total movido: {stats['operations']['total_moved_mb']:.1f} MB")
        print(f"   Total no lixão: {stats['operations']['total_trashed_mb']:.1f} MB")
        print("=" * 60)
    
    def get_policies(self) -> Dict:
        """Retorna as políticas de retenção"""
        return self._load_json(self.policies_file)
    
    def update_policy(self, category: str, policy: Dict) -> bool:
        """Atualiza política de uma categoria"""
        try:
            policies = self.get_policies()
            policies[category] = policy
            self._save_json(self.policies_file, policies)
            return True
        except Exception as e:
            print(f"❌ Erro ao atualizar política: {e}")
            return False
    
    def increment_usage(self, moved_mb: float = 0, trashed_mb: float = 0):
        """Incrementa estatísticas de uso"""
        try:
            usage = self._load_json(self.usage_file)
            usage["total_operations"] = usage.get("total_operations", 0) + 1
            usage["total_moved_mb"] = usage.get("total_moved_mb", 0) + moved_mb
            usage["total_trashed_mb"] = usage.get("total_trashed_mb", 0) + trashed_mb
            usage["last_updated"] = datetime.now().isoformat()
            self._save_json(self.usage_file, usage)
        except Exception as e:
            print(f"⚠️  Erro ao atualizar estatísticas: {e}")
    
    def cleanup_old_recovery(self, days: int = 7):
        """Remove arquivos antigos da pasta recovery"""
        try:
            now = datetime.now().timestamp()
            removed = 0
            
            for item in self.recovery_path.iterdir():
                if item.is_dir():
                    # Verifica idade
                    age_days = (now - item.stat().st_mtime) / (24 * 3600)
                    if age_days > days:
                        shutil.rmtree(item)
                        removed += 1
            
            if removed > 0:
                print(f"   🧹 Removidos {removed} diretórios antigos de recovery")
                
        except Exception as e:
            print(f"⚠️  Erro ao limpar recovery: {e}")
    
    def _load_json(self, file_path: Path) -> Dict:
        """Carrega arquivo JSON"""
        try:
            if file_path.exists():
                with open(file_path, 'r', encoding='utf-8') as f:
                    return json.load(f)
            return {}
        except Exception as e:
            print(f"⚠️  Erro ao ler {file_path.name}: {e}")
            return {}
    
    def _save_json(self, file_path: Path, data: Dict):
        """Salva arquivo JSON"""
        try:
            with open(file_path, 'w', encoding='utf-8') as f:
                json.dump(data, f, indent=2, ensure_ascii=False)
        except Exception as e:
            print(f"❌ Erro ao salvar {file_path.name}: {e}")
    
    @staticmethod
    def format_size(size_bytes: float) -> str:
        """Formata tamanho em bytes para formato legível"""
        for unit in ['B', 'KB', 'MB', 'GB', 'TB']:
            if size_bytes < 1024.0:
                return f"{size_bytes:.1f} {unit}"
            size_bytes /= 1024.0
        return f"{size_bytes:.1f} PB"


def main():
    """Teste do StorageManager"""
    manager = StorageManager()
    
    # Inicializa storage
    if manager.initialize_storage():
        # Mostra informações
        manager.show_storage_info()


if __name__ == "__main__":
    main()
