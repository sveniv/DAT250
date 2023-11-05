#!/bin/bash

#pdm run gunicorn -b 0.0.0.0 --access-logfile=- --error-logfile=- --reload -w 10 'app:app'
pdm run gunicorn -b 0.0.0.0 --access-logfile=- --error-logfile=- 'app:app'

