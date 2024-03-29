# -*- coding: utf-8 -*-
# Generated by Django 1.10.5 on 2017-06-05 07:56
from __future__ import unicode_literals

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('challenges', '0036_auto_20170602_1300'),
    ]

    operations = [
        migrations.CreateModel(
            name='SubcategoryProficiencyAward',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('xp_reward', models.IntegerField()),
                ('proficiency', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='challenges.Proficiency')),
                ('subcategory', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='challenges.SubCategory')),
            ],
        ),
        migrations.AlterUniqueTogether(
            name='subcategoryproficiencyaward',
            unique_together=set([('subcategory', 'proficiency')]),
        ),
    ]
