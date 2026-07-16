"""
Capa de infraestructura.

Adaptadores concretos que conectan el dominio con el mundo exterior:
    - persistencia: Django ORM
    - sunat: cliente SOAP con SUNAT/OSE (mock y real)
    - xml: generacion y firma de XML UBL 2.1
"""

__version__ = "1.0.0"