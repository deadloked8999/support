#!/usr/bin/env python3
# Тестовый скрипт для проверки импортов и базовой функциональности

import sys
print("Python version:", sys.version)
print("Python path:", sys.executable)

print("\n1. Проверка базовых импортов...")
try:
    import os
    print("✓ os imported")
except Exception as e:
    print(f"✗ os failed: {e}")

try:
    from datetime import datetime
    print("✓ datetime imported")
except Exception as e:
    print(f"✗ datetime failed: {e}")

print("\n2. Проверка telegram импортов...")
try:
    from telegram import Update
    print("✓ telegram.Update imported")
except Exception as e:
    print(f"✗ telegram.Update failed: {e}")
    import traceback
    traceback.print_exc()

try:
    from telegram.ext import Application
    print("✓ telegram.ext.Application imported")
except Exception as e:
    print(f"✗ telegram.ext.Application failed: {e}")
    import traceback
    traceback.print_exc()

print("\n3. Проверка config...")
try:
    from config import BOT_TOKEN
    print(f"✓ config imported, BOT_TOKEN length: {len(BOT_TOKEN)}")
except Exception as e:
    print(f"✗ config failed: {e}")
    import traceback
    traceback.print_exc()

print("\n4. Проверка database...")
try:
    from database import init_database
    print("✓ database imported")
    init_database()
    print("✓ database initialized")
except Exception as e:
    print(f"✗ database failed: {e}")
    import traceback
    traceback.print_exc()

print("\n5. Создание Application...")
try:
    from config import BOT_TOKEN
    from telegram.ext import Application
    application = Application.builder().token(BOT_TOKEN).build()
    print("✓ Application created")
except Exception as e:
    print(f"✗ Application creation failed: {e}")
    import traceback
    traceback.print_exc()

print("\n6. Импорт main.py...")
try:
    import main
    print("✓ main.py imported successfully")
except Exception as e:
    print(f"✗ main.py import failed: {e}")
    import traceback
    traceback.print_exc()

print("\n=== Все проверки завершены ===")

