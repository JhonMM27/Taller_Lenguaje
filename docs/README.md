# Documentación del proyecto

| Documento | Contenido |
|---|---|
| [GUIA_EXPOSICION_PROYECTO.md](GUIA_EXPOSICION_PROYECTO.md) | Guion completo de exposición: problema, arquitectura, frameworks, lógica SUNAT y demostración |
| [SUNAT.md](SUNAT.md) | Configuración OSE, emisión, estados, errores y reglas tributarias |
| [EXPORTACION_SUNAT_40.md](EXPORTACION_SUNAT_40.md) | Uso paso a paso del producto SUNAT-40 y operación 0200 |
| [ARQUITECTURA.md](ARQUITECTURA.md) | Capas, servicios, repositorios, mappers y reglas transversales |
| [TESTING.md](TESTING.md) | Instalación y ejecución de pruebas |
| [CAMBIOS.md](CAMBIOS.md) | Historial de cambios y correcciones |

## Reglas operativas clave

- Factura nacional: cliente con RUC.
- Cliente con DNI: boleta.
- Exportación de bienes: factura `01`, operación `0200`, receptor no domiciliado
  y todas las líneas con afectación `40`.
- Documento extranjero: de 1 a 15 caracteres sin espacios; 11 dígitos solo se
  exigen para un RUC peruano de tipo `6`.
- Rechazo SUNAT/OSE: generar un comprobante nuevo.
- Fallo técnico `ERROR_ENVIO`: reintentar el mismo comprobante.
- Aceptado: corregir mediante nota de crédito o débito.
