# Generated by Django 5.1.3 on 2024-11-29 12:23

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ("blog", "0002_alter_post_image_name"),
    ]

    operations = [
        migrations.RenameField(
            model_name="post", old_name="image_name", new_name="image",
        ),
    ]
