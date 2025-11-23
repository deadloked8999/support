# Инструкция по развертыванию бота на сервере

## Подключение к серверу

```bash
ssh root@193.46.217.83
# Пароль: mT5ggteE
```

## Автоматическая установка (рекомендуется)

1. Подключитесь к серверу
2. Загрузите скрипт развертывания:

```bash
cd /tmp
wget https://raw.githubusercontent.com/deadloked8999/support/main/deploy.sh
chmod +x deploy.sh
./deploy.sh
```

Или вручную скопируйте содержимое `deploy.sh` на сервер и выполните.

## Ручная установка

### 1. Создать директорию для ботов

```bash
mkdir -p /opt/bots
cd /opt/bots
```

### 2. Клонировать репозиторий

```bash
git clone https://github.com/deadloked8999/support.git starlink_bot
cd starlink_bot
```

### 3. Создать виртуальное окружение

```bash
python3 -m venv venv
source venv/bin/activate
```

### 4. Установить зависимости

```bash
pip install --upgrade pip
pip install -r requirements.txt
```

### 5. Настроить конфигурацию

Отредактируйте `config.py`:
```bash
nano config.py
```

Убедитесь, что:
- `BOT_TOKEN` - правильный токен бота
- `ADMIN_IDS` - ID администраторов
- `ADMIN_PASSWORD` - пароль для админ-панели

### 6. Создать systemd service

Создайте файл `/etc/systemd/system/starlink_bot.service`:

```ini
[Unit]
Description=Starlink Bot Telegram
After=network.target

[Service]
Type=simple
User=root
WorkingDirectory=/opt/bots/starlink_bot
Environment="PATH=/opt/bots/starlink_bot/venv/bin"
ExecStart=/opt/bots/starlink_bot/venv/bin/python /opt/bots/starlink_bot/main.py
Restart=always
RestartSec=10
StandardOutput=append:/opt/bots/starlink_bot/logs/bot.log
StandardError=append:/opt/bots/starlink_bot/logs/bot_error.log

[Install]
WantedBy=multi-user.target
```

### 7. Запустить бота

```bash
# Создать директорию для логов
mkdir -p logs

# Перезагрузить systemd
systemctl daemon-reload

# Запустить бота
systemctl start starlink_bot

# Включить автозапуск
systemctl enable starlink_bot

# Проверить статус
systemctl status starlink_bot
```

## Управление ботом

```bash
# Запустить
systemctl start starlink_bot

# Остановить
systemctl stop starlink_bot

# Перезапустить
systemctl restart starlink_bot

# Статус
systemctl status starlink_bot

# Логи
journalctl -u starlink_bot -f
# или
tail -f /opt/bots/starlink_bot/logs/bot.log
```

## Обновление бота

```bash
cd /opt/bots/starlink_bot
git pull
source venv/bin/activate
pip install -r requirements.txt
systemctl restart starlink_bot
```

## Структура директорий для нескольких ботов

```
/opt/bots/
├── starlink_bot/          # Этот бот
│   ├── main.py
│   ├── config.py
│   ├── database.py
│   ├── venv/
│   └── logs/
├── other_bot/             # Другой бот
│   ├── main.py
│   ├── venv/
│   └── logs/
└── another_bot/           # Еще один бот
    ├── main.py
    ├── venv/
    └── logs/
```

Каждый бот изолирован в своей директории с собственным виртуальным окружением и логами.


