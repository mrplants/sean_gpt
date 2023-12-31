kubectl delete statefulset redis
kubectl delete pvc redis-data-redis-0
# Get the directory of the script
SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
kubectl apply -f "${SCRIPT_DIR}/redis-set.yaml"