import csv
from django.http import HttpResponse
from django.shortcuts import render
from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response

from .models import Project, Segment, Appliance, Cabinet
from .serializers import ProjectSerializer, SegmentSerializer, ApplianceSerializer, CabinetSerializer
from .engine import generate_cabinets
from .cutlist import generate_cutlist

# Frontend View
def index(request):
    return render(request, 'index.html')

class ProjectViewSet(viewsets.ModelViewSet):
    queryset = Project.objects.all()
    serializer_class = ProjectSerializer

    @action(detail=True, methods=['post'])
    def generate(self, request, pk=None):
        project = self.get_object()
        try:
            generate_cabinets(project)
            return Response({"status": "Dolap üretimi başarıyla tamamlandı."})
        except ValueError as e:
            return Response({"error": str(e)}, status=status.HTTP_400_BAD_REQUEST)

    @action(detail=True, methods=['get'])
    def cutlist(self, request, pk=None):
        project = self.get_object()
        parts = generate_cutlist(project)
        return Response(parts)

    @action(detail=True, methods=['get'])
    def cutlist_csv(self, request, pk=None):
        project = self.get_object()
        parts = generate_cutlist(project)

        response = HttpResponse(content_type='text/csv')
        response['Content-Disposition'] = f'attachment; filename="project_{project.id}_cutlist.csv"'

        if not parts:
            csv.writer(response).writerow(['Parça bulunamadı'])
            return response

        writer = csv.DictWriter(response, fieldnames=parts[0].keys())
        writer.writeheader()
        for part in parts:
            writer.writerow(part)
            
        return response

    @action(detail=True, methods=['get'])
    def export_state(self, request, pk=None):
        project = self.get_object()
        appliances = ApplianceSerializer(project.appliances.all(), many=True).data
        cabinets = CabinetSerializer(project.cabinets.all(), many=True).data
        return Response({
            "appliances": appliances,
            "cabinets": cabinets
        })

    @action(detail=True, methods=['post'])
    def restore_state(self, request, pk=None):
        project = self.get_object()
        data = request.data
        
        # Temizle
        project.appliances.all().delete()
        project.cabinets.all().delete()
        
        # Yeniden Yarat
        if "appliances" in data:
            for app_data in data["appliances"]:
                # Serilileştirilmiş veriden ID'yi silip yeni nesne yaratıyoruz.
                # Segment ilişkisi ID olarak gelir.
                Appliance.objects.create(
                    project=project,
                    segment_id=app_data['segment'],
                    type=app_data['type'],
                    start_mm=app_data['start_mm'],
                    width_mm=app_data['width_mm'],
                    note=app_data.get('note', '')
                )
        
        if "cabinets" in data:
            for cab_data in data["cabinets"]:
                Cabinet.objects.create(
                    project=project,
                    segment_id=cab_data['segment'],
                    kind=cab_data['kind'],
                    start_mm=cab_data['start_mm'],
                    width_mm=cab_data['width_mm'],
                    depth_mm=cab_data['depth_mm'],
                    height_mm=cab_data['height_mm'],
                    label=cab_data.get('label', ''),
                    has_drawers=cab_data.get('has_drawers', False),
                    is_locked=cab_data.get('is_locked', False)
                )
                
        return Response({"status": "Durum başarıyla geri yüklendi."})

class SegmentViewSet(viewsets.ModelViewSet):
    queryset = Segment.objects.all()
    serializer_class = SegmentSerializer

class ApplianceViewSet(viewsets.ModelViewSet):
    queryset = Appliance.objects.all()
    serializer_class = ApplianceSerializer

    def perform_create(self, serializer):
        # Eğer Konum X (start_mm) -1 olarak gönderildiyse (boş bırakıldıysa), otomatik yan yana ekle
        start_mm = serializer.validated_data.get('start_mm')
        segment = serializer.validated_data.get('segment')
        project = serializer.validated_data.get('project')
        
        if start_mm == -1 and segment and project:
            existing_appliances = Appliance.objects.filter(
                project=project, segment=segment
            ).exclude(type='HOOD')
            existing_cabinets = Cabinet.objects.filter(
                project=project, segment=segment, kind__in=['BASE', 'TALL']
            )
            
            max_end = 0
            for app in existing_appliances:
                end_pos = app.start_mm + app.width_mm
                if end_pos > max_end:
                    max_end = end_pos
            for cab in existing_cabinets:
                end_pos = cab.start_mm + cab.width_mm
                if end_pos > max_end:
                    max_end = end_pos
            
            serializer.validated_data['start_mm'] = max_end

        appliance = serializer.save()
        
        # Eğer fırın (OVEN) ekleniyorsa, otomatik olarak üstüne davlumbaz (HOOD) ekle.
        if appliance.type == 'OVEN':
            Appliance.objects.create(
                project=appliance.project,
                segment=appliance.segment,
                type='HOOD',
                start_mm=appliance.start_mm,
                width_mm=appliance.width_mm
            )

    def perform_update(self, serializer):
        old_start_mm = serializer.instance.start_mm
        appliance = serializer.save()
        
        # Eğer fırın taşındıysa, üstündeki kopyası olan davlumbazı da taşı.
        if appliance.type == 'OVEN' and old_start_mm != appliance.start_mm:
            hoods = Appliance.objects.filter(
                project=appliance.project,
                segment=appliance.segment,
                type='HOOD',
                start_mm=old_start_mm
            )
            for hood in hoods:
                hood.start_mm = appliance.start_mm
                hood.save()
        
        # Eğer davlumbaz taşındıysa, altındaki kopyası olan fırını da taşı.
        if appliance.type == 'HOOD' and old_start_mm != appliance.start_mm:
            ovens = Appliance.objects.filter(
                project=appliance.project,
                segment=appliance.segment,
                type='OVEN',
                start_mm=old_start_mm
            )
            for oven in ovens:
                oven.start_mm = appliance.start_mm
                oven.save()

    def perform_destroy(self, instance):
        # Eğer fırın silinirse, üstündeki davlumbazı da sil.
        if instance.type == 'OVEN':
            Appliance.objects.filter(
                project=instance.project,
                segment=instance.segment,
                type='HOOD',
                start_mm=instance.start_mm
            ).delete()
        instance.delete()

class CabinetViewSet(viewsets.ModelViewSet):
    queryset = Cabinet.objects.all()
    serializer_class = CabinetSerializer

    def perform_create(self, serializer):
        start_mm = serializer.validated_data.get('start_mm')
        segment = serializer.validated_data.get('segment')
        project = serializer.validated_data.get('project')
        kind = serializer.validated_data.get('kind')

        if start_mm == -1 and segment and project:
            max_end = 0
            if kind in ['BASE', 'TALL']:
                existing_appliances = Appliance.objects.filter(
                    project=project, segment=segment
                ).exclude(type='HOOD')
                existing_cabinets = Cabinet.objects.filter(
                    project=project, segment=segment, kind__in=['BASE', 'TALL']
                )
                for app in existing_appliances:
                    end_pos = app.start_mm + app.width_mm
                    if end_pos > max_end: max_end = end_pos
                for cab in existing_cabinets:
                    end_pos = cab.start_mm + cab.width_mm
                    if end_pos > max_end: max_end = end_pos
            elif kind == 'WALL':
                existing_hoods = Appliance.objects.filter(
                    project=project, segment=segment, type='HOOD'
                )
                existing_cabinets = Cabinet.objects.filter(
                    project=project, segment=segment, kind='WALL'
                )
                for app in existing_hoods:
                    end_pos = app.start_mm + app.width_mm
                    if end_pos > max_end: max_end = end_pos
                for cab in existing_cabinets:
                    end_pos = cab.start_mm + cab.width_mm
                    if end_pos > max_end: max_end = end_pos
            
            serializer.validated_data['start_mm'] = max_end

        serializer.save()
