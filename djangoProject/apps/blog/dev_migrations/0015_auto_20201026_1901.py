# Generated by Django 3.1.2 on 2020-10-26 19:01

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('blog', '0014_lookupkey_lookupvalue'),
    ]

    operations = [
        migrations.CreateModel(
            name='Recommend',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('name', models.CharField(max_length=20)),
            ],
        ),
        migrations.RenameModel(
            old_name='LookUpValue',
            new_name='RecommendInfo',
        ),
        migrations.DeleteModel(
            name='LookUpKey',
        ),
        migrations.AddField(
            model_name='recommend',
            name='Look_up_value',
            field=models.ForeignKey(db_constraint=False, on_delete=django.db.models.deletion.DO_NOTHING, related_name='info', to='blog.recommendinfo'),
        ),
    ]
