#!/usr/bin/env bash
echo "Creating mongo users..."
mongo admin --host localhost:27017 -u "${MONGO_INITDB_ROOT_USERNAME}" -p "${MONGO_INITDB_ROOT_PASSWORD}" --eval "db.createUser({user: '${DB_USER}', pwd: '${DB_PASSWORD}', roles: [{role: 'readWrite', db: '${DB_NAME}'}]}); db.createUser({user: '${DB_ADMIN_USER}', pwd: '${DB_ADMIN_PASSWORD}', roles: [{role: 'userAdminAnyDatabase', db: 'admin'}]});"
echo "Mongo users created."