set -e

# Reset Postgres
kubectl scale statefulset/postgres --replicas=0
kubectl delete pods postgres-0
kubectl delete pvc postgres-volume-postgres-0
kubectl scale statefulset/postgres --replicas=1
kubectl rollout status statefulset postgres

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
