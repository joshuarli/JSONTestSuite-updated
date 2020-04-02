FROM python:3.7.7-slim-buster

RUN pip install "python-rapidjson==0.9.1"

COPY main.py /tmp

ENTRYPOINT ["/tmp/main.py", "/tmp/test-payload.json"]
