# Generated by Django 4.1.2 on 2023-05-18 19:43

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('index', '0005_rename_prioridade_processament_position_and_more'),
    ]

    operations = [
        migrations.AddField(
            model_name='processament',
            name='output',
            field=models.TextField(blank=True),
        ),
    ]
