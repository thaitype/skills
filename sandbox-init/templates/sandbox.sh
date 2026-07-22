#!/usr/bin/env bash
# Sandbox manager — every dev command runs inside the __NAME__-sandbox container.
# The Compose project name comes from `name:` in docker-compose.yml — see the
# comment there for why it must stay unique per project.
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
COMPOSE=(docker compose -f "$SCRIPT_DIR/docker-compose.yml")
CONTAINER=__NAME__-sandbox

usage() {
  cat <<'EOF'
Usage: sandbox.sh <command>

Commands:
  up         Build (if needed) and start the sandbox container
  down       Stop and remove the sandbox container
  status     Show container state
  exec CMD…  Run a command inside the sandbox (in /workspace)
  shell      Open an interactive bash shell inside the sandbox
  rebuild    Rebuild the image (after Dockerfile changes) and restart
EOF
}

case "${1:-}" in
  up)
    "${COMPOSE[@]}" up -d
    ;;
  down)
    "${COMPOSE[@]}" down
    ;;
  status)
    docker ps -a --filter "name=^${CONTAINER}$" --format 'table {{.Names}}\t{{.Status}}\t{{.Image}}'
    ;;
  exec)
    shift
    [ $# -gt 0 ] || { echo "exec: missing command" >&2; exit 1; }
    docker exec -i "$CONTAINER" "$@"
    ;;
  shell)
    docker exec -it "$CONTAINER" bash
    ;;
  rebuild)
    "${COMPOSE[@]}" build --no-cache
    "${COMPOSE[@]}" up -d --force-recreate
    ;;
  *)
    usage
    exit 1
    ;;
esac
