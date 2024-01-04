#!/bin/bash

# Create a new user
PGPASSWORD=$POSTGRES_PASSWORD psql -v ON_ERROR_STOP=1 -U $POSTGRES_USER -d postgres -c "CREATE USER \"$API_DB_USER\" WITH ENCRYPTED PASSWORD '$API_DB_PASSWORD';"

# Create a new database
PGPASSWORD=$POSTGRES_PASSWORD psql -v ON_ERROR_STOP=1 -U $POSTGRES_USER -d postgres -c "CREATE DATABASE $DATABASE_NAME;"

# Grant the user the ability to create tables in the public schema
PGPASSWORD=$POSTGRES_PASSWORD psql -v ON_ERROR_STOP=1 -U $POSTGRES_USER -d $DATABASE_NAME -c "
    GRANT CREATE ON SCHEMA public TO \"$API_DB_USER\";
"