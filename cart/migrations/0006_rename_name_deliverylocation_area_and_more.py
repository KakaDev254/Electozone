# Generated by Django 5.2 on 2025-05-07 21:36

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('cart', '0005_cart_delivery_location'),
    ]

    operations = [
        migrations.RenameField(
            model_name='deliverylocation',
            old_name='name',
            new_name='area',
        ),
        migrations.RemoveField(
            model_name='deliverylocation',
            name='fee',
        ),
        migrations.AddField(
            model_name='deliverylocation',
            name='delivery_fee',
            field=models.DecimalField(decimal_places=2, default=0.0, max_digits=8),
        ),
    ]
