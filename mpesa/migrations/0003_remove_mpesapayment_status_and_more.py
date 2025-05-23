# Generated by Django 5.2 on 2025-04-28 09:45

import django.db.models.deletion
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('mpesa', '0002_mpesapayment_transaction_date'),
        ('orders', '0005_order_payment_reference_order_phone_number'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='mpesapayment',
            name='status',
        ),
        migrations.RemoveField(
            model_name='mpesapayment',
            name='transaction_date',
        ),
        migrations.AddField(
            model_name='mpesapayment',
            name='checkout_request_id',
            field=models.CharField(blank=True, max_length=100, null=True),
        ),
        migrations.AddField(
            model_name='mpesapayment',
            name='merchant_request_id',
            field=models.CharField(blank=True, max_length=100, null=True),
        ),
        migrations.AddField(
            model_name='mpesapayment',
            name='order',
            field=models.OneToOneField(blank=True, null=True, on_delete=django.db.models.deletion.CASCADE, related_name='mpesa_payment', to='orders.order'),
        ),
        migrations.AddField(
            model_name='mpesapayment',
            name='response_code',
            field=models.CharField(blank=True, max_length=10, null=True),
        ),
        migrations.AddField(
            model_name='mpesapayment',
            name='response_description',
            field=models.CharField(blank=True, max_length=255, null=True),
        ),
        migrations.AddField(
            model_name='mpesapayment',
            name='result_code',
            field=models.CharField(blank=True, max_length=10, null=True),
        ),
        migrations.AddField(
            model_name='mpesapayment',
            name='result_description',
            field=models.CharField(blank=True, max_length=255, null=True),
        ),
        migrations.AddField(
            model_name='mpesapayment',
            name='updated_at',
            field=models.DateTimeField(auto_now=True),
        ),
        migrations.AlterField(
            model_name='mpesapayment',
            name='phone_number',
            field=models.CharField(max_length=20),
        ),
    ]
