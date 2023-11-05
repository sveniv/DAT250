#!/bin/bash

#openssl req -x509 -nodes -days 3650 -newkey ec:<(openssl ecparam -name prime256v1) -keyout private_key.pem -out certificate.pem

pdm run gunicorn -b 0.0.0.0 --access-logfile=- --error-logfile=- --keyfile private_key.pem --certfile certificate.pem 'app:app'
