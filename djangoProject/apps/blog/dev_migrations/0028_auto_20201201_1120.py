# Generated by Django 3.1.2 on 2020-12-01 11:20

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('blog', '0027_auto_20201201_1117'),
    ]

    operations = [
        migrations.AlterModelTable(
            name='receivemessage',
            table='blog_receive_message',
        ),
        migrations.AlterModelTable(
            name='tagship',
            table='blog_tag_ship',
        ),
        migrations.AlterModelTable(
            name='websocketticket',
            table='blog_websocket_ticket',
        ),
    ]