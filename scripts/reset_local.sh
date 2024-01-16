set -e

# Reset Postgres
kubectl scale statefulset/postgres --replicas=0
kubectl delete pods postgres-0
kubectl delete pvc postgres-volume-postgres-0
kubectl scale statefulset/postgres --replicas=1
kubectl rollout status statefulset postgres

# Run the database migrations
# First, wait for the database to be ready
kubectl rollout status statefulset postgres
# Port forward to the database
kubectl port-forward service/postgres 5432:5432 &
# Save the PID of the port-forwarding process
port_forward_pid=$!
# Set a trap to kill the port-forwarding process when the script exits
trap "kill $port_forward_pid" EXIT
# Run the migrations
sean_gpt_database_host=localhost python -m alembic upgrade head

# Reset Redis
kubectl scale statefulset/redis --replicas=0
kubectl delete pods redis-0
kubectl delete pvc redis-data-redis-0
kubectl scale statefulset/redis --replicas=1
kubectl rollout status statefulset redis

# Reset Sean GPT
kubectl scale deployment/sean-gpt --replicas=0
kubectl scale deployment/sean-gpt --replicas=1
kubectl rollout status deployment sean-gpt

# Wait for the Kafka statefulset to be ready
kubectl rollout status statefulset seangpt-local-kafka-controller
# Wait for the Milvus deployment to be ready
kubectl rollout status deployment seangpt-local-milvus-standalone
