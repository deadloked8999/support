#!/bin/bash

BOT_NAME="starlink_bot"
BOT_DIR="/opt/bots/$BOT_NAME"
REPO_URL="https://github.com/deadloked8999/support.git"

echo "🚀 Установка бота $BOT_NAME на сервер..."

# Создаем директорию для ботов
mkdir -p /opt/bots

# Клонируем репозиторий
if [ -d "$BOT_DIR" ]; then
    echo "📁 Директория уже существует, обновляю..."
    cd $BOT_DIR
    git pull
else
    echo "📥 Клонирую репозиторий..."
    git clone $REPO_URL $BOT_DIR
    cd $BOT_DIR
fi

# Создаем виртуальное окружение
if [ ! -d "venv" ]; then
    echo "🐍 Создаю виртуальное окружение..."
    python3 -m venv venv
fi

# Активируем окружение и устанавливаем зависимости
echo "📦 Устанавливаю зависимости..."
source venv/bin/activate
pip install --upgrade pip
pip install -r requirements.txt

# Создаем директорию для логов
mkdir -p logs

# Создаем systemd service файл
echo "⚙️ Создаю systemd service..."
cat > /etc/systemd/system/$BOT_NAME.service << EOF
[Unit]
Description=Starlink Bot Telegram
After=network.target

[Service]
Type=simple
User=root
WorkingDirectory=$BOT_DIR
Environment="PATH=$BOT_DIR/venv/bin"
ExecStart=$BOT_DIR/venv/bin/python $BOT_DIR/main.py
Restart=always
RestartSec=10
StandardOutput=append:$BOT_DIR/logs/bot.log
StandardError=append:$BOT_DIR/logs/bot_error.log

[Install]
WantedBy=multi-user.target
EOF

# Перезагружаем systemd
systemctl daemon-reload

echo "✅ Бот установлен!"
echo ""
echo "Для запуска бота:"
echo "  systemctl start $BOT_NAME"
echo ""
echo "Для автозапуска при перезагрузке:"
echo "  systemctl enable $BOT_NAME"
echo ""
echo "Просмотр статуса:"
echo "  systemctl status $BOT_NAME"
echo ""
echo "Просмотр логов:"
echo "  journalctl -u $BOT_NAME -f"
echo "  или"
echo "  tail -f $BOT_DIR/logs/bot.log"

