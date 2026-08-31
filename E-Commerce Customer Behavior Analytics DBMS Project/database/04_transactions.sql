-- ============================================================
-- ACID Transaction Demonstrations
-- ============================================================

-- ============================================================
-- TRANSACTION 1: Checkout / Order Creation
-- Demonstrates: Atomicity — either ALL steps complete or NONE
-- ============================================================
-- This is a template; actual values would come from the application.

/*
BEGIN;

-- Step 1: Create the order
INSERT INTO order_table (customer_id, cart_id, order_date, order_status, total_amount, payment_method)
VALUES (1, 1, NOW(), 'confirmed', 2499.00, 'UPI')
RETURNING order_id;
-- Assume returned order_id = 100

-- Step 2: Copy cart items to order items
INSERT INTO order_item (order_id, product_id, quantity, unit_price, subtotal)
SELECT 100, ci.product_id, ci.quantity, ci.unit_price, ci.quantity * ci.unit_price
FROM cart_item ci
WHERE ci.cart_id = 1 AND ci.removed_at IS NULL;

-- Step 3: Mark cart as converted
UPDATE cart SET cart_status = 'converted', updated_at = NOW() WHERE cart_id = 1;

-- Step 4: Reduce product stock
UPDATE product p
SET stock_quantity = p.stock_quantity - ci.quantity
FROM cart_item ci
WHERE ci.cart_id = 1 AND ci.removed_at IS NULL AND p.product_id = ci.product_id
  AND p.stock_quantity >= ci.quantity;  -- Safety check

-- Step 5: Record payment
INSERT INTO payment (order_id, payment_method, payment_status, amount, payment_date)
VALUES (100, 'UPI', 'completed', 2499.00, NOW());

-- Step 6: Log purchase events
INSERT INTO event (session_id, customer_id, product_id, event_type, event_timestamp)
SELECT s.session_id, 1, ci.product_id, 'purchase', NOW()
FROM cart_item ci
CROSS JOIN (SELECT session_id FROM cart WHERE cart_id = 1) s
WHERE ci.cart_id = 1 AND ci.removed_at IS NULL;

-- If ANY step fails, PostgreSQL automatically rolls back ALL changes
COMMIT;
*/

-- ============================================================
-- TRANSACTION 2: Return Processing
-- Demonstrates: Consistency — order status, refund, and stock update in one transaction
-- ============================================================
/*
BEGIN;

-- Step 1: Create return record
INSERT INTO return_table (order_id, product_id, customer_id, return_reason, refund_amount, return_status)
VALUES (100, 5, 1, 'defective', 999.00, 'approved');

-- Step 2: Update order status
UPDATE order_table SET order_status = 'returned' WHERE order_id = 100;

-- Step 3: Restore product stock
UPDATE product SET stock_quantity = stock_quantity + 1 WHERE product_id = 5;

-- Step 4: Record refund payment
INSERT INTO payment (order_id, payment_method, payment_status, amount, payment_date)
VALUES (100, 'UPI', 'refunded', 999.00, NOW());

-- Step 5: Log return event
INSERT INTO event (session_id, customer_id, product_id, event_type, event_timestamp)
VALUES ((SELECT MAX(session_id) FROM session WHERE customer_id = 1), 1, 5, 'return_request', NOW());

COMMIT;
*/

-- ============================================================
-- TRANSACTION 3: Isolation Demo — Concurrent Cart Updates
-- Demonstrates: Isolation level behavior
-- ============================================================
/*
-- Terminal 1:
BEGIN;
SET TRANSACTION ISOLATION LEVEL SERIALIZABLE;
SELECT total_value FROM cart WHERE cart_id = 1;
-- Sees: 1500.00
UPDATE cart SET total_value = total_value + 500 WHERE cart_id = 1;
-- Waits for commit...

-- Terminal 2 (concurrent):
BEGIN;
SET TRANSACTION ISOLATION LEVEL SERIALIZABLE;
SELECT total_value FROM cart WHERE cart_id = 1;
-- Sees: 1500.00 (isolated from Terminal 1)
UPDATE cart SET total_value = total_value + 300 WHERE cart_id = 1;
-- This will WAIT or ERROR due to serializable isolation

-- Terminal 1:
COMMIT;
-- Terminal 2 will now get a serialization error if conflicting
*/

-- ============================================================
-- Durability is handled by PostgreSQL WAL (Write-Ahead Logging)
-- automatically. No special SQL needed.
-- ============================================================

SELECT 'Transaction demonstration templates ready.' AS status;
