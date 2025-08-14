FROM python:3.6.8

WORKDIR /app

RUN mkdir ./conf
COPY ./conf/*.json ./conf/
COPY ./retriever.py .
COPY ./util.py .


COPY ./requirements.txt .
RUN pip3 install -r requirements.txt



