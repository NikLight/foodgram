# Сайт рецептов

Сервис для обмена рецептами, где пользователи могут создавать, просматривать, 
редактировать и сохранять свои любимые рецепты.
![Сайт рецептов](https://github.com/NikLight/foodgram/blob/main/1.jpg)


[https://foodgramya.hopto.org](https://foodgramya.hopto.org)

## Автор

*   ФИО: **
*   GitHub: [https://github.com/niklight](https://github.com/niklight)

## Технологический стек

*   **Python:** Язык программирования, используемый для серверной части приложения.
*   **Django:** Web-фреймворк для разработки серверной части.
*   **Django REST Framework:** Инструмент для создания API.
*   **PostgreSQL:** База данных.
*   **Nginx:** Web-сервер.
*   **Gunicorn:** WSGI-сервер.
*   **Docker:** Инструмент контейнеризации.
*   **GitHub Actions:** Сервис CI/CD.


## CI/CD (GitHub Actions)
=======

Описание workflow развертывания приложения на сервере. 
*(Опишите ваш workflow, например: 
"Workflow автоматически запускается при каждом push в ветку `main`, 
собирает Docker образ, 
запускает тесты и разворачивает приложение на сервере.")*

## Локальное развертывание с Docker

1.  Клонирование репозитория:

    ```bash
    git clone [https://github.com/ваш-логин/foodgram.git](https://github.com/niklight/foodgram.git)
    ```

2.  Переход в папку с `docker-compose.yml`:

    ```bash
    cd foodgram
    ```

3.  Заполнение `.env`:

    Создайте файл `.env` в корневой папке проекта и заполните его переменными окружения. Пример:

    ```
    POSTGRES_NAME=foodgram_db
    POSTGRES_USER=foodgram
    POSTGRES_PASSWORD=your_password
    POSTGRES_HOST=db
    POSTGRES_PORT=5432
    SECRET_KEY=your_secret_key
    ```

4.  Подъем контейнеров:

    ```bash
    docker-compose up -d --build
    ```

5.  Подготовка базы данных:
![Сайт рецептов](https://github.com/NikLight/foodgram/blob/main/2.jpg)

    ```bash
    docker-compose exec web python manage.py migrate
    docker-compose exec web python manage.py createsuperuser # Опционально
    docker-compose exec web python manage.py import_ingredients  # Опционально
    docker-compose exec web python manage.py import_recipes  # Опционально
    docker-compose exec web python manage.py import_tags  # Опционально
    ```

6.  Сборка статики:

    ```bash
    docker-compose exec web python manage.py collectstatic --noinput
    ```

7.  Запуск сервера:

    Сервер будет доступен по адресу `https://foodgramya.hopto.org`.

## Локальное развертывание без Docker

1.  Клонирование репозитория:

    ```bash
    git clone [https://github.com/ваш-логин/foodgram.git](https://github.com/niklight/foodgram.git)
    ```

2.  Переход в папку проекта:

    ```bash
    cd foodgram
    ```

3.  Создание виртуального окружения:

    ```bash
    python3 -m venv .venv
    ```

4.  Активация виртуального окружения:

    ```bash
    source .venv/bin/activate  # Linux/macOS
    .venv\Scripts\activate  # Windows
    ```

5.  Установка зависимостей:

    ```bash
    pip install -r requirements.txt
    ```

6.  Заполнение `.env`:

    Создайте файл `.env` в корневой папке проекта и заполните его переменными окружения. Пример:

    ```
    POSTGRES_NAME=foodgram_db
    POSTGRES_USER=foodgram
    POSTGRES_PASSWORD=your_password
    POSTGRES_HOST=localhost # или 127.0.0.1
    POSTGRES_PORT=5432
    SECRET_KEY=your_secret_key
    # ... другие переменные
    ```

7.  Миграция базы данных и создание суперпользователя:

    ```bash
    python manage.py migrate
    python manage.py createsuperuser # Опционально
    ```

8.  Импорт данных (опционально):

    ```bash
    python manage.py loaddata fixtures.json # или fixtures.json
    ```

9.  Запуск сервера:

    ```bash
    python manage.py runserver
    ```

10. Документация API:

    После запуска сервера документация API будет доступна по адресу: 
    `https://foodgramya.hopto.org/redoc/`

## API

Для взаимодействия с API используйте следующие endpoints:

*   `/api/recipes/`: Получение списка рецептов, создание нового рецепта.
*   `/api/recipes/{id}/`: Получение, изменение и удаление рецепта по ID.
*   `/api/tags/`: Получение списка тегов.
*   `/api/ingredients/`: Получение списка ингредиентов.
*   `/api/users/`: Получение информации о пользователях.

## Лицензия

MIT
