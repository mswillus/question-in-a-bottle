FROM python:3.8-alpine

WORKDIR /srv/question-in-a-bottle

COPY requirements.txt requirements.txt
COPY src app

EXPOSE 8080/tcp

RUN pip install -r requirements.txt

CMD ["waitress-serve", "--port=8080", "--call", "app:app.create_app"]
