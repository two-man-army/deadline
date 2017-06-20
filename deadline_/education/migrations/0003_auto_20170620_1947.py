# -*- coding: utf-8 -*-
# Generated by Django 1.10.5 on 2017-06-20 19:47
from __future__ import unicode_literals

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('challenges', '0038_auto_20170605_0809'),
        ('education', '0002_lesson'),
    ]

    operations = [
        migrations.CreateModel(
            name='Homework',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
            ],
        ),
        migrations.CreateModel(
            name='HomeworkTask',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('test_case_count', models.IntegerField()),
                ('is_mandatory', models.BooleanField()),
                ('consecutive_number', models.IntegerField(default=0)),
                ('difficulty', models.IntegerField()),
            ],
        ),
        migrations.CreateModel(
            name='HomeworkTaskDescription',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('content', models.CharField(max_length=3000, null=True)),
                ('input_format', models.CharField(max_length=500, null=True)),
                ('output_format', models.CharField(max_length=1000, null=True)),
                ('constraints', models.CharField(max_length=1000, null=True)),
                ('sample_input', models.CharField(max_length=1000, null=True)),
                ('sample_output', models.CharField(max_length=1000, null=True)),
                ('explanation', models.CharField(max_length=1000, null=True)),
            ],
        ),
        migrations.AddField(
            model_name='homeworktask',
            name='description',
            field=models.OneToOneField(on_delete=django.db.models.deletion.CASCADE, to='education.HomeworkTaskDescription'),
        ),
        migrations.AddField(
            model_name='homeworktask',
            name='homework',
            field=models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='education.Homework'),
        ),
        migrations.AddField(
            model_name='homeworktask',
            name='supported_languages',
            field=models.ManyToManyField(to='challenges.Language'),
        ),
    ]
