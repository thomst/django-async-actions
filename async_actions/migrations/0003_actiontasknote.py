# Generated by Django 4.2.4 on 2023-09-15 09:21

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('async_actions', '0002_actiontaskresult_delete_objecttaskstate_and_more'),
    ]

    operations = [
        migrations.CreateModel(
            name='ActionTaskNote',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('level', models.CharField(choices=[(10, 'debug'), (20, 'info'), (25, 'success'), (30, 'warning'), (40, 'error')], default='info', help_text='Level with which the message were added.', max_length=128, verbose_name='Message-level')),
                ('note', models.TextField(help_text='ActionTask note', verbose_name='Note')),
                ('created_time', models.DateTimeField(auto_now_add=True, help_text='The datetime this message were added.', verbose_name='Time of creation')),
                ('action_task', models.ForeignKey(help_text='AktionTaskResult', on_delete=django.db.models.deletion.CASCADE, related_name='notes', to='async_actions.actiontaskresult', verbose_name='AktionTaskResult')),
            ],
            options={
                'verbose_name': 'Note',
                'verbose_name_plural': 'Notes',
                'ordering': ('action_task', 'created_time'),
            },
        ),
    ]