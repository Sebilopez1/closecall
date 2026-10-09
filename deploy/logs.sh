#!/usr/bin/env bash
# Show the last lines of the CloseCall app log (run on the event build machine).
set -euo pipefail
mapfile -t TEAM_CONFIGS < <(find /config -maxdepth 1 -type f -name '*.config' | sort)
NS=$(grep '^USERNAME=' "${TEAM_CONFIGS[0]}" | cut -d= -f2-)
if [ -f "/config/${NS}-k8s.yaml" ]; then export KUBECONFIG="/config/${NS}-k8s.yaml"; else export KUBECONFIG=/config/kubeconfig; fi
kubectl -n "$NS" get pods -l app=closecall
kubectl -n "$NS" logs -l app=closecall --tail="${1:-40}"
