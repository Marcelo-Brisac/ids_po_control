from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('procurement', '0015_sienge_fields'),
    ]

    operations = [
        migrations.AddField(
            model_name='product',
            name='financial_category_purchase',
            field=models.IntegerField(blank=True, null=True, verbose_name='Sienge Financial Category (Purchase)'),
        ),
        migrations.AddField(
            model_name='po',
            name='product',
            field=models.ForeignKey(
                null=True,
                on_delete=django.db.models.deletion.PROTECT,
                related_name='purchase_orders',
                to='procurement.product',
                verbose_name='Product',
            ),
        ),
    ]
