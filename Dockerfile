# ============================================================
# Stage 1: Test — ejecuta TDD (unittest) y BDD (behave)
# Nota: integration y system tests se omiten porque requieren
# TestContainers (Docker-in-Docker) y docker compose up.
# ============================================================
FROM python:3.10-slim AS test

WORKDIR /app

# Instalar dependencias de prueba
RUN pip install --no-cache-dir behave

# Copiar el código fuente y solo los tests unitarios + features BDD
COPY src/ src/
COPY tests/test_shopping_cart.py tests/
COPY features/ features/

# Ejecutar TDD (solo el archivo original) y BDD
RUN python -m unittest discover tests -p "test_shopping_cart.py" && \
    python -m behave features

# ============================================================
# Stage 2: Producción — imagen mínima con el código fuente
# ============================================================
FROM python:3.10-slim AS production

WORKDIR /app

# Etiquetas de metadata
LABEL org.opencontainers.image.source="https://github.com/Brandon0304/cicloTDDPythonRequisitos"
LABEL org.opencontainers.image.description="Shopping Cart — TDD + BDD con Python"
LABEL org.opencontainers.image.licenses="MIT"

# Copiar solo el código fuente desde la etapa de test
COPY --from=test /app/src /app/src

# Comando por defecto: validar que el módulo carga correctamente
CMD ["python", "-c", "from src.shopping_cart import ShoppingCart, Product; print('✓ ShoppingCart module loaded successfully')"]
