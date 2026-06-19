"""FastAPI web application — Shopping Cart API."""

from contextlib import asynccontextmanager

from fastapi import FastAPI, HTTPException
from psycopg import OperationalError
from pydantic import BaseModel, Field

from src.database import create_pool, init_schema
from src.repository import CarritoRepositorio

pool = None


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Start the connection pool and init the schema on startup."""
    global pool
    # On startup
    pool = create_pool("postgres://postgres:postgres@db:5432/carritos")
    # Init schema
    try:
        conn = pool.getconn()
        init_schema(conn)
        pool.putconn(conn)
    except OperationalError as e:
        print(f"WARNING: could not init schema: {e}")
    yield
    # On shutdown
    if pool:
        pool.close()


app = FastAPI(title="Shopping Cart API", version="1.0.0", lifespan=lifespan)


def _get_repo() -> CarritoRepositorio:
    """Get a repository instance from the pool."""
    conn = pool.getconn()
    return CarritoRepositorio(conn), conn


# ------------------------------------------------------------------
# Schemas
# ------------------------------------------------------------------
class ItemIn(BaseModel):
    product_name: str = Field(..., min_length=1)
    product_price: float = Field(..., gt=0)
    quantity: int = Field(default=1, ge=1)


class DiscountIn(BaseModel):
    percentage: float = Field(..., ge=0, le=100)


class CartOut(BaseModel):
    cart_id: str


class ItemOut(BaseModel):
    id: int
    product_name: str
    product_price: float
    quantity: int
    subtotal: float


class TotalWithTaxOut(BaseModel):
    subtotal: float
    discount_percentage: float
    discount_amount: float
    total_after_discount: float
    iva_rate: float
    iva_amount: float
    total: float


class MessageOut(BaseModel):
    message: str


# ------------------------------------------------------------------
# Endpoints
# ------------------------------------------------------------------
@app.post("/carts", response_model=CartOut, status_code=201)
def create_cart():
    """Create a new empty cart."""
    repo, conn = _get_repo()
    try:
        cart_id = repo.crear_carrito()
        conn.commit()
        return {"cart_id": cart_id}
    finally:
        pool.putconn(conn)


@app.post("/carts/{cart_id}/items", response_model=MessageOut)
def add_item(cart_id: str, item: ItemIn):
    """Add a product to the cart. Duplicate product_name sums quantity."""
    repo, conn = _get_repo()
    try:
        try:
            repo.agregar_producto(cart_id, item.product_name, item.product_price, item.quantity)
        except ValueError as e:
            raise HTTPException(status_code=404, detail=str(e))
        conn.commit()
        return {"message": "Item added"}
    finally:
        pool.putconn(conn)


@app.get("/carts/{cart_id}/items", response_model=list[ItemOut])
def get_items(cart_id: str):
    """Return all items in the cart."""
    repo, conn = _get_repo()
    try:
        items = repo.obtener_items(cart_id)
        return items
    finally:
        pool.putconn(conn)


@app.delete("/carts/{cart_id}/items", response_model=MessageOut)
def clear_cart(cart_id: str):
    """Remove all items from the cart (table is cleared, not just memory)."""
    repo, conn = _get_repo()
    try:
        repo.vaciar_carrito(cart_id)
        conn.commit()
        return {"message": "Cart emptied"}
    finally:
        pool.putconn(conn)


@app.get("/carts/{cart_id}/total")
def get_total(cart_id: str):
    """Return the raw total (sum of subtotals)."""
    repo, conn = _get_repo()
    try:
        total = repo.calcular_total(cart_id)
        return {"total": total}
    finally:
        pool.putconn(conn)


@app.post("/carts/{cart_id}/discount", response_model=MessageOut)
def apply_discount(cart_id: str, discount: DiscountIn):
    """Apply a percentage discount to the cart."""
    repo, conn = _get_repo()
    try:
        try:
            repo.aplicar_descuento(cart_id, discount.percentage)
        except ValueError as e:
            raise HTTPException(status_code=404, detail=str(e))
        conn.commit()
        return {"message": f"Discount of {discount.percentage}% applied"}
    finally:
        pool.putconn(conn)


@app.get("/carts/{cart_id}/total-with-tax", response_model=TotalWithTaxOut)
def get_total_with_tax(cart_id: str):
    """Return the total breakdown including IVA (19%) and discount."""
    repo, conn = _get_repo()
    try:
        breakdown = repo.calcular_total_con_iva(cart_id)
        return breakdown
    finally:
        pool.putconn(conn)
