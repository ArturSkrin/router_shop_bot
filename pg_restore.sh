#!/bin/bash

CONTAINER="control_bot_db"
DB="control_bot_db"
USER="deploy"
DUMP="backup.dump"
TMP_PATH="/tmp/$DUMP"

if [ ! -f "$DUMP" ]; then
  echo "❌ Файл $DUMP не найден!"
  exit 1
fi

echo "📤 Копируем дамп $DUMP в контейнер $CONTAINER..."
docker cp "$DUMP" "$CONTAINER":"$TMP_PATH" || {
  echo "❌ Ошибка копирования дампа"
  exit 1
}

echo "💣 Удаляем базу $DB..."
docker exec -it "$CONTAINER" dropdb -U "$USER" "$DB" || echo "⚠️ База не существует, продолжаем..."

echo "🧱 Создаём новую базу $DB..."
docker exec -it "$CONTAINER" createdb -U "$USER" "$DB" || {
  echo "❌ Ошибка создания базы!"
  exit 1
}

echo "📥 Восстанавливаем из дампа..."
docker exec -it "$CONTAINER" pg_restore -U "$USER" -d "$DB" "$TMP_PATH" || {
  echo "❌ Ошибка восстановления!"
  exit 1
}

echo "✅ Восстановление завершено."

