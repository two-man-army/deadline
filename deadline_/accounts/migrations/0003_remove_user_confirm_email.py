# -*- coding: utf-8 -*-
# Generated by Django 1.10.5 on 2017-02-18 10:55
from __future__ import unicode_literals

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('accounts', '0002_auto_20170218_1049'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='user',
            name='confirm_email',
        ),
    ]
