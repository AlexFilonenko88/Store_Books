## Writing to me

- Reply in Russian, even when the project's language is English.
- Before your first reply in a session, open the `plain-writing` skill. Follow it in every text I read: chat replies, reports, PR descriptions, issue comments.

## Запуск тестов

Тесты требуют переменную `DJANGO_SETTINGS_MODULE=books.settings`. По умолчанию проект использует PostgreSQL; для локального запуска без БД включите sqlite через `DJANGO_TEST=True`:

```bash
DJANGO_SETTINGS_MODULE=books.settings DJANGO_TEST=True .venv/bin/python -m pytest store/tests/
```

Для запуска через PostgreSQL убедитесь, что сервер БД запущен и переменные `DB_*` заданы в `.env`.
