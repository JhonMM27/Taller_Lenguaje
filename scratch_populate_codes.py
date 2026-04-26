import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings.local')
django.setup()

from apps.clientes.models import Cliente
from apps.empresas.models import Empresa

def populate_codes():
    print("Populating Cliente codes...")
    for i, cliente in enumerate(Cliente.objects.filter(codigo__isnull=True) | Cliente.objects.filter(codigo=''), 1):
        cliente.codigo = f"CL{i:04d}"
        cliente.save()
        print(f"Updated {cliente.razon_social} -> {cliente.codigo}")

    print("\nPopulating Empresa codes...")
    for i, empresa in enumerate(Empresa.objects.filter(codigo__isnull=True) | Empresa.objects.filter(codigo=''), 1):
        empresa.codigo = f"EM{i:04d}"
        empresa.save()
        print(f"Updated {empresa.razon_social} -> {empresa.codigo}")

if __name__ == "__main__":
    populate_codes()
