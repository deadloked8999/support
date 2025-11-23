# Проверка работы бота на сервере

## Шаги для диагностики:

1. Подключитесь к серверу:
```bash
ssh root@193.46.217.83
# Пароль: mT5ggteE
```

2. Перейдите в директорию бота:
```bash
cd /opt/bots/starlink_bot
```

3. Обновите код:
```bash
git pull
```

4. Проверьте статус бота:
```bash
systemctl status starlink_bot
```

5. Проверьте логи бота:
```bash
journalctl -u starlink_bot -n 50 --no-pager
```

6. Если бот не запущен или есть ошибки, перезапустите:
```bash
systemctl restart starlink_bot
```

7. Снова проверьте логи:
```bash
journalctl -u starlink_bot -f
```

8. В другом терминале отправьте команду /start боту и смотрите логи в реальном времени.

## Что искать в логах:

- `DEBUG: start command received from user XXX` - команда получена
- `DEBUG: user_data cleared for user XXX` - контекст очищен
- `DEBUG: start message sent to user XXX` - сообщение отправлено
- Любые ошибки (Exception, Error, Traceback)

## Возможные проблемы:

1. **Бот не запущен** - запустите через systemctl
2. **Ошибки в коде** - проверьте логи на наличие ошибок
3. **Проблемы с базой данных** - проверьте права доступа к файлу bot_data.db
4. **Проблемы с токеном** - убедитесь, что токен правильный в config.py

