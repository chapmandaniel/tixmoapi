# Ticket Vendor API - Architecture Design Document

## Project Overview

A comprehensive ticket vendor solution API that enables Event Promoters to publish events and sell tickets with advanced features including tiered pricing, waitlists, and inventory management.

## Requirements

### Functional Requirements
- Event creation and management by promoters
- Ticket creation with multiple pricing tiers
- Ticket purchase and sales tracking
- Waitlist management for sold-out events
- Inventory control and availability tracking
- Order management and confirmation
- Email notifications for purchases and waitlist updates

### Non-Functional Requirements
- Scalability: Handle concurrent ticket purchases
- Performance: Sub-200ms API response times
- Reliability: 99.9% uptime
- Security: PCI-DSS compliant for payments
- Concurrency: Handle race conditions for limited tickets

## Architecture Pattern

**Decision: Monolithic REST API with Modular Design**

### Rationale
- **MVP Focus**: Get to market quickly with full-featured API
- **Team Size**: Single development team initially
- **Complexity**: Moderate - not complex enough to justify microservices overhead
- **Deployment**: Simple deployment and testing
- **Future Path**: Modular design allows extraction to microservices later if needed

### Architecture Diagram

```
┌─────────────────────────────────────────────────────────┐
│                    Client Applications                   │
│           (Web, Mobile, Admin Dashboard)                 │
└──────────────────────┬──────────────────────────────────┘
                       │
                       ▼
┌─────────────────────────────────────────────────────────┐
│                    API Gateway / Load Balancer           │
│                   (NGINX / AWS ALB)                      │
└──────────────────────┬──────────────────────────────────┘
                       │
                       ▼
┌─────────────────────────────────────────────────────────┐
│              FastAPI Application Server                  │
│  ┌────────────────────────────────────────────────┐    │
│  │              API Layer                          │    │
│  │  ┌──────────┐ ┌──────────┐ ┌──────────┐       │    │
│  │  │  Events  │ │ Tickets  │ │ Orders   │       │    │
│  │  └──────────┘ └──────────┘ └──────────┘       │    │
│  ├────────────────────────────────────────────────┤    │
│  │           Business Logic Layer                  │    │
│  │  • Event Management   • Ticket Tiers           │    │
│  │  • Inventory Control  • Waitlist Logic         │    │
│  │  • Payment Processing • Email Notifications    │    │
│  ├────────────────────────────────────────────────┤    │
│  │              Data Access Layer                  │    │
│  │         (SQLAlchemy ORM / Raw SQL)             │    │
│  └────────────────────────────────────────────────┘    │
└──────────────────────┬──────────────────────────────────┘
                       │
        ┌──────────────┴───────────────┬──────────────────┐
        ▼                              ▼                  ▼
┌───────────────┐            ┌──────────────┐    ┌──────────────┐
│  PostgreSQL   │            │    Redis     │    │  S3 Storage  │
│   Database    │            │    Cache     │    │  (Assets)    │
│               │            │              │    │              │
│ • Events      │            │ • Sessions   │    │ • Event      │
│ • Tickets     │            │ • Rate Limit │    │   Images     │
│ • Orders      │            │ • Temp Holds │    │ • Receipts   │
│ • Waitlist    │            │              │    │              │
│ • Users       │            │              │    │              │
└───────────────┘            └──────────────┘    └──────────────┘
        │
        ▼
┌───────────────┐
│ Message Queue │
│  (RabbitMQ)   │
│               │
│ • Email Jobs  │
│ • Analytics   │
│ • Audit Log   │
└───────────────┘
```

## Technology Stack

### Backend Framework
**Choice: FastAPI (Python 3.11+)**

**Rationale:**
- ✅ High performance (async support)
- ✅ Automatic API documentation (Swagger/OpenAPI)
- ✅ Type hints and validation (Pydantic)
- ✅ Modern Python features
- ✅ Easy testing and development
- ✅ Great ecosystem for payment integrations
- ✅ Built-in dependency injection

### Database
**Choice: PostgreSQL 15+**

**Rationale:**
- ✅ ACID compliance (critical for ticket sales)
- ✅ Row-level locking for inventory management
- ✅ JSON/JSONB support for flexible data
- ✅ Full-text search capabilities
- ✅ Excellent indexing and query performance
- ✅ Proven reliability at scale
- ✅ Strong transaction support

### Caching Layer
**Choice: Redis 7+**

**Rationale:**
- ✅ In-memory speed for hot data
- ✅ Temporary ticket holds (TTL support)
- ✅ Rate limiting
- ✅ Session management
- ✅ Real-time inventory tracking
- ✅ Pub/Sub for notifications

### Message Queue
**Choice: RabbitMQ**

**Rationale:**
- ✅ Reliable message delivery
- ✅ Async processing for emails
- ✅ Decouples long-running tasks
- ✅ Retry logic for failures
- ✅ Easy monitoring

### Email Service
**Choice: SendGrid or AWS SES**

**Rationale:**
- ✅ High deliverability rates
- ✅ Email templates
- ✅ Analytics and tracking
- ✅ Transactional email optimized
- ✅ Scalable

### Payment Processing
**Choice: Stripe**

**Rationale:**
- ✅ PCI-DSS compliant
- ✅ Excellent API and documentation
- ✅ Strong Python SDK
- ✅ Handles complex payment flows
- ✅ Fraud detection built-in
- ✅ Webhook support

### Authentication
**Choice: JWT (JSON Web Tokens)**

**Rationale:**
- ✅ Stateless authentication
- ✅ Scalable across instances
- ✅ Industry standard
- ✅ Easy integration with frontend
- ✅ Short-lived access tokens + refresh tokens

## Data Model Design

### Core Entities

```
┌─────────────┐
│  Promoters  │
│─────────────│
│ id (PK)     │
│ name        │
│ email       │
│ company     │
│ verified    │
└─────────────┘
       │ 1
       │
       │ N
┌─────────────┐
│   Events    │
│─────────────│
│ id (PK)     │
│ promoter_id │ (FK)
│ title       │
│ description │
│ venue       │
│ start_time  │
│ end_time    │
│ status      │
│ capacity    │
│ image_url   │
└─────────────┘
       │ 1
       │
       │ N
┌──────────────┐
│ Ticket Tiers │
│──────────────│
│ id (PK)      │
│ event_id (FK)│
│ name         │
│ description  │
│ price        │
│ quantity     │
│ sold         │
│ position     │
│ sale_start   │
│ sale_end     │
└──────────────┘
       │ 1
       │
       │ N
┌─────────────┐
│   Orders    │
│─────────────│
│ id (PK)     │
│ tier_id (FK)│
│ user_id (FK)│
│ quantity    │
│ total_price │
│ status      │
│ created_at  │
│ payment_id  │
└─────────────┘
       │ 1
       │
       │ N
┌─────────────┐
│   Tickets   │
│─────────────│
│ id (PK)     │
│ order_id    │ (FK)
│ tier_id     │ (FK)
│ ticket_code │
│ qr_code     │
│ status      │
│ attendee    │
└─────────────┘

┌─────────────┐
│  Waitlist   │
│─────────────│
│ id (PK)     │
│ event_id    │ (FK)
│ user_id     │ (FK)
│ tier_id     │ (FK - optional)
│ position    │
│ notified    │
│ created_at  │
└─────────────┘
```

## API Design

### RESTful Endpoints

```python
# Authentication
POST   /api/v1/auth/register         # Register user/promoter
POST   /api/v1/auth/login            # Login
POST   /api/v1/auth/refresh          # Refresh token
POST   /api/v1/auth/logout           # Logout

# Promoters
GET    /api/v1/promoters             # List promoters
GET    /api/v1/promoters/:id         # Get promoter
PUT    /api/v1/promoters/:id         # Update promoter
GET    /api/v1/promoters/:id/events  # Get promoter's events

# Events
POST   /api/v1/events                # Create event (promoter only)
GET    /api/v1/events                # List public events
GET    /api/v1/events/:id            # Get event details
PUT    /api/v1/events/:id            # Update event (promoter only)
DELETE /api/v1/events/:id            # Delete event (promoter only)
POST   /api/v1/events/:id/publish    # Publish event
POST   /api/v1/events/:id/unpublish  # Unpublish event

# Ticket Tiers
POST   /api/v1/events/:id/tiers      # Add tier (promoter only)
GET    /api/v1/events/:id/tiers      # Get event tiers
PUT    /api/v1/tiers/:id             # Update tier
DELETE /api/v1/tiers/:id             # Delete tier
GET    /api/v1/tiers/:id/availability # Check availability

# Orders & Tickets
POST   /api/v1/orders                # Create order (purchase tickets)
GET    /api/v1/orders                # Get user's orders
GET    /api/v1/orders/:id            # Get order details
POST   /api/v1/orders/:id/confirm    # Confirm payment
GET    /api/v1/tickets               # Get user's tickets
GET    /api/v1/tickets/:id           # Get ticket details
POST   /api/v1/tickets/:id/validate  # Validate ticket (check-in)

# Waitlist
POST   /api/v1/waitlist              # Join waitlist
GET    /api/v1/waitlist              # Get user's waitlist entries
DELETE /api/v1/waitlist/:id          # Leave waitlist
GET    /api/v1/events/:id/waitlist   # Get event waitlist (promoter)
POST   /api/v1/waitlist/:id/notify   # Notify waitlist user

# Analytics (Promoter)
GET    /api/v1/events/:id/analytics  # Event analytics
GET    /api/v1/events/:id/sales      # Sales report
```

## Critical Features

### 1. Inventory Management (Race Condition Prevention)

```python
# Using database row-level locking
@transaction.atomic
async def purchase_tickets(tier_id: int, quantity: int):
    # Lock the tier row for update
    tier = await TicketTier.select_for_update().get(id=tier_id)
    
    # Check availability
    available = tier.quantity - tier.sold
    if available < quantity:
        raise InsufficientTicketsError()
    
    # Hold tickets in Redis with TTL (5 minutes)
    hold_key = f"ticket_hold:{tier_id}:{user_id}"
    await redis.setex(hold_key, 300, quantity)
    
    # Create order with PENDING status
    order = await create_order(tier_id, quantity, status="PENDING")
    
    return order
```

### 2. Waitlist Management

```python
async def join_waitlist(event_id: int, user_id: int):
    # Check if already in waitlist
    existing = await Waitlist.filter(
        event_id=event_id,
        user_id=user_id
    ).first()
    
    if existing:
        return existing
    
    # Get current position
    max_position = await Waitlist.filter(
        event_id=event_id
    ).max('position')
    
    # Add to waitlist
    waitlist_entry = await Waitlist.create(
        event_id=event_id,
        user_id=user_id,
        position=max_position + 1 if max_position else 1
    )
    
    return waitlist_entry

async def notify_waitlist(event_id: int, available_tickets: int):
    # Get top N users from waitlist who haven't been notified
    entries = await Waitlist.filter(
        event_id=event_id,
        notified=False
    ).order_by('position').limit(available_tickets)
    
    for entry in entries:
        await send_email(
            to=entry.user.email,
            template="waitlist_available",
            data={...}
        )
        entry.notified = True
        await entry.save()
```

### 3. Ticket Hold Mechanism

```python
# When user starts checkout
async def hold_tickets(tier_id: int, quantity: int, user_id: int):
    hold_key = f"hold:{tier_id}:{user_id}"
    
    # Try to hold tickets
    held = await redis.setex(hold_key, 300, quantity)  # 5 min TTL
    
    if held:
        # Decrement available count in Redis
        await redis.decrby(f"available:{tier_id}", quantity)
        return True
    
    return False

# Background job to release expired holds
async def release_expired_holds():
    # Scan for expired holds and restore inventory
    pass
```

## Scalability Considerations

### Horizontal Scaling
- Stateless application servers (can run multiple instances)
- Redis for shared state (holds, sessions)
- Database connection pooling
- Load balancer for request distribution

### Database Optimization
- Indexes on foreign keys and lookup columns
- Composite indexes for common queries
- Read replicas for analytics queries
- Connection pooling (pgbouncer)
- Query optimization with EXPLAIN ANALYZE

### Caching Strategy
```
┌──────────┐
│ Request  │
└────┬─────┘
     │
     ▼
┌────────────┐    Hit    ┌──────────┐
│  Redis     │◄─────────▶│ Response │
│  Cache     │            └──────────┘
└────┬───────┘
     │ Miss
     ▼
┌────────────┐
│ PostgreSQL │
│  Database  │
└────┬───────┘
     │
     ▼
┌────────────┐
│ Cache & Return │
└────────────┘
```

**Cache Keys:**
- Event details: `event:{event_id}`
- Tier availability: `available:{tier_id}`
- User sessions: `session:{user_id}`
- Rate limits: `ratelimit:{user_id}`

### Performance Targets
- API Response Time: < 200ms (p95)
- Database Query Time: < 50ms (p95)
- Ticket Purchase Flow: < 3 seconds end-to-end
- Support: 100+ concurrent purchases
- Uptime: 99.9%

## Security Architecture

### Authentication Flow
```
1. User Login → JWT Access Token (15 min) + Refresh Token (7 days)
2. Access Token in Authorization header
3. Validate token on each request
4. Refresh when expired
```

### Authorization Levels
- **Public**: Browse events, view tiers
- **User**: Purchase tickets, join waitlist
- **Promoter**: Create/manage events, view analytics
- **Admin**: System management

### Security Measures
- ✅ Input validation (Pydantic models)
- ✅ SQL injection prevention (ORM)
- ✅ XSS protection (sanitized responses)
- ✅ CSRF tokens for sensitive operations
- ✅ Rate limiting (Redis)
- ✅ HTTPS only
- ✅ Password hashing (bcrypt)
- ✅ PCI-DSS for payment data

## Deployment Architecture

### Development
```
Docker Compose:
- FastAPI container
- PostgreSQL container
- Redis container
- RabbitMQ container
```

### Production (AWS)
```
- ECS Fargate (API containers)
- RDS PostgreSQL (Multi-AZ)
- ElastiCache Redis (Cluster mode)
- ALB (Load balancer)
- S3 (Static assets)
- CloudFront (CDN)
- Route53 (DNS)
- CloudWatch (Monitoring)
```

## Monitoring & Observability

### Metrics to Track
- Request rate and latency (p50, p95, p99)
- Error rates (4xx, 5xx)
- Database connection pool usage
- Cache hit ratio
- Ticket purchase success rate
- Waitlist conversion rate
- Payment success rate

### Logging
- Structured JSON logs
- Log levels: DEBUG, INFO, WARNING, ERROR
- Correlation IDs for request tracing
- Centralized logging (CloudWatch or ELK)

### Alerts
- High error rate (> 1%)
- Slow response times (> 500ms)
- Database connection issues
- Payment failures
- Low ticket inventory

## Development Roadmap

### Phase 1: MVP (Weeks 1-2)
- ✅ Basic event CRUD
- ✅ Ticket tier management
- ✅ Simple ticket purchase
- ✅ User authentication
- ✅ Basic inventory tracking

### Phase 2: Core Features (Weeks 3-4)
- ✅ Waitlist functionality
- ✅ Email notifications
- ✅ Payment integration (Stripe)
- ✅ Ticket hold mechanism
- ✅ Order confirmation

### Phase 3: Advanced Features (Weeks 5-6)
- ✅ Analytics dashboard
- ✅ QR code generation
- ✅ Ticket validation/check-in
- ✅ Promoter admin panel
- ✅ Performance optimization

### Phase 4: Polish & Scale (Weeks 7-8)
- ✅ Load testing
- ✅ Security audit
- ✅ Documentation
- ✅ Deployment automation
- ✅ Monitoring setup

## Architecture Decision Records

### ADR-001: Use PostgreSQL for Primary Database
**Status**: Accepted  
**Rationale**: ACID compliance essential for ticket inventory management

### ADR-002: Use Redis for Ticket Holds
**Status**: Accepted  
**Rationale**: TTL support perfect for temporary holds, prevents over-selling

### ADR-003: Monolithic Architecture Initially
**Status**: Accepted  
**Rationale**: Faster MVP delivery, can extract services later if needed

### ADR-004: JWT for Authentication
**Status**: Accepted  
**Rationale**: Stateless, scalable, industry standard

### ADR-005: FastAPI Framework
**Status**: Accepted  
**Rationale**: Modern, high-performance, excellent developer experience

## Risk Mitigation

### Race Conditions
- **Risk**: Multiple users buying last ticket
- **Mitigation**: Database row-level locking + Redis holds

### Payment Failures
- **Risk**: Tickets held but payment fails
- **Mitigation**: 5-minute hold timeout, async payment processing

### Email Delivery
- **Risk**: Critical emails not delivered
- **Mitigation**: Use reliable service (SendGrid), retry logic, status tracking

### Database Performance
- **Risk**: Slow queries under load
- **Mitigation**: Proper indexing, connection pooling, query optimization

### Security Vulnerabilities
- **Risk**: Payment data exposure
- **Mitigation**: PCI-DSS compliance, use Stripe, no card storage

## Success Metrics

- ✅ Ticket purchase success rate > 99%
- ✅ API uptime > 99.9%
- ✅ P95 response time < 200ms
- ✅ Zero double-selling incidents
- ✅ Email delivery rate > 98%
- ✅ Promoter satisfaction > 4.5/5

---

**Document Version**: 1.0  
**Last Updated**: October 2025  
**Author**: Solutions Architect (AI Dev Team)  
**Status**: Approved for Implementation
