#!/bin/bash

pdm run gunicorn -b 0.0.0.0 --access-logfile=- --error-logfile=- --reload 'app:app'

