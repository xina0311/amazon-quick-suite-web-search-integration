#!/bin/bash
REGION=$1

if [ -z "$REGION" ]; then
    echo "Usage: ./setup_cognito_s2s_bocha.sh <region>"
    echo "Example: ./setup_cognito_s2s_bocha.sh us-west-2"
    exit 1
fi

echo "================================================"
echo "Setting up Cognito S2S Authentication for Bocha Web Search"
echo "Region: $REGION"
echo "================================================"

# 1. 创建 User Pool
echo ""
echo "[1/5] Creating User Pool..."
POOL_RESPONSE=$(aws cognito-idp create-user-pool \
  --pool-name "BochaWebSearchAuthPool" \
  --region $REGION)
POOL_ID=$(echo $POOL_RESPONSE | jq -r '.UserPool.Id')
echo "✓ User Pool ID: $POOL_ID"

# 2. 创建 Domain
echo ""
echo "[2/5] Creating Domain..."
DOMAIN_PREFIX="bocha-search-$(date +%s)"
aws cognito-idp create-user-pool-domain \
  --domain $DOMAIN_PREFIX \
  --user-pool-id $POOL_ID \
  --region $REGION
TOKEN_ENDPOINT="https://${DOMAIN_PREFIX}.auth.${REGION}.amazoncognito.com/oauth2/token"
echo "✓ Token URL: $TOKEN_ENDPOINT"

# 3. 创建 Resource Server
echo ""
echo "[3/5] Creating Resource Server..."
RESOURCE_SERVER_IDENTIFIER="bocha-api"
aws cognito-idp create-resource-server \
  --user-pool-id $POOL_ID \
  --identifier $RESOURCE_SERVER_IDENTIFIER \
  --name "Bocha Web Search API" \
  --scopes \
    ScopeName=search,ScopeDescription="Search access" \
    ScopeName=read,ScopeDescription="Read access" \
  --region $REGION
echo "✓ Resource Server: $RESOURCE_SERVER_IDENTIFIER"

# 4. 创建 App Client (Service-to-Service)
echo ""
echo "[4/5] Creating App Client for Service-to-Service Auth..."
CLIENT_RESPONSE=$(aws cognito-idp create-user-pool-client \
  --user-pool-id $POOL_ID \
  --client-name "BochaSearchServiceClient" \
  --generate-secret \
  --allowed-o-auth-flows "client_credentials" \
  --allowed-o-auth-scopes \
    "${RESOURCE_SERVER_IDENTIFIER}/search" \
    "${RESOURCE_SERVER_IDENTIFIER}/read" \
  --allowed-o-auth-flows-user-pool-client \
  --region $REGION)
CLIENT_ID=$(echo $CLIENT_RESPONSE | jq -r '.UserPoolClient.ClientId')
CLIENT_SECRET=$(echo $CLIENT_RESPONSE | jq -r '.UserPoolClient.ClientSecret')
echo "✓ Client ID: $CLIENT_ID"
echo "✓ Client Secret: $CLIENT_SECRET"

# 5. 测试获取 Token
echo ""
echo "[5/5] Testing token retrieval..."
TOKEN_RESPONSE=$(curl -s -X POST "$TOKEN_ENDPOINT" \
  -H "Content-Type: application/x-www-form-urlencoded" \
  -u "${CLIENT_ID}:${CLIENT_SECRET}" \
  -d "grant_type=client_credentials&scope=${RESOURCE_SERVER_IDENTIFIER}/search ${RESOURCE_SERVER_IDENTIFIER}/read")
ACCESS_TOKEN=$(echo $TOKEN_RESPONSE | jq -r '.access_token')

if [ "$ACCESS_TOKEN" != "null" ] && [ ! -z "$ACCESS_TOKEN" ]; then
  echo "✓ Token obtained successfully!"
  echo "Access Token (first 50 chars): ${ACCESS_TOKEN:0:50}..."
else
  echo "✗ Failed to obtain token"
  echo $TOKEN_RESPONSE | jq
fi

# 生成 Discovery URL
DISCOVERY_URL="https://cognito-idp.${REGION}.amazonaws.com/${POOL_ID}/.well-known/openid-configuration"

# 输出配置摘要
OUTPUT="
================================================
Bocha Web Search S2S Authentication Configuration
================================================
User Pool ID: $POOL_ID
Region: $REGION
Domain Prefix: $DOMAIN_PREFIX
Token Endpoint: $TOKEN_ENDPOINT
Discovery URL: $DISCOVERY_URL
Resource Server: $RESOURCE_SERVER_IDENTIFIER

App Client (Service-to-Service):
  Client ID: $CLIENT_ID
  Client Secret: $CLIENT_SECRET

Scopes:
  - ${RESOURCE_SERVER_IDENTIFIER}/search
  - ${RESOURCE_SERVER_IDENTIFIER}/read

Test Access Token:
${ACCESS_TOKEN:0:50}...
================================================
"

# Output to console
echo "$OUTPUT"

# Write to file
cat > cognito-bocha-s2s.txt << EOFCONFIG
$OUTPUT
================================================
Raw Configuration (for scripts)
================================================
POOL_ID=$POOL_ID
REGION=$REGION
DOMAIN_PREFIX=$DOMAIN_PREFIX
TOKEN_ENDPOINT=$TOKEN_ENDPOINT
DISCOVERY_URL=$DISCOVERY_URL
RESOURCE_SERVER_IDENTIFIER=$RESOURCE_SERVER_IDENTIFIER
CLIENT_ID=$CLIENT_ID
CLIENT_SECRET=$CLIENT_SECRET
SCOPES=${RESOURCE_SERVER_IDENTIFIER}/search ${RESOURCE_SERVER_IDENTIFIER}/read
ACCESS_TOKEN=$ACCESS_TOKEN
EOFCONFIG

echo ""
echo "✓ Configuration saved to cognito-bocha-s2s.txt"

# Create cleanup script
cat > cleanup-cognito-bocha-s2s.sh << 'EOFCLEANUP'
#!/bin/bash
echo "Cleaning up Cognito S2S resources for Bocha..."
source cognito-bocha-s2s.txt
aws cognito-idp delete-user-pool-domain --domain $DOMAIN_PREFIX --user-pool-id $POOL_ID --region $REGION 2>/dev/null
sleep 2
aws cognito-idp delete-user-pool --user-pool-id $POOL_ID --region $REGION 2>/dev/null
echo "✓ Resources deleted"
rm -f cognito-bocha-s2s.txt cleanup-cognito-bocha-s2s.sh test-bocha-s2s-token.sh
EOFCLEANUP

chmod +x cleanup-cognito-bocha-s2s.sh
echo "✓ Cleanup script created: ./cleanup-cognito-bocha-s2s.sh"

# Create token test script
cat > test-bocha-s2s-token.sh << 'EOFTEST'
#!/bin/bash
source cognito-bocha-s2s.txt

echo "Retrieving access token for Bocha Web Search..."
TOKEN_RESPONSE=$(curl -s -X POST "$TOKEN_ENDPOINT" \
  -H "Content-Type: application/x-www-form-urlencoded" \
  -u "${CLIENT_ID}:${CLIENT_SECRET}" \
  -d "grant_type=client_credentials&scope=${SCOPES}")

ACCESS_TOKEN=$(echo $TOKEN_RESPONSE | jq -r '.access_token')

if [ "$ACCESS_TOKEN" != "null" ]; then
  echo "✓ Token obtained successfully!"
  echo ""
  echo "Access Token:"
  echo $ACCESS_TOKEN
  echo ""
  echo "Token payload:"
  echo $ACCESS_TOKEN | cut -d'.' -f2 | base64 -d 2>/dev/null | jq .
else
  echo "✗ Failed to obtain token"
  echo $TOKEN_RESPONSE | jq
fi
EOFTEST

chmod +x test-bocha-s2s-token.sh
echo "✓ Token test script created: ./test-bocha-s2s-token.sh"

echo ""
echo "================================================"
echo "Setup complete! Use these files:"
echo "  - cognito-bocha-s2s.txt: Full configuration"
echo "  - cleanup-cognito-bocha-s2s.sh: Delete resources"
echo "  - test-bocha-s2s-token.sh: Test token retrieval"
echo "================================================"
