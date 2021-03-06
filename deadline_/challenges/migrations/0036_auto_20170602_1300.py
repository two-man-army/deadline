# -*- coding: utf-8 -*-
# Generated by Django 1.10.5 on 2017-06-02 13:00
from __future__ import unicode_literals

from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
        ('challenges', '0035_proficiency'),
    ]

    operations = [
        migrations.CreateModel(
            name='UserSubcategoryProficiency',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('proficiency', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='challenges.Proficiency')),
                ('subcategory', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='challenges.SubCategory')),
                ('user', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to=settings.AUTH_USER_MODEL)),
            ],
        ),
        migrations.AlterUniqueTogether(
            name='usersubcategoryproficiency',
            unique_together=set([('user', 'subcategory')]),
        ),
    ]
