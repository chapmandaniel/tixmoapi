# 🔐 Authentication System - Quick Reference

## 📡 API Endpoints Cheat Sheet

### Authentication
| Method | Endpoint | Auth | Purpose |
|--------|----------|------|---------|
| POST | `/auth/register` | ❌ | Create new account |
| POST | `/auth/login` | ❌ | Get access & refresh tokens |
| POST | `/auth/refresh` | ✅ Refresh | Get new access token |
| POST | `/auth/logout` | ✅ Access | Logout (client cleanup) |

### Profile
| Method | Endpoint | Auth | Purpose |
|--------|----------|------|---------|
| GET | `/auth/me` | ✅ Access | Get current user |
| POST | `/auth/email/verify` | ✅ Access | Verify email |

### Password
| Method | Endpoint | Auth | Purpose |
|--------|----------|------|---------|
| POST | `/auth/password/change` | ✅ Access | Change password |
| POST | `/auth/password/reset` | ❌ | Request reset email |

---

## 🔑 Authentication Headers

```bash
# Access Token
Authorization: Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...

# Refresh Token
Authorization: Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...
```

---

## 💡 Code Examples

### Register & Login
```python
import httpx

# Register
async with httpx.AsyncClient() as client:
    response = await client.post("http://localhost:8000/auth/register", json={
        "email": "user@example.com",
        "password": "SecurePass123",
        "name": "John Doe",
        "is_promoter": False
    })
    access_token = response.json()["access_token"]
```

### Protect Routes
```python
from fastapi import Depends
from src.core.dependencies import get_current_user
from src.models.users import User

@app.post("/events")
async def create_event(
    data: dict,
    current_user: User = Depends(get_current_user)  # 🔒 Protected!
):
    return {"created_by": current_user.id}
```

### Admin-Only Routes
```python
from src.core.dependencies import get_current_admin

@app.delete("/admin/users/{user_id}")
async def delete_user(
    user_id: int,
    admin: User = Depends(get_current_admin)  # 🔒 Admin only!
):
    return {"deleted": True}
```

### Optional Authentication
```python
from src.core.dependencies import get_optional_user
from typing import Optional

@app.get("/events")
async def list_events(
    user: Optional[User] = Depends(get_optional_user)  # 🔒 Optional
):
    if user:
        return {"user_id": user.id}
    return {"anonymous": True}
```

---

## 🔒 Security Checklist

- ✅ Never pass password in URL
- ✅ Always use HTTPS in production
- ✅ Store tokens in secure HTTP-only cookies (frontend)
- ✅ Don't expose tokens in logs or error messages
- ✅ Rotate refresh tokens periodically
- ✅ Implement rate limiting on auth endpoints
- ✅ Use strong SECRET_KEY (min 32 characters)

---

## 📦 Token Response Format

```json
{
  "access_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
  "refresh_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
  "token_type": "bearer",
  "expires_in": 1800
}
```

---

## 🔧 Environment Setup

```bash
# .env file
SECRET_KEY=your-super-secret-key-min-32-chars
ACCESS_TOKEN_EXPIRE_MINUTES=30
REFRESH_TOKEN_EXPIRE_DAYS=7
DATABASE_URL=postgresql+asyncpg://user:pass@localhost/db
ENVIRONMENT=development
DEBUG=True
```

---

## ⚡ Performance Tips

- ✅ Cache user lookups in Redis for high-traffic apps
- ✅ Use database connection pooling
- ✅ Consider async password hashing for large scale
- ✅ Implement token blacklist in Redis for logout
- ✅ Monitor failed login attempts

---

## 🐛 Common Issues

### "Invalid token"
- Token expired → Use refresh token
- Wrong SECRET_KEY → Check env variables
- Token malformed → Verify format

### "User not found"
- User deleted → Account was deleted
- Wrong user_id in token → Check token claims
- Database connection issue → Check DB status

### "Email already registered"
- Email in use → Use different email or login
- Case sensitivity → Check email lowercase

---

## 📚 File Locations

```
src/
├── core/
│   ├── security.py          # 🔐 JWT & password functions
│   ├── dependencies.py      # 🔑 FastAPI dependency injection
│   └── database.py
├── api/
│   ├── auth.py             # 📡 Endpoints
│   └── __init__.py
├── services/
│   ├── auth_service.py     # 💼 Business logic
│   └── __init__.py
├── models/
│   └── users.py            # 🗄️ Database model
├── schemas/
│   └── auth.py             # 📋 Request/response schemas
└── main.py                 # 🚀 App initialization
```

---

## 🚀 Testing Endpoints

```bash
# Health check
curl http://localhost:8000/health

# Swagger docs
open http://localhost:8000/api/docs

# Register
curl -X POST http://localhost:8000/auth/register \
  -H "Content-Type: application/json" \
  -d '{
    "email":"test@example.com",
    "password":"TestPass123",
    "name":"Test User"
  }'

# Login
curl -X POST http://localhost:8000/auth/login \
  -H "Content-Type: application/json" \
  -d '{
    "email":"test@example.com",
    "password":"TestPass123"
  }'

# Get current user
curl -X GET http://localhost:8000/auth/me \
  -H "Authorization: Bearer YOUR_ACCESS_TOKEN"
```

---

## 🔄 Request/Response Lifecycle

```
Client Request
     ↓
Bearer Token Extraction (Authorization header)
     ↓
Token Verification (JWT decode)
     ↓
User Lookup (database)
     ↓
Permission Check (role/scope)
     ↓
Route Handler Execution
     ↓
Response Generation
     ↓
Client Receives Response
```

---

## 📞 Support Resources

- **Full Docs**: `AUTH_SYSTEM_DOCUMENTATION.md`
- **Source Code**: `/mnt/user-data/outputs/src_*.py`
- **API Docs**: Swagger UI at `/api/docs`
- **Examples**: Check docstrings in each module

---

**Version**: 1.0  
**Last Updated**: October 26, 2025  
**Status**: ✅ Production Ready
