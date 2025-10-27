# 🧪 API Testing Guide - Ticket Vendor API

Complete guide for testing all 28 endpoints across Authentication, Events, and Tickets.

---

## 📋 Table of Contents

1. [Quick Start](#quick-start)
2. [Prerequisites](#prerequisites)
3. [Testing Methods](#testing-methods)
4. [Setup & Installation](#setup--installation)
5. [Running Tests](#running-tests)
6. [Testing Each Module](#testing-each-module)
7. [Troubleshooting](#troubleshooting)
8. [API Reference](#api-reference)

---

## 🚀 Quick Start

**Fastest way to test:**

```bash
# Method 1: Python test suite (recommended)
pip install httpx rich
python test_api_comprehensive.py

# Method 2: Bash/curl script
chmod +x test_api_curl.sh
./test_api_curl.sh

# Method 3: Import Postman collection
# Import: Ticket_Vendor_API_Postman_Collection.json
```

---

## 📦 Prerequisites

### Required

1. **Running API Server**
   ```bash
   # The API must be running at http://localhost:8000
   # Start it with:
   cd /path/to/project
   uvicorn src.main:app --reload
   ```

2. **Database Connection**
   - PostgreSQL database must be running
   - Migrations applied
   - Connection string configured in `.env`

### Optional (for automated tests)

```bash
# For Python test suite
pip install httpx rich

# For curl script
# jq (JSON processor)
sudo apt-get install jq  # Ubuntu/Debian
brew install jq          # macOS
```

---

## 🔧 Testing Methods

### Method 1: Python Test Suite (Recommended) ⭐

**Best for:** Comprehensive automated testing with detailed reports

**Features:**
- Tests all 28 endpoints automatically
- Beautiful formatted output with colors
- Detailed error messages
- JSON results file
- Handles authentication flow
- Auto-saves tokens and IDs

**Usage:**
```bash
python test_api_comprehensive.py
```

**Output:**
- Real-time test results with colored status
- Summary table with pass/fail/skip counts
- JSON report saved to `test_results.json`

---

### Method 2: Bash/Curl Script

**Best for:** Quick testing without Python dependencies

**Features:**
- Pure bash script using curl
- Tests 28 endpoints
- Colored output
- No external dependencies except jq

**Usage:**
```bash
chmod +x test_api_curl.sh
./test_api_curl.sh

# With verbose mode
VERBOSE=true ./test_api_curl.sh

# Custom API URL
API_BASE_URL=http://localhost:8080 ./test_api_curl.sh
```

---

### Method 3: Postman Collection

**Best for:** Manual testing and exploration

**Setup:**
1. Open Postman
2. Click "Import"
3. Select `Ticket_Vendor_API_Postman_Collection.json`
4. Collection will appear in left sidebar

**Usage:**
1. Run "1. Authentication" → "4. Login Promoter"
2. Access token auto-saved to environment
3. Test other endpoints as needed
4. Can run entire collection with "Run collection"

**Environment Variables:**
- `base_url` - API base URL (default: http://localhost:8000)
- `access_token` - Auto-populated on login
- `refresh_token` - Auto-populated on login
- `event_id` - Auto-populated on event creation
- `tier_id` - Auto-populated on tier creation

---

## 📥 Setup & Installation

### 1. Start the API

```bash
# Navigate to project directory
cd /path/to/ticket-vendor-api

# Activate virtual environment
source venv/bin/activate  # or `venv\Scripts\activate` on Windows

# Install dependencies
pip install -r requirements.txt

# Start the server
uvicorn src.main:app --reload
```

**Verify API is running:**
```bash
curl http://localhost:8000/health
# Should return: {"status":"healthy","timestamp":"..."}
```

### 2. Install Test Dependencies

**For Python test suite:**
```bash
pip install httpx rich
```

**For curl script:**
```bash
# Ubuntu/Debian
sudo apt-get install jq curl

# macOS
brew install jq curl
```

---

## 🏃 Running Tests

### Full Test Suite

```bash
# Python suite - all tests
python test_api_comprehensive.py

# Curl script - all tests
./test_api_curl.sh
```

### Test Specific Modules

**Python Suite** (modify main() function):
```python
# Test only authentication
await test_authentication(tester)

# Test only events
await test_events(tester)

# Test only tickets
await test_tickets(tester)
```

**Curl Script** (comment out sections):
```bash
# Edit test_api_curl.sh
# Comment out unwanted test sections
```

---

## 🎯 Testing Each Module

### 1. Health Check (1 endpoint)

**Endpoint:** `GET /health`

```bash
# Curl
curl http://localhost:8000/health

# Expected response
{
  "status": "healthy",
  "timestamp": "2025-10-26T...",
  "features": {
    "authentication": "enabled",
    "events": "enabled",
    "tickets": "enabled"
  }
}
```

---

### 2. Authentication (8 endpoints)

#### A. Register Users

```bash
# Register Admin
curl -X POST http://localhost:8000/auth/register \
  -H "Content-Type: application/json" \
  -d '{
    "email": "admin@test.com",
    "password": "Admin123!@#",
    "full_name": "Admin User",
    "role": "admin"
  }'

# Register Promoter
curl -X POST http://localhost:8000/auth/register \
  -H "Content-Type: application/json" \
  -d '{
    "email": "promoter@test.com",
    "password": "Promoter123!@#",
    "full_name": "Test Promoter",
    "role": "promoter"
  }'

# Register User
curl -X POST http://localhost:8000/auth/register \
  -H "Content-Type: application/json" \
  -d '{
    "email": "user@test.com",
    "password": "User123!@#",
    "full_name": "Test User",
    "role": "user"
  }'
```

#### B. Login

```bash
# Login as Promoter
curl -X POST http://localhost:8000/auth/login \
  -H "Content-Type: application/json" \
  -d '{
    "email": "promoter@test.com",
    "password": "Promoter123!@#"
  }'

# Response
{
  "access_token": "eyJ0eXAiOiJKV1QiLCJhbGc...",
  "refresh_token": "eyJ0eXAiOiJKV1QiLCJhbGc...",
  "token_type": "bearer",
  "user": {...}
}

# Save the access_token for subsequent requests
TOKEN="eyJ0eXAiOiJKV1QiLCJhbGc..."
```

#### C. Protected Endpoints

```bash
# Get current user
curl http://localhost:8000/auth/me \
  -H "Authorization: Bearer $TOKEN"

# Refresh token
curl -X POST http://localhost:8000/auth/refresh \
  -H "Content-Type: application/json" \
  -d "{\"refresh_token\": \"$REFRESH_TOKEN\"}"

# Logout
curl -X POST http://localhost:8000/auth/logout \
  -H "Authorization: Bearer $TOKEN"
```

---

### 3. Events (9 endpoints)

#### A. Create Event

```bash
curl -X POST http://localhost:8000/events \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "title": "Summer Music Festival 2025",
    "description": "The biggest music event of the summer",
    "venue_name": "Central Park Amphitheater",
    "venue_address": "123 Park Ave, New York, NY 10001",
    "city": "New York",
    "state": "NY",
    "country": "USA",
    "event_date": "2025-07-15T18:00:00Z",
    "doors_open_time": "17:00:00",
    "event_start_time": "18:00:00",
    "event_end_time": "23:00:00",
    "category": "music",
    "tags": ["music", "festival", "outdoor"],
    "image_url": "https://example.com/festival.jpg",
    "total_capacity": 5000
  }'

# Save EVENT_ID from response
EVENT_ID=1
```

#### B. List & Search Events

```bash
# List all events
curl "http://localhost:8000/events?limit=10"

# Search events
curl "http://localhost:8000/events?search=Music&status_filter=published"

# Filter by category
curl "http://localhost:8000/events?category=music"

# Filter by city
curl "http://localhost:8000/events?search=New%20York"
```

#### C. Event Details & Updates

```bash
# Get event details
curl "http://localhost:8000/events/$EVENT_ID"

# Update event
curl -X PUT "http://localhost:8000/events/$EVENT_ID" \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "title": "Summer Music Festival 2025 - UPDATED",
    "description": "Now with more stages!"
  }'

# Get my events (promoter)
curl "http://localhost:8000/events/my/events" \
  -H "Authorization: Bearer $TOKEN"
```

#### D. Event Status Management

```bash
# Publish event
curl -X POST "http://localhost:8000/events/$EVENT_ID/publish" \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"is_featured": true}'

# Cancel event
curl -X POST "http://localhost:8000/events/$EVENT_ID/cancel" \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "cancellation_reason": "Venue unavailable",
    "refund_policy": "Full refund"
  }'

# Complete event
curl -X POST "http://localhost:8000/events/$EVENT_ID/complete" \
  -H "Authorization: Bearer $TOKEN"

# Delete event (soft delete)
curl -X DELETE "http://localhost:8000/events/$EVENT_ID" \
  -H "Authorization: Bearer $TOKEN"
```

---

### 4. Tickets (11 endpoints)

#### A. Create Ticket Tiers

```bash
# Create General Admission tier
curl -X POST "http://localhost:8000/tickets/events/$EVENT_ID/tiers" \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "name": "General Admission",
    "description": "Standard entry ticket",
    "price": 49.99,
    "quantity": 1000,
    "min_purchase": 1,
    "max_purchase": 10,
    "sale_start_time": "2025-10-27T00:00:00Z",
    "sale_end_time": "2025-07-14T23:59:59Z",
    "is_active": true
  }'

# Save TIER_ID from response
TIER_ID=1

# Create VIP tier
curl -X POST "http://localhost:8000/tickets/events/$EVENT_ID/tiers" \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "name": "VIP Access",
    "description": "VIP seating with meet & greet",
    "price": 199.99,
    "quantity": 100,
    "min_purchase": 1,
    "max_purchase": 4,
    "sale_start_time": "2025-10-27T00:00:00Z",
    "sale_end_time": "2025-07-14T23:59:59Z",
    "is_active": true
  }'
```

#### B. View Tiers

```bash
# List all tiers for event
curl "http://localhost:8000/tickets/events/$EVENT_ID/tiers"

# Get tier details
curl "http://localhost:8000/tickets/tiers/$TIER_ID"

# Check availability
curl "http://localhost:8000/tickets/tiers/$TIER_ID/availability"

# Response:
{
  "tier_id": 1,
  "tier_name": "General Admission",
  "price": 49.99,
  "available": 1000,
  "sold": 0,
  "quantity": 1000,
  "is_sold_out": false,
  "is_on_sale": true,
  "can_purchase": true,
  "message": null
}
```

#### C. Update & Delete Tiers

```bash
# Update tier
curl -X PUT "http://localhost:8000/tickets/tiers/$TIER_ID" \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "quantity": 1500,
    "description": "Standard entry - More tickets available!"
  }'

# Delete tier (only if no tickets sold)
curl -X DELETE "http://localhost:8000/tickets/tiers/$TIER_ID" \
  -H "Authorization: Bearer $TOKEN"
```

#### D. Ticket Operations (requires purchase)

```bash
# Get my tickets
curl "http://localhost:8000/tickets/my/tickets" \
  -H "Authorization: Bearer $USER_TOKEN"

# Get ticket details
curl "http://localhost:8000/tickets/$TICKET_ID" \
  -H "Authorization: Bearer $USER_TOKEN"

# Set attendee info
curl -X PATCH "http://localhost:8000/tickets/$TICKET_ID/attendee" \
  -H "Authorization: Bearer $USER_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "attendee_name": "Jane Smith",
    "attendee_email": "jane@example.com",
    "attendee_phone": "+1234567890"
  }'

# Transfer ticket
curl -X POST "http://localhost:8000/tickets/$TICKET_ID/transfer" \
  -H "Authorization: Bearer $USER_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"recipient_email": "recipient@example.com"}'

# Validate ticket (check-in)
curl -X POST "http://localhost:8000/tickets/validate" \
  -H "Authorization: Bearer $PROMOTER_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"ticket_uuid": "550e8400-e29b-41d4-a716-446655440000"}'
```

---

## 🔍 Troubleshooting

### API Not Running

```bash
# Check if API is accessible
curl http://localhost:8000/health

# If connection refused:
# 1. Start the API server
# 2. Check port 8000 is not in use
# 3. Verify firewall settings
```

### Authentication Failures

```bash
# Common issues:
# 1. Token expired - login again
# 2. Wrong role - use correct user type
# 3. Invalid credentials - check password

# Debug: View token contents
echo $TOKEN | cut -d. -f2 | base64 -d | jq
```

### Database Errors

```bash
# Common fixes:
# 1. Check PostgreSQL is running
# 2. Verify connection string in .env
# 3. Run migrations
# 4. Check database exists
```

### Permission Denied

```bash
# Common causes:
# 1. Wrong user role (user trying to create event)
# 2. Not event owner (updating someone else's event)
# 3. Missing/expired token

# Fix: Login with correct user type
```

---

## 📚 API Reference

### Endpoint Summary

| Module | Endpoint Count | Auth Required |
|--------|----------------|---------------|
| Health | 1 | No |
| Authentication | 8 | Varies |
| Events | 9 | Some |
| Tickets | 11 | Some |
| **Total** | **28** | - |

### Response Codes

| Code | Meaning | Common Cause |
|------|---------|--------------|
| 200 | Success | Request succeeded |
| 201 | Created | Resource created |
| 400 | Bad Request | Invalid data |
| 401 | Unauthorized | Missing/invalid token |
| 403 | Forbidden | Wrong permissions |
| 404 | Not Found | Resource doesn't exist |
| 422 | Validation Error | Invalid field values |
| 500 | Server Error | Internal error |

---

## 📊 Test Results

### Expected Results

**Full Test Run:**
- Passed: ~18-20 tests
- Failed: 0 tests
- Skipped: 8-10 tests (ticket operations requiring purchase)

**Test Coverage:**
- ✅ Authentication: 8/8 tests
- ✅ Events: 8/9 tests (cancel skipped)
- ✅ Tickets: 6/11 tests (5 require purchase)

### Interpreting Results

**Green (PASS):** Endpoint working correctly
**Red (FAIL):** Issue with endpoint or setup
**Yellow (SKIP):** Test skipped (requires additional setup)

---

## 🎯 Next Steps

After testing:

1. **Review Results**
   - Check `test_results.json` for details
   - Investigate any failures

2. **Integration Testing**
   - Test complete workflows
   - Test with order processing (when implemented)

3. **Performance Testing**
   - Load test with multiple concurrent requests
   - Test with large datasets

4. **Security Testing**
   - Verify authorization checks
   - Test SQL injection protection
   - Test XSS protection

---

## 📞 Support

**Common Resources:**
- API Documentation: `/docs` (Swagger UI)
- Project README: `README.md`
- Architecture Docs: `docs/ARCHITECTURE.md`
- Database Schema: `docs/DATABASE.md`

**Test Files:**
- Python Suite: `test_api_comprehensive.py`
- Curl Script: `test_api_curl.sh`
- Postman Collection: `Ticket_Vendor_API_Postman_Collection.json`

---

**Happy Testing! 🧪**
