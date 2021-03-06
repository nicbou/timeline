# Generated by Django 3.1.2 on 2021-05-02 12:44

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('archive', '0006_n26archive'),
    ]

    operations = [
        migrations.AlterField(
            model_name='googletakeoutarchive',
            name='key',
            field=models.SlugField(max_length=80, primary_key=True, serialize=False),
        ),
        migrations.AlterField(
            model_name='gpxarchive',
            name='key',
            field=models.SlugField(max_length=80, primary_key=True, serialize=False),
        ),
        migrations.AlterField(
            model_name='jsonarchive',
            name='key',
            field=models.SlugField(max_length=80, primary_key=True, serialize=False),
        ),
        migrations.AlterField(
            model_name='n26csvarchive',
            name='key',
            field=models.SlugField(max_length=80, primary_key=True, serialize=False),
        ),
        migrations.AlterField(
            model_name='twitterarchive',
            name='key',
            field=models.SlugField(max_length=80, primary_key=True, serialize=False),
        ),
    ]
