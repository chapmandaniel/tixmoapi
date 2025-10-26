# 🚀 EVENT MANAGEMENT API - QUICK REFERENCE

## 📡 API Endpoints Cheat Sheet

### Public Endpoints (No Auth Required)

```bash
# List all published events
GET /events?status_filter=published

# Search events
GET /events?search=music&category=concert

# Get event details
GET /events/{event_id}

# Filter by location
GET /events?search=New+York

# Get featured events
GET /events?is_featured=true

# Pagination
GET /events?skip=0&limit=20
```

### Promoter Endpoints (Auth Required)

```bash
# Create new event
POST /events
Headers: Authorization: Bearer {token}
Body: EventCreate JSON

# Update event
PUT /events/{event_id}
Headers: Authorization: Bearer {token}
Body: EventUpdate JSON

# Delete event (soft delete)
DELETE /events/{event_id}
Headers: Authorization: Bearer {token}

# Publish event
POST /events/{event_id}/publish
Headers: Authorization: Bearer {token}
Body: {"is_featured": true}

# Cancel event
POST /events/{event_id}/cancel
Headers: Authorization: Bearer {token}
Body: {"reason": "...", "refund_attendees": true}

# Mark completed
POST /events/{event_id}/complete
Headers: Authorization: Bearer {token}

# Get my events
GET /events/my/events
Headers: Authorization: Bearer {token}
```

---

## 🎯 Common Request Bodies

### Create Event

```json
{
  "title": "Summer Music Festival 2025",
  "description": "An amazing outdoor concert featuring top artists",
  "venue_name": "Central Park",
  "venue_address": "123 Park Avenue",
  "venue_city": "New York",
  "venue_state": "NY",
  "venue_country": "US",
  "venue_latitude": 40.7829,
  "venue_longitude": -73.9654,
  "start_time": "2025-07-15T18:00:00Z",
  "end_time": "2025-07-15T23:00:00Z",
  "doors_open_time": "2025-07-15T17:00:00Z",
  "timezone": "America/New_York",
  "capacity": 5000,
  "age_restriction": 18,
  "is_private": false,
  "featured_image_url": "https://example.com/image.jpg",
  "banner_image_url": "https://example.com/banner.jpg",
  "category": "music",
  "tags": ["outdoor", "festival", "summer", "concert"]
}
```

### Update Event (Partial)

```json
{
  "description": "Updated description with new artist lineup!",
  "featured_image_url": "https://example.com/new-image.jpg"
}
```

### Publish Event

```json
{
  "is_featured": true
}
```

### Cancel Event

```json
{
  "reason": "Weather conditions unsafe",
  "refund_attendees": true
}
```

---

## 📊 Response Examples

### Event Response

```json
{
  "id": 123,
  "uuid": "550e8400-e29b-41d4-a716-446655440000",
  "title": "Summer Music Festival 2025",
  "description": "An amazing outdoor concert",
  "status": "published",
  "venue_name": "Central Park",
  "venue_city": "New York",
  "venue_state": "NY",
  "venue_country": "US",
  "start_time": "2025-07-15T18:00:00Z",
  "end_time": "2025-07-15T23:00:00Z",
  "timezone": "America/New_York",
  "capacity": 5000,
  "is_featured": true,
  "is_private": false,
  "category": "music",
  "tags": ["outdoor", "festival"],
  "view_count": 1247,
  "created_at": "2025-06-01T10:00:00Z",
  "updated_at": "2025-06-15T14:30:00Z"
}
```

### Event List Response (Paginated)

```json
{
  "items": [
    { /* Event 1 */ },
    { /* Event 2 */ },
    { /* Event 3 */ }
  ],
  "total": 47,
  "page": 1,
  "size": 20,
  "pages": 3
}
```

### Error Response

```json
{
  "detail": "Event not found"
}
```

---

## 🔐 Authentication

### Get Token

```bash
# Register
POST /auth/register
{
  "email": "promoter@example.com",
  "password": "SecurePass123!",
  "first_name": "John",
  "last_name": "Doe",
  "role": "promoter"
}

# Login
POST /auth/login
{
  "email": "promoter@example.com",
  "password": "SecurePass123!"
}

# Response
{
  "access_token": "eyJhbGc...",
  "refresh_token": "eyJhbGc...",
  "token_type": "bearer"
}
```

### Use Token

```bash
curl -X POST "http://localhost:8000/events" \
  -H "Authorization: Bearer eyJhbGc..." \
  -H "Content-Type: application/json" \
  -d '{...}'
```

---

## ⚡ Quick Testing Commands

### Using cURL

```bash
# List events
curl "http://localhost:8000/events"

# Get event
curl "http://localhost:8000/events/123"

# Create event (with auth)
curl -X POST "http://localhost:8000/events" \
  -H "Authorization: Bearer YOUR_TOKEN" \
  -H "Content-Type: application/json" \
  -d @event.json

# Search events
curl "http://localhost:8000/events?search=concert&limit=5"

# Get my events
curl "http://localhost:8000/events/my/events" \
  -H "Authorization: Bearer YOUR_TOKEN"
```

### Using Python (httpx)

```python
import httpx

# List events
response = httpx.get("http://localhost:8000/events")
events = response.json()

# Create event
token = "your_access_token"
headers = {"Authorization": f"Bearer {token}"}
event_data = {
    "title": "Test Event",
    "venue_name": "Test Venue",
    # ... other fields
}
response = httpx.post(
    "http://localhost:8000/events",
    headers=headers,
    json=event_data
)
```

---

## 🎯 Common Workflows

### Complete Event Creation Flow

```bash
# 1. Register as promoter
POST /auth/register {...}

# 2. Login
POST /auth/login {...}
# Save access_token

# 3. Create draft event
POST /events {...}
# Save event_id

# 4. Add ticket tiers (next implementation)
POST /events/{event_id}/tiers {...}

# 5. Review event
GET /events/{event_id}

# 6. Publish event
POST /events/{event_id}/publish {"is_featured": true}

# 7. Event is now live!
GET /events?status_filter=published
```

### Event Management Flow

```bash
# View my events
GET /events/my/events

# Update event details
PUT /events/{event_id} {"description": "Updated!"}

# Check event stats
GET /events/{event_id}

# Cancel if needed
POST /events/{event_id}/cancel {"reason": "..."}
```

---

## 🔍 Query Parameters Guide

### Filtering

```bash
# By status
?status_filter=published
?status_filter=draft

# By promoter
?promoter_id=123

# By category
?category=music
?category=sports

# Featured only
?is_featured=true

# Include past events
?include_past=true
```

### Search

```bash
# Search in multiple fields
?search=concert           # Searches title, description, venue, city
?search=New+York          # Multi-word search
?search=music+festival    # Multiple terms
```

### Pagination

```bash
# First page (20 items)
?skip=0&limit=20

# Second page
?skip=20&limit=20

# Custom page size
?skip=0&limit=50

# Get all (max 100)
?skip=0&limit=100
```

### Combining Filters

```bash
# Published music events in New York
?status_filter=published&category=music&search=New+York

# Featured events, first 10
?is_featured=true&limit=10

# My draft events
GET /events/my/events?status_filter=draft
```

---

## ❌ Common Error Codes

| Code | Meaning | Common Cause |
|------|---------|--------------|
| 400 | Bad Request | Invalid data, missing required fields |
| 401 | Unauthorized | Invalid/missing token |
| 403 | Forbidden | Not a promoter, or not event owner |
| 404 | Not Found | Event doesn't exist |
| 422 | Validation Error | Invalid field values |

### Error Examples

```json
// 400 - Cannot publish without tiers
{
  "detail": "Event must have at least one ticket tier before publishing"
}

// 403 - Not owner
{
  "detail": "You don't have permission to modify this event"
}

// 404 - Not found
{
  "detail": "Event not found"
}

// 422 - Validation error
{
  "detail": [
    {
      "loc": ["body", "end_time"],
      "msg": "End time must be after start time",
      "type": "value_error"
    }
  ]
}
```

---

## 💡 Pro Tips

### 1. **Always Use Pagination**
Don't request all events at once. Use `skip` and `limit`.

### 2. **Filter for Performance**
Use `status_filter` and `category` to reduce response size.

### 3. **Search Wisely**
Search is case-insensitive and searches multiple fields.

### 4. **Check Status Before Updates**
Published/cancelled events have restrictions on what can be updated.

### 5. **Use Featured Flag**
Mark important events as featured for homepage display.

### 6. **Set Proper Timezone**
Always include timezone in event creation.

### 7. **Validate Before Publishing**
Ensure all required fields are complete before publishing.

### 8. **Soft Delete by Default**
Use soft delete to preserve historical data.

---

## 🧪 Testing Checklist

### Create Event
- [ ] Create draft event
- [ ] Verify all fields saved
- [ ] Check promoter association
- [ ] Verify status is DRAFT

### List Events
- [ ] List all events
- [ ] Filter by status
- [ ] Search by keyword
- [ ] Check pagination works
- [ ] Verify sorting

### Update Event
- [ ] Update draft event (all fields)
- [ ] Update published event (limited fields)
- [ ] Try update as non-owner (should fail)
- [ ] Verify changes saved

### Publish Event
- [ ] Try publish without tiers (should fail)
- [ ] Add tiers, then publish
- [ ] Verify status changed
- [ ] Check event appears in public list

### Permissions
- [ ] Create as promoter
- [ ] Try create as regular user (should fail)
- [ ] Update own event
- [ ] Try update other's event (should fail)
- [ ] Admin can update any event

---

## 📚 Related Documentation

- **Full Documentation:** `EVENT_MANAGEMENT_COMPLETE.md`
- **Authentication:** `AUTH_SYSTEM_DOCUMENTATION.md`
- **API Docs:** `http://localhost:8000/api/docs` (when running)
- **Project Status:** `PROJECT_STATUS_REPORT.md`

---

## 🆘 Troubleshooting

### "Promoter account must be verified"
→ Ensure your promoter account is verified in the database

### "Event must have at least one ticket tier"
→ Add ticket tiers before publishing (next implementation)

### "Invalid or expired token"
→ Refresh your access token using `/auth/refresh`

### "Forbidden - Insufficient permissions"
→ Ensure you're the event owner or admin

### "Cannot modify core details of published events"
→ Only description and images can be updated after publishing

---

**Last Updated:** October 26, 2025  
**Version:** 1.0.0  
**Status:** ✅ Complete & Ready
