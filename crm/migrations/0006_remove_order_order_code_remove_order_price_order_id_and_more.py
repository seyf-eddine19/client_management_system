# Generated by Django 5.0.7 on 2024-09-23 07:57

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('crm', '0005_alter_order_product_code'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='order',
            name='order_code',
        ),
        migrations.RemoveField(
            model_name='order',
            name='price',
        ),
        migrations.AddField(
            model_name='order',
            name='id',
            field=models.BigAutoField(auto_created=True, default=1, primary_key=True, serialize=False, verbose_name='ID'),
            preserve_default=False,
        ),
        migrations.AlterField(
            model_name='invoice',
            name='invoice_number',
            field=models.AutoField(default=1, primary_key=True, serialize=False),
        ),
    ]