# Books-DRF

API-каталог книг на Django + Django REST Framework. Поддерживает авторов,
лаики, рейтинги (1–5), фильтрацию и сортировку, а также GitHub OAuth2.

## Требования

- Python 3.14
- PostgreSQL (для разработки/продакшена) или SQLite (для тестов без БД)

## Установка

```bash
cd /home/alex/Projects/Educational_projects/Books-DRF
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

Скопируйте `.env.example` в `.env` и заполните переменные:

```bash
cp .env.example .env
```

### Переменные окружения (`.env`)

| Переменная | Описание | По умолчанию |
|---|---|---|
| `DJANGO_SECRET_KEY` | Секретный ключ Django (обязателен в проде) | — |
| `DJANGO_DEBUG` | Вкл/выкл режим отладки | `True` |
| `ALLOWED_HOSTS` | Разрешённые хосты через запятую | `*` (в debug) |
| `DB_NAME` | Имя БД PostgreSQL | `books_db` |
| `DB_USER` | Пользователь PostgreSQL | `books_user` |
| `DB_PASSWORD` | Пароль PostgreSQL | `books_password` |
| `DB_HOST` | Хост PostgreSQL | `localhost` |
| `DB_PORT` | Порт PostgreSQL | `5432` |
| `SOCIAL_AUTH_GITHUB_KEY` | Client ID GitHub OAuth2 | — |
| `SOCIAL_AUTH_GITHUB_SECRET` | Client Secret GitHub OAuth2 | — |

## Запуск сервера

```bash
DJANGO_SETTINGS_MODULE=books.settings .venv/bin/python manage.py runserver
```

API доступно по `http://127.0.0.1:8000/api/books/`.

## Запуск тестов

Для локального запуска без PostgreSQL используется SQLite через `DJANGO_TEST=True`:

```bash
DJANGO_SETTINGS_MODULE=books.settings DJANGO_TEST=True .venv/bin/python -m pytest store/tests/
```

Для запуска через PostgreSQL убедитесь, что сервер БД запущен и переменные `DB_*` заданы в `.env`.

## Основные endpoints

- `GET/POST /api/books/` — список и создание книг
- `GET/PUT/PATCH/DELETE /api/books/<id>/` — чтение/обновление/удаление книги
- `POST/DELETE /api/books/<id>/like/` — лайк/снятие лайка (требуется авторизация)
- `GET/POST/DELETE /api/books/<id>/rating/` — моя оценка книги (требуется авторизация)
- `GET/POST/PUT/PATCH/DELETE /api/ratings/` — мои оценки (требуется авторизация)
- `GET /api/ratings/<id>/` — чтение/удаление своей оценки
- `GET /oauth/login/github/` — вход через GitHub OAuth2
