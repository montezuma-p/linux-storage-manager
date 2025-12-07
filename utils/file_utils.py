#!/usr/bin/env python3
"""
UTILS - Funções Utilitárias
============================

Funções auxiliares reutilizáveis para o sistema de limpeza.

Este módulo fornece funções puras (sem side effects) para:
- Formatação de tamanhos de arquivo
- Cálculo de tamanho de diretórios
- Verificação de idade de arquivos

FUNÇÕES:
--------
format_size(size_bytes) -> str
    Converte bytes para formato legível (KB, MB, GB, TB)

get_dir_size(path) -> int
    Calcula tamanho total de um diretório recursivamente

is_old_file(file_path, days=7) -> bool
    Verifica se arquivo foi modificado há mais de X dias

is_old_or_inactive(path, days=30) -> bool
    Verifica se diretório está inativo há mais de X dias

EXEMPLOS:
---------
>>> from utils.file_utils import format_size, get_dir_size
>>> size = get_dir_size(Path('/tmp/cache'))
>>> print(f"Cache: {format_size(size)}")
Cache: 145.3 MB

>>> from utils.file_utils import is_old_file
>>> if is_old_file(Path('/tmp/log.txt'), days=7):
...     print("Log file is older than 7 days")

AUTOR: Pedro Montezuma
DATA: 6 de dezembro de 2025
"""

import os
import time
from pathlib import Path


def format_size(size_bytes):
    """Formata tamanho em bytes para formato legível"""
    for unit in ['B', 'KB', 'MB', 'GB']:
        if size_bytes < 1024.0:
            return f"{size_bytes:.1f} {unit}"
        size_bytes /= 1024.0
    return f"{size_bytes:.1f} TB"


def get_dir_size(path):
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


def is_old_file(file_path, days=7):
    """Verifica se um arquivo é antigo"""
    try:
        mtime = file_path.stat().st_mtime
        age_days = (time.time() - mtime) / (24 * 3600)
        return age_days > days
    except:
        return False


def is_old_or_inactive(path, days=30):
    """Verifica se um diretório é antigo ou inativo"""
    try:
        # Verifica a data de modificação mais recente
        mtime = path.stat().st_mtime
        age_days = (time.time() - mtime) / (24 * 3600)
        return age_days > days
    except:
        return False
