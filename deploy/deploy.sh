#!/usr/bin/env bash
# Deploy CloseCall to this team's Kubernetes namespace. Run on the event build machine:
#   cd ~/vast-builders-challenge/closecall && git pull && bash deploy/deploy.sh
# Optional: CLOSECALL_CAMERA=pie_cam-3 bash deploy/deploy.sh   (limit the scan to one camera)
#           RESTART=1 bash deploy/deploy.sh                      (force a fresh pod)
# Credentials are read from /config on this machine and go straight into a Kubernetes Secret.
set -euo pipefail
cd "$(dirname "$0")/.."

mapfile -t TEAM_CONFIGS < <(find /config -maxdepth 1 -type f -name '*.config' | sort)
(( ${#TEAM_CONFIGS[@]} == 1 )) || { echo "expected exactly one /config/*.config"; exit 1; }
TEAM_CONFIG="${TEAM_CONFIGS[0]}"
USERNAME=$(grep '^USERNAME=' "$TEAM_CONFIG" | cut -d= -f2-)
INGRESS_URL=$(grep '^INGRESS_URL=' "$TEAM_CONFIG" | cut -d= -f2-)
PASSWORD=$(grep '^PASSWORD=' "$TEAM_CONFIG" | cut -d= -f2-)
NS="$USERNAME"
if [ -f "/config/${NS}-k8s.yaml" ]; then export KUBECONFIG="/config/${NS}-k8s.yaml"; else export KUBECONFIG=/config/kubeconfig; fi
TEAM_N="${USERNAME#team-}"
APP_HOST="video-lab-team-${TEAM_N}.cosmos.vastdata.com"
APP_NAME=closecall
APP_PORT=8080
CAMERA="${CLOSECALL_CAMERA:-}"
# Pods can't always resolve the VSS hostname that this machine knows (it may live in /etc/hosts here),
# so pin it inside the pod with hostAliases.
VSS_HOST=$(echo "$INGRESS_URL" | sed -E 's#^[a-z]+://##; s#[/:].*$##')
VSS_IP=$(getent hosts "$VSS_HOST" | awk '{print $1; exit}' || true)
HOST_ALIASES=""
if [ -n "$VSS_IP" ]; then
  HOST_ALIASES="      hostAliases:
      - ip: \"$VSS_IP\"
        hostnames: [\"$VSS_HOST\"]"
fi
echo "== VSS backend host $VSS_HOST -> ${VSS_IP:-not in /etc/hosts}"

echo "== namespace $NS, host $APP_HOST"
# only the app's code files go into the ConfigMap (a note like "app/app link" would break it)
re_name='^[-._a-zA-Z0-9]+$'; re_ext='\.(py|html|js|css|json)$'
CODE_FILES=()
for f in app/*; do
  b=$(basename "$f")
  if [[ -f "$f" && "$b" =~ $re_name && "$b" =~ $re_ext ]]; then CODE_FILES+=("--from-file=$f"); fi
done
echo "== code files: ${CODE_FILES[*]#--from-file=}"
kubectl -n "$NS" create configmap "${APP_NAME}-code" "${CODE_FILES[@]}" \
  --dry-run=client -o yaml | kubectl apply -f -
kubectl -n "$NS" create secret generic "${APP_NAME}-vss-creds" \
  --from-literal=VSS_URL="$INGRESS_URL" \
  --from-literal=VSS_USERNAME="$USERNAME" \
  --from-literal=VSS_PASSWORD="$PASSWORD" \
  --dry-run=client -o yaml | kubectl apply -f - >/dev/null && echo "secret ${APP_NAME}-vss-creds ok"

kubectl -n "$NS" apply -f - <<EOF
apiVersion: apps/v1
kind: Deployment
metadata:
  name: ${APP_NAME}
  labels: {app: ${APP_NAME}}
spec:
  replicas: 1
  selector: {matchLabels: {app: ${APP_NAME}}}
  template:
    metadata:
      labels: {app: ${APP_NAME}}
    spec:
${HOST_ALIASES}
      containers:
      - name: app
        image: python:3.12-slim
        imagePullPolicy: IfNotPresent
        ports: [{containerPort: ${APP_PORT}}]
        env:
        - {name: PORT, value: "${APP_PORT}"}
        - {name: DATA_DIR, value: /data}
        - {name: CLOSECALL_CAMERA, value: "${CAMERA}"}
        - name: VSS_URL
          valueFrom: {secretKeyRef: {name: ${APP_NAME}-vss-creds, key: VSS_URL}}
        - name: VSS_USERNAME
          valueFrom: {secretKeyRef: {name: ${APP_NAME}-vss-creds, key: VSS_USERNAME}}
        - name: VSS_PASSWORD
          valueFrom: {secretKeyRef: {name: ${APP_NAME}-vss-creds, key: VSS_PASSWORD}}
        volumeMounts:
        - {name: code, mountPath: /code}
        - {name: data, mountPath: /data}
        workingDir: /code
        command: ["python", "-u", "/code/main.py"]
        readinessProbe:
          httpGet: {path: /health, port: ${APP_PORT}}
          initialDelaySeconds: 3
          periodSeconds: 10
      volumes:
      - name: code
        configMap: {name: ${APP_NAME}-code}
      - name: data
        emptyDir: {}
---
apiVersion: v1
kind: Service
metadata:
  name: ${APP_NAME}
  labels: {app: ${APP_NAME}}
spec:
  selector: {app: ${APP_NAME}}
  ports: [{name: http, port: 80, targetPort: ${APP_PORT}}]
  type: ClusterIP
---
apiVersion: networking.k8s.io/v1
kind: Ingress
metadata:
  name: ${APP_NAME}
  labels: {app: ${APP_NAME}}
  annotations:
    nginx.ingress.kubernetes.io/rewrite-target: /\$2
    nginx.ingress.kubernetes.io/proxy-read-timeout: "300"
    nginx.ingress.kubernetes.io/proxy-buffering: "off"
spec:
  ingressClassName: nginx
  rules:
  - host: ${APP_HOST}
    http:
      paths:
      - path: /app(/|$)(.*)
        pathType: ImplementationSpecific
        backend:
          service:
            name: ${APP_NAME}
            port: {number: 80}
EOF

if [ "${RESTART:-0}" = "1" ]; then
  kubectl -n "$NS" rollout restart deploy/"$APP_NAME"
fi
kubectl -n "$NS" rollout status deploy/"$APP_NAME" --timeout=180s
kubectl -n "$NS" get pods -l app="$APP_NAME" -o wide
echo "== services in $NS:"; kubectl -n "$NS" get svc 2>/dev/null | head -15 || true
echo "== health:"; curl -sS -m 10 "http://${APP_HOST}/app/health" || echo "(health check from this machine failed; check the App button)"
echo
echo "== code changes reach the running app in about a minute (no restart, saved decisions are kept)."
echo "== Open https://workshop.thecosmoslabs.com and click App."
