# Generated by Django 4.0.6 on 2022-07-12 09:54

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('main', '0011_comment_delete_search'),
    ]

    operations = [
        migrations.AlterModelOptions(
            name='comment',
            options={'verbose_name': 'Коментарии', 'verbose_name_plural': 'Коментарии'},
        ),
    ]
