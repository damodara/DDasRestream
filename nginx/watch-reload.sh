#!/bin/sh
# Устанавливаем inotifywait (если не установлен)
if ! command -v inotifywait >/dev/null 2>&1; then
    apk add --no-cache inotify-tools
fi

while inotifywait -e modify,create,delete,move --format '%w%f' /etc/nginx/rtmp-push/; do
    echo "Обнаружено изменение в /etc/nginx/rtmp-push/, выполняется перезагрузка nginx..."
    nginx -s reload
done