# Generated by Django 5.1.7 on 2025-03-29 09:36

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('training_app', '0003_remove_user_username_alter_user_user_type'),
    ]

    operations = [
        migrations.AlterModelManagers(
            name='user',
            managers=[
            ],
        ),
        migrations.AlterField(
            model_name='user',
            name='phone_number',
            field=models.CharField(blank=True, max_length=15, null=True),
        ),
    ]
