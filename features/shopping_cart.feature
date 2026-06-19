Feature: Carrito de Compras
  Como cliente
  Quiero calcular el total de mi carrito de compras
  Para saber cuánto debo pagar

  Scenario: Calcular total con múltiples productos
    Given un carrito de compras
    When agrego un producto "Laptop" con precio 1000.0 y cantidad 2
    And agrego un producto "Mouse" con precio 500.0 y cantidad 3
    Then el total debe ser 3500.0

  Scenario: Calcular total con impuestos
    Given un carrito de compras
    When agrego un producto "Webcam" con precio 1000.0 y cantidad 1
    Then el total con impuestos debe ser 1190.0

  Scenario: Calcular total para carrito vacío
    Given un carrito de compras
    Then el total debe ser 0.0
