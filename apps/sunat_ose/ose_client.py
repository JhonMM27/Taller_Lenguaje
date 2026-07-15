"""
Compatibilidad: re-exporta el cliente OSE.

La implementacion real/mock se hace desde `infraestructura.sunat`.
Este archivo se mantiene solo por compatibilidad con codigo viejo
que pueda importar `from apps.sunat_ose.ose_client import get_ose_client`.
"""
from infraestructura.sunat.factory import get_ose_client

__all__ = ["get_ose_client"]