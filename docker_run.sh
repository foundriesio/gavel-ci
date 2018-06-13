#!/bin/sh -e

# Make sure we are in the proper directory to the correct "migrations" folder
# is used.
if [ "$FLASK_APP" == "jobserv_gavel_ci.app:app" ] ; then
	cd /srv/jobserv

	# Create the Fernet key needed for encryption of secrets
	[ -f /data/db-encryption-key ] || python3 -c "from cryptography.fernet import Fernet; print(Fernet.generate_key().decode())" > /data/db-encryption-key
	export SECRETS_FERNET_KEY=$(cat /data/db-encryption-key)
	export LOCAL_STORAGE_KEY=$(python3 -c "import secrets; print(secrets.token_urlsafe())")
else
	cd /srv/gavel-ci
fi

# Create JWT secret needed for UI->JobServ communication
export JWT_SECRET_FILE="${JWT_SECRET_FILE-/data/jwt-secret}"
python3 -c "import secrets; print(secrets.token_urlsafe())" > $JWT_SECRET_FILE

create_flock_script () {
	# /usr/bin/flock uses the "flock" call instead of fcntl.
	# fcntl is required for NFS shares
	cat > /tmp/flock <<EOF
#!/usr/bin/python3
import fcntl
import subprocess
import sys


with open(sys.argv[1], 'a') as f:
    fcntl.flock(f, fcntl.LOCK_EX)
    subprocess.check_call(sys.argv[2:])
EOF
chmod +x /tmp/flock
}

if [ -n "$FLASK_AUTO_MIGRATE" ] ; then
	create_flock_script
	echo "Performing DB migration"
	mkdir -p $(dirname $FLASK_AUTO_MIGRATE)
	/tmp/flock $FLASK_AUTO_MIGRATE flask db upgrade
fi

# if FLASK_DEBUG is defined, we'll run via flask with dynamic reloading of
# code changes to disk. This is helpful for debugging something already in k8s

if [ -z "$FLASK_DEBUG" ] ; then
	if [ -n "$STATSD_HOST" ] ; then
		STATSD="--statsd-host $STATSD_HOST"
	fi
	exec /usr/bin/gunicorn $STATSD -n gavel-ci -w4 -b 0.0.0.0:8000 $FLASK_APP
fi

exec /usr/bin/flask run -h 0.0.0.0 -p 8000
