from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('procurement', '0019_add_sienge_obra_to_po'),
    ]

    operations = [
        # Rename models (renames DB tables automatically)
        migrations.RenameModel('Supplier', 'Counterparty'),
        migrations.RenameModel('SupplierBankAccount', 'CounterpartyBankAccount'),

        # Rename FK field on CounterpartyBankAccount
        migrations.RenameField(
            model_name='counterpartybankaccount',
            old_name='supplier',
            new_name='counterparty',
        ),

        # Rename FK field on PO
        migrations.RenameField(
            model_name='po',
            old_name='supplier',
            new_name='counterparty',
        ),

        # Update verbose_name_plural on CounterpartyBankAccount
        migrations.AlterModelOptions(
            name='counterpartybankaccount',
            options={
                'ordering': ['beneficiary_bank_name'],
                'verbose_name_plural': 'Counterparty bank accounts',
            },
        ),

        # Update Meta on Counterparty
        migrations.AlterModelOptions(
            name='counterparty',
            options={
                'ordering': ['name'],
                'verbose_name': 'Counterparty',
                'verbose_name_plural': 'Counterparties',
            },
        ),

        # Add document_type to PO
        migrations.AddField(
            model_name='po',
            name='document_type',
            field=models.CharField(
                choices=[('PO', 'Purchase Order'), ('INV', 'Invoice')],
                default='PO',
                max_length=3,
                verbose_name='Document Type',
            ),
        ),
    ]
