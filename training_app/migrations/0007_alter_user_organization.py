# Generated by Django 5.1.7 on 2025-05-10 09:35

import django.db.models.deletion
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('training_app', '0006_alter_courseprogress_cadet_and_more'),
    ]

    operations = [
        migrations.AlterField(
            model_name='user',
            name='organization',
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.CASCADE, related_name='users', to='training_app.organization'),
        ),
    ]
