FROM python:3.7.7-slim-buster

RUN pip install "ujson==2.0.3"

COPY main.py /tmp

ENTRYPOINT ["/tmp/main.py", "/tmp/test-payload.json"]
