# Generated by Django 3.1.2 on 2020-10-27 12:59

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('blog', '0017_auto_20201027_1058'),
    ]

    operations = [
        migrations.AddField(
            model_name='article',
            name='object_id',
            field=models.IntegerField(null=True),
        ),
    ]
