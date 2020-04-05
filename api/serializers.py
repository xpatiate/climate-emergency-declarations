from govtrack.models import Area, Structure
from rest_framework import serializers


class AreaSerializer(serializers.ModelSerializer):
    class Meta:
        model = Area
        fields = [
            "id",
            "name",
            "location",
            "population",
            "structure",
            "parent",
            "supplements",
            "agglomeration",
            "num_children",
        ]


class StructureChildSerializer(serializers.ModelSerializer):
    class Meta:
        model = Structure
        fields = ["id", "country", "name", "parent", "height", "num_children"]


class StructureSerializer(serializers.ModelSerializer):
    children = StructureChildSerializer(many=True)

    class Meta:
        model = Structure
        fields = [
            "id",
            "country",
            "name",
            "parent",
            "height",
            "num_children",
            "children",
        ]
