#!/bin/sh
set -e

echo 'Waiting for Floci...'
until curl -sf http://floci:4566/_localstack/health > /dev/null 2>&1; do
  sleep 2
done

echo 'Deploying test infrastructure...'
cd /infra/test
terraform init
terraform apply -auto-approve -var='aws_endpoint_url=http://floci:4566'

echo 'Fetching API ID...'
API_ID=$(terraform output -raw api_id)

if [ -z "$API_ID" ]; then
  echo 'ERROR: API_ID is empty. Deployment may have failed.' >&2
  exit 1
fi

echo 'Writing shared .env...'
# Floci v1.5.16 (LocalStack) API Gateway v2 URL format:
# http://floci:4566/restapis/{api_id}/$default/_user_request_/{path}
# Note: $default is the stage name (literal, not a shell variable)
cat > /shared/.env << ENVEOF
API_ID=$API_ID
API_BASE_URL=http://floci:4566
API_ENDPOINT=http://floci:4566/restapis/$API_ID/\$default/_user_request_
STAGE=local
NEXT_PUBLIC_API_URL=/api/proxy
NEXT_PUBLIC_API_ENDPOINT=http://floci:4566/restapis/$API_ID/\$default/_user_request_
ENVEOF

echo "Setup complete! API_ID: $API_ID"
