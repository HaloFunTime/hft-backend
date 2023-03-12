FROM python:3.11-slim-bullseye

RUN apt-get -y update\
 && apt-get -y install libpq-dev gcc\
 && apt-get -y autoremove

RUN mkdir -p /app
WORKDIR /app

COPY requirements.txt .
RUN pip install -r requirements.txt
COPY . .
RUN python manage.py collectstatic --noinput

EXPOSE 8000
CMD ["gunicorn", "--access-logfile", "-", "--bind", "0.0.0.0:8000", "--workers", "2", "config.wsgi"]
