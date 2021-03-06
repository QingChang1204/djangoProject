# Generated by Django 3.1.2 on 2020-12-01 14:58

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('blog', '0006_auto_20201201_1201'),
    ]

    operations = [
        migrations.CreateModel(
            name='Tag',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('content', models.CharField(max_length=50)),
            ],
        ),
        migrations.RemoveField(
            model_name='user',
            name='groups',
        ),
        migrations.RemoveField(
            model_name='user',
            name='is_superuser',
        ),
        migrations.RemoveField(
            model_name='user',
            name='user_permissions',
        ),
        migrations.RemoveField(
            model_name='article',
            name='tag',
        ),
        migrations.AlterModelTable(
            name='receivemessage',
            table='blog_receive_message',
        ),
        migrations.AlterModelTable(
            name='verifycode',
            table='blog_verify_code',
        ),
        migrations.AlterModelTable(
            name='websocketticket',
            table='blog_websocket_ticket',
        ),
        migrations.CreateModel(
            name='TagShip',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('datetime_created', models.DateTimeField(auto_now_add=True)),
                ('article', models.ForeignKey(db_constraint=False, on_delete=django.db.models.deletion.CASCADE, to='blog.article')),
                ('tag', models.ForeignKey(db_constraint=False, on_delete=django.db.models.deletion.CASCADE, to='blog.tag')),
            ],
            options={
                'db_table': 'blog_tag_ship',
                'unique_together': {('article', 'tag')},
            },
        ),
        migrations.AddField(
            model_name='article',
            name='tag',
            field=models.ManyToManyField(through='blog.TagShip', to='blog.Tag'),
        ),
    ]
