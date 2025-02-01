FROM python:3.10

WORKDIR /app

RUN pip install gunicorn==20.1.0

COPY requirements.txt .

RUN pip install --upgrade pip
RUN pip install -r requirements.txt --no-cache-dir

COPY . .

CMD ["sh", "-c", "python manage.py makemigrations  && \
                   python manage.py migrate --noinput && \
                   python manage.py collectstatic --no-input --clear --verbosity 2 && \
                   cp -r /app/media/. /media/ && \
                   cp -r /app/collected_static/. /backend_static/static/ && \
                   cp -r /app/docs/. /docs/ && \
                   python manage.py create_superusers && \
                   python manage.py import_ingredients && \
                   python manage.py import_tags && \
                   python manage.py import_recipes && \
                   gunicorn --bind 0.0.0.0:8000 backend.wsgi"]
