"""System tests for the Shopping Cart API.

Requires the full stack running at http://localhost:8000
(start with: docker compose up -d).
"""

import pytest
import httpx

BASE_URL = "http://localhost:8000"


@pytest.fixture
def client():
    """HTTP client with base URL pre-configured."""
    with httpx.Client(base_url=BASE_URL) as c:
        yield c


# ------------------------------------------------------------------
# Tests
# ------------------------------------------------------------------
class TestShoppingFlow:

    def test_flujo_completo_con_descuento_e_iva(self, client):
        """Agregar productos, aplicar un descuento del 10 % y verificar
        que el total con IVA (19 %) es correcto."""
        # 1. Crear carrito
        resp = client.post("/carts")
        assert resp.status_code == 201
        cart_id = resp.json()["cart_id"]

        # 2. Agregar productos
        client.post(f"/carts/{cart_id}/items", json={
            "product_name": "Laptop", "product_price": 1000.0, "quantity": 2,
        })
        client.post(f"/carts/{cart_id}/items", json={
            "product_name": "Mouse", "product_price": 500.0, "quantity": 3,
        })

        # 3. Aplicar descuento del 10 %
        client.post(f"/carts/{cart_id}/discount", json={"percentage": 10.0})

        # 4. Verificar total con IVA
        resp = client.get(f"/carts/{cart_id}/total-with-tax")
        assert resp.status_code == 200
        data = resp.json()

        # subtotal = (1000*2) + (500*3) = 3500
        assert data["subtotal"] == 3500.0
        assert data["discount_percentage"] == 10.0
        # descuento = 3500 * 10% = 350
        assert data["discount_amount"] == 350.0
        # after discount = 3500 - 350 = 3150
        assert data["total_after_discount"] == 3150.0
        # IVA = 3150 * 0.19 = 598.5
        assert data["iva_amount"] == 598.5
        # total = 3150 + 598.5 = 3748.5
        assert data["total"] == 3748.5

    def test_dos_sesiones_no_se_mezclan(self, client):
        """Dos carritos distintos mantienen sus items aislados."""
        # Crear dos carritos
        cart_a = client.post("/carts").json()["cart_id"]
        cart_b = client.post("/carts").json()["cart_id"]

        # Agregar items diferentes
        client.post(f"/carts/{cart_a}/items", json={
            "product_name": "Laptop", "product_price": 1000.0, "quantity": 1,
        })
        client.post(f"/carts/{cart_b}/items", json={
            "product_name": "Mouse", "product_price": 500.0, "quantity": 2,
        })

        # Verificar que cada carrito solo ve sus propios items
        items_a = client.get(f"/carts/{cart_a}/items").json()
        items_b = client.get(f"/carts/{cart_b}/items").json()

        assert len(items_a) == 1
        assert items_a[0]["product_name"] == "Laptop"

        assert len(items_b) == 1
        assert items_b[0]["product_name"] == "Mouse"

        # Totales independientes
        assert client.get(f"/carts/{cart_a}/total").json()["total"] == 1000.0
        assert client.get(f"/carts/{cart_b}/total").json()["total"] == 1000.0

    def test_vaciar_carrito_via_api_elimina_items(self, client):
        """Vaciar el carrito a través de la API realmente borra los items
        de la tabla (no solo en memoria)."""
        cart_id = client.post("/carts").json()["cart_id"]

        # Agregar productos
        client.post(f"/carts/{cart_id}/items", json={
            "product_name": "Laptop", "product_price": 1000.0, "quantity": 1,
        })
        client.post(f"/carts/{cart_id}/items", json={
            "product_name": "Mouse", "product_price": 500.0, "quantity": 2,
        })

        # Verificar que hay 2 items
        assert len(client.get(f"/carts/{cart_id}/items").json()) == 2

        # Vaciar
        resp = client.delete(f"/carts/{cart_id}/items")
        assert resp.status_code == 200
        assert resp.json()["message"] == "Cart emptied"

        # Confirmar que ya no hay items
        assert client.get(f"/carts/{cart_id}/items").json() == []
        assert client.get(f"/carts/{cart_id}/total").json()["total"] == 0.0
