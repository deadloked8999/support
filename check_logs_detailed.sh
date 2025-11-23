#!/bin/bash
echo "=== Проверка директории logs ==="
ls -la /opt/bots/starlink_bot/logs/ 2>/dev/null || echo "Директория logs не существует!"

echo ""
echo "=== Создание директории logs если её нет ==="
mkdir -p /opt/bots/starlink_bot/logs
chmod 755 /opt/bots/starlink_bot/logs

echo ""
echo "=== Проверка файла bot.log ==="
if [ -f /opt/bots/starlink_bot/logs/bot.log ]; then
    echo "Размер: $(du -h /opt/bots/starlink_bot/logs/bot.log | cut -f1)"
    echo "Последние 50 строк:"
    tail -50 /opt/bots/starlink_bot/logs/bot.log
else
    echo "Файл bot.log не существует!"
fi

echo ""
echo "=== Проверка файла bot_error.log ==="
if [ -f /opt/bots/starlink_bot/logs/bot_error.log ]; then
    echo "Размер: $(du -h /opt/bots/starlink_bot/logs/bot_error.log | cut -f1)"
    echo "Последние 50 строк:"
    tail -50 /opt/bots/starlink_bot/logs/bot_error.log
else
    echo "Файл bot_error.log не существует!"
fi

echo ""
echo "=== Попытка запуска бота вручную ==="
cd /opt/bots/starlink_bot
source venv/bin/activate
timeout 5 python main.py 2>&1 | head -20 || echo "Бот запущен (timeout через 5 секунд)"

