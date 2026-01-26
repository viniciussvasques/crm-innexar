INSERT INTO site_addons (id, name, slug, description, price, is_active, sort_order, created_at) VALUES 
(1, 'Logo Design', 'logo', 'Professional logo with 3 concepts', 99.00, true, 1, NOW()),
(2, 'SEO Local Pro', 'seo', 'Advanced local SEO optimization', 149.00, true, 2, NOW()),
(3, 'Extra Page', 'extra-page', 'Additional custom page', 79.00, true, 3, NOW()),
(4, 'WhatsApp Widget', 'whatsapp', 'Direct WhatsApp integration', 49.00, true, 4, NOW()),
(5, 'Google Business Setup', 'google-business', 'Complete GMB optimization', 49.00, true, 5, NOW())
ON CONFLICT (id) DO NOTHING;
