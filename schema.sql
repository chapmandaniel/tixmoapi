-- ============================================================================
-- Ticket Vendor API - Database Schema
-- PostgreSQL 15+
-- ============================================================================

-- Enable UUID extension
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";

-- Enable pg_trgm for text search
CREATE EXTENSION IF NOT EXISTS pg_trgm;

-- ============================================================================
-- ENUMS
-- ============================================================================

CREATE TYPE user_role AS ENUM ('user', 'promoter', 'admin');
CREATE TYPE event_status AS ENUM ('draft', 'published', 'cancelled', 'completed');
CREATE TYPE order_status AS ENUM ('pending', 'confirmed', 'cancelled', 'refunded');
CREATE TYPE ticket_status AS ENUM ('valid', 'used', 'cancelled', 'refunded');
CREATE TYPE payment_status AS ENUM ('pending', 'completed', 'failed', 'refunded');

-- ============================================================================
-- CORE TABLES
-- ============================================================================

-- Users Table
CREATE TABLE users (
    id SERIAL PRIMARY KEY,
    uuid UUID DEFAULT uuid_generate_v4() UNIQUE NOT NULL,
    email VARCHAR(255) UNIQUE NOT NULL,
    password_hash VARCHAR(255) NOT NULL,
    first_name VARCHAR(100) NOT NULL,
    last_name VARCHAR(100) NOT NULL,
    phone VARCHAR(20),
    role user_role DEFAULT 'user' NOT NULL,
    email_verified BOOLEAN DEFAULT false,
    is_active BOOLEAN DEFAULT true,
    metadata JSONB DEFAULT '{}'::jsonb,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    last_login_at TIMESTAMP WITH TIME ZONE,
    deleted_at TIMESTAMP WITH TIME ZONE
);

-- Promoters Table (extended user information)
CREATE TABLE promoters (
    id SERIAL PRIMARY KEY,
    user_id INTEGER UNIQUE NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    company_name VARCHAR(255),
    company_website VARCHAR(255),
    description TEXT,
    logo_url VARCHAR(500),
    verification_status VARCHAR(20) DEFAULT 'pending',
    verified_at TIMESTAMP WITH TIME ZONE,
    stripe_account_id VARCHAR(255),
    tax_id VARCHAR(50),
    address_line1 VARCHAR(255),
    address_line2 VARCHAR(255),
    city VARCHAR(100),
    state VARCHAR(100),
    postal_code VARCHAR(20),
    country VARCHAR(2) DEFAULT 'US',
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- Events Table
CREATE TABLE events (
    id SERIAL PRIMARY KEY,
    uuid UUID DEFAULT uuid_generate_v4() UNIQUE NOT NULL,
    promoter_id INTEGER NOT NULL REFERENCES promoters(id) ON DELETE RESTRICT,
    title VARCHAR(255) NOT NULL,
    slug VARCHAR(255) UNIQUE NOT NULL,
    description TEXT,
    venue_name VARCHAR(255) NOT NULL,
    venue_address VARCHAR(500),
    venue_city VARCHAR(100),
    venue_state VARCHAR(100),
    venue_country VARCHAR(2) DEFAULT 'US',
    venue_latitude DECIMAL(10, 8),
    venue_longitude DECIMAL(11, 8),
    start_time TIMESTAMP WITH TIME ZONE NOT NULL,
    end_time TIMESTAMP WITH TIME ZONE NOT NULL,
    doors_open_time TIMESTAMP WITH TIME ZONE,
    timezone VARCHAR(50) DEFAULT 'UTC',
    status event_status DEFAULT 'draft' NOT NULL,
    capacity INTEGER NOT NULL CHECK (capacity > 0),
    age_restriction INTEGER CHECK (age_restriction >= 0),
    is_featured BOOLEAN DEFAULT false,
    is_private BOOLEAN DEFAULT false,
    featured_image_url VARCHAR(500),
    banner_image_url VARCHAR(500),
    tags TEXT[],
    category VARCHAR(50),
    metadata JSONB DEFAULT '{}'::jsonb,
    view_count INTEGER DEFAULT 0,
    published_at TIMESTAMP WITH TIME ZONE,
    cancelled_at TIMESTAMP WITH TIME ZONE,
    cancellation_reason TEXT,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    deleted_at TIMESTAMP WITH TIME ZONE,
    
    CONSTRAINT check_dates CHECK (end_time > start_time),
    CONSTRAINT check_doors_open CHECK (doors_open_time IS NULL OR doors_open_time <= start_time)
);

-- Ticket Tiers Table
CREATE TABLE ticket_tiers (
    id SERIAL PRIMARY KEY,
    uuid UUID DEFAULT uuid_generate_v4() UNIQUE NOT NULL,
    event_id INTEGER NOT NULL REFERENCES events(id) ON DELETE CASCADE,
    name VARCHAR(100) NOT NULL,
    description TEXT,
    price DECIMAL(10, 2) NOT NULL CHECK (price >= 0),
    quantity INTEGER NOT NULL CHECK (quantity > 0),
    sold INTEGER DEFAULT 0 CHECK (sold >= 0),
    reserved INTEGER DEFAULT 0 CHECK (reserved >= 0),
    min_purchase INTEGER DEFAULT 1 CHECK (min_purchase > 0),
    max_purchase INTEGER DEFAULT 10 CHECK (max_purchase > 0),
    position INTEGER DEFAULT 0,
    sale_start_time TIMESTAMP WITH TIME ZONE,
    sale_end_time TIMESTAMP WITH TIME ZONE,
    is_active BOOLEAN DEFAULT true,
    requires_approval BOOLEAN DEFAULT false,
    metadata JSONB DEFAULT '{}'::jsonb,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    
    CONSTRAINT check_quantity_valid CHECK (sold + reserved <= quantity),
    CONSTRAINT check_min_max_purchase CHECK (max_purchase >= min_purchase),
    CONSTRAINT check_sale_dates CHECK (sale_end_time IS NULL OR sale_end_time > sale_start_time)
);

-- Orders Table
CREATE TABLE orders (
    id SERIAL PRIMARY KEY,
    uuid UUID DEFAULT uuid_generate_v4() UNIQUE NOT NULL,
    user_id INTEGER NOT NULL REFERENCES users(id) ON DELETE RESTRICT,
    event_id INTEGER NOT NULL REFERENCES events(id) ON DELETE RESTRICT,
    order_number VARCHAR(50) UNIQUE NOT NULL,
    status order_status DEFAULT 'pending' NOT NULL,
    subtotal DECIMAL(10, 2) NOT NULL CHECK (subtotal >= 0),
    service_fee DECIMAL(10, 2) DEFAULT 0 CHECK (service_fee >= 0),
    tax DECIMAL(10, 2) DEFAULT 0 CHECK (tax >= 0),
    total_amount DECIMAL(10, 2) NOT NULL CHECK (total_amount >= 0),
    currency VARCHAR(3) DEFAULT 'USD',
    payment_status payment_status DEFAULT 'pending' NOT NULL,
    payment_intent_id VARCHAR(255),
    payment_method VARCHAR(50),
    expires_at TIMESTAMP WITH TIME ZONE,
    confirmed_at TIMESTAMP WITH TIME ZONE,
    cancelled_at TIMESTAMP WITH TIME ZONE,
    refunded_at TIMESTAMP WITH TIME ZONE,
    refund_amount DECIMAL(10, 2),
    refund_reason TEXT,
    billing_email VARCHAR(255),
    billing_name VARCHAR(255),
    billing_address JSONB,
    metadata JSONB DEFAULT '{}'::jsonb,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- Order Items Table (Line items for each order)
CREATE TABLE order_items (
    id SERIAL PRIMARY KEY,
    order_id INTEGER NOT NULL REFERENCES orders(id) ON DELETE CASCADE,
    tier_id INTEGER NOT NULL REFERENCES ticket_tiers(id) ON DELETE RESTRICT,
    quantity INTEGER NOT NULL CHECK (quantity > 0),
    unit_price DECIMAL(10, 2) NOT NULL CHECK (unit_price >= 0),
    subtotal DECIMAL(10, 2) NOT NULL CHECK (subtotal >= 0),
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- Tickets Table
CREATE TABLE tickets (
    id SERIAL PRIMARY KEY,
    uuid UUID DEFAULT uuid_generate_v4() UNIQUE NOT NULL,
    order_id INTEGER NOT NULL REFERENCES orders(id) ON DELETE RESTRICT,
    tier_id INTEGER NOT NULL REFERENCES ticket_tiers(id) ON DELETE RESTRICT,
    event_id INTEGER NOT NULL REFERENCES events(id) ON DELETE RESTRICT,
    user_id INTEGER NOT NULL REFERENCES users(id) ON DELETE RESTRICT,
    ticket_code VARCHAR(50) UNIQUE NOT NULL,
    qr_code TEXT,
    status ticket_status DEFAULT 'valid' NOT NULL,
    attendee_first_name VARCHAR(100),
    attendee_last_name VARCHAR(100),
    attendee_email VARCHAR(255),
    checked_in_at TIMESTAMP WITH TIME ZONE,
    checked_in_by INTEGER REFERENCES users(id),
    transferred_to INTEGER REFERENCES users(id),
    transferred_at TIMESTAMP WITH TIME ZONE,
    cancelled_at TIMESTAMP WITH TIME ZONE,
    metadata JSONB DEFAULT '{}'::jsonb,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- Waitlist Table
CREATE TABLE waitlist (
    id SERIAL PRIMARY KEY,
    event_id INTEGER NOT NULL REFERENCES events(id) ON DELETE CASCADE,
    user_id INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    tier_id INTEGER REFERENCES ticket_tiers(id) ON DELETE SET NULL,
    position INTEGER NOT NULL,
    notified BOOLEAN DEFAULT false,
    notified_at TIMESTAMP WITH TIME ZONE,
    notification_expires_at TIMESTAMP WITH TIME ZONE,
    responded_at TIMESTAMP WITH TIME ZONE,
    status VARCHAR(20) DEFAULT 'waiting',
    metadata JSONB DEFAULT '{}'::jsonb,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    
    UNIQUE(event_id, user_id, tier_id)
);

-- Payment Transactions Table
CREATE TABLE payment_transactions (
    id SERIAL PRIMARY KEY,
    order_id INTEGER NOT NULL REFERENCES orders(id) ON DELETE RESTRICT,
    transaction_id VARCHAR(255) UNIQUE NOT NULL,
    payment_provider VARCHAR(50) NOT NULL,
    amount DECIMAL(10, 2) NOT NULL,
    currency VARCHAR(3) DEFAULT 'USD',
    status payment_status NOT NULL,
    payment_method VARCHAR(50),
    error_code VARCHAR(50),
    error_message TEXT,
    metadata JSONB DEFAULT '{}'::jsonb,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- Email Notifications Table
CREATE TABLE email_notifications (
    id SERIAL PRIMARY KEY,
    user_id INTEGER REFERENCES users(id) ON DELETE SET NULL,
    email VARCHAR(255) NOT NULL,
    template_name VARCHAR(100) NOT NULL,
    subject VARCHAR(255) NOT NULL,
    status VARCHAR(20) DEFAULT 'pending',
    sent_at TIMESTAMP WITH TIME ZONE,
    opened_at TIMESTAMP WITH TIME ZONE,
    clicked_at TIMESTAMP WITH TIME ZONE,
    bounced_at TIMESTAMP WITH TIME ZONE,
    error_message TEXT,
    metadata JSONB DEFAULT '{}'::jsonb,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- Audit Log Table
CREATE TABLE audit_log (
    id SERIAL PRIMARY KEY,
    user_id INTEGER REFERENCES users(id) ON DELETE SET NULL,
    action VARCHAR(100) NOT NULL,
    entity_type VARCHAR(50) NOT NULL,
    entity_id INTEGER,
    old_data JSONB,
    new_data JSONB,
    ip_address INET,
    user_agent TEXT,
    metadata JSONB DEFAULT '{}'::jsonb,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- ============================================================================
-- INDEXES
-- ============================================================================

-- Users indexes
CREATE INDEX idx_users_email ON users(email);
CREATE INDEX idx_users_role ON users(role);
CREATE INDEX idx_users_created_at ON users(created_at DESC);
CREATE INDEX idx_users_deleted_at ON users(deleted_at) WHERE deleted_at IS NOT NULL;

-- Promoters indexes
CREATE INDEX idx_promoters_user_id ON promoters(user_id);
CREATE INDEX idx_promoters_verification_status ON promoters(verification_status);

-- Events indexes
CREATE INDEX idx_events_promoter_id ON events(promoter_id);
CREATE INDEX idx_events_status ON events(status);
CREATE INDEX idx_events_slug ON events(slug);
CREATE INDEX idx_events_start_time ON events(start_time);
CREATE INDEX idx_events_category ON events(category);
CREATE INDEX idx_events_published_at ON events(published_at DESC);
CREATE INDEX idx_events_location ON events(venue_city, venue_state, venue_country);
CREATE INDEX idx_events_featured ON events(is_featured) WHERE is_featured = true;
CREATE INDEX idx_events_tags ON events USING GIN(tags);
CREATE INDEX idx_events_search ON events USING GIN(to_tsvector('english', title || ' ' || description));

-- Ticket Tiers indexes
CREATE INDEX idx_ticket_tiers_event_id ON ticket_tiers(event_id);
CREATE INDEX idx_ticket_tiers_position ON ticket_tiers(event_id, position);
CREATE INDEX idx_ticket_tiers_active ON ticket_tiers(event_id, is_active) WHERE is_active = true;

-- Orders indexes
CREATE INDEX idx_orders_user_id ON orders(user_id);
CREATE INDEX idx_orders_event_id ON orders(event_id);
CREATE INDEX idx_orders_status ON orders(status);
CREATE INDEX idx_orders_payment_status ON orders(payment_status);
CREATE INDEX idx_orders_created_at ON orders(created_at DESC);
CREATE INDEX idx_orders_number ON orders(order_number);

-- Order Items indexes
CREATE INDEX idx_order_items_order_id ON order_items(order_id);
CREATE INDEX idx_order_items_tier_id ON order_items(tier_id);

-- Tickets indexes
CREATE INDEX idx_tickets_order_id ON tickets(order_id);
CREATE INDEX idx_tickets_tier_id ON tickets(tier_id);
CREATE INDEX idx_tickets_event_id ON tickets(event_id);
CREATE INDEX idx_tickets_user_id ON tickets(user_id);
CREATE INDEX idx_tickets_code ON tickets(ticket_code);
CREATE INDEX idx_tickets_status ON tickets(status);
CREATE INDEX idx_tickets_created_at ON tickets(created_at DESC);

-- Waitlist indexes
CREATE INDEX idx_waitlist_event_id ON waitlist(event_id);
CREATE INDEX idx_waitlist_user_id ON waitlist(user_id);
CREATE INDEX idx_waitlist_position ON waitlist(event_id, position);
CREATE INDEX idx_waitlist_notified ON waitlist(notified) WHERE notified = false;

-- Payment Transactions indexes
CREATE INDEX idx_payment_transactions_order_id ON payment_transactions(order_id);
CREATE INDEX idx_payment_transactions_transaction_id ON payment_transactions(transaction_id);
CREATE INDEX idx_payment_transactions_status ON payment_transactions(status);

-- Email Notifications indexes
CREATE INDEX idx_email_notifications_user_id ON email_notifications(user_id);
CREATE INDEX idx_email_notifications_status ON email_notifications(status);
CREATE INDEX idx_email_notifications_created_at ON email_notifications(created_at DESC);

-- Audit Log indexes
CREATE INDEX idx_audit_log_user_id ON audit_log(user_id);
CREATE INDEX idx_audit_log_entity ON audit_log(entity_type, entity_id);
CREATE INDEX idx_audit_log_created_at ON audit_log(created_at DESC);

-- ============================================================================
-- FUNCTIONS AND TRIGGERS
-- ============================================================================

-- Function to update updated_at timestamp
CREATE OR REPLACE FUNCTION update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = CURRENT_TIMESTAMP;
    RETURN NEW;
END;
$$ language 'plpgsql';

-- Apply updated_at trigger to all relevant tables
CREATE TRIGGER update_users_updated_at BEFORE UPDATE ON users
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_promoters_updated_at BEFORE UPDATE ON promoters
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_events_updated_at BEFORE UPDATE ON events
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_ticket_tiers_updated_at BEFORE UPDATE ON ticket_tiers
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_orders_updated_at BEFORE UPDATE ON orders
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_tickets_updated_at BEFORE UPDATE ON tickets
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_waitlist_updated_at BEFORE UPDATE ON waitlist
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

-- Function to validate ticket tier constraints
CREATE OR REPLACE FUNCTION validate_ticket_tier()
RETURNS TRIGGER AS $$
BEGIN
    -- Ensure sold + reserved doesn't exceed quantity
    IF NEW.sold + NEW.reserved > NEW.quantity THEN
        RAISE EXCEPTION 'Sold + reserved tickets cannot exceed total quantity';
    END IF;
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER validate_ticket_tier_before_update
    BEFORE INSERT OR UPDATE ON ticket_tiers
    FOR EACH ROW EXECUTE FUNCTION validate_ticket_tier();

-- Function to automatically create audit log entries
CREATE OR REPLACE FUNCTION create_audit_log()
RETURNS TRIGGER AS $$
BEGIN
    IF (TG_OP = 'DELETE') THEN
        INSERT INTO audit_log (action, entity_type, entity_id, old_data)
        VALUES (TG_OP, TG_TABLE_NAME, OLD.id, row_to_json(OLD));
        RETURN OLD;
    ELSIF (TG_OP = 'UPDATE') THEN
        INSERT INTO audit_log (action, entity_type, entity_id, old_data, new_data)
        VALUES (TG_OP, TG_TABLE_NAME, NEW.id, row_to_json(OLD), row_to_json(NEW));
        RETURN NEW;
    ELSIF (TG_OP = 'INSERT') THEN
        INSERT INTO audit_log (action, entity_type, entity_id, new_data)
        VALUES (TG_OP, TG_TABLE_NAME, NEW.id, row_to_json(NEW));
        RETURN NEW;
    END IF;
END;
$$ LANGUAGE plpgsql;

-- Apply audit triggers to critical tables (optional - can be resource intensive)
-- CREATE TRIGGER audit_orders AFTER INSERT OR UPDATE OR DELETE ON orders
--     FOR EACH ROW EXECUTE FUNCTION create_audit_log();

-- CREATE TRIGGER audit_tickets AFTER INSERT OR UPDATE OR DELETE ON tickets
--     FOR EACH ROW EXECUTE FUNCTION create_audit_log();

-- ============================================================================
-- VIEWS
-- ============================================================================

-- View for active events with ticket availability
CREATE OR REPLACE VIEW active_events_with_availability AS
SELECT 
    e.id,
    e.uuid,
    e.title,
    e.slug,
    e.description,
    e.venue_name,
    e.venue_city,
    e.venue_state,
    e.start_time,
    e.end_time,
    e.featured_image_url,
    e.category,
    e.tags,
    e.capacity,
    p.company_name as promoter_name,
    COALESCE(SUM(tt.quantity), 0) as total_tickets,
    COALESCE(SUM(tt.sold), 0) as tickets_sold,
    COALESCE(SUM(tt.quantity - tt.sold - tt.reserved), 0) as tickets_available,
    MIN(tt.price) as min_price,
    MAX(tt.price) as max_price
FROM events e
JOIN promoters p ON e.promoter_id = p.id
LEFT JOIN ticket_tiers tt ON e.id = tt.event_id AND tt.is_active = true
WHERE e.status = 'published' 
    AND e.deleted_at IS NULL
    AND e.start_time > CURRENT_TIMESTAMP
GROUP BY e.id, e.uuid, e.title, e.slug, e.description, e.venue_name, 
         e.venue_city, e.venue_state, e.start_time, e.end_time, 
         e.featured_image_url, e.category, e.tags, e.capacity, p.company_name;

-- View for user ticket summary
CREATE OR REPLACE VIEW user_tickets_summary AS
SELECT 
    u.id as user_id,
    u.email,
    t.id as ticket_id,
    t.uuid as ticket_uuid,
    t.ticket_code,
    t.status as ticket_status,
    e.title as event_title,
    e.start_time as event_start_time,
    e.venue_name,
    e.venue_city,
    tt.name as tier_name,
    o.order_number,
    o.total_amount,
    o.created_at as purchase_date
FROM users u
JOIN tickets t ON u.id = t.user_id
JOIN orders o ON t.order_id = o.id
JOIN events e ON t.event_id = e.id
JOIN ticket_tiers tt ON t.tier_id = tt.id
WHERE t.deleted_at IS NULL;

-- ============================================================================
-- GRANT PERMISSIONS (adjust for your environment)
-- ============================================================================

-- Create application user (run separately if needed)
-- CREATE USER ticket_vendor_app WITH PASSWORD 'your_secure_password';
-- GRANT CONNECT ON DATABASE ticket_vendor TO ticket_vendor_app;
-- GRANT USAGE ON SCHEMA public TO ticket_vendor_app;
-- GRANT SELECT, INSERT, UPDATE, DELETE ON ALL TABLES IN SCHEMA public TO ticket_vendor_app;
-- GRANT USAGE, SELECT ON ALL SEQUENCES IN SCHEMA public TO ticket_vendor_app;

-- ============================================================================
-- COMMENTS (Documentation)
-- ============================================================================

COMMENT ON TABLE users IS 'Core users table for both attendees and promoters';
COMMENT ON TABLE promoters IS 'Extended information for event promoters';
COMMENT ON TABLE events IS 'Events being offered for ticket sales';
COMMENT ON TABLE ticket_tiers IS 'Different pricing tiers for event tickets';
COMMENT ON TABLE orders IS 'Customer orders for tickets';
COMMENT ON TABLE order_items IS 'Line items for each order';
COMMENT ON TABLE tickets IS 'Individual tickets issued from orders';
COMMENT ON TABLE waitlist IS 'Waitlist entries for sold-out events';
COMMENT ON TABLE payment_transactions IS 'Payment transaction records';
COMMENT ON TABLE email_notifications IS 'Email notification tracking';
COMMENT ON TABLE audit_log IS 'Audit trail for critical operations';

-- ============================================================================
-- INDEXES FOR PERFORMANCE
-- ============================================================================

-- Additional composite indexes for common query patterns
CREATE INDEX idx_tickets_event_user ON tickets(event_id, user_id);
CREATE INDEX idx_tickets_order_tier ON tickets(order_id, tier_id);
CREATE INDEX idx_orders_user_status ON orders(user_id, status);
CREATE INDEX idx_events_status_start ON events(status, start_time) 
    WHERE status = 'published' AND deleted_at IS NULL;

-- ============================================================================
-- MATERIALIZED VIEWS FOR ANALYTICS
-- ============================================================================

-- Event sales summary (refresh periodically)
CREATE MATERIALIZED VIEW event_sales_summary AS
SELECT 
    e.id as event_id,
    e.title as event_title,
    e.start_time,
    p.company_name as promoter_name,
    COUNT(DISTINCT o.id) as total_orders,
    COUNT(DISTINCT t.id) as total_tickets_sold,
    COALESCE(SUM(o.total_amount), 0) as total_revenue,
    COALESCE(AVG(o.total_amount), 0) as average_order_value,
    e.capacity,
    ROUND((COUNT(DISTINCT t.id)::DECIMAL / e.capacity) * 100, 2) as capacity_percentage
FROM events e
JOIN promoters p ON e.promoter_id = p.id
LEFT JOIN orders o ON e.id = o.event_id AND o.status = 'confirmed'
LEFT JOIN tickets t ON o.id = t.order_id AND t.status IN ('valid', 'used')
WHERE e.deleted_at IS NULL
GROUP BY e.id, e.title, e.start_time, p.company_name, e.capacity;

CREATE INDEX idx_event_sales_summary_event_id ON event_sales_summary(event_id);
CREATE INDEX idx_event_sales_summary_total_revenue ON event_sales_summary(total_revenue DESC);

-- ============================================================================
-- END OF SCHEMA
-- ============================================================================
