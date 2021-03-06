# Generated by Django 3.1.2 on 2020-10-27 10:58

from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('contenttypes', '0002_remove_content_type_name'),
        ('blog', '0016_auto_20201026_1902'),
    ]

    operations = [
        migrations.CreateModel(
            name='Activity',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('activity_type', models.CharField(choices=[('F', 'Favorite'), ('L', 'Like'), ('S', 'Save')], max_length=20)),
                ('object_id', models.PositiveIntegerField()),
                ('content_type', models.ForeignKey(db_constraint=False, on_delete=django.db.models.deletion.DO_NOTHING, to='contenttypes.contenttype')),
                ('user', models.ForeignKey(db_constraint=False, on_delete=django.db.models.deletion.DO_NOTHING, to=settings.AUTH_USER_MODEL)),
            ],
        ),
        migrations.RemoveField(
            model_name='recommendinfo',
            name='article',
        ),
        migrations.RemoveField(
            model_name='recommendinfo',
            name='comment',
        ),
        migrations.DeleteModel(
            name='Recommend',
        ),
        migrations.DeleteModel(
            name='RecommendInfo',
        ),
    ]
