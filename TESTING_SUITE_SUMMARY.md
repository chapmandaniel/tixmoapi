# 🧪 API Testing Suite - Ready to Use!

## 📦 What You Have

A complete testing suite for all **28 endpoints** across Authentication, Events, and Tickets.

---

## 🎯 Quick Start (3 Options)

### Option 1: Python Test Suite (Recommended) ⭐

**Best for:** Automated comprehensive testing

```bash
# Install dependencies
pip install httpx rich

# Run all tests
python test_api_comprehensive.py
```

**Features:**
- ✅ Tests all 28 endpoints automatically
- ✅ Beautiful colored output
- ✅ Detailed error reporting
- ✅ Saves results to JSON
- ✅ Auto-handles auth flow

---

### Option 2: Bash/Curl Script

**Best for:** Quick testing without Python

```bash
# Make executable (if needed)
chmod +x test_api_curl.sh

# Run tests
./test_api_curl.sh

# With verbose output
VERBOSE=true ./test_api_curl.sh
```

**Requirements:** bash, curl, jq

---

### Option 3: Postman Collection

**Best for:** Manual testing and API exploration

1. Open Postman
2. Import `Ticket_Vendor_API_Postman_Collection.json`
3. Run requests individually or as a collection

**Features:**
- ✅ All 28 endpoints organized
- ✅ Auto-saves tokens and IDs
- ✅ Environment variables setup
- ✅ Can run entire collection

---

## 📋 Files Included

### Test Scripts

1. **`test_api_comprehensive.py`** (21 KB)
   - Python async test suite
   - Uses httpx and rich libraries
   - Comprehensive error handling
   - JSON results output

2. **`test_api_curl.sh`** (14 KB)
   - Bash script using curl
   - No Python dependencies
   - Colored terminal output
   - Pass/Fail/Skip tracking

3. **`Ticket_Vendor_API_Postman_Collection.json`** (20 KB)
   - Complete Postman collection
   - 28 endpoints organized
   - Auto-scripting for tokens
   - Environment variable support

### Documentation

4. **`API_TESTING_GUIDE.md`** (15 KB)
   - Complete testing guide
   - Setup instructions
   - Troubleshooting tips
   - curl examples for all endpoints

---

## 🔧 Prerequisites

### Required

1. **API Server Running**
   ```bash
   # Start the API (in project directory)
   uvicorn src.main:app --reload
   
   # Verify it's running
   curl http://localhost:8000/health
   ```

2. **Database Connected**
   - PostgreSQL running
   - Migrations applied
   - Connection configured

### Optional

```bash
# For Python suite
pip install httpx rich

# For curl script
sudo apt-get install jq  # Ubuntu
brew install jq          # macOS
```

---

## 🚀 Running Tests

### Before Running Tests

**Start the API:**
```bash
# In your project directory
cd /path/to/ticket-vendor-api
source venv/bin/activate
uvicorn src.main:app --reload
```

**Verify API is healthy:**
```bash
curl http://localhost:8000/health
```

### Run Full Test Suite

**Python (Comprehensive):**
```bash
python test_api_comprehensive.py
```

**Bash (Quick):**
```bash
./test_api_curl.sh
```

**Expected Results:**
- ✅ Passed: ~18-20 tests
- ⊘ Skipped: ~8-10 tests (require purchase flow)
- ✗ Failed: 0 tests (if API is working)

---

## 📊 What Gets Tested

### 🔐 Authentication (8 endpoints)

1. Register Admin
2. Register Promoter
3. Register User
4. Login Promoter
5. Login User
6. Get Current User
7. Refresh Token
8. Logout

### 🎪 Events (9 endpoints)

1. Create Event
2. List Events
3. Get Event Details
4. Update Event
5. Get My Events
6. Publish Event
7. Search Events
8. Filter Events
9. Cancel Event

### 🎫 Tickets (11 endpoints)

1. Create Ticket Tier
2. Create VIP Tier
3. List Event Tiers
4. Get Tier Details
5. Check Tier Availability
6. Update Tier
7. Delete Tier
8. Get My Tickets*
9. Get Ticket Details*
10. Set Attendee Info*
11. Validate Ticket*

*Requires actual ticket purchase (skipped in automated tests)

---

## 📈 Test Flow

The automated tests follow this flow:

```
1. Health Check
   ↓
2. Create Test Users (admin, promoter, user)
   ↓
3. Login & Get Tokens
   ↓
4. Create Test Event
   ↓
5. Publish Event
   ↓
6. Create Ticket Tiers
   ↓
7. Test All CRUD Operations
   ↓
8. Generate Report
```

---

## 🎨 Example Output

### Python Test Suite

```
═══ Testing Authentication (8 endpoints) ═══
✓ PASS 1. Register Admin User - POST /auth/register
✓ PASS 2. Register Promoter User - POST /auth/register
✓ PASS 3. Register Regular User - POST /auth/register
✓ PASS 4. Login Promoter - POST /auth/login
✓ PASS 5. Login User - POST /auth/login
✓ PASS 6. Get Current User - GET /auth/me
✓ PASS 7. Refresh Token - POST /auth/refresh
✓ PASS 8. Logout - POST /auth/logout

═══ Testing Event Management (9 endpoints) ═══
✓ PASS 1. Create Event - POST /events
✓ PASS 2. List Events - GET /events
...

TEST SUMMARY
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
Status          Count    Percentage
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
Passed             18        64.3%
Failed              0         0.0%
Skipped            10        35.7%
Total              28       100.0%

✓ ALL TESTS PASSED!
```

### Curl Script

```
━━━ Authentication (8 endpoints) ━━━
✓ PASS 1. Register Admin
✓ PASS 2. Register Promoter
✓ PASS 3. Register User
✓ PASS 4. Login Promoter
✓ PASS 5. Login User
✓ PASS 6. Get Current User
✓ PASS 7. Refresh Token
✓ PASS 8. Logout

TEST SUMMARY
═══════════════════════════════════════════
Passed:  18 (64%)
Failed:  0
Skipped: 10
Total:   28

✓ ALL RUNNABLE TESTS PASSED!
```

---

## 🔍 Troubleshooting

### "Connection Refused"

**Problem:** API not running

**Solution:**
```bash
cd /path/to/project
uvicorn src.main:app --reload
```

### "401 Unauthorized"

**Problem:** Token expired or invalid

**Solution:**
- Tests handle this automatically
- For manual testing: login again

### "Database Error"

**Problem:** PostgreSQL not running or configured

**Solution:**
```bash
# Check PostgreSQL status
sudo systemctl status postgresql

# Verify connection in .env file
DATABASE_URL=postgresql://user:pass@localhost:5432/dbname
```

### "Import Error: httpx"

**Problem:** Python dependencies not installed

**Solution:**
```bash
pip install httpx rich
```

### "jq: command not found"

**Problem:** jq not installed (for curl script)

**Solution:**
```bash
sudo apt-get install jq  # Ubuntu/Debian
brew install jq          # macOS
```

---

## 📚 Additional Resources

### Documentation Files

- **`API_TESTING_GUIDE.md`** - Complete guide with curl examples
- **`EXECUTIVE_SUMMARY.md`** - Project status and progress
- **`TICKET_MANAGEMENT_COMPLETE.md`** - Ticket system docs
- **`EVENT_MANAGEMENT_COMPLETE.md`** - Event system docs

### Interactive API Docs

When API is running, visit:
- **Swagger UI:** http://localhost:8000/docs
- **ReDoc:** http://localhost:8000/redoc

---

## 🎯 Quick Testing Scenarios

### Scenario 1: Happy Path Test

```bash
# 1. Start API
uvicorn src.main:app --reload

# 2. Run tests
python test_api_comprehensive.py

# 3. Check results
cat test_results.json
```

### Scenario 2: Manual Exploration

```bash
# 1. Import Postman collection
# 2. Run "Authentication" folder
# 3. Token auto-saved
# 4. Test other endpoints
```

### Scenario 3: Quick Smoke Test

```bash
# Test if API is working
./test_api_curl.sh

# Should show mostly passing tests
```

---

## 📊 Success Criteria

✅ **Tests are working if:**
- Health check passes
- User registration works
- Login returns tokens
- Events can be created
- Tiers can be created
- No unexpected failures

⚠️ **Expected skips:**
- Ticket operations (7-11) - require purchase flow
- Some destructive operations (delete, cancel)

❌ **Investigate if:**
- Connection refused errors
- Multiple authentication failures
- Database connection errors
- Consistent 500 errors

---

## 🚀 Next Steps

After successful testing:

1. **Review Results**
   - Check `test_results.json` for details
   - Identify any issues

2. **Test Complete Workflows**
   - Create event → Add tiers → Purchase (when order system ready)
   - User journey testing

3. **Performance Testing**
   - Load testing with concurrent users
   - Stress testing with large datasets

4. **Integration Testing**
   - Test with order processing
   - Test with payment integration

---

## 💡 Tips

**Best Practices:**
- Always start with health check
- Run tests in clean database state
- Check logs for detailed errors
- Use verbose mode for debugging

**Performance:**
- Python suite is faster for bulk testing
- Postman better for interactive exploration
- Curl script good for CI/CD pipelines

**Maintenance:**
- Update collection when adding endpoints
- Keep test data realistic
- Document test scenarios

---

## 📞 Summary

You now have:
- ✅ 3 different ways to test the API
- ✅ Comprehensive test coverage (28 endpoints)
- ✅ Automated and manual testing options
- ✅ Complete documentation
- ✅ Troubleshooting guide

**All files are ready to use in `/mnt/user-data/outputs/`**

---

**Happy Testing! 🧪**

Questions? Check `API_TESTING_GUIDE.md` for detailed examples.
