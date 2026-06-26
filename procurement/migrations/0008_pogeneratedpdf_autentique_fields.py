from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('procurement', '0007_legalrepresentative_po_signer_primary_and_more'),
    ]

    operations = [
        migrations.AddField(
            model_name='pogeneratedpdf',
            name='autentique_doc_id',
            field=models.CharField(blank=True, max_length=100),
        ),
        migrations.AddField(
            model_name='pogeneratedpdf',
            name='autentique_links',
            field=models.JSONField(blank=True, null=True),
        ),
    ]
