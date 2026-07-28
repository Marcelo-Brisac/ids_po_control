from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('procurement', '0017_add_sienge_fields_to_po'),
    ]

    operations = [
        migrations.AddField(
            model_name='po',
            name='sienge_payment_category_id',
            field=models.CharField(blank=True, max_length=50, null=True, verbose_name='Sienge Payment Category ID'),
        ),
    ]
