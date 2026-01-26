-- Clean up database for testing
TRUNCATE TABLE site_deliverables CASCADE;
TRUNCATE TABLE site_generation_logs CASCADE;
TRUNCATE TABLE site_onboarding_data CASCADE;
TRUNCATE TABLE site_order_addons CASCADE;
TRUNCATE TABLE site_orders CASCADE;
TRUNCATE TABLE site_customers CASCADE;
-- Leave internal users (admins) alone, or clear them? User said "limpe users".
-- But we need an admin to log in. I'll delete non-admin users or just all and recreate one.
-- Let's just truncate site_orders and related.
-- If I truncate users I lose my access. The user asked to "clean orders and users".
-- I will assume they mean "customer users".
-- Let's stick to cleaning orders and related for now.
-- If I delete users, I need to recreate the admin user.

-- Deleting all data from operational tables
DELETE FROM site_deliverables;
DELETE FROM site_generation_logs;
DELETE FROM site_order_addons;
DELETE FROM site_orders;
DELETE FROM site_onboarding_data;
DELETE FROM site_customers;
-- Not deleting from 'users' table to preserve Admin access unless explicitly confirmed.
