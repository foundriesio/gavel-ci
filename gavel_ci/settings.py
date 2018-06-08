# Copyright (C) 2018 Open Source Foundries
# Author: Andy Doan <andy@opensourcefoundries.com>

import os

SQLALCHEMY_TRACK_MODIFICATIONS = False
SQLALCHEMY_DATABASE_URI = os.environ.get(
    'SQLALCHEMY_DATABASE_URI', 'sqlite:////tmp/test.db')

SECRET_KEY = os.environ.get('SESSION_SECRET', 'NotSafe')

GITHUB_CLIENT_ID = os.environ.get('GITHUB_CLIENT_ID')
GITHUB_CLIENT_SECRET = os.environ.get('GITHUB_CLIENT_SECRET')

JOBSERV_URL = os.environ.get('JOBSERV_URL')
if not JOBSERV_URL:
    raise ValueError('JOBSERV_URL environment variable not defined')

if JOBSERV_URL[-1] == '/':
    # strip off trailing slash, to make url joining easy in code
    JOBSERV_URL = JOBSERV_URL[:-1]
