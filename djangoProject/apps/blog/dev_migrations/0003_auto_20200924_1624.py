# Generated by Django 3.1 on 2020-09-24 16:24

from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('blog', '0002_auto_20200923_1315'),
    ]

    operations = [
        migrations.CreateModel(
            name='VerifyCode',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('phone', models.CharField(max_length=11, verbose_name='手机号')),
                ('code', models.CharField(max_length=6, verbose_name='验证码')),
                ('datetime_sent', models.DateTimeField(auto_now_add=True, verbose_name='发送时间')),
            ],
        ),
        migrations.AlterField(
            model_name='article',
            name='category',
            field=models.ForeignKey(db_constraint=False, null=True, on_delete=django.db.models.deletion.DO_NOTHING, related_name='articles', related_query_name='article', to='blog.category'),
        ),
        migrations.AlterField(
            model_name='article',
            name='user',
            field=models.ForeignKey(db_constraint=False, on_delete=django.db.models.deletion.DO_NOTHING, related_name='articles', related_query_name='article', to=settings.AUTH_USER_MODEL),
        ),
        migrations.AlterField(
            model_name='comment',
            name='article',
            field=models.ForeignKey(db_constraint=False, on_delete=django.db.models.deletion.DO_NOTHING, related_name='comments', related_query_name='comment', to='blog.article'),
        ),
        migrations.AlterField(
            model_name='comment',
            name='user',
            field=models.ForeignKey(db_constraint=False, on_delete=django.db.models.deletion.DO_NOTHING, related_name='comments', related_query_name='comment', to=settings.AUTH_USER_MODEL),
        ),
        migrations.AlterField(
            model_name='reply',
            name='to_user',
            field=models.ForeignKey(db_constraint=False, on_delete=django.db.models.deletion.DO_NOTHING, related_name='to_replies', related_query_name='to_reply', to=settings.AUTH_USER_MODEL),
        ),
        migrations.AlterField(
            model_name='reply',
            name='user',
            field=models.ForeignKey(db_constraint=False, on_delete=django.db.models.deletion.DO_NOTHING, related_name='replies', related_query_name='reply', to=settings.AUTH_USER_MODEL),
        ),
    ]
