from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('procurement', '0008_pogeneratedpdf_autentique_fields'),
    ]

    operations = [
        migrations.AddField(
            model_name='pogeneratedpdf',
            name='is_signed',
            field=models.BooleanField(default=False),
        ),
    ]
