FROM python:3.7.7-slim-buster

RUN pip install "simplejson==3.17.0"

COPY main.py /tmp

ENTRYPOINT ["/tmp/main.py", "/tmp/test-payload.json"]
