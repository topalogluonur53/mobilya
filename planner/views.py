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
                    height_mm=app_data.get('height_mm'),
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
                    is_locked=cab_data.get('is_locked', False),
                    door_style=cab_data.get('door_style', 'AUTO'),
                    partition_style=cab_data.get('partition_style', 'AUTO')
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
            app_type = serializer.validated_data.get('type')
            is_wall = (app_type in ['HOOD', 'FRIDGE'])
            is_base = (app_type != 'HOOD')

            max_end = 0
            
            # Find obstacles for the level(s) this appliance occupies
            
            # 1. Check other appliances
            other_apps = Appliance.objects.filter(project=project, segment=segment)
            for a in other_apps:
                a_is_wall = (a.type in ['HOOD', 'FRIDGE'])
                a_is_base = (a.type != 'HOOD')
                if (is_wall and a_is_wall) or (is_base and a_is_base):
                    max_end = max(max_end, a.start_mm + a.width_mm)

            # 2. Check locked cabinets
            other_cabs = Cabinet.objects.filter(project=project, segment=segment, is_locked=True)
            for c in other_cabs:
                c_is_wall = (c.kind in ['WALL', 'EMPTY_WALL', 'TALL'])
                c_is_base = (c.kind in ['BASE', 'TALL', 'EMPTY_BASE', 'APPL'])
                if (is_wall and c_is_wall) or (is_base and c_is_base):
                    max_end = max(max_end, c.start_mm + c.width_mm)
            
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
            is_wall = (kind == 'WALL')
            is_base = (kind in ['BASE', 'TALL'])

            # 1. Check appliances
            other_apps = Appliance.objects.filter(project=project, segment=segment)
            for a in other_apps:
                a_is_wall = (a.type in ['HOOD', 'FRIDGE'])
                a_is_base = (a.type != 'HOOD')
                if (is_wall and a_is_wall) or (is_base and a_is_base):
                    max_end = max(max_end, a.start_mm + a.width_mm)

            # 2. Check cabinets
            other_cabs = Cabinet.objects.filter(project=project, segment=segment)
            for c in other_cabs:
                c_is_wall = (c.kind in ['WALL', 'EMPTY_WALL', 'TALL'])
                c_is_base = (c.kind in ['BASE', 'TALL', 'EMPTY_BASE', 'APPL'])
                if (is_wall and c_is_wall) or (is_base and c_is_base):
                    max_end = max(max_end, c.start_mm + c.width_mm)
            
            serializer.validated_data['start_mm'] = max_end

        serializer.save()

    @action(detail=True, methods=['post'])
    def split(self, request, pk=None):
        cab = self.get_object()
        if cab.width_mm <= 100:
            return Response({'error': 'Dolap daha fazla bölünemez'}, status=status.HTTP_400_BAD_REQUEST)
        
        half_width = cab.width_mm // 2
        new_width = cab.width_mm - half_width
        
        # update current
        cab.width_mm = half_width
        cab.is_locked = True
        cab.save()
        
        # create new
        Cabinet.objects.create(
            project=cab.project,
            segment=cab.segment,
            kind=cab.kind,
            start_mm=cab.start_mm + half_width,
            width_mm=new_width,
            depth_mm=cab.depth_mm,
            height_mm=cab.height_mm,
            label=cab.label,
            has_drawers=cab.has_drawers,
            is_locked=True,
            door_style=cab.door_style,
            partition_style=cab.partition_style
        )
        return Response({'status': 'ok'})

    @action(detail=True, methods=['post'])
    def merge_next(self, request, pk=None):
        cab = self.get_object()
        next_cab = Cabinet.objects.filter(
            project=cab.project, segment=cab.segment, kind=cab.kind,
            start_mm=cab.start_mm + cab.width_mm
        ).first()
        
        if next_cab:
            cab.width_mm += next_cab.width_mm
            cab.is_locked = True
            cab.save()
            next_cab.delete()
            return Response({'status': 'ok'})
        return Response({'error': 'Sağda birleştirilecek dolap yok.'}, status=status.HTTP_400_BAD_REQUEST)

    @action(detail=True, methods=['post'])
    def merge_prev(self, request, pk=None):
        cab = self.get_object()
        prev_cab = Cabinet.objects.filter(
            project=cab.project, segment=cab.segment, kind=cab.kind,
            start_mm__lt=cab.start_mm
        ).order_by('-start_mm').first()
        
        if prev_cab and prev_cab.start_mm + prev_cab.width_mm == cab.start_mm:
            prev_cab.width_mm += cab.width_mm
            prev_cab.is_locked = True
            prev_cab.save()
            cab.delete()
            return Response({'status': 'ok'})
        return Response({'error': 'Solda birleştirilecek dolap yok.'}, status=status.HTTP_400_BAD_REQUEST)
