# Plan de Pruebas TDD - Requerimientos R3 y R6

Este documento detalla la fase **Red** del ciclo TDD para los siguientes requerimientos:

- **R3: Calcular el total del carrito**: Suma de (precio × cantidad) de cada producto.
- **R6: Calcular total con impuestos**: IVA del 19% sobre el total con descuento (en este caso, total base ya que no hay descuentos aplicados en este ciclo).

## Casos de Prueba (Fase Red)

### 1. Calcular total del carrito (R3)
- **Escenario**: Carrito con múltiples productos.
- **Entrada**: 
    - Producto A: precio 1000, cantidad 2
    - Producto B: precio 500, cantidad 3
- **Resultado esperado**: 3500 ( (1000 * 2) + (500 * 3) )
- **Estado inicial**: El método `calculate_total()` no existe o devuelve 0.

### 2. Calcular total con impuestos (R6)
- **Escenario**: Carrito con productos y aplicación de IVA del 19%.
- **Entrada**: 
    - Producto A: precio 1000, cantidad 1
- **Resultado esperado**: 1190 ( 1000 + 19% de 1000 )
- **Estado inicial**: El método `calculate_total_with_tax()` no existe o devuelve 0.

### 3. Calcular total de carrito vacío
- **Escenario**: Carrito sin productos.
- **Resultado esperado**: 0
- **Estado inicial**: El método `calculate_total()` debería manejar el caso base.

---
**Nota**: En la fase Red, ejecutaremos estas pruebas y confirmaremos que fallan debido a la falta de implementación.

## Integración Continua (CI)
Se ha configurado un pipeline de **GitHub Actions** para automatizar la ejecución de pruebas en cada cambio de código.

- **Archivo de configuración**: [.github/workflows/python-app.yml](.github/workflows/python-app.yml)
- **Acciones**:
    - Checkout del código.
    - Configuración de entorno Python 3.10.
    - Ejecución automática de `unittest` sobre la carpeta `tests/`.
- **Propósito**: Garantizar que el ciclo TDD se mantenga íntegro y prevenir regresiones durante las fases de Refactor.