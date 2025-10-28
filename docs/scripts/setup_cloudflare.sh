#!/bin/bash
# Cloudflare DNS and SSL Setup Script
# Uses Cloudflare API v4 directly

API_TOKEN="$1"
DOMAIN="vertice-maximus.com"

if [ -z "$API_TOKEN" ]; then
    echo "Usage: $0 <API_TOKEN>"
    exit 1
fi

echo "🔍 Getting account information..."

# Get account ID
ACCOUNT_RESPONSE=$(curl -s -X GET "https://api.cloudflare.com/client/v4/accounts" \
     -H "Authorization: Bearer $API_TOKEN" \
     -H "Content-Type: application/json")

ACCOUNT_ID=$(echo "$ACCOUNT_RESPONSE" | python3 -c "import sys, json; data=json.load(sys.stdin); print(data['result'][0]['id'] if data.get('result') and len(data['result']) > 0 else '')")

if [ -z "$ACCOUNT_ID" ]; then
    echo "❌ Could not get account ID. Response:"
    echo "$ACCOUNT_RESPONSE" | python3 -m json.tool
    echo ""
    echo "Please verify your API token has the following permissions:"
    echo "  - Zone:Read"
    echo "  - Zone:Edit"
    echo "  - DNS:Edit"
    exit 1
fi

echo "✅ Account ID: $ACCOUNT_ID"

# Check if zone exists
echo "🔍 Checking if domain $DOMAIN exists..."

ZONE_RESPONSE=$(curl -s -X GET "https://api.cloudflare.com/client/v4/zones?name=$DOMAIN" \
     -H "Authorization: Bearer $API_TOKEN" \
     -H "Content-Type: application/json")

ZONE_ID=$(echo "$ZONE_RESPONSE" | python3 -c "import sys, json; data=json.load(sys.stdin); print(data['result'][0]['id'] if data.get('result') and len(data['result']) > 0 else '')")

if [ -z "$ZONE_ID" ]; then
    echo "➕ Adding domain $DOMAIN to Cloudflare..."

    CREATE_RESPONSE=$(curl -s -X POST "https://api.cloudflare.com/client/v4/zones" \
         -H "Authorization: Bearer $API_TOKEN" \
         -H "Content-Type: application/json" \
         --data "{\"name\":\"$DOMAIN\",\"account\":{\"id\":\"$ACCOUNT_ID\"},\"jump_start\":true}")

    ZONE_ID=$(echo "$CREATE_RESPONSE" | python3 -c "import sys, json; data=json.load(sys.stdin); print(data['result']['id'] if data.get('result') else '')")

    if [ -z "$ZONE_ID" ]; then
        echo "❌ Could not create zone. Response:"
        echo "$CREATE_RESPONSE" | python3 -m json.tool
        exit 1
    fi

    echo "✅ Domain added (Zone ID: $ZONE_ID)"
else
    echo "✅ Domain already exists (Zone ID: $ZONE_ID)"
fi

# Get nameservers
NAMESERVERS=$(curl -s -X GET "https://api.cloudflare.com/client/v4/zones/$ZONE_ID" \
     -H "Authorization: Bearer $API_TOKEN" \
     -H "Content-Type: application/json" | \
     python3 -c "import sys, json; data=json.load(sys.stdin); print('\n'.join(data['result']['name_servers']) if data.get('result') and data['result'].get('name_servers') else '')")

if [ -n "$NAMESERVERS" ]; then
    echo ""
    echo "📋 Cloudflare Nameservers:"
    echo "$NAMESERVERS" | while read ns; do echo "   - $ns"; done
fi

# Configure DNS records
echo ""
echo "🔧 Configuring DNS records..."

# Function to create or update DNS record
update_dns_record() {
    local TYPE="$1"
    local NAME="$2"
    local CONTENT="$3"
    local PROXIED="$4"
    local TTL="$5"

    # Check if record exists
    EXISTING=$(curl -s -X GET "https://api.cloudflare.com/client/v4/zones/$ZONE_ID/dns_records?type=$TYPE&name=$NAME" \
         -H "Authorization: Bearer $API_TOKEN" \
         -H "Content-Type: application/json")

    RECORD_ID=$(echo "$EXISTING" | python3 -c "import sys, json; data=json.load(sys.stdin); print(data['result'][0]['id'] if data.get('result') and len(data['result']) > 0 else '')")

    if [ -n "$RECORD_ID" ]; then
        # Update existing record
        curl -s -X PUT "https://api.cloudflare.com/client/v4/zones/$ZONE_ID/dns_records/$RECORD_ID" \
             -H "Authorization: Bearer $API_TOKEN" \
             -H "Content-Type: application/json" \
             --data "{\"type\":\"$TYPE\",\"name\":\"$NAME\",\"content\":\"$CONTENT\",\"proxied\":$PROXIED,\"ttl\":$TTL}" > /dev/null
        echo "   ✅ Updated $TYPE record: $NAME"
    else
        # Create new record
        curl -s -X POST "https://api.cloudflare.com/client/v4/zones/$ZONE_ID/dns_records" \
             -H "Authorization: Bearer $API_TOKEN" \
             -H "Content-Type: application/json" \
             --data "{\"type\":\"$TYPE\",\"name\":\"$NAME\",\"content\":\"$CONTENT\",\"proxied\":$PROXIED,\"ttl\":$TTL}" > /dev/null
        echo "   ✅ Created $TYPE record: $NAME"
    fi
}

# Create DNS records
update_dns_record "A" "$DOMAIN" "199.36.158.100" "true" "1"  # Firebase with proxy
update_dns_record "A" "api.$DOMAIN" "34.49.122.184" "true" "1"  # GKE with proxy
update_dns_record "TXT" "$DOMAIN" "hosting-site=vertice-maximus" "false" "3600"
update_dns_record "TXT" "$DOMAIN" "v=spf1 include:_spf.google.com ~all" "false" "3600"

# Configure SSL/TLS
echo ""
echo "🔒 Configuring SSL/TLS..."

# Set SSL mode to Full
curl -s -X PATCH "https://api.cloudflare.com/client/v4/zones/$ZONE_ID/settings/ssl" \
     -H "Authorization: Bearer $API_TOKEN" \
     -H "Content-Type: application/json" \
     --data '{"value":"full"}' > /dev/null
echo "   ✅ SSL mode set to 'Full'"

# Enable Always Use HTTPS
curl -s -X PATCH "https://api.cloudflare.com/client/v4/zones/$ZONE_ID/settings/always_use_https" \
     -H "Authorization: Bearer $API_TOKEN" \
     -H "Content-Type: application/json" \
     --data '{"value":"on"}' > /dev/null
echo "   ✅ Always Use HTTPS enabled"

# Enable Automatic HTTPS Rewrites
curl -s -X PATCH "https://api.cloudflare.com/client/v4/zones/$ZONE_ID/settings/automatic_https_rewrites" \
     -H "Authorization: Bearer $API_TOKEN" \
     -H "Content-Type: application/json" \
     --data '{"value":"on"}' > /dev/null
echo "   ✅ Automatic HTTPS Rewrites enabled"

# Set minimum TLS version
curl -s -X PATCH "https://api.cloudflare.com/client/v4/zones/$ZONE_ID/settings/min_tls_version" \
     -H "Authorization: Bearer $API_TOKEN" \
     -H "Content-Type: application/json" \
     --data '{"value":"1.2"}' > /dev/null
echo "   ✅ Minimum TLS version set to 1.2"

echo ""
echo "✅ Cloudflare setup complete!"
echo ""
echo "============================================================"
echo "NEXT STEPS:"
echo "============================================================"
echo ""
echo "1. Go to Google Domains DNS settings"
echo "2. Change nameservers to CUSTOM and add:"
if [ -n "$NAMESERVERS" ]; then
    echo "$NAMESERVERS" | while read ns; do echo "   - $ns"; done
else
    echo "   (Check Cloudflare dashboard for nameservers)"
fi
echo ""
echo "3. Wait 5-30 minutes for propagation"
echo "4. SSL certificate will be active immediately after propagation"
echo ""
echo "============================================================"
