#!/bin/sh -e

cd /srv/jobserv

[ -d /data/secrets ] || mkdir /data/secrets

# Create the Fernet key needed for encryption of secrets
FERNET_FILE="/data/secrets/db-key"
[ -f $FERNET_FILE ] || python3 -c "from cryptography.fernet import Fernet; print(Fernet.generate_key().decode())" > $FERNET_FILE
export SECRETS_FERNET_KEY=$(cat $FERNET_FILE)
export LOCAL_STORAGE_KEY=$(python3 -c "import secrets; print(secrets.token_urlsafe())")

# Create JWT secret needed for UI->JobServ communication
export JWT_SECRET_FILE="${JWT_SECRET_FILE-/data/secrets/jwt-secret}"
python3 -c "import secrets; print(secrets.token_urlsafe())" > $JWT_SECRET_FILE

exec /srv/jobserv/docker_run.sh
