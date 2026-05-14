import unittest
from src.shopping_cart import ShoppingCart, Product

class TestShoppingCart(unittest.TestCase):
    def setUp(self):
        self.cart = ShoppingCart()

    def test_calculate_total_multiple_items(self):
        # R3: calcular el total del carrito
        product_a = Product("Laptop", 1000.0)
        product_b = Product("Mouse", 500.0)
        self.cart.add_item(product_a, 2)
        self.cart.add_item(product_b, 3)
        
        # (1000 * 2) + (500 * 3) = 2000 + 1500 = 3500
        self.assertEqual(self.cart.calculate_total(), 3500.0)

    def test_calculate_total_with_tax(self):
        # R6: calcular el total con impuestos (IVA 19%)
        product = Product("Webcam", 1000.0)
        self.cart.add_item(product, 1)
        
        # 1000 + 19% = 1190
        self.assertEqual(self.cart.calculate_total_with_tax(), 1190.0)

    def test_calculate_total_empty_cart(self):
        self.assertEqual(self.cart.calculate_total(), 0.0)

if __name__ == '__main__':
    unittest.main()
