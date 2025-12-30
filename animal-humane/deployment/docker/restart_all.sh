#!/usr/bin/env bash
# Safe restart helper for Animal Humane Docker stack
# - Logs invocations to /var/log/ah-restart.log
# - Avoids restarting the `scheduler` during protected scrape windows by default
# - Use --with-scheduler to include scheduler in the restart
# - Use --force to bypass time-window protections

set -euo pipefail

LOGFILE=/var/log/ah-restart.log
PROTECTED_WINDOWS=("08:50-09:20" "10:50-11:20" "12:50-13:20" "14:50-15:20" "16:50-17:20" "18:50-19:20")
WITH_SCHEDULER=0
FORCE=0

usage() {
  cat <<EOF
Usage: $0 [--with-scheduler] [--force]

Options:
  --with-scheduler, -s   Include the scheduler when restarting (default: skip scheduler during protected windows)
  --force, -f            Bypass protected time windows and perform full restart
  --help, -h             Show this message

Notes:
 - Protected windows are centered around scheduled scrapes (9:00, 11:00, 13:00, 15:00, 17:00, 19:00)
 - This script logs to $LOGFILE (may require sudo to write there)
EOF
}

while [[ $# -gt 0 ]]; do
  case "$1" in
    --with-scheduler|-s)
      WITH_SCHEDULER=1
      shift
      ;;
    --force|-f)
      FORCE=1
      shift
      ;;
    --help|-h)
      usage
      exit 0
      ;;
    *)
      echo "Unknown option: $1"
      usage
      exit 2
      ;;
  esac
done

# Log invocation (best-effort; may need sudo to write to /var/log)
mkdir -p "$(dirname "$LOGFILE")" || true
echo "$(date -u '+%Y-%m-%dT%H:%M:%SZ') restart_all invoked by $(whoami) host=$(hostname) args=\"$*\"" >> "$LOGFILE" 2>/dev/null || true

# Helper: convert HH:MM to minutes since midnight
_hm_to_min() {
  IFS=':' read -r hh mm <<< "$1"
  echo $((10#$hh * 60 + 10#$mm))
}

now_hm=$(date +%H:%M)
now_min=$(_hm_to_min "$now_hm")

within_protected=0
for window in "${PROTECTED_WINDOWS[@]}"; do
  IFS='-' read -r start end <<< "$window"
  start_min=$(_hm_to_min "$start")
  end_min=$(_hm_to_min "$end")
  if (( now_min >= start_min && now_min <= end_min )); then
    within_protected=1
    break
  fi
done

if (( within_protected == 1 && FORCE == 0 )); then
  if (( WITH_SCHEDULER == 0 )); then
    echo "Within protected scrape window ($now_hm). Will NOT restart 'scheduler' by default. Use --with-scheduler --force to override."
    echo "$(date -u '+%Y-%m-%dT%H:%M:%SZ') restart_all aborted scheduler-restart due to protected window (now=$now_hm)." >> "$LOGFILE" 2>/dev/null || true
    SKIP_SCHEDULER=1
  else
    echo "Within protected scrape window ($now_hm) but --with-scheduler was supplied. Proceeding after confirmation."
    SKIP_SCHEDULER=0
  fi
else
  SKIP_SCHEDULER=0
fi

if (( SKIP_SCHEDULER == 1 )); then
  echo "Restarting containers (scheduler will be skipped to avoid missed scrapes)..."
  # Restart all services except scheduler in a best-effort rolling manner
  services=$(docker-compose ps --services || true)
  for svc in $services; do
    if [[ "$svc" == "scheduler" ]]; then
      echo "Skipping service: $svc"
      echo "$(date -u '+%Y-%m-%dT%H:%M:%SZ') skipping scheduler restart" >> "$LOGFILE" 2>/dev/null || true
      continue
    fi
    echo "Restarting service: $svc"
    docker-compose up --build -d "$svc"
    echo "$(date -u '+%Y-%m-%dT%H:%M:%SZ') restarted $svc" >> "$LOGFILE" 2>/dev/null || true
  done
  echo "Finished restarting non-scheduler services."
  docker-compose ps
  echo "Done. Scheduler was intentionally left running."
  echo "$(date -u '+%Y-%m-%dT%H:%M:%SZ') restart_all completed (scheduler skipped)" >> "$LOGFILE" 2>/dev/null || true
  exit 0
fi

# If we get here, either not in protected window OR WITH_SCHEDULER was requested OR FORCE=1
if (( WITH_SCHEDULER == 1 )); then
  echo "Performing full restart including scheduler..."
  echo "$(date -u '+%Y-%m-%dT%H:%M:%SZ') performing full restart (including scheduler)" >> "$LOGFILE" 2>/dev/null || true
  docker-compose down
  docker-compose up --build -d
  echo "$(date -u '+%Y-%m-%dT%H:%M:%SZ') full restart completed" >> "$LOGFILE" 2>/dev/null || true
  docker-compose ps
  exit 0
fi

# Default safe behavior: restart non-scheduler services first, then restart scheduler last
echo "Restarting services (scheduler will be restarted last)..."
services=$(docker-compose ps --services || true)
for svc in $services; do
  if [[ "$svc" == "scheduler" ]]; then
    echo "Deferring scheduler restart"
    continue
  fi
  echo "Restarting service: $svc"
  docker-compose up --build -d "$svc"
  echo "$(date -u '+%Y-%m-%dT%H:%M:%SZ') restarted $svc" >> "$LOGFILE" 2>/dev/null || true
done

# Restart scheduler explicitly
if echo "$services" | grep -qw "scheduler"; then
  echo "Restarting scheduler service (now safe)..."
  docker-compose up --build -d scheduler
  echo "$(date -u '+%Y-%m-%dT%H:%M:%SZ') restarted scheduler" >> "$LOGFILE" 2>/dev/null || true
fi

docker-compose ps
echo "All services processed. See $LOGFILE for invocation history."
echo "$(date -u '+%Y-%m-%dT%H:%M:%SZ') restart_all completed" >> "$LOGFILE" 2>/dev/null || true
