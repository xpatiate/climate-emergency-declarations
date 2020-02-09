from govtrack.models import Area
from rest_framework import serializers


class AreaSerializer(serializers.ModelSerializer):
    class Meta:
        model = Area
        fields = [
            'id',
            'name',
            'location',
            'population',
            'structure',
            'parent',
            'supplements',
            'agglomeration',
            'num_children'
            ]
