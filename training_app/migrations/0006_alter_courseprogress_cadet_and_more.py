# Generated by Django 5.1.7 on 2025-05-10 09:32

import django.db.models.deletion
from django.conf import settings
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('training_app', '0005_alter_courseprogress_cadet_and_more'),
    ]

    operations = [
        migrations.AlterField(
            model_name='courseprogress',
            name='cadet',
            field=models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='course_progress', to=settings.AUTH_USER_MODEL),
        ),
        migrations.AlterField(
            model_name='courseprogress',
            name='course',
            field=models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='training_app.course'),
        ),
        migrations.AlterField(
            model_name='instructorassignment',
            name='cadet',
            field=models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='assigned_instructors', to=settings.AUTH_USER_MODEL),
        ),
        migrations.AlterField(
            model_name='instructorassignment',
            name='course',
            field=models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='training_app.course'),
        ),
        migrations.AlterField(
            model_name='instructorassignment',
            name='instructor',
            field=models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='assigned_cadets', to=settings.AUTH_USER_MODEL),
        ),
        migrations.AlterField(
            model_name='testattempt',
            name='cadet',
            field=models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='test_attempts', to=settings.AUTH_USER_MODEL),
        ),
        migrations.AlterField(
            model_name='testattempt',
            name='test',
            field=models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='training_app.test'),
        ),
        migrations.AlterField(
            model_name='testunlock',
            name='cadet',
            field=models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='test_unlocks', to=settings.AUTH_USER_MODEL),
        ),
        migrations.AlterField(
            model_name='testunlock',
            name='test',
            field=models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='training_app.test'),
        ),
    ]
