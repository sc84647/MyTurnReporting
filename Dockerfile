FROM python:3.11-slim
ENV TZ="Europe/London"

WORKDIR /app

COPY requirements.txt .

RUN pip install -r requirements.txt

COPY main.py .
COPY *.json .

RUN apt-get update && apt-get install -y cron dos2unix
COPY crontab /etc/cron.d/crontab
RUN chmod 0644 /etc/cron.d/crontab
RUN dos2unix /etc/cron.d/crontab
RUN /usr/bin/crontab /etc/cron.d/crontab

#CMD [ "python", "./main.py", "--persist" ]
CMD [ "cron", "-f" ]



