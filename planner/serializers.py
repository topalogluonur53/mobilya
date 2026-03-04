from rest_framework import serializers
from .models import Project, Segment, Appliance, Cabinet

class SegmentSerializer(serializers.ModelSerializer):
    class Meta:
        model = Segment
        fields = '__all__'

class ApplianceSerializer(serializers.ModelSerializer):
    class Meta:
        model = Appliance
        fields = '__all__'

class CabinetSerializer(serializers.ModelSerializer):
    class Meta:
        model = Cabinet
        fields = '__all__'

class ProjectSerializer(serializers.ModelSerializer):
    segments = SegmentSerializer(many=True, read_only=True)
    appliances = ApplianceSerializer(many=True, read_only=True)
    cabinets = CabinetSerializer(many=True, read_only=True)

    class Meta:
        model = Project
        fields = '__all__'
