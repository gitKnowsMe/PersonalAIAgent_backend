"""
PyInstaller hook for app.db modules

This hook ensures that the portable database modules are properly included
in the executable build.
"""

from PyInstaller.utils.hooks import collect_all

# Collect all app.db modules
datas, binaries, hiddenimports = collect_all('app.db')

# Add specific portable database modules
hiddenimports.extend([
    'app.db.database_portable',
    'app.db.models_portable',
    'app.db.database',
    'app.db.models',
])

# Ensure SQLAlchemy dialects are included
hiddenimports.extend([
    'sqlalchemy.dialects.sqlite',
    'sqlalchemy.dialects.postgresql',
    'sqlalchemy.dialects.postgresql.psycopg2',
])