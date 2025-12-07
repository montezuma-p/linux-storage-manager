"""
Módulos do Sistema de Limpeza Inteligente
==========================================

Módulos reutilizáveis para gerenciamento de arquivamento,
lixão e restauração no storage.

NOTA: Absolute imports (from modules.xxx) são usados em vez de
relative imports (from .xxx) para melhor suporte de IDEs e
clareza na estrutura do projeto.
"""

# Absolute imports - melhor IntelliSense e navegação
from modules.storage_manager import StorageManager
from modules.archive_manager import ArchiveManager
from modules.trash_manager import TrashManager
from modules.restore_manager import RestoreManager

__all__ = [
    'StorageManager',
    'ArchiveManager',
    'TrashManager',
    'RestoreManager'
]
