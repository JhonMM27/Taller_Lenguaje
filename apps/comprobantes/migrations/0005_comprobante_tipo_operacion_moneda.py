from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ('comprobantes', '0004_comprobante_reemplaza_a_y_error_envio'),
    ]

    operations = [
        migrations.AddField(
            model_name='comprobante',
            name='tipo_operacion',
            field=models.CharField(
                choices=[('0101', 'Venta interna'), ('0200', 'Exportación de bienes')],
                default='0101', max_length=4,
            ),
        ),
        migrations.AddField(
            model_name='comprobante',
            name='moneda',
            field=models.CharField(
                choices=[
                    ('PEN', 'Sol peruano'),
                    ('USD', 'Dólar estadounidense'),
                    ('EUR', 'Euro'),
                ],
                default='PEN', max_length=3,
            ),
        ),
    ]
