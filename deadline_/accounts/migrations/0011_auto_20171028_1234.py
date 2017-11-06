# -*- coding: utf-8 -*-
# Generated by Django 1.10.5 on 2017-10-28 12:34
from __future__ import unicode_literals

import django.core.validators
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('accounts', '0010_userpersonaldetails'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='userpersonaldetails',
            name='facebook_link',
        ),
        migrations.RemoveField(
            model_name='userpersonaldetails',
            name='github_link',
        ),
        migrations.RemoveField(
            model_name='userpersonaldetails',
            name='linkedin_link',
        ),
        migrations.RemoveField(
            model_name='userpersonaldetails',
            name='twitter_link',
        ),
        migrations.AddField(
            model_name='userpersonaldetails',
            name='facebook_profile',
            field=models.CharField(default='tank', max_length=50),
            preserve_default=False,
        ),
        migrations.AddField(
            model_name='userpersonaldetails',
            name='github_profile',
            field=models.CharField(default='tank', max_length=50),
            preserve_default=False,
        ),
        migrations.AddField(
            model_name='userpersonaldetails',
            name='linkedin_profile',
            field=models.CharField(default='tank', max_length=50),
            preserve_default=False,
        ),
        migrations.AddField(
            model_name='userpersonaldetails',
            name='twitter_profile',
            field=models.CharField(default='tank', max_length=50),
            preserve_default=False,
        ),
        migrations.AlterField(
            model_name='userpersonaldetails',
            name='personal_website',
            field=models.CharField(max_length=100, validators=[django.core.validators.URLValidator()]),
        ),
    ]