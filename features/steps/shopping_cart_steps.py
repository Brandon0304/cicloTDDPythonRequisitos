from behave import given, when, then
from src.shopping_cart import ShoppingCart, Product


@given("un carrito de compras")
def step_given_shopping_cart(context):
    """Crea un carrito de compras vacío."""
    context.cart = ShoppingCart()


@when('agrego un producto "{name}" con precio {price:g} y cantidad {quantity:d}')
def step_when_add_product(context, name, price, quantity):
    """Agrega un producto con nombre, precio y cantidad al carrito."""
    product = Product(name, price)
    context.cart.add_item(product, quantity)


@then("el total debe ser {expected:g}")
def step_then_check_total(context, expected):
    """Verifica que el total del carrito coincida con el valor esperado."""
    actual = context.cart.calculate_total()
    assert actual == expected, (
        f"Se esperaba total {expected}, pero se obtuvo {actual}"
    )


@then("el total con impuestos debe ser {expected:g}")
def step_then_check_total_with_tax(context, expected):
    """Verifica que el total con IVA (19%) coincida con el valor esperado."""
    actual = context.cart.calculate_total_with_tax()
    assert actual == expected, (
        f"Se esperaba total con impuestos {expected}, pero se obtuvo {actual}"
    )
