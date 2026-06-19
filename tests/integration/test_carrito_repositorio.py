"""Integration tests for CarritoRepositorio against a real PostgreSQL
instance via TestContainers.  Each test runs inside its own transaction
that is rolled back automatically, so the database remains clean."""

import pytest
from testcontainers.postgres import PostgresContainer
import psycopg

from src.database import init_schema
from src.repository import CarritoRepositorio


# ------------------------------------------------------------------
# Fixture: one PostgresContainer per session, one transaction per test
# ------------------------------------------------------------------
@pytest.fixture(scope="session")
def postgres_container():
    """Start a real PostgreSQL 16 container for the whole session."""
    with PostgresContainer("postgres:16-alpine") as pg:
        yield pg


@pytest.fixture(autouse=True)
def repo(postgres_container):
    """Create a fresh transaction for each test that rolls back
    automatically, leaving zero side effects."""
    raw_dsn = postgres_container.get_connection_url()
    # psycopg 3 doesn't understand the +psycopg2 driver suffix
    dsn = raw_dsn.replace("+psycopg2", "")
    conn = psycopg.connect(dsn)
    init_schema(conn)                     # ensure tables exist

    # Start a transaction boundary
    conn.execute("BEGIN")
    try:
        yield CarritoRepositorio(conn)
    finally:
        conn.execute("ROLLBACK")          # discard every change
        conn.close()


# ------------------------------------------------------------------
# Tests
# ------------------------------------------------------------------
class TestCarritoRepositorio:

    def test_crear_carrito_retorna_id_unico(self, repo):
        """Un carrito nuevo se crea correctamente y devuelve un UUID."""
        cart_id = repo.crear_carrito()

        assert cart_id is not None
        assert len(cart_id) == 36         # UUID4 format

        # Verify it's actually persisted
        cart = repo.obtener_carrito(cart_id)
        assert cart is not None
        assert cart["discount_percentage"] == 0.0

    def test_mismo_producto_suma_cantidad(self, repo):
        """Agregar el mismo producto dos veces suma la cantidad en lugar
        de duplicar el registro."""
        cart_id = repo.crear_carrito()

        repo.agregar_producto(cart_id, "Laptop", 1000.0, 1)
        repo.agregar_producto(cart_id, "Laptop", 1000.0, 2)

        items = repo.obtener_items(cart_id)
        assert len(items) == 1                     # solo un registro
        assert items[0]["quantity"] == 3           # 1 + 2 = 3
        assert items[0]["subtotal"] == 3000.0      # 1000 * 3

    def test_total_se_calcula_con_datos_persistidos(self, repo):
        """El total se calcula correctamente con los datos en DB."""
        cart_id = repo.crear_carrito()
        repo.agregar_producto(cart_id, "Laptop", 1000.0, 2)
        repo.agregar_producto(cart_id, "Mouse", 500.0, 3)

        total = repo.calcular_total(cart_id)
        # (1000 * 2) + (500 * 3) = 2000 + 1500 = 3500
        assert total == 3500.0

        # Also verify total with tax (no discount)
        breakdown = repo.calcular_total_con_iva(cart_id)
        assert breakdown["subtotal"] == 3500.0
        assert breakdown["discount_percentage"] == 0.0
        assert breakdown["iva_amount"] == 665.0   # 3500 * 0.19
        assert breakdown["total"] == 4165.0

    def test_vaciar_carrito_elimina_items_de_tabla(self, repo):
        """Vaciar el carrito realmente elimina los items de la tabla
        (no solo en memoria)."""
        cart_id = repo.crear_carrito()
        repo.agregar_producto(cart_id, "Laptop", 1000.0, 2)
        repo.agregar_producto(cart_id, "Mouse", 500.0, 1)
        assert len(repo.obtener_items(cart_id)) == 2

        # Act — empty the cart
        repo.vaciar_carrito(cart_id)

        items = repo.obtener_items(cart_id)
        assert items == []                         # DB really has zero rows
        assert repo.calcular_total(cart_id) == 0.0
