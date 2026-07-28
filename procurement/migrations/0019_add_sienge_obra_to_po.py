from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('procurement', '0018_add_sienge_payment_category_to_po'),
    ]

    operations = [
        migrations.AddField(
            model_name='po',
            name='sienge_obra_id',
            field=models.IntegerField(blank=True, null=True, verbose_name='Obra (Sienge)'),
        ),
    ]
