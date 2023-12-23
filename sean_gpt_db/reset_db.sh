kubectl delete statefulset postgres
kubectl delete pvc postgres-volume-postgres-0
# Get the directory of the script
SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
kubectl apply -f "${SCRIPT_DIR}/postgres-set.yaml"