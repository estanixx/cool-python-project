#!/bin/sh
set -a
# Source shared env vars from terraform-setup if available
if [ -f /shared/.env ]; then
  . /shared/.env
fi
set +a

exec "$@"
