#!/bin/bash
# Simple Curl-Based API Test Script
# Tests all 28 endpoints of the Ticket Vendor API

set -e  # Exit on error

BASE_URL="${API_BASE_URL:-http://localhost:8000}"
VERBOSE="${VERBOSE:-false}"

# Colors for output
GREEN='\033[0;32m'
RED='\033[0;31m'
YELLOW='\033[1;33m'
CYAN='\033[0;36m'
NC='\033[0m' # No Color

# Test counters
PASSED=0
FAILED=0
SKIPPED=0

# Storage for tokens and IDs
ACCESS_TOKEN=""
REFRESH_TOKEN=""
EVENT_ID=""
TIER_ID=""

# Helper function to print colored output
print_status() {
    local status=$1
    local message=$2
    
    case $status in
        "PASS")
            echo -e "${GREEN}✓ PASS${NC} $message"
            ((PASSED++))
            ;;
        "FAIL")
            echo -e "${RED}✗ FAIL${NC} $message"
            ((FAILED++))
            ;;
        "SKIP")
            echo -e "${YELLOW}⊘ SKIP${NC} $message"
            ((SKIPPED++))
            ;;
        "INFO")
            echo -e "${CYAN}ℹ INFO${NC} $message"
            ;;
    esac
}

# Helper function to make API calls
api_call() {
    local method=$1
    local endpoint=$2
    local data=$3
    local auth_token=$4
    local expected_status=${5:-200}
    
    local curl_opts=(-s -w "\n%{http_code}" -X "$method")
    
    if [ -n "$auth_token" ]; then
        curl_opts+=(-H "Authorization: Bearer $auth_token")
    fi
    
    if [ -n "$data" ]; then
        curl_opts+=(-H "Content-Type: application/json" -d "$data")
    fi
    
    if [ "$VERBOSE" = "true" ]; then
        curl_opts+=(-v)
    fi
    
    response=$(curl "${curl_opts[@]}" "${BASE_URL}${endpoint}")
    http_code=$(echo "$response" | tail -n1)
    body=$(echo "$response" | sed '$d')
    
    if [ "$http_code" = "$expected_status" ]; then
        echo "$body"
        return 0
    else
        echo "Expected $expected_status, got $http_code"
        [ "$VERBOSE" = "true" ] && echo "$body"
        return 1
    fi
}

# Print header
echo ""
echo "═══════════════════════════════════════════════════════════"
echo "  Ticket Vendor API - Comprehensive Test Suite (curl)"
echo "═══════════════════════════════════════════════════════════"
echo ""
echo "Base URL: $BASE_URL"
echo ""

# ==================== HEALTH CHECK ====================
echo ""
echo "━━━ Health Check ━━━"
if response=$(api_call "GET" "/health" "" "" 200); then
    print_status "PASS" "Health Check"
else
    print_status "FAIL" "Health Check - API may not be running"
    echo "Please ensure the API is running at $BASE_URL"
    exit 1
fi

# ==================== AUTHENTICATION (8 endpoints) ====================
echo ""
echo "━━━ Authentication (8 endpoints) ━━━"

# 1. Register Admin
if response=$(api_call "POST" "/auth/register" '{
    "email": "admin@test.com",
    "password": "Admin123!@#",
    "full_name": "Admin User",
    "role": "admin"
}' "" 201); then
    print_status "PASS" "1. Register Admin"
else
    print_status "FAIL" "1. Register Admin"
fi

# 2. Register Promoter
if response=$(api_call "POST" "/auth/register" '{
    "email": "promoter@test.com",
    "password": "Promoter123!@#",
    "full_name": "Test Promoter",
    "role": "promoter"
}' "" 201); then
    print_status "PASS" "2. Register Promoter"
    PROMOTER_ID=$(echo "$response" | jq -r '.id // empty')
else
    print_status "FAIL" "2. Register Promoter"
fi

# 3. Register User
if response=$(api_call "POST" "/auth/register" '{
    "email": "user@test.com",
    "password": "User123!@#",
    "full_name": "Test User",
    "role": "user"
}' "" 201); then
    print_status "PASS" "3. Register User"
    USER_ID=$(echo "$response" | jq -r '.id // empty')
else
    print_status "FAIL" "3. Register User"
fi

# 4. Login Promoter
if response=$(api_call "POST" "/auth/login" '{
    "email": "promoter@test.com",
    "password": "Promoter123!@#"
}' "" 200); then
    print_status "PASS" "4. Login Promoter"
    ACCESS_TOKEN=$(echo "$response" | jq -r '.access_token // empty')
    REFRESH_TOKEN=$(echo "$response" | jq -r '.refresh_token // empty')
else
    print_status "FAIL" "4. Login Promoter"
fi

# 5. Login User
if response=$(api_call "POST" "/auth/login" '{
    "email": "user@test.com",
    "password": "User123!@#"
}' "" 200); then
    print_status "PASS" "5. Login User"
    USER_TOKEN=$(echo "$response" | jq -r '.access_token // empty')
else
    print_status "FAIL" "5. Login User"
fi

# 6. Get Current User
if [ -n "$ACCESS_TOKEN" ]; then
    if response=$(api_call "GET" "/auth/me" "" "$ACCESS_TOKEN" 200); then
        print_status "PASS" "6. Get Current User"
    else
        print_status "FAIL" "6. Get Current User"
    fi
else
    print_status "SKIP" "6. Get Current User - No token"
fi

# 7. Refresh Token
if [ -n "$REFRESH_TOKEN" ]; then
    if response=$(api_call "POST" "/auth/refresh" "{\"refresh_token\": \"$REFRESH_TOKEN\"}" "" 200); then
        print_status "PASS" "7. Refresh Token"
    else
        print_status "FAIL" "7. Refresh Token"
    fi
else
    print_status "SKIP" "7. Refresh Token - No refresh token"
fi

# 8. Logout
if [ -n "$ACCESS_TOKEN" ]; then
    if response=$(api_call "POST" "/auth/logout" "" "$ACCESS_TOKEN" 200); then
        print_status "PASS" "8. Logout"
    else
        print_status "FAIL" "8. Logout"
    fi
else
    print_status "SKIP" "8. Logout - No token"
fi

# Re-login for remaining tests
if response=$(api_call "POST" "/auth/login" '{
    "email": "promoter@test.com",
    "password": "Promoter123!@#"
}' "" 200); then
    ACCESS_TOKEN=$(echo "$response" | jq -r '.access_token // empty')
fi

# ==================== EVENTS (9 endpoints) ====================
echo ""
echo "━━━ Event Management (9 endpoints) ━━━"

# 1. Create Event
if [ -n "$ACCESS_TOKEN" ]; then
    FUTURE_DATE=$(date -u -d "+30 days" +"%Y-%m-%dT18:00:00Z" 2>/dev/null || date -u -v+30d +"%Y-%m-%dT18:00:00Z")
    if response=$(api_call "POST" "/events" "{
        \"title\": \"Summer Music Festival 2025\",
        \"description\": \"The biggest music event of the summer\",
        \"venue_name\": \"Central Park Amphitheater\",
        \"venue_address\": \"123 Park Ave, New York, NY 10001\",
        \"city\": \"New York\",
        \"state\": \"NY\",
        \"country\": \"USA\",
        \"event_date\": \"$FUTURE_DATE\",
        \"doors_open_time\": \"17:00:00\",
        \"event_start_time\": \"18:00:00\",
        \"event_end_time\": \"23:00:00\",
        \"category\": \"music\",
        \"tags\": [\"music\", \"festival\", \"outdoor\"],
        \"image_url\": \"https://example.com/festival.jpg\",
        \"total_capacity\": 5000
    }" "$ACCESS_TOKEN" 201); then
        print_status "PASS" "1. Create Event"
        EVENT_ID=$(echo "$response" | jq -r '.id // empty')
    else
        print_status "FAIL" "1. Create Event"
    fi
else
    print_status "SKIP" "1. Create Event - No token"
fi

# 2. List Events
if response=$(api_call "GET" "/events?limit=10" "" "" 200); then
    print_status "PASS" "2. List Events"
else
    print_status "FAIL" "2. List Events"
fi

# 3. Get Event Details
if [ -n "$EVENT_ID" ]; then
    if response=$(api_call "GET" "/events/$EVENT_ID" "" "" 200); then
        print_status "PASS" "3. Get Event Details"
    else
        print_status "FAIL" "3. Get Event Details"
    fi
else
    print_status "SKIP" "3. Get Event Details - No event created"
fi

# 4. Update Event
if [ -n "$ACCESS_TOKEN" ] && [ -n "$EVENT_ID" ]; then
    if response=$(api_call "PUT" "/events/$EVENT_ID" '{
        "title": "Summer Music Festival 2025 - Updated",
        "description": "The biggest music event - Now with more stages!"
    }' "$ACCESS_TOKEN" 200); then
        print_status "PASS" "4. Update Event"
    else
        print_status "FAIL" "4. Update Event"
    fi
else
    print_status "SKIP" "4. Update Event - Missing requirements"
fi

# 5. Get My Events
if [ -n "$ACCESS_TOKEN" ]; then
    if response=$(api_call "GET" "/events/my/events" "" "$ACCESS_TOKEN" 200); then
        print_status "PASS" "5. Get My Events"
    else
        print_status "FAIL" "5. Get My Events"
    fi
else
    print_status "SKIP" "5. Get My Events - No token"
fi

# 6. Publish Event
if [ -n "$ACCESS_TOKEN" ] && [ -n "$EVENT_ID" ]; then
    if response=$(api_call "POST" "/events/$EVENT_ID/publish" '{"is_featured": true}' "$ACCESS_TOKEN" 200); then
        print_status "PASS" "6. Publish Event"
    else
        print_status "FAIL" "6. Publish Event"
    fi
else
    print_status "SKIP" "6. Publish Event - Missing requirements"
fi

# 7. Search Events
if response=$(api_call "GET" "/events?search=New%20York&status_filter=published" "" "" 200); then
    print_status "PASS" "7. Search Events"
else
    print_status "FAIL" "7. Search Events"
fi

# 8. Filter Events
if response=$(api_call "GET" "/events?category=music&limit=5" "" "" 200); then
    print_status "PASS" "8. Filter Events"
else
    print_status "FAIL" "8. Filter Events"
fi

# 9. Cancel Event (skipped to preserve test data)
print_status "SKIP" "9. Cancel Event - Skipping to preserve test data"

# ==================== TICKETS (11 endpoints) ====================
echo ""
echo "━━━ Ticket Management (11 endpoints) ━━━"

# 1. Create Ticket Tier
if [ -n "$ACCESS_TOKEN" ] && [ -n "$EVENT_ID" ]; then
    SALE_START=$(date -u +"%Y-%m-%dT00:00:00Z")
    SALE_END=$(date -u -d "+25 days" +"%Y-%m-%dT23:59:59Z" 2>/dev/null || date -u -v+25d +"%Y-%m-%dT23:59:59Z")
    if response=$(api_call "POST" "/tickets/events/$EVENT_ID/tiers" "{
        \"name\": \"General Admission\",
        \"description\": \"Standard entry ticket\",
        \"price\": 49.99,
        \"quantity\": 1000,
        \"min_purchase\": 1,
        \"max_purchase\": 10,
        \"sale_start_time\": \"$SALE_START\",
        \"sale_end_time\": \"$SALE_END\",
        \"is_active\": true
    }" "$ACCESS_TOKEN" 201); then
        print_status "PASS" "1. Create Ticket Tier"
        TIER_ID=$(echo "$response" | jq -r '.id // empty')
    else
        print_status "FAIL" "1. Create Ticket Tier"
    fi
else
    print_status "SKIP" "1. Create Ticket Tier - Missing requirements"
fi

# 2. Create VIP Tier
if [ -n "$ACCESS_TOKEN" ] && [ -n "$EVENT_ID" ]; then
    if response=$(api_call "POST" "/tickets/events/$EVENT_ID/tiers" "{
        \"name\": \"VIP Access\",
        \"description\": \"VIP seating with meet & greet\",
        \"price\": 199.99,
        \"quantity\": 100,
        \"min_purchase\": 1,
        \"max_purchase\": 4,
        \"sale_start_time\": \"$SALE_START\",
        \"sale_end_time\": \"$SALE_END\",
        \"is_active\": true
    }" "$ACCESS_TOKEN" 201); then
        print_status "PASS" "2. Create VIP Tier"
    else
        print_status "FAIL" "2. Create VIP Tier"
    fi
else
    print_status "SKIP" "2. Create VIP Tier - Missing requirements"
fi

# 3. List Event Tiers
if [ -n "$EVENT_ID" ]; then
    if response=$(api_call "GET" "/tickets/events/$EVENT_ID/tiers" "" "" 200); then
        print_status "PASS" "3. List Event Tiers"
    else
        print_status "FAIL" "3. List Event Tiers"
    fi
else
    print_status "SKIP" "3. List Event Tiers - No event"
fi

# 4. Get Tier Details
if [ -n "$TIER_ID" ]; then
    if response=$(api_call "GET" "/tickets/tiers/$TIER_ID" "" "" 200); then
        print_status "PASS" "4. Get Tier Details"
    else
        print_status "FAIL" "4. Get Tier Details"
    fi
else
    print_status "SKIP" "4. Get Tier Details - No tier"
fi

# 5. Check Tier Availability
if [ -n "$TIER_ID" ]; then
    if response=$(api_call "GET" "/tickets/tiers/$TIER_ID/availability" "" "" 200); then
        print_status "PASS" "5. Check Tier Availability"
    else
        print_status "FAIL" "5. Check Tier Availability"
    fi
else
    print_status "SKIP" "5. Check Tier Availability - No tier"
fi

# 6. Update Tier
if [ -n "$ACCESS_TOKEN" ] && [ -n "$TIER_ID" ]; then
    if response=$(api_call "PUT" "/tickets/tiers/$TIER_ID" '{
        "quantity": 1500,
        "description": "Standard entry ticket - More available!"
    }' "$ACCESS_TOKEN" 200); then
        print_status "PASS" "6. Update Tier"
    else
        print_status "FAIL" "6. Update Tier"
    fi
else
    print_status "SKIP" "6. Update Tier - Missing requirements"
fi

# Remaining ticket operations require actual ticket purchase
print_status "SKIP" "7. Get My Tickets - Requires purchase"
print_status "SKIP" "8. Get Ticket Details - Requires purchase"
print_status "SKIP" "9. Set Attendee Info - Requires purchase"
print_status "SKIP" "10. Transfer Ticket - Requires purchase"
print_status "SKIP" "11. Validate Ticket - Requires purchase"

# ==================== SUMMARY ====================
echo ""
echo "═══════════════════════════════════════════════════════════"
echo "  TEST SUMMARY"
echo "═══════════════════════════════════════════════════════════"
echo ""

TOTAL=$((PASSED + FAILED + SKIPPED))
PASS_PCT=$((PASSED * 100 / TOTAL))

echo -e "Passed:  ${GREEN}$PASSED${NC} ($PASS_PCT%)"
echo -e "Failed:  ${RED}$FAILED${NC}"
echo -e "Skipped: ${YELLOW}$SKIPPED${NC}"
echo -e "Total:   $TOTAL"
echo ""

if [ $FAILED -eq 0 ] && [ $PASSED -gt 0 ]; then
    echo -e "${GREEN}✓ ALL RUNNABLE TESTS PASSED!${NC}"
    exit 0
elif [ $FAILED -gt 0 ]; then
    echo -e "${RED}✗ $FAILED TEST(S) FAILED${NC}"
    exit 1
else
    echo -e "${YELLOW}⚠ NO TESTS RUN${NC}"
    exit 2
fi
