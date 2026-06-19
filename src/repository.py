"""CarritoRepositorio — persists shopping carts in PostgreSQL."""

from psycopg import Connection
from psycopg.rows import dict_row


class CarritoRepositorio:
    """Repository for shopping cart persistence.

    All operations use the same connection passed at construction time.
    The caller is responsible for transaction management (commit/rollback).
    """

    IVA_RATE = 0.19

    def __init__(self, conn: Connection):
        self._conn = conn

    # ------------------------------------------------------------------
    # Helpers
    # ------------------------------------------------------------------
    def _cart_exists(self, cart_id: str) -> bool:
        with self._conn.cursor() as cur:
            cur.execute("SELECT 1 FROM carts WHERE id = %s", (cart_id,))
            return cur.fetchone() is not None

    # ------------------------------------------------------------------
    # Carts
    # ------------------------------------------------------------------
    def crear_carrito(self) -> str:
        """Create a new cart and return its UUID."""
        with self._conn.cursor() as cur:
            cur.execute(
                "INSERT INTO carts (discount_percentage) VALUES (0.0) RETURNING id"
            )
            row = cur.fetchone()
            return str(row[0])

    def obtener_carrito(self, cart_id: str) -> dict | None:
        """Return cart metadata or None if not found."""
        with self._conn.cursor(row_factory=dict_row) as cur:
            cur.execute(
                "SELECT id, discount_percentage, created_at FROM carts WHERE id = %s",
                (cart_id,),
            )
            return cur.fetchone()

    # ------------------------------------------------------------------
    # Items
    # ------------------------------------------------------------------
    def agregar_producto(
        self, cart_id: str, product_name: str, product_price: float, quantity: int
    ) -> None:
        """Add a product to the cart.

        If the same product_name already exists in this cart, the
        quantity is *summed* (not duplicated).
        """
        if not self._cart_exists(cart_id):
            raise ValueError(f"Cart {cart_id} does not exist")

        with self._conn.cursor() as cur:
            cur.execute(
                """
                INSERT INTO cart_items (cart_id, product_name, product_price, quantity)
                VALUES (%s, %s, %s, %s)
                ON CONFLICT (cart_id, product_name)
                DO UPDATE SET quantity = cart_items.quantity + EXCLUDED.quantity
                """,
                (cart_id, product_name, product_price, quantity),
            )

    def obtener_items(self, cart_id: str) -> list[dict]:
        """Return all items in a cart with computed subtotal."""
        with self._conn.cursor(row_factory=dict_row) as cur:
            cur.execute(
                """
                SELECT
                    id, product_name, product_price::float8 AS product_price,
                    quantity,
                    (product_price * quantity)::float8 AS subtotal
                FROM cart_items
                WHERE cart_id = %s
                ORDER BY id
                """,
                (cart_id,),
            )
            return cur.fetchall()

    def vaciar_carrito(self, cart_id: str) -> None:
        """Delete all items from a cart."""
        with self._conn.cursor() as cur:
            cur.execute("DELETE FROM cart_items WHERE cart_id = %s", (cart_id,))

    # ------------------------------------------------------------------
    # Discounts
    # ------------------------------------------------------------------
    def aplicar_descuento(self, cart_id: str, percentage: float) -> None:
        """Set a discount percentage on the cart (0-100)."""
        if not (0 <= percentage <= 100):
            raise ValueError("Discount must be between 0 and 100")
        if not self._cart_exists(cart_id):
            raise ValueError(f"Cart {cart_id} does not exist")
        with self._conn.cursor() as cur:
            cur.execute(
                "UPDATE carts SET discount_percentage = %s WHERE id = %s",
                (percentage, cart_id),
            )

    # ------------------------------------------------------------------
    # Totals
    # ------------------------------------------------------------------
    def calcular_total(self, cart_id: str) -> float:
        """Return the raw sum of (price × quantity) for all items."""
        items = self.obtener_items(cart_id)
        return sum(item["subtotal"] for item in items)

    def calcular_total_con_iva(self, cart_id: str) -> dict:
        """Return a full breakdown of the total with IVA and discount.

        Returns:
            {
                "subtotal": float,
                "discount_percentage": float,
                "discount_amount": float,
                "total_after_discount": float,
                "iva_rate": float,
                "iva_amount": float,
                "total": float,
            }
        """
        subtotal = self.calcular_total(cart_id)
        cart = self.obtener_carrito(cart_id)
        discount_pct = float(cart["discount_percentage"]) if cart else 0.0

        discount_amount = subtotal * (discount_pct / 100.0)
        after_discount = subtotal - discount_amount
        iva_amount = after_discount * self.IVA_RATE
        total = after_discount + iva_amount

        return {
            "subtotal": round(subtotal, 2),
            "discount_percentage": discount_pct,
            "discount_amount": round(discount_amount, 2),
            "total_after_discount": round(after_discount, 2),
            "iva_rate": self.IVA_RATE,
            "iva_amount": round(iva_amount, 2),
            "total": round(total, 2),
        }
