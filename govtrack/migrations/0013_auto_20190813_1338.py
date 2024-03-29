# Generated by Django 2.2.4 on 2019-08-13 03:38

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("govtrack", "0012_auto_20190811_1722"),
    ]

    operations = [
        migrations.RenameModel(old_name="NodeType", new_name="Structure",),
        migrations.AlterField(
            model_name="declaration",
            name="status",
            field=models.CharField(
                choices=[
                    ("D", "Declared"),
                    ("N", "Inactive"),
                    ("R", "Rejected"),
                    ("V", "Revoked"),
                    ("P", "In Progress"),
                    ("J", "Listing Rejected"),
                ],
                default="D",
                max_length=1,
            ),
        ),
        migrations.AlterField(
            model_name="node", name="nodetype", field=models.IntegerField(),
        ),
    ]
