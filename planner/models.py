from django.db import models

class Project(models.Model):
    LAYOUT_CHOICES = [
        ('STRAIGHT', 'Straight'),
        ('L', 'L-Shape')
    ]
    name = models.CharField(max_length=200)
    layout_type = models.CharField(max_length=20, choices=LAYOUT_CHOICES, default='STRAIGHT')
    panel_thickness = models.IntegerField(default=18)
    
    base_depth = models.IntegerField(default=600)
    base_height = models.IntegerField(default=720)
    gap_height = models.IntegerField(default=600)
    wall_depth = models.IntegerField(default=320)
    wall_height = models.IntegerField(default=720)
    
    module_set = models.CharField(max_length=200, default='300,400,450,500,600,800,900')

    def __str__(self):
        return self.name

class Segment(models.Model):
    NAME_CHOICES = [('A', 'A'), ('B', 'B')]
    project = models.ForeignKey(Project, on_delete=models.CASCADE, related_name='segments')
    name = models.CharField(max_length=1, choices=NAME_CHOICES)
    length_mm = models.IntegerField()
    height_mm = models.IntegerField(default=2500)

    def __str__(self):
        return f"{self.project.name} - Segment {self.name}"

class Appliance(models.Model):
    TYPE_CHOICES = [
        ('FRIDGE', 'Buzdolabı'),
        ('DW', 'Bulaşık Makinesi'),
        ('OVEN', 'Fırın'),
        ('SINK', 'Eviye'),
        ('HOOD', 'Davlumbaz'),
        ('CORNER', 'Köşe Modülü')
    ]
    project = models.ForeignKey(Project, on_delete=models.CASCADE, related_name='appliances')
    segment = models.ForeignKey(Segment, on_delete=models.CASCADE, related_name='appliances')
    type = models.CharField(max_length=20, choices=TYPE_CHOICES)
    start_mm = models.IntegerField()
    width_mm = models.IntegerField()
    height_mm = models.IntegerField(null=True, blank=True)
    note = models.TextField(blank=True, null=True)

    def __str__(self):
        return f"{self.type} ({self.start_mm}-{self.start_mm+self.width_mm})"

class Cabinet(models.Model):
    KIND_CHOICES = [
        ('BASE', 'Alt Dolap'),
        ('WALL', 'Üst Dolap'),
        ('TALL', 'Boy Dolap'),
        ('FILLER', 'Kör Parça'),
        ('APPL', 'Beyaz Eşya'),
        ('EMPTY_BASE', 'Boşluk (Alt)'),
        ('EMPTY_WALL', 'Boşluk (Üst)')
    ]
    project = models.ForeignKey(Project, on_delete=models.CASCADE, related_name='cabinets')
    segment = models.ForeignKey(Segment, on_delete=models.CASCADE, related_name='cabinets')
    kind = models.CharField(max_length=20, choices=KIND_CHOICES)
    start_mm = models.IntegerField()
    width_mm = models.IntegerField()
    depth_mm = models.IntegerField()
    height_mm = models.IntegerField()
    label = models.CharField(max_length=100, blank=True)
    code = models.CharField(max_length=20, blank=True)
    door_style = models.CharField(max_length=10, default='AUTO', choices=[
        ('AUTO', 'Otomatik'),
        ('1', '1 Kapaklı'),
        ('2', '2 Kapaklı'),
        ('4', '4 Kapaklı')
    ])
    partition_style = models.CharField(max_length=10, default='AUTO', choices=[
        ('AUTO', 'Otomatik'),
        ('1', 'Bölmesiz'),
        ('2', '2 Bölmeli'),
        ('4', '4 Bölmeli')
    ])
    has_drawers = models.BooleanField(default=False)
    is_locked = models.BooleanField(default=False)

    def __str__(self):
        return f"[{self.code}] {self.kind} {self.width_mm}mm ({self.start_mm}-{self.start_mm+self.width_mm})"
