#!/bin/bash
# Create test order in database

docker exec crm-postgres psql -U crm_user -d innexarcrm << 'EOF'
INSERT INTO site_orders (
    stripe_session_id, 
    customer_name, 
    customer_email, 
    total_price, 
    status,
    created_at,
    updated_at
) VALUES (
    'cs_test_6NHGBTL7', 
    'Test Customer', 
    'test@test.com', 
    399.00, 
    'paid',
    NOW(),
    NOW()
);
SELECT id, stripe_session_id, customer_email, status FROM site_orders;
EOF
