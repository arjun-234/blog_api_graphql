# Generated by Django 3.2 on 2022-06-03 07:13

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('blog_app', '0009_remove_blog_img_link'),
    ]

    operations = [
        migrations.AddField(
            model_name='blog',
            name='img_link',
            field=models.CharField(default='img', max_length=300),
            preserve_default=False,
        ),
    ]
