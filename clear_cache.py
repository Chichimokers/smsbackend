"""
Script para limpiar caché de URLs y reiniciar el servidor.
"""

import os
import sys
import django
from django.conf import settings

# Setup Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
django.setup()

print("🔄 Limpiando caché de URLs de Django...")

# Eliminar archivos de caché
import shutil
cache_dirs = [
    '__pycache__',
    '*.pyc',
    'migrations/__pycache__',
    'apps/**/__pycache__',
]

for pattern in cache_dirs:
    print(f"🗑 Eliminando {pattern}...")
    os.system(f'find . -name "__pycache__" -type d -exec rm -rf {{}} + 2>/dev/null || true')
    os.system(f'find . -name "*.pyc" -delete 2>/dev/null || true')

# Resetear URLs
print("🔄 Reseteando URLs...")
try:
    from django.urls import get_resolver
    resolver = get_resolver()
    resolver.url_patterns = []
    print("✅ URLs reseteadas")
except Exception as e:
    print(f"❌ Error reseteando URLs: {e}")

print("✅ Caché limpiado. Reinicia el servidor.")