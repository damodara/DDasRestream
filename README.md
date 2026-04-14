# DDasRestream

Веб-интерфейс для управления RTMP-ретрансляциями через Nginx с модулем RTMP.

## Запуск проекта

1. Убедитесь, что у вас установлены Docker и docker-compose
2. Создайте файл `.env` в корневой директории проекта:
```bash
cd /Users/damodaraguranov/Desktop/DDasRestream
cat > .env << 'EOL'
ADMIN_USER=admin
ADMIN_PASS=securepass123
SECRET_KEY=my-very-secret-key-change-me
EOL
```

3. Запустите проект:
```bash
docker-compose -f docker-compose.yml up --build
```

## Переменные окружения

Проект использует следующие переменные окружения, которые можно задать в файле `.env`:

- `ADMIN_USER` - имя пользователя для входа в веб-интерфейс
- `ADMIN_PASS` - пароль для входа в веб-интерфейс
- `SECRET_KEY` - секретный ключ Flask для подписи сессий

### Генерация SECRET_KEY

Для генерации надежного SECRET_KEY используйте один из следующих способов:

**Через Python:**
```python
import secrets
print(secrets.token_hex(32))
```

**Через командную строку:**
```bash
python -c "import secrets; print(secrets.token_hex(32))"
```

**Через OpenSSL:**
```bash
openssl rand -hex 32
```

Перед запуском контейнеров необходимо дать право на выполнение скрипту `watch-reload.sh`, который отслеживает изменения в папке с push-конфигами и перезагружает Nginx.

В терминале, из корневой папки проекта, выполните:

```bash
chmod +x nginx/watch-reload.sh
```

## Доступ к приложению

После запуска:
- Веб-интерфейс: http://localhost:5000
- RTMP сервер: rtmp://localhost:1935
- HTTP (статистика): http://localhost:8080

## Функциональность

Веб-интерфейс позволяет:
- Добавлять, редактировать и удалять push-адреса RTMP для рестрима
- Все изменения автоматически применяются к Nginx без перезагрузки контейнера

Конфигурация push-адресов хранится в volume и доступна обоим контейнерам.