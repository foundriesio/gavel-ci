FROM jobserv

ARG GAVEL_VERSION=?
ENV APP_VERSION="$GAVEL_VERSION"

ENV PYTHONPATH=/srv/gavel-ci:/srv/jobserv

RUN mkdir -p /srv/gavel-ci
COPY ./docker_run.sh /srv/gavel-ci/docker_run.sh
COPY ./gavel_ci /srv/gavel-ci/gavel_ci
COPY ./gavel_db /srv/gavel-ci/gavel_db
COPY ./jobserv_gavel_ci /srv/gavel-ci/jobserv_gavel_ci
COPY ./migrations /srv/gavel-ci/migrations

RUN pip3 install Flask-Dance[sqla]==1.0.0 Flask-Login==0.4.1 pyjwt==1.6.4
