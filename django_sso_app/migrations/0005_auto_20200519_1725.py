# Generated by Django 2.2.11 on 2020-05-19 15:25

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('django_sso_app', '0004_django_user_fields_in_profile__20200417_1757'),
    ]

    operations = [
        migrations.AddField(
            model_name='profile',
            name='alias',
            field=models.CharField(blank=True, max_length=255, null=True, verbose_name='alias'),
        ),
        migrations.AddField(
            model_name='profile',
            name='completed_at',
            field=models.DateTimeField(blank=True, null=True, verbose_name='profile completion date'),
        ),
        migrations.AddField(
            model_name='profile',
            name='meta',
            field=models.TextField(blank=True, null=True, verbose_name='meta'),
        ),
        migrations.AlterField(
            model_name='service',
            name='service_url',
            field=models.CharField(db_index=True, max_length=255, unique=True, verbose_name='service url'),
        ),
    ]