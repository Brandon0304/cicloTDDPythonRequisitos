"""Database connection management and schema DDL."""

import psycopg
from psycopg import Connection
from psycopg_pool import ConnectionPool

SCHEMA_SQL = """
CREATE TABLE IF NOT EXISTS carts (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    discount_percentage NUMERIC(5,2) NOT NULL DEFAULT 0.0,
    created_at TIMESTAMP NOT NULL DEFAULT NOW()
);

CREATE TABLE IF NOT EXISTS cart_items (
    id SERIAL PRIMARY KEY,
    cart_id UUID NOT NULL REFERENCES carts(id) ON DELETE CASCADE,
    product_name VARCHAR(255) NOT NULL,
    product_price NUMERIC(10,2) NOT NULL,
    quantity INTEGER NOT NULL DEFAULT 1,
    UNIQUE(cart_id, product_name)
);
"""


def create_pool(dsn: str, minconn: int = 1, maxconn: int = 10) -> ConnectionPool:
    """Create a connection pool to PostgreSQL."""
    return ConnectionPool(dsn, min_size=minconn, max_size=maxconn)


def init_schema(conn: Connection) -> None:
    """Execute DDL to create tables if they don't exist."""
    with conn.cursor() as cur:
        cur.execute(SCHEMA_SQL)
    conn.commit()
