#!/usr/bin/env bash
set -euo pipefail

STAGE="${STAGE:-prod}"
ECR_REPOSITORY="${ECR_REPOSITORY:-mcp-server-${STAGE}}"

LOG_GROUP_VPC="/aws/vpc/flow-logs/${STAGE}"
LOG_GROUP_ECS="/ecs/mcp-server-${STAGE}"
LOG_GROUP_API_GW="/api-gw/access-logs-${STAGE}"

import_log_group_if_exists() {
  local log_group_name="$1"
  local terraform_address="$2"

  if aws logs describe-log-groups \
    --log-group-name-prefix "$log_group_name" \
    --query "logGroups[?logGroupName=='$log_group_name']" \
    --output text | grep -q "$log_group_name"; then
    terraform import "$terraform_address" "$log_group_name"
  fi
}

import_ecr_if_exists() {
  local repository_name="$1"
  local terraform_address="$2"

  if aws ecr describe-repositories \
    --repository-names "$repository_name" \
    --query 'repositories[0].repositoryName' \
    --output text 2>/dev/null | grep -q "$repository_name"; then
    terraform import "$terraform_address" "$repository_name"
  fi
}

import_log_group_if_exists "$LOG_GROUP_VPC" "module.crud.aws_cloudwatch_log_group.vpc_flow_logs[0]"
import_log_group_if_exists "$LOG_GROUP_ECS" "module.crud.aws_cloudwatch_log_group.mcp_server[0]"
import_log_group_if_exists "$LOG_GROUP_API_GW" "module.crud.aws_cloudwatch_log_group.api_gw_access_logs[0]"
import_ecr_if_exists "$ECR_REPOSITORY" "module.crud.aws_ecr_repository.mcp_server[0]"
