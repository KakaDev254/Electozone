# Generated by Django 5.2 on 2025-04-29 14:00

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('core', '0009_product_spec_4'),
    ]

    operations = [
        migrations.AlterField(
            model_name='product',
            name='price',
            field=models.IntegerField(),
        ),
    ]
