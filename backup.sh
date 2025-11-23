#!/bin/bash

# Конфигурация
BOT_DIR="/opt/bots/starlink_bot"
BACKUP_DIR="/opt/bots/starlink_bot/backups"
DB_FILE="$BOT_DIR/bot_data.db"
RETENTION_DAYS=45
DATE=$(date +%Y%m%d_%H%M%S)
BACKUP_FILE="$BACKUP_DIR/starlink_bot_backup_$DATE.db"

# Создаем директорию для бэкапов если не существует
mkdir -p "$BACKUP_DIR"

# Проверяем существование БД
if [ ! -f "$DB_FILE" ]; then
    echo "Ошибка: База данных не найдена: $DB_FILE"
    exit 1
fi

# Создаем бэкап
echo "Создание бэкапа базы данных..."
cp "$DB_FILE" "$BACKUP_FILE"

# Сжимаем бэкап для экономии места
if command -v gzip &> /dev/null; then
    echo "Сжатие бэкапа..."
    gzip "$BACKUP_FILE"
    BACKUP_FILE="${BACKUP_FILE}.gz"
fi

# Проверяем успешность создания бэкапа
if [ -f "$BACKUP_FILE" ]; then
    BACKUP_SIZE=$(du -h "$BACKUP_FILE" | cut -f1)
    echo "✅ Бэкап успешно создан: $BACKUP_FILE (размер: $BACKUP_SIZE)"
else
    echo "❌ Ошибка: Бэкап не был создан"
    exit 1
fi

# Удаляем старые бэкапы (старше RETENTION_DAYS дней)
echo "Удаление бэкапов старше $RETENTION_DAYS дней..."
find "$BACKUP_DIR" -name "starlink_bot_backup_*.db*" -type f -mtime +$RETENTION_DAYS -delete

# Показываем информацию о текущих бэкапах
BACKUP_COUNT=$(find "$BACKUP_DIR" -name "starlink_bot_backup_*.db*" -type f | wc -l)
TOTAL_SIZE=$(du -sh "$BACKUP_DIR" | cut -f1)
echo "Всего бэкапов: $BACKUP_COUNT"
echo "Общий размер бэкапов: $TOTAL_SIZE"

# Логируем в файл
LOG_FILE="$BOT_DIR/logs/backup.log"
mkdir -p "$BOT_DIR/logs"
echo "$(date '+%Y-%m-%d %H:%M:%S') - Бэкап создан: $BACKUP_FILE (размер: $BACKUP_SIZE)" >> "$LOG_FILE"


