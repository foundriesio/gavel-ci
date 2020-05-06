#!/bin/sh -e

if [ -z "$GITHUB_CLIENT_ID" ] ; then
	echo "Missing GITHUB_CLIENT_ID"
	exit 1
fi
if [ -z "$GITHUB_CLIENT_SECRET" ] ; then
	echo "Missing GITHUB_CLIENT_SECRET"
	exit 1
fi
for x in api.crt api.key ui.crt ui.key ; do
	if [ ! -f /data/secrets/$x ] ; then
		echo "Missing required SSL file(s)"
		exit 1
	fi
done
if [ ! -f "${JWT_SECRET_FILE}" ] ; then
  echo "Missing JWT file"
  exit 1
fi

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
