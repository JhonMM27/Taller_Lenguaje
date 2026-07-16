import django.db.models.deletion
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('comprobantes', '0003_alter_comprobante_options_and_more'),
    ]

    operations = [
        migrations.AddField(
            model_name='comprobante',
            name='reemplaza_a',
            field=models.OneToOneField(
                blank=True,
                help_text='Comprobante rechazado que fue sustituido por este documento.',
                null=True,
                on_delete=django.db.models.deletion.PROTECT,
                related_name='reemplazado_por',
                to='comprobantes.comprobante',
            ),
        ),
        migrations.AlterField(
            model_name='comprobante',
            name='estado',
            field=models.CharField(
                choices=[
                    ('BORRADOR', 'Borrador'),
                    ('EMITIDO', 'Emitido'),
                    ('ENVIADO', 'Enviado'),
                    ('ACEPTADO', 'Aceptado'),
                    ('RECHAZADO', 'Rechazado'),
                    ('ERROR_ENVIO', 'Error de envio'),
                    ('ANULADO_PARCIAL', 'Anulado Parcial'),
                    ('ANULADO_TOTAL', 'Anulado Total'),
                ],
                default='BORRADOR',
                max_length=20,
            ),
        ),
    ]
