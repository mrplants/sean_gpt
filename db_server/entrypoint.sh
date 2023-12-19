#!/bin/bash

# Start MongoDB in the background
mongod --bind_ip_all &

# Wait for MongoDB to be ready
while ! mongo --eval "print('waited for connection')" &> /dev/null; do
    sleep 1
done

# Run import script
mongoimport --uri "mongodb://localhost:27017" --db sean_gpt --collection user --file /data/dev_user_export.json --jsonArray

echo "Data import complete."

# Stop the background MongoDB process
mongod --shutdown

# Start MongoDB in the foreground
exec mongod --bind_ip_all