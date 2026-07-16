from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ('clientes', '0003_rename_updated_at_cliente_actualizado_en_and_more'),
    ]

    operations = [
        migrations.AlterField(
            model_name='cliente',
            name='tipo_doc',
            field=models.CharField(
                choices=[
                    ('0', 'Doc. tributario no domiciliado sin RUC'),
                    ('1', 'DNI'),
                    ('6', 'RUC'),
                    ('4', 'Carnet de Extranjería'),
                    ('7', 'Pasaporte'),
                    ('A', 'Cédula de Identidad'),
                ],
                default='6',
                max_length=2,
            ),
        ),
        migrations.AlterField(
            model_name='cliente',
            name='num_doc',
            field=models.CharField(max_length=15),
        ),
        migrations.AddField(
            model_name='cliente',
            name='pais_codigo',
            field=models.CharField(
                default='PE', max_length=2,
                verbose_name='País de residencia (ISO-3166)',
            ),
        ),
    ]
