class Product:
    def __init__(self, name: str, price: float):
        self.name = name
        self.price = price

class CartItem:
    # Se añade propiedad subtotal para desacoplar el cálculo del item de la clase ShoppingCart
    def __init__(self, product: Product, quantity: int):
        self.product = product
        self.quantity = quantity

    @property
    def subtotal(self) -> float:
        return self.product.price * self.quantity

class ShoppingCart:
    # Refactorización: Uso de constante para el IVA y sum() con generadores para mayor legibilidad
    IVA_RATE = 0.19

    def __init__(self):
        self._items = []

    def add_item(self, product: Product, quantity: int):
        self._items.append(CartItem(product, quantity))

    def calculate_total(self) -> float:
        return sum(item.subtotal for item in self._items)

    def calculate_total_with_tax(self) -> float:
        total = self.calculate_total()
        return total * (1 + self.IVA_RATE)
