# Generated by Django 2.2.3 on 2019-07-19 04:08

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("govtrack", "0003_auto_20190717_1551"),
    ]

    operations = [
        migrations.AlterField(
            model_name="declaration",
            name="status",
            field=models.CharField(
                choices=[("D", "Declared"), ("R", "Rejected"), ("P", "Provisional")],
                default="D",
                max_length=1,
            ),
        ),
    ]
