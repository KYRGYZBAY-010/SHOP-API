# Generated by Django 4.0.6 on 2022-07-12 10:04

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('main', '0012_alter_comment_options'),
    ]

    operations = [
        migrations.AlterField(
            model_name='comment',
            name='txt',
            field=models.TextField(max_length=300, verbose_name='Коментарии'),
        ),
    ]
