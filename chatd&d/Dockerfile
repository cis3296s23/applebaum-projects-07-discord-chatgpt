FROM python:3.10-alpine

ENV PYTHONUNBUFFERED 1

WORKDIR /Bot
COPY requirements.txt requirements.txt
RUN pip3 install -r requirements.txt
COPY . .

CMD ["python3", "main.py"]