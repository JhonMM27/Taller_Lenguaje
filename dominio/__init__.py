"""
Dominio del sistema de facturacion electronica.

Capa de dominio pura en Python. NO importa Django, ni settings, ni models.
Contiene:
    - entidades:    dataclasses con la logica de negocio.
    - servicios:    casos de uso que orquestan entidades y puertos.
    - puertos:      contratos (Protocol) para repositorios y servicios externos.
    - excepciones:  jerarquia propia de errores del dominio.
    - eventos:      dataclasses inmutables para comunicacion entre modulos.
"""

__version__ = "1.0.0"