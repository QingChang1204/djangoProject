# Generated by Django 3.1.2 on 2020-11-16 11:42

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('blog', '0024_auto_20201028_1331'),
    ]

    operations = [
        migrations.AlterField(
            model_name='article',
            name='publish_status',
            field=models.BooleanField(db_index=True, default=False, verbose_name='发布状态'),
        ),
        migrations.AlterField(
            model_name='comment',
            name='content',
            field=models.CharField(max_length=100, verbose_name='评论内容'),
        ),
    ]
