#!/bin/bash
# Cloudflare Setup Script - Based on Official API Documentation
# https://developers.cloudflare.com/api/

set -e

API_TOKEN="$1"
DOMAIN="vertice-maximus.com"

if [ -z "$API_TOKEN" ]; then
    echo "Usage: $0 <API_TOKEN>"
    exit 1
fi

echo "🔍 Step 1: Getting Account ID..."
ACCOUNT_RESPONSE=$(curl -s -X GET "https://api.cloudflare.com/client/v4/accounts" \
     -H "Authorization: Bearer $API_TOKEN" \
     -H "Content-Type: application/json")

echo "$ACCOUNT_RESPONSE" | python3 -m json.tool

ACCOUNT_ID=$(echo "$ACCOUNT_RESPONSE" | python3 -c "import sys, json; data=json.load(sys.stdin); print(data['result'][0]['id'] if data.get('success') and data.get('result') and len(data['result']) > 0 else '')" 2>/dev/null)

if [ -z "$ACCOUNT_ID" ]; then
    echo "❌ Failed to get Account ID"
    echo "Response: $ACCOUNT_RESPONSE"
    exit 1
fi

echo "✅ Account ID: $ACCOUNT_ID"

echo ""
echo "🔍 Step 2: Checking if zone exists..."
ZONE_LIST=$(curl -s -X GET "https://api.cloudflare.com/client/v4/zones?name=$DOMAIN" \
     -H "Authorization: Bearer $API_TOKEN" \
     -H "Content-Type: application/json")

ZONE_ID=$(echo "$ZONE_LIST" | python3 -c "import sys, json; data=json.load(sys.stdin); print(data['result'][0]['id'] if data.get('success') and data.get('result') and len(data['result']) > 0 else '')" 2>/dev/null)

if [ -z "$ZONE_ID" ]; then
    echo "➕ Creating new zone for $DOMAIN..."

    CREATE_ZONE=$(curl -s -X POST "https://api.cloudflare.com/client/v4/zones" \
         -H "Authorization: Bearer $API_TOKEN" \
         -H "Content-Type: application/json" \
         --data "{\"account\":{\"id\":\"$ACCOUNT_ID\"},\"name\":\"$DOMAIN\",\"type\":\"full\"}")

    ZONE_ID=$(echo "$CREATE_ZONE" | python3 -c "import sys, json; data=json.load(sys.stdin); print(data['result']['id'] if data.get('success') and data.get('result') else '')" 2>/dev/null)

    if [ -z "$ZONE_ID" ]; then
        echo "❌ Failed to create zone"
        echo "$CREATE_ZONE" | python3 -m json.tool
        exit 1
    fi

    echo "✅ Zone created: $ZONE_ID"
else
    echo "✅ Zone exists: $ZONE_ID"
fi

echo ""
echo "📋 Step 3: Getting nameservers..."
ZONE_INFO=$(curl -s -X GET "https://api.cloudflare.com/client/v4/zones/$ZONE_ID" \
     -H "Authorization: Bearer $API_TOKEN" \
     -H "Content-Type: application/json")

NAMESERVERS=$(echo "$ZONE_INFO" | python3 -c "import sys, json; data=json.load(sys.stdin); ns=data['result'].get('name_servers', []); print('\\n'.join(ns) if ns else '')" 2>/dev/null)

if [ -n "$NAMESERVERS" ]; then
    echo "✅ Nameservers:"
    echo "$NAMESERVERS" | while read ns; do echo "   $ns"; done
fi

echo ""
echo "🔧 Step 4: Configuring DNS records..."

# Function to create/update DNS record
configure_dns() {
    local TYPE="$1"
    local NAME="$2"
    local CONTENT="$3"
    local PROXIED="$4"
    local TTL="${5:-3600}"

    # Check existing
    EXISTING=$(curl -s -X GET "https://api.cloudflare.com/client/v4/zones/$ZONE_ID/dns_records?type=$TYPE&name=$NAME" \
         -H "Authorization: Bearer $API_TOKEN" \
         -H "Content-Type: application/json")

    RECORD_ID=$(echo "$EXISTING" | python3 -c "import sys, json; data=json.load(sys.stdin); print(data['result'][0]['id'] if data.get('success') and data.get('result') and len(data['result']) > 0 else '')" 2>/dev/null)

    if [ -n "$RECORD_ID" ]; then
        # Update
        UPDATE=$(curl -s -X PATCH "https://api.cloudflare.com/client/v4/zones/$ZONE_ID/dns_records/$RECORD_ID" \
             -H "Authorization: Bearer $API_TOKEN" \
             -H "Content-Type: application/json" \
             --data "{\"type\":\"$TYPE\",\"name\":\"$NAME\",\"content\":\"$CONTENT\",\"proxied\":$PROXIED,\"ttl\":$TTL}")

        SUCCESS=$(echo "$UPDATE" | python3 -c "import sys, json; data=json.load(sys.stdin); print('yes' if data.get('success') else 'no')" 2>/dev/null)

        if [ "$SUCCESS" = "yes" ]; then
            echo "   ✅ Updated $TYPE $NAME"
        else
            echo "   ⚠️  Failed to update $TYPE $NAME"
            echo "$UPDATE" | python3 -m json.tool
        fi
    else
        # Create
        CREATE=$(curl -s -X POST "https://api.cloudflare.com/client/v4/zones/$ZONE_ID/dns_records" \
             -H "Authorization: Bearer $API_TOKEN" \
             -H "Content-Type: application/json" \
             --data "{\"type\":\"$TYPE\",\"name\":\"$NAME\",\"content\":\"$CONTENT\",\"proxied\":$PROXIED,\"ttl\":$TTL}")

        SUCCESS=$(echo "$CREATE" | python3 -c "import sys, json; data=json.load(sys.stdin); print('yes' if data.get('success') else 'no')" 2>/dev/null)

        if [ "$SUCCESS" = "yes" ]; then
            echo "   ✅ Created $TYPE $NAME"
        else
            echo "   ⚠️  Failed to create $TYPE $NAME"
            echo "$CREATE" | python3 -m json.tool
        fi
    fi
}

# Configure records
configure_dns "A" "$DOMAIN" "199.36.158.100" "true" "1"
configure_dns "A" "api.$DOMAIN" "34.49.122.184" "true" "1"
configure_dns "TXT" "$DOMAIN" "hosting-site=vertice-maximus" "false" "3600"
configure_dns "TXT" "$DOMAIN" "v=spf1 include:_spf.google.com ~all" "false" "3600"

echo ""
echo "🔒 Step 5: Configuring SSL/TLS settings..."

# SSL Mode to Full
SSL_RESULT=$(curl -s -X PATCH "https://api.cloudflare.com/client/v4/zones/$ZONE_ID/settings/ssl" \
     -H "Authorization: Bearer $API_TOKEN" \
     -H "Content-Type: application/json" \
     --data '{"value":"full"}')

echo "$SSL_RESULT" | python3 -c "import sys, json; data=json.load(sys.stdin); print('   ✅ SSL: Full') if data.get('success') else print('   ⚠️  SSL config failed')" 2>/dev/null

# Always Use HTTPS
HTTPS_RESULT=$(curl -s -X PATCH "https://api.cloudflare.com/client/v4/zones/$ZONE_ID/settings/always_use_https" \
     -H "Authorization: Bearer $API_TOKEN" \
     -H "Content-Type: application/json" \
     --data '{"value":"on"}')

echo "$HTTPS_RESULT" | python3 -c "import sys, json; data=json.load(sys.stdin); print('   ✅ Always Use HTTPS: On') if data.get('success') else print('   ⚠️  HTTPS config failed')" 2>/dev/null

# Auto HTTPS Rewrites
REWRITE_RESULT=$(curl -s -X PATCH "https://api.cloudflare.com/client/v4/zones/$ZONE_ID/settings/automatic_https_rewrites" \
     -H "Authorization: Bearer $API_TOKEN" \
     -H "Content-Type: application/json" \
     --data '{"value":"on"}')

echo "$REWRITE_RESULT" | python3 -c "import sys, json; data=json.load(sys.stdin); print('   ✅ Auto HTTPS Rewrites: On') if data.get('success') else print('   ⚠️  Rewrite config failed')" 2>/dev/null

# Min TLS 1.2
TLS_RESULT=$(curl -s -X PATCH "https://api.cloudflare.com/client/v4/zones/$ZONE_ID/settings/min_tls_version" \
     -H "Authorization: Bearer $API_TOKEN" \
     -H "Content-Type: application/json" \
     --data '{"value":"1.2"}')

echo "$TLS_RESULT" | python3 -c "import sys, json; data=json.load(sys.stdin); print('   ✅ Min TLS: 1.2') if data.get('success') else print('   ⚠️  TLS config failed')" 2>/dev/null

echo ""
echo "============================================================"
echo "✅ CLOUDFLARE SETUP COMPLETE!"
echo "============================================================"
echo ""
echo "NEXT STEP: Update nameservers in Google Domains"
echo ""
if [ -n "$NAMESERVERS" ]; then
    echo "Go to: https://domains.google.com/registrar/$DOMAIN/dns"
    echo "Set custom nameservers to:"
    echo "$NAMESERVERS" | while read ns; do echo "   $ns"; done
else
    echo "Check nameservers at: https://dash.cloudflare.com"
fi
echo ""
echo "After nameserver update:"
echo "  • Propagation: 5-30 minutes"
echo "  • SSL will be active automatically"
echo ""
echo "============================================================"
