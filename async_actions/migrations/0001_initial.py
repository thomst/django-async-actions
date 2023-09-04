# Generated by Django 4.2.4 on 2023-09-04 07:32

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    initial = True

    dependencies = [
        ('contenttypes', '0002_remove_content_type_name'),
    ]

    operations = [
        migrations.CreateModel(
            name='ObjectTaskState',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('task_id', models.CharField(max_length=128, unique=True)),
                ('object_id', models.PositiveIntegerField()),
                ('created_time', models.DateTimeField(auto_now_add=True)),
                ('active', models.BooleanField(null=True)),
                ('content_type', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='contenttypes.contenttype')),
            ],
            options={
                'ordering': ('-created_time',),
                'indexes': [models.Index(fields=['task_id'], name='async_actio_task_id_6f7efe_idx')],
                'unique_together': {('content_type', 'object_id', 'active')},
            },
        ),
    ]
