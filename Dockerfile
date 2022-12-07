FROM python:3.9-alpine3.13
LABEL proprietaire="interactivbs.com"

ENV PYTHONUNBUFFERED 1

COPY ./requirements.txt /requirements.txt
COPY ./electron /electron
COPY ./scripts /scripts

WORKDIR /electron
EXPOSE 8000

RUN apk add --no-cache --virtual .build-deps gcc musl-dev

RUN python3.9 -m venv /py && \
    /py/bin/pip install --upgrade pip setuptools wheel && \
    apk add --update --no-cache postgresql-client && \
    apk add --update --no-cache --virtual .temp-deps \
        build-base postgresql-dev musl-dev linux-headers && \
    /py/bin/pip install pyproject-toml && \
    /py/bin/pip install backports.zoneinfo && \
    /py/bin/pip install -r /requirements.txt && \
    adduser --disabled-password --no-create-home ozangue && \
    mkdir -p /vol/web/media && \
    chown -R ozangue:ozangue /vol && \
    chmod -R 755 /vol && \
    chmod -R +x /scripts

ENV PATH="/scripts:/py/bin:$PATH"

USER ozangue

CMD ["run.sh"]