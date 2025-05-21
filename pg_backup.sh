#!/bin/bash

CONTAINER="control_bot_db"
DB="control_bot_db"
USER="deploy"
DUMP="backup.dump"

echo "📦 Создаём дамп базы $DB из контейнера $CONTAINER..."
docker exec $CONTAINER pg_dump -U $USER -F c -d $DB > $DUMP || {
  echo "❌ Ошибка создания дампа!"
  exit 1
}

echo "✅ Бэкап сохранён в $DUMP"

