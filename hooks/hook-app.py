"""
PyInstaller hook for Personal AI Agent app modules
Ensures proper module discovery and prevents duplicate file issues
"""

from PyInstaller.utils.hooks import collect_all

# Collect all app modules
datas, binaries, hiddenimports = collect_all('app')

# Additional specific imports that might be missed
hiddenimports.extend([
    'app.db.database_portable',
    'app.core.config',
    'app.main',
])