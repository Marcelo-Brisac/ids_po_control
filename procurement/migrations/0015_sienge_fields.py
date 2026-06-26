from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('procurement', '0014_issuer_prefix_suffix_required'),
    ]

    operations = [
        migrations.AddField(
            model_name='issuer',
            name='sienge_company_id',
            field=models.IntegerField(null=True, verbose_name='Sienge Company ID'),
        ),
        migrations.AddField(
            model_name='supplier',
            name='sienge_creditor_id',
            field=models.IntegerField(null=True, verbose_name='Sienge Creditor ID'),
        ),
        migrations.AddField(
            model_name='po',
            name='sienge_bill_id',
            field=models.IntegerField(blank=True, null=True, verbose_name='Sienge Bill ID'),
        ),
    ]
