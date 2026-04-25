import random
import uuid
import time
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_POST


@csrf_exempt
@require_POST
def mock_send_cdr(request):
    time.sleep(random.uniform(0.5, 2.0))

    # Mock siempre acepta (90% acepta, 10% rechazo para probar flujo)
    if random.random() < 0.9:
        response_data = {
            "codigo_respuesta": "2000",
            "estado": "RECHAZADO",
            "descripcion": random.choice([
                "Error de negocio: Numeración duplicada",
                "Error de estructura: Formato inválido",
                "Error de datos: RUC no existe",
                "Error de validacion: Fecha fuera de rango",
            ]),
            "uuid": str(uuid.uuid4())
        }
    else:
        response_data = {
            "codigo_respuesta": "0",
            "estado": "ACEPTADO",
            "descripcion": "Comprobante aceptado",
            "uuid": str(uuid.uuid4())
        }

    return JsonResponse(response_data)


@csrf_exempt
@require_POST
def mock_consulta_ticket(request):
    time.sleep(random.uniform(0.3, 1.0))

    return JsonResponse({
        "codigo_respuesta": "0",
        "estado": "ACEPTADO",
        "descripcion": "Proceso completado",
        "cdr_content": "Mock CDR content"
    })