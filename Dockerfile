FROM python:3.8-alpine

ARG BRANCH="develop"
ARG BUILD_VERSION="1.0.0-snapshot"
ARG PROJECT_NAME=

ENV VCB_BRANCH=${BRANCH}
ENV TWITCH_CLIENT_SECRET=
ENV TWITCH_CLIENT_ID=
ENV TWITCH_OAUTH_TOKEN=
ENV PYTHONUNBUFFERED=0
ENV VCB_DB_CONNECTION_STRING=
ENV APP_VERSION=${BUILD_VERSION}

LABEL VERSION="${BUILD_VERSION}"
LABEL BRANCH="${BRANCH}"
LABEL PROJECT_NAME="${PROJECT_NAME}"

COPY ./ /app/
RUN \
	apk update && \
	apk add --update git curl build-base tcl tk && \
	mkdir -p /app /data && \
	pip install --upgrade pip && \
	pip install -r /app/setup/requirements.txt && \
	sed -i "s/APP_VERSION = \"1.0.0-snapshot\"/APP_VERSION = \"${APP_VERSION}\"/g" "/app/bot/cogs/lib/settings.py" && \
	sed -i "s/\"version\": \"1.0.0-snapshot\"/\"version\": \"${APP_VERSION}\"/g" "/app/app.manifest" && \
	apk del git build-base && \
	rm -rf /app/setup && \
	rm -rf /var/cache/apk/*

VOLUME ["/data"]
WORKDIR /app

CMD ["python", "-u", "/app/main.py"]
