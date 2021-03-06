# Generated by Django 3.1.2 on 2020-10-28 13:04

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('blog', '0022_auto_20201027_1547'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='article',
            name='content',
        ),
        migrations.RemoveField(
            model_name='article',
            name='datetime_update',
        ),
        migrations.RemoveField(
            model_name='article',
            name='publish_status',
        ),
        migrations.RemoveField(
            model_name='article',
            name='tag',
        ),
        migrations.CreateModel(
            name='ArticleInfo',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('content', models.TextField(verbose_name='内容')),
                ('publish_status', models.BooleanField(default=False, verbose_name='发布状态')),
                ('datetime_update', models.DateTimeField(auto_now=True, verbose_name='修改时间')),
                ('article', models.OneToOneField(db_constraint=False, on_delete=django.db.models.deletion.DO_NOTHING, related_name='info', related_query_name='info', to='blog.article')),
            ],
        ),
    ]
