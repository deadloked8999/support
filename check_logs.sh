#!/bin/bash
# Скрипт для проверки логов бота

echo "=== Статус сервиса ==="
systemctl status starlink_bot --no-pager -l

echo ""
echo "=== Последние 100 строк логов ==="
journalctl -u starlink_bot -n 100 --no-pager

echo ""
echo "=== Логи с ошибками ==="
journalctl -u starlink_bot --no-pager | grep -i "error\|exception\|traceback\|failed\|ошибка" | tail -20

echo ""
echo "=== Попытка запуска вручную ==="
cd /opt/bots/starlink_bot
source venv/bin/activate
python main.py 2>&1 | head -50

