# Generated by Django 2.2.4 on 2019-08-13 03:42

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ("govtrack", "0014_auto_20190813_1338"),
    ]

    operations = [
        migrations.RenameField(
            model_name="node", old_name="nodetype", new_name="structure",
        ),
    ]
