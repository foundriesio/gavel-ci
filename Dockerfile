FROM alpine:3.19

ARG GAVEL_VERSION=?
ENV APP_VERSION="$GAVEL_VERSION"
ENV FLASK_APP="gavel_ci.app:app"

ARG BUILD_PKGS="python3-dev py3-pip musl-dev gcc libffi-dev openssl-dev"

ENV PYTHONPATH=/srv/gavel-ci
WORKDIR /srv/gavel-ci

COPY ./wait-for /srv/gavel-ci/
COPY ./requirements.txt /srv/gavel-ci/
COPY ./docker_run.sh /srv/gavel-ci/
COPY ./gavel_ci /srv/gavel-ci/gavel_ci
COPY ./gavel_jwt.py /srv/gavel-ci/
COPY ./gavel_permissions.py /srv/gavel-ci/
COPY ./migrations /srv/gavel-ci/migrations

RUN apk --no-cache add python3 openssl $BUILD_PKGS \
	&& pip3 install --break-system-packages -r requirements.txt \
	&& apk del $BUILD_PKGS
