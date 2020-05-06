#!/bin/bash

SECRETS_PATH=/data/secrets
SHARED_VOLUME=gavel-ci_shared_artifacts
SCRIPT_PATH="$( cd "$(dirname "$0")" >/dev/null 2>&1 ; pwd -P )"
IMG_NAME=gavel-ci

if [ $# -eq 0 ]; then
    action=""
else
   action=$1
    shift
fi

setup() {
  setup_docker
  setup_artifacts
  echo "
  The Gavel-CI development instance is almost ready to start up!
  Review the README for next steps :)
  NOTE: your CA root is '$(mkcert -CAROOT)'
  "
}


setup_artifacts() {
  echo "setting up artifacts..."

  existing_volume=$(docker volume ls --filter name=${SHARED_VOLUME} -q)
  if ! [[ $existing_volume ]]; then
    docker volume create --driver local $SHARED_VOLUME
  fi

  tmp_dir=$(mktemp -d -t artifacts-XXXXXXXXXX)
  mute pushd "$tmp_dir" || exit 1
  setup_certs
  setup_keys
  setup_env
  mute popd || exit 1
  rm -rf $tmp_dir
}

setup_certs() {
  echo "setting up certs..."
  check_commands_exist openssl mkcert
  mute mkcert -install
  if [ $? -ne 0 ]; then
    echo "failed to make tls certificate"
    exit 1
  fi
  for entry in ui:gavelci.us api:api.gavelci.us ; do
    svc=${entry%:*}
    uri=${entry#*:}
    mute mkcert $uri
    openssl crl2pkcs7 -nocrl -certfile ${uri}.pem | openssl pkcs7 -print_certs -out tls-${svc}.crt
    openssl pkey -in ${uri}-key.pem -out tls-${svc}.key
    volume_copy tls-${svc}.crt ${SHARED_VOLUME}:${SECRETS_PATH}/${svc}.crt
    volume_copy tls-${svc}.key ${SHARED_VOLUME}:${SECRETS_PATH}/${svc}.key
  done
}

setup_docker() {
  echo "setting up docker..."
  docker build --build-arg APP_VERSION=local -t $IMG_NAME ./
  docker run -it --rm --mount type=volume,src=${SHARED_VOLUME},dst=/data $IMG_NAME mkdir -p $SECRETS_PATH
}

setup_env() {
  # sets files that end with '*_ENV' as entries in '.env' file docker uses
  # backs up any existing '.env' to '.env.bak' before replacing
  echo "setting up .env..."
  envfile="${SCRIPT_PATH}/.env"
  cat "$envfile" 1> "${envfile}.bak" 2> /dev/null
  cat "${envfile}.example" > "${envfile}"

  for f in *_ENV ; do
    echo "${f%_ENV}=$(cat ${f})" >> $envfile
  done
}

setup_keys() {
  echo "setting up keys and tokens..."
  # db-key: reuse if existing
  FERNET="FERNET_SECRET_ENV"
  volume_copy ${SHARED_VOLUME}:${SECRETS_PATH}/db-key $FERNET
  [ -f $FERNET ] || python3 -c "from cryptography.fernet import Fernet; print(Fernet.generate_key().decode())" > $FERNET
  volume_copy $FERNET ${SHARED_VOLUME}:${SECRETS_PATH}/db-key
  # local storage key: overwrite each time
  LOCAL_STORAGE_KEY="LOCAL_STORAGE_KEY_ENV"
  python3 -c "import secrets; print(secrets.token_urlsafe())" > $LOCAL_STORAGE_KEY
  # jwt secret: overwrite each time
  JWT_SECRET="JWT_SECRET"
  python3 -c "import secrets; print(secrets.token_urlsafe())" > $JWT_SECRET
  volume_copy $JWT_SECRET ${SHARED_VOLUME}:${SECRETS_PATH}/jwt-secret
}

purge() {
  echo "purge in process..."
  docker-compose stop
  mute docker rm --force $(docker ps --filter ancestor=${IMG_NAME} -aq)
  mute docker rm --force $(docker ps --filter name=${IMG_NAME} -aq)
  mute docker rmi --force $(docker images --filter reference=${IMG_NAME} -q)
  mute docker volume rm --force $(docker volume ls --filter name=${IMG_NAME} -q)
  echo "purge complete."
}


volume_copy() {
  # copied from https://github.com/moby/moby/issues/25245
  SOURCE=$1
  DEST=$2
  check_commands_exist docker
  SOURCE_ARR=(${SOURCE//:/ })
  DEST_ARR=(${DEST//:/ })

  if [[ ${#SOURCE_ARR[@]} -eq 2 && ${#DEST_ARR[@]} -eq 1 ]]; then
    # volume --> host
    VOL=${SOURCE_ARR[0]}
    VOL_PATH=${SOURCE_ARR[1]}
    HOST_PATH=${DEST_ARR[0]}
    mute docker container create --name docker_volume_cp --mount type=volume,src=${VOL},dst=/data $IMG_NAME
    mute docker cp docker_volume_cp:$VOL_PATH $HOST_PATH
    mute docker rm docker_volume_cp
  elif [[ ${#SOURCE_ARR[@]} -eq 1 && ${#DEST_ARR[@]} -eq 2 ]]; then
    # host --> volume
    VOL=${DEST_ARR[0]}
    VOL_PATH=${DEST_ARR[1]}
    HOST_PATH=${SOURCE_ARR[0]}
    mute docker container create --name docker_volume_cp --mount type=volume,src=${VOL},dst=/data $IMG_NAME
    mute docker cp $HOST_PATH docker_volume_cp:$VOL_PATH
    mute docker rm docker_volume_cp
  else
    echo "Usage:"
    echo " volume --> host: $0 VOLUME:VOL_PATH HOST_PATH"
    echo " host --> volume: $0 HOST_PATH VOLUME:VOL_PATH"
  fi
}

mute() {
  temp_file=$(mktemp)
  "$@" &> temp_file
  if [[ $? -ne 0 ]]; then
    cat "$temp_file"
  fi
  rm "$temp_file"
}

check_commands_exist() {
  for cmd in "$@"; do
    if ! [ -x "$(command -v ${cmd})" ]; then
      echo "Error: required 'cmd' application not installed." >&2
      exit 1
    fi
  done
}

case "${action}" in
    setup)
      setup
      ;;
    purge)
      purge
      ;;
    *)
        echo $"Usage: $0 "
        echo "  Commands:"
        echo "     setup "
        echo "     purge "
        echo ""
        exit 1
esac