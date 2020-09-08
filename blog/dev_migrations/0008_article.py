# Generated by Django 3.1 on 2020-09-08 17:14

from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('blog', '0007_auto_20200908_1302'),
    ]

    operations = [
        migrations.CreateModel(
            name='Article',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('content', models.TextField(verbose_name='内容')),
                ('title', models.CharField(max_length=150, verbose_name='文章标题')),
                ('tag', models.CharField(max_length=30, null=True, verbose_name='标签')),
                ('datetime_created', models.DateTimeField(auto_now_add=True, verbose_name='创建时间')),
                ('datetime_update', models.DateTimeField(auto_now=True, verbose_name='修改时间')),
                ('category', models.CharField(max_length=100, null=True, verbose_name='目录')),
                ('user', models.ForeignKey(db_constraint=False, on_delete=django.db.models.deletion.DO_NOTHING, to=settings.AUTH_USER_MODEL)),
            ],
        ),
    ]
