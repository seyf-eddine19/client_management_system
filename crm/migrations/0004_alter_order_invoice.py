# Generated by Django 5.0.7 on 2024-09-21 19:23

import django.db.models.deletion
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('crm', '0003_order_invoice_alter_customer_gender_and_more'),
    ]

    operations = [
        migrations.AlterField(
            model_name='order',
            name='Invoice',
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.CASCADE, related_name='orders', to='crm.invoice'),
        ),
    ]
