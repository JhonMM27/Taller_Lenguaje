from django.urls import path
from .views import EnviarComprobanteView, ConsultarTicketView
from . import mock_ose

app_name = 'sunat_ose'

urlpatterns = [
    path('comprobante/<int:pk>/enviar/', EnviarComprobanteView.as_view(), name='enviar_comprobante'),
    path('comprobante/<int:pk>/consultar/', ConsultarTicketView.as_view(), name='consultar_ticket'),
    path('ose/send/', mock_ose.mock_send_cdr, name='mock_send_cdr'),
    path('ose/consulta/', mock_ose.mock_consulta_ticket, name='mock_consulta_ticket'),
]