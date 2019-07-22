# Generated by Django 2.2.3 on 2019-07-22 01:22

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('govtrack', '0006_node_supplements'),
    ]

    operations = [
        migrations.AlterField(
            model_name='node',
            name='supplements',
            field=models.ManyToManyField(blank=True, null=True, related_name='supplement', to='govtrack.Node'),
        ),
    ]
