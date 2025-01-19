FROM python:3.10

WORKDIR /app

RUN pip install gunicorn==20.1.0

COPY requirements.txt .

RUN pip install -r requirements.txt --no-cache-dir

COPY . .

RUN python manage.py makemigrations
RUN python manage.py migrate --noinput


RUN python manage.py collectstatic --no-input --clear


RUN mkdir -p /media /backend_static/static /docs && \
    chown -R root:root /media /backend_static/static /docs && \
    cp -r /app/media/. /media/ && \
    cp -r /app/collected_static/. /backend_static/static/ && \
    cp -r /app/docs/. /docs/

RUN python manage.py import_ingredients
RUN python manage.py import_tags


CMD ["gunicorn", "--bind", "0.0.0.0:8000", "backend.wsgi"]
