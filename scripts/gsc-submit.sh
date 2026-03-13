#!/bin/bash
# =============================================================================
# Google Search Console Indexing API Submission
# =============================================================================
#
# Submits URLs to Google's Indexing API for faster crawling and indexing.
#
# Usage:
#   ./scripts/gsc-submit.sh <url>                    # Submit single URL
#   ./scripts/gsc-submit.sh --sitemap                # Submit all URLs from sitemap
#   ./scripts/gsc-submit.sh --status <url>           # Check indexing status
#
# Setup:
#   1. Go to Google Cloud Console (https://console.cloud.google.com)
#   2. Create a new project or select existing
#   3. Enable "Web Search Indexing API" (APIs & Services → Library)
#   4. Create a Service Account (IAM & Admin → Service Accounts)
#   5. Create a JSON key for the service account
#   6. Save the key as: scripts/gsc-credentials.json
#   7. In Google Search Console, add the service account email as an Owner:
#      - Go to Settings → Users and permissions → Add user
#      - Use the service account email (e.g., mybot@project.iam.gserviceaccount.com)
#      - Set permission to "Owner"
#
# =============================================================================

set -euo pipefail

REPO_DIR="$(cd "$(dirname "$0")/.." && pwd)"
CREDS_FILE="$REPO_DIR/scripts/gsc-credentials.json"
TOKEN_FILE="$REPO_DIR/scripts/.gsc-token.tmp"
INDEXING_API="https://indexing.googleapis.com/v3/urlNotifications:publish"
SITEMAP_FILE="$REPO_DIR/sitemap.xml"

# ---- Check credentials ----
if [ ! -f "$CREDS_FILE" ]; then
  echo "ERROR: Google credentials not found at $CREDS_FILE"
  echo ""
  echo "Setup instructions:"
  echo "  1. Create a Google Cloud service account with Indexing API enabled"
  echo "  2. Download the JSON key"
  echo "  3. Save it to: $CREDS_FILE"
  echo "  4. Add the service account email as Owner in Google Search Console"
  exit 1
fi

# ---- Generate OAuth2 access token from service account ----
get_access_token() {
  # Extract credentials
  local client_email=$(jq -r '.client_email' "$CREDS_FILE")
  local private_key=$(jq -r '.private_key' "$CREDS_FILE")
  local token_uri=$(jq -r '.token_uri' "$CREDS_FILE")

  # Create JWT header
  local header=$(echo -n '{"alg":"RS256","typ":"JWT"}' | openssl base64 -e | tr -d '\n=' | tr '/+' '_-')

  # Create JWT claim set
  local now=$(date +%s)
  local exp=$((now + 3600))
  local claim=$(echo -n "{\"iss\":\"${client_email}\",\"scope\":\"https://www.googleapis.com/auth/indexing\",\"aud\":\"${token_uri}\",\"exp\":${exp},\"iat\":${now}}" | openssl base64 -e | tr -d '\n=' | tr '/+' '_-')

  # Create JWT signature
  local unsigned="${header}.${claim}"
  local signature=$(echo -n "$unsigned" | openssl dgst -sha256 -sign <(echo "$private_key") | openssl base64 -e | tr -d '\n=' | tr '/+' '_-')

  local jwt="${unsigned}.${signature}"

  # Exchange JWT for access token
  local response=$(curl -s -X POST "$token_uri" \
    -H "Content-Type: application/x-www-form-urlencoded" \
    -d "grant_type=urn:ietf:params:oauth:grant-type:jwt-bearer&assertion=${jwt}")

  echo "$response" | jq -r '.access_token'
}

# ---- Submit a URL for indexing ----
submit_url() {
  local url="$1"
  local token="$2"
  local action="${3:-URL_UPDATED}"  # URL_UPDATED or URL_DELETED

  echo -n "  Submitting: $url ... "

  local response=$(curl -s -X POST "$INDEXING_API" \
    -H "Content-Type: application/json" \
    -H "Authorization: Bearer $token" \
    -d "{\"url\": \"${url}\", \"type\": \"${action}\"}")

  local error=$(echo "$response" | jq -r '.error.message // empty')
  if [ -n "$error" ]; then
    echo "FAILED: $error"
    return 1
  else
    local notify_time=$(echo "$response" | jq -r '.urlNotificationMetadata.latestUpdate.notifyTime // "submitted"')
    echo "OK ($notify_time)"
    return 0
  fi
}

# ---- Check indexing status ----
check_status() {
  local url="$1"
  local token="$2"

  local encoded_url=$(python3 -c "import urllib.parse; print(urllib.parse.quote('$url', safe=''))")
  local response=$(curl -s "https://indexing.googleapis.com/v3/urlNotifications/metadata?url=${encoded_url}" \
    -H "Authorization: Bearer $token")

  echo "$response" | jq .
}

# ---- Main ----
if [ $# -lt 1 ]; then
  echo "Usage: $0 <url> | --sitemap | --status <url>"
  exit 1
fi

echo "Authenticating with Google..."
ACCESS_TOKEN=$(get_access_token)

if [ -z "$ACCESS_TOKEN" ] || [ "$ACCESS_TOKEN" = "null" ]; then
  echo "ERROR: Failed to get access token. Check your credentials."
  exit 1
fi

echo "Authenticated successfully."
echo ""

case "$1" in
  --sitemap)
    echo "Submitting all URLs from sitemap..."
    echo ""
    # Extract URLs from sitemap.xml
    urls=$(grep -oP '(?<=<loc>)https://[^<]+' "$SITEMAP_FILE")
    success=0
    failed=0
    for url in $urls; do
      if submit_url "$url" "$ACCESS_TOKEN"; then
        ((success++))
      else
        ((failed++))
      fi
      sleep 1  # Rate limiting
    done
    echo ""
    echo "Done: $success submitted, $failed failed"
    ;;

  --status)
    if [ $# -lt 2 ]; then
      echo "Usage: $0 --status <url>"
      exit 1
    fi
    echo "Checking indexing status for: $2"
    check_status "$2" "$ACCESS_TOKEN"
    ;;

  *)
    submit_url "$1" "$ACCESS_TOKEN"
    ;;
esac
