# Copyright (C) 2018 Open Source Foundries
# Author: Andy Doan <andy@opensourcefoundries.com>

import os

SQLALCHEMY_TRACK_MODIFICATIONS = False
SQLALCHEMY_DATABASE_URI = os.environ.get(
    'SQLALCHEMY_DATABASE_URI', 'sqlite:////tmp/test.db')

SECRET_KEY = os.environ.get('SESSION_SECRET', 'NotSafe')

JWT_SECRET_FILE = os.environ.get('JWT_SECRET_FILE')
if not JWT_SECRET_FILE:
    raise RuntimeError('No JWT_SECRET_FILE defined for deployment')


GITHUB_CLIENT_ID = os.environ.get('GITHUB_CLIENT_ID')
GITHUB_CLIENT_SECRET = os.environ.get('GITHUB_CLIENT_SECRET')


# Allows a custom rule for project names.
# Eg - projects could be defined as user/projname with:
#   PROJECT_NAME_REGEX = '(?:\S+\/\S+^/)'
# This needs to match the setting used by the target JobServ API server
PROJECT_NAME_REGEX = os.environ.get('PROJECT_NAME_REGEX')

JOBSERV_URL = os.environ.get('JOBSERV_URL')
if not JOBSERV_URL:
    raise ValueError('JOBSERV_URL environment variable not defined')

if JOBSERV_URL[-1] == '/':
    # strip off trailing slash, to make url joining easy in code
    JOBSERV_URL = JOBSERV_URL[:-1]
