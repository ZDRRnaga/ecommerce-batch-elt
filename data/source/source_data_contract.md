# Source Data Contract

## Business domain
Synthetic e-commerce transactional dataset for batch ELT practice.

## Source tables

### customers
Represents end customers who place orders.

| column_name   | type      | description |
|---------------|-----------|-------------|
| customer_id    | integer   | Unique customer identifier |
| first_name     | text      | Customer first name |
| last_name      | text      | Customer last name |
| email          | text      | Customer email |
| signup_date    | date      | Customer registration date |
| country_code   | text      | Country code |
| is_active      | boolean   | Whether the customer is active |

### products
Represents products available for sale.

| column_name   | type      | description |
|---------------|-----------|-------------|
| product_id     | integer   | Unique product identifier |
| product_name   | text      | Product name |
| category       | text      | Product category |
| unit_price     | numeric   | Current product price |
| is_active      | boolean   | Whether product is active |
| created_at     | timestamp | Product creation timestamp |

### orders
Represents customer purchase orders.

| column_name   | type      | description |
|---------------|-----------|-------------|
| order_id       | integer   | Unique order identifier |
| customer_id    | integer   | Customer who placed the order |
| order_date     | timestamp | Order creation timestamp |
| order_status   | text      | Order status |
| currency       | text      | Currency code |
| total_amount   | numeric   | Total order amount |

### order_items
Represents line items within each order.

| column_name   | type      | description |
|---------------|-----------|-------------|
| order_item_id  | integer   | Unique order item identifier |
| order_id       | integer   | Related order |
| product_id     | integer   | Product sold |
| quantity       | integer   | Quantity purchased |
| unit_price     | numeric   | Unit price at purchase time |
| line_amount    | numeric   | quantity * unit_price |

### payments
Represents payments associated with orders.

| column_name   | type      | description |
|---------------|-----------|-------------|
| payment_id      | integer   | Unique payment identifier |
| order_id         | integer   | Related order |
| payment_date     | timestamp | Payment timestamp |
| payment_method   | text      | Payment method |
| payment_status   | text      | Payment status |
| payment_amount   | numeric   | Payment amount |

## Relationships
- customers 1:N orders
- orders 1:N order_items
- products 1:N order_items
- orders 1:N payments

## Initial business rules
- Every order belongs to exactly one customer.
- Every order has at least one order item.
- Every order item references one valid product.
- `line_amount = quantity * unit_price`
- `total_amount = sum(line_amount)` by order
- Every payment belongs to one order.
- Not every order must be paid successfully.
- `payment_amount` may equal `total_amount`, but some failed payments can exist.
- Only active products can appear in recent orders.
- Emails in customers should be unique.

## Recommended initial dataset size
- customers: 1,000
- products: 200
- orders: 5,000
- order_items: 15,000 to 20,000
- payments: 5,000 to 6,000