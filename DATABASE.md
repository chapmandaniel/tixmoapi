# Database Schema Documentation

## Entity Relationship Diagram (Text Format)

```
┌─────────────┐
│    USERS    │
│─────────────│
│ id (PK)     │
│ email       │
│ password_hash│
│ role        │
└─────────────┘
       │ 1
       ├────────────────────┐
       │ 1                  │ 1
       ▼                    ▼
┌─────────────┐      ┌─────────────┐
│  PROMOTERS  │      │   ORDERS    │
│─────────────│      │─────────────│
│ id (PK)     │      │ id (PK)     │
│ user_id(FK) │      │ user_id(FK) │
│ company     │      │ event_id(FK)│
└─────────────┘      │ status      │
       │ 1           │ total_amount│
       │             └─────────────┘
       │ N                  │ 1
       ▼                    │
┌─────────────┐             │ N
│   EVENTS    │             ▼
│─────────────│      ┌──────────────┐
│ id (PK)     │      │ ORDER_ITEMS  │
│ promoter(FK)│      │──────────────│
│ title       │      │ id (PK)      │
│ venue       │      │ order_id(FK) │
│ start_time  │      │ tier_id(FK)  │
│ status      │      │ quantity     │
└─────────────┘      └──────────────┘
       │ 1                  │
       │                    │
       ├────────────────────┤
       │ N                  │ N
       ▼                    │
┌──────────────┐            │
│ TICKET_TIERS │            │
│──────────────│            │
│ id (PK)      │◄───────────┘
│ event_id(FK) │
│ name         │
│ price        │
│ quantity     │
│ sold         │
└──────────────┘
       │ 1
       │
       │ N
       ▼
┌─────────────┐
│   TICKETS   │
│─────────────│
│ id (PK)     │
│ order_id(FK)│
│ tier_id(FK) │
│ event_id(FK)│
│ ticket_code │
│ qr_code     │
│ status      │
└─────────────┘


┌─────────────┐
│  WAITLIST   │
│─────────────│
│ id (PK)     │
│ event_id(FK)│
│ user_id(FK) │
│ tier_id(FK) │
│ position    │
│ notified    │
└─────────────┘
```

## Table Relationships

### Users → Promoters (One-to-One)
- Each user can be a promoter
- Promoters table extends user information

### Promoters → Events (One-to-Many)
- One promoter can create many events
- ON DELETE RESTRICT: Cannot delete promoter with active events

### Events → Ticket Tiers (One-to-Many)
- Each event has multiple pricing tiers
- ON DELETE CASCADE: Tiers deleted when event is deleted

### Events → Waitlist (One-to-Many)
- Each event can have multiple waitlist entries
- ON DELETE CASCADE: Waitlist cleared when event is deleted

### Users → Orders (One-to-Many)
- Users can place multiple orders
- ON DELETE RESTRICT: Cannot delete user with orders

### Orders → Order Items (One-to-Many)
- Each order has multiple line items
- ON DELETE CASCADE: Items deleted when order is deleted

### Orders → Tickets (One-to-Many)
- Each order generates multiple tickets
- ON DELETE RESTRICT: Cannot delete order with issued tickets

### Ticket Tiers → Tickets (One-to-Many)
- Each tier can have many tickets sold
- ON DELETE RESTRICT: Cannot delete tier with issued tickets

## Key Indexes

### Critical Performance Indexes

1. **Event Lookup**
   ```sql
   idx_events_status_start - For finding active events
   idx_events_slug - For URL-based event lookup
   idx_events_search - Full-text search on title/description
   ```

2. **Ticket Availability**
   ```sql
   idx_ticket_tiers_event_id - Finding tiers for an event
   idx_ticket_tiers_active - Finding available tiers
   ```

3. **Order Processing**
   ```sql
   idx_orders_user_status - User's order history
   idx_tickets_order_tier - Ticket generation queries
   ```

4. **Waitlist Management**
   ```sql
   idx_waitlist_position - Ordered waitlist retrieval
   idx_waitlist_notified - Finding users to notify
   ```

## Common Query Patterns

### 1. Get Available Events with Ticket Info

```sql
SELECT * FROM active_events_with_availability
WHERE start_time > CURRENT_TIMESTAMP
  AND tickets_available > 0
ORDER BY start_time ASC
LIMIT 20;
```

### 2. Check Ticket Availability for an Event

```sql
SELECT 
    tt.id,
    tt.name,
    tt.price,
    tt.quantity,
    tt.sold,
    tt.reserved,
    (tt.quantity - tt.sold - tt.reserved) as available
FROM ticket_tiers tt
WHERE tt.event_id = $1
  AND tt.is_active = true
  AND (tt.sale_start_time IS NULL OR tt.sale_start_time <= CURRENT_TIMESTAMP)
  AND (tt.sale_end_time IS NULL OR tt.sale_end_time >= CURRENT_TIMESTAMP)
ORDER BY tt.position, tt.price;
```

### 3. Purchase Tickets (with row locking)

```sql
BEGIN;

-- Lock the tier row for update
SELECT id, quantity, sold, reserved
FROM ticket_tiers
WHERE id = $1
FOR UPDATE;

-- Check availability
-- If available, update sold count
UPDATE ticket_tiers
SET sold = sold + $2
WHERE id = $1;

-- Create order and tickets
INSERT INTO orders (user_id, event_id, ...) VALUES (...);
INSERT INTO tickets (order_id, tier_id, ...) VALUES (...);

COMMIT;
```

### 4. Get User's Upcoming Tickets

```sql
SELECT * FROM user_tickets_summary
WHERE user_id = $1
  AND event_start_time > CURRENT_TIMESTAMP
  AND ticket_status = 'valid'
ORDER BY event_start_time ASC;
```

### 5. Join Waitlist

```sql
INSERT INTO waitlist (event_id, user_id, tier_id, position)
SELECT 
    $1, -- event_id
    $2, -- user_id
    $3, -- tier_id (optional)
    COALESCE(MAX(position), 0) + 1
FROM waitlist
WHERE event_id = $1
ON CONFLICT (event_id, user_id, tier_id) DO NOTHING;
```

### 6. Notify Waitlist When Tickets Available

```sql
-- Get top N users who haven't been notified
SELECT w.id, w.user_id, u.email, u.first_name
FROM waitlist w
JOIN users u ON w.user_id = u.id
WHERE w.event_id = $1
  AND w.notified = false
  AND (w.tier_id = $2 OR w.tier_id IS NULL)
ORDER BY w.position
LIMIT $3
FOR UPDATE SKIP LOCKED;

-- Mark as notified
UPDATE waitlist
SET notified = true, 
    notified_at = CURRENT_TIMESTAMP,
    notification_expires_at = CURRENT_TIMESTAMP + INTERVAL '24 hours'
WHERE id = ANY($1);
```

## Data Integrity Rules

### Ticket Tier Constraints
- `sold + reserved ≤ quantity` (enforced by trigger)
- `min_purchase ≤ max_purchase`
- `sale_end_time > sale_start_time`

### Event Constraints
- `end_time > start_time`
- `doors_open_time ≤ start_time`
- `capacity > 0`

### Order Constraints
- `total_amount = subtotal + service_fee + tax`
- All amounts must be ≥ 0

## Performance Considerations

### 1. Connection Pooling
Use a connection pool (e.g., pgbouncer) with:
- Min connections: 5
- Max connections: 20
- Connection timeout: 30s

### 2. Query Optimization
- Always use parameterized queries (prevent SQL injection)
- Use `EXPLAIN ANALYZE` for slow queries
- Add indexes based on actual query patterns
- Consider partial indexes for filtered queries

### 3. Caching Strategy
Cache the following in Redis with TTL:
- Event details: 5 minutes
- Ticket availability: 1 minute
- User sessions: 15 minutes
- Rate limit counters: 1 hour

### 4. Materialized Views
Refresh `event_sales_summary` view:
- Every 15 minutes during events
- Hourly during normal times
- Use `REFRESH MATERIALIZED VIEW CONCURRENTLY`

## Backup Strategy

### Daily Backups
```bash
pg_dump ticket_vendor | gzip > backup_$(date +%Y%m%d).sql.gz
```

### Point-in-Time Recovery
Enable WAL archiving for PITR:
```postgresql
wal_level = replica
archive_mode = on
archive_command = 'cp %p /backup/archive/%f'
```

## Monitoring Queries

### Find Slow Queries
```sql
SELECT query, mean_exec_time, calls
FROM pg_stat_statements
ORDER BY mean_exec_time DESC
LIMIT 10;
```

### Check Table Sizes
```sql
SELECT 
    tablename,
    pg_size_pretty(pg_total_relation_size(tablename::text)) as size
FROM pg_tables
WHERE schemaname = 'public'
ORDER BY pg_total_relation_size(tablename::text) DESC;
```

### Check Index Usage
```sql
SELECT 
    schemaname,
    tablename,
    indexname,
    idx_scan,
    pg_size_pretty(pg_relation_size(indexrelid)) as size
FROM pg_stat_user_indexes
ORDER BY idx_scan ASC;
```

### Monitor Connection Count
```sql
SELECT 
    count(*) as total_connections,
    state,
    usename
FROM pg_stat_activity
GROUP BY state, usename;
```

## Migration Strategy

### Adding New Columns (Safe)
```sql
-- Step 1: Add nullable column
ALTER TABLE events ADD COLUMN new_field VARCHAR(255);

-- Step 2: Backfill data (if needed)
UPDATE events SET new_field = 'default_value' WHERE new_field IS NULL;

-- Step 3: Add NOT NULL constraint (if needed)
ALTER TABLE events ALTER COLUMN new_field SET NOT NULL;
```

### Removing Columns (Safe)
```sql
-- Step 1: Stop using column in application
-- Step 2: Wait for all instances to deploy
-- Step 3: Drop column
ALTER TABLE events DROP COLUMN old_field;
```

### Renaming Columns (Requires Downtime)
```sql
-- Option 1: Downtime approach
ALTER TABLE events RENAME COLUMN old_name TO new_name;

-- Option 2: No downtime approach
-- 1. Add new column
-- 2. Dual-write to both columns
-- 3. Backfill old data
-- 4. Switch reads to new column
-- 5. Remove old column
```

## Security Best Practices

1. **Never store plain text passwords** - Use bcrypt/argon2
2. **Use parameterized queries** - Prevent SQL injection
3. **Limit database user permissions** - Principle of least privilege
4. **Enable SSL/TLS** - Encrypt data in transit
5. **Encrypt sensitive data at rest** - PII, payment info
6. **Regular security audits** - Review permissions and logs
7. **Implement row-level security** (if needed for multi-tenancy)

## Useful Views

All views are defined in schema.sql:
- `active_events_with_availability` - Browse events with ticket counts
- `user_tickets_summary` - User's ticket dashboard
- `event_sales_summary` - Analytics and reporting (materialized)

## Data Retention Policy

Recommended retention:
- Active data: Indefinite
- Audit logs: 7 years
- Email notifications: 1 year
- Soft-deleted records: 90 days (then hard delete)
- Payment transactions: 7 years (compliance)
