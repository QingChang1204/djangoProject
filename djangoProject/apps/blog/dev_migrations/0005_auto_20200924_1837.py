# Generated by Django 3.1 on 2020-09-24 18:37

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('blog', '0004_auto_20200924_1836'),
    ]

    operations = [
        migrations.AlterField(
            model_name='verifycode',
            name='datetime_sent',
            field=models.DateTimeField(null=True, verbose_name='发送时间'),
        ),
    ]