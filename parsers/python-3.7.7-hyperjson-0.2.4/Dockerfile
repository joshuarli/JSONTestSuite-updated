FROM python:3.7.7-slim-buster

RUN pip install "hyperjson==0.2.4"

COPY main.py /tmp

ENTRYPOINT ["/tmp/main.py", "/tmp/test-payload.json"]
