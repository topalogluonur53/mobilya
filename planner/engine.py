from .models import Project, Segment, Appliance, Cabinet

def solve_gap(gap_width, module_list):
    """
    Kalan boşluğu eşit parçalara böler.
    Kullanıcının isteği: Eşit bölme mantığına devam et, sadece parçalar 30cm'e yakın olmak zorunda değil, alabildiğine geniş (max ~900mm) olsun, ama 30cm'den küçük parça çıkmasın.
    """
    if gap_width < 300:
        # Eğer boşluk 30 cm'den küçükse, bu mecburen kör nokta (filler) olur.
        return gap_width, []
        
    MAX_WIDTH = 900
    
    # En az kaç modüle bölersek her biri MAX_WIDTH sınırını aşmaz?
    # (Tavandan yuvarlama mantığı: Ceil(gap_width / MAX_WIDTH))
    num_modules = (gap_width + MAX_WIDTH - 1) // MAX_WIDTH
    
    base_module_width = gap_width // num_modules
    remainder = gap_width % num_modules
    
    mods = []
    for i in range(num_modules):
        w = base_module_width + (1 if i < remainder else 0)
        mods.append(w)
        
    return 0, mods

def generate_cabinets(project):
    try:
        module_list = [int(m.strip()) for m in project.module_set.split(',')]
        module_list.sort(reverse=True)
    except ValueError:
        module_list = [300, 400, 450, 500, 600, 800, 900]
        
    # Delete only unlocked cabinets. Keep 'APPL' kind and 'is_locked=True' cabinets.
    # Wait, APPL cabinets were just placeholders. Let's delete all unlocked BASE, WALL, FILLER 
    Cabinet.objects.filter(project=project, is_locked=False).delete()
    
    # Hata düzeltme: Eskiden kilitli bırakılmış olan beyaz eşya dolaplarını iz kalmaması için temizle
    Cabinet.objects.filter(project=project, is_locked=True, label__contains=' Modülü ').delete()
    
    segments = project.segments.all()
    
    for segment in segments:
        appliances = list(segment.appliances.all().order_by('start_mm'))
        locked_cabs = list(Cabinet.objects.filter(segment=segment, is_locked=True).order_by('start_mm'))
        
        # Combine appliances and locked cabinets as obstacles
        base_appliances = [a for a in appliances if a.type != 'HOOD']
        wall_appliances = [a for a in appliances if a.type in ['HOOD', 'FRIDGE']]
        
        base_locked = [c for c in locked_cabs if c.kind in ['BASE', 'TALL']]
        wall_locked = [c for c in locked_cabs if c.kind == 'WALL']

        class Obstacle:
            def __init__(self, start, width, obj_type, obj_itself=None):
                self.start_mm = start
                self.width_mm = width
                self.type = obj_type
                self.obj = obj_itself
                self.end_mm = start + width

        base_obstacles = []
        for a in base_appliances:
            base_obstacles.append(Obstacle(a.start_mm, a.width_mm, a.type, a))
        for c in base_locked:
            base_obstacles.append(Obstacle(c.start_mm, c.width_mm, c.kind, c))
            
        wall_obstacles = []
        for a in wall_appliances:
            wall_obstacles.append(Obstacle(a.start_mm, a.width_mm, a.type, a))
        for c in wall_locked:
            wall_obstacles.append(Obstacle(c.start_mm, c.width_mm, c.kind, c))

        base_obstacles.sort(key=lambda o: o.start_mm)
        wall_obstacles.sort(key=lambda o: o.start_mm)

        # Check constraints per level
        def check_bounds_and_overlap(obs_list):
            for i in range(len(obs_list)):
                o = obs_list[i]
                if o.start_mm < 0 or o.end_mm > segment.length_mm:
                    return False # Out of bounds
                if i < len(obs_list) - 1:
                    next_o = obs_list[i+1]
                    if o.end_mm > next_o.start_mm:
                        return False # Overlap
            return True
        
        if not check_bounds_and_overlap(base_obstacles) or not check_bounds_and_overlap(wall_obstacles):
            raise ValueError(f"Çakışma veya sığmama tespit edildi! Lütfen kilitli dolap/cihaz ölçülerini kontrol edin. Duvar: {segment.name}")
        
        # 1. BASE LEVEL
        current_x = 0
        for obs in base_obstacles:
            gap = obs.start_mm - current_x
            if gap > 0:
                fill_base_gap(project, segment, current_x, gap, module_list)
            
            # create cabinet for APPL if it is an actual appliance (not a locked cabinet)
            if hasattr(obs.obj, 'type'): # it's an Appliance
                a = obs.obj
                if a.type == 'SINK':
                    Cabinet.objects.create(project=project, segment=segment, kind='BASE', start_mm=a.start_mm, width_mm=a.width_mm, depth_mm=project.base_depth, height_mm=project.base_height, label=f"Evye Modülü {a.width_mm}", is_locked=False)
                elif a.type == 'OVEN':
                    Cabinet.objects.create(project=project, segment=segment, kind='BASE', start_mm=a.start_mm, width_mm=a.width_mm, depth_mm=project.base_depth, height_mm=project.base_height, label=f"Fırın Modülü {a.width_mm}", is_locked=False)
                elif a.type == 'DW':
                    Cabinet.objects.create(project=project, segment=segment, kind='BASE', start_mm=a.start_mm, width_mm=a.width_mm, depth_mm=project.base_depth, height_mm=project.base_height, label=f"Bulaşık Mak. Modülü {a.width_mm}", is_locked=False)
                elif a.type == 'FRIDGE':
                    Cabinet.objects.create(project=project, segment=segment, kind='BASE', start_mm=a.start_mm, width_mm=a.width_mm, depth_mm=project.base_depth, height_mm=2000, label=f"Buzdolabı Modülü {a.width_mm}", is_locked=False)
                else:
                    Cabinet.objects.create(project=project, segment=segment, kind='APPL', start_mm=a.start_mm, width_mm=a.width_mm, depth_mm=project.base_depth, height_mm=project.base_height, label=f"{a.type} Boşluk", is_locked=False)
            
            current_x = obs.end_mm
            
        # final base gap
        last_gap = segment.length_mm - current_x
        if last_gap > 0:
            fill_base_gap(project, segment, current_x, last_gap, module_list)
            
        # 2. WALL LEVEL
        current_x = 0
        for obs in wall_obstacles:
            gap = obs.start_mm - current_x
            if gap > 0:
                fill_wall_gap(project, segment, current_x, gap, module_list)
            current_x = obs.end_mm
            
        last_gap = segment.length_mm - current_x
        if last_gap > 0:
            fill_wall_gap(project, segment, current_x, last_gap, module_list)

    # After all segments are processed, assign/update completely sequential codes to all cabinets
    all_cabs = project.cabinets.all().order_by('segment__name', 'kind', 'start_mm')
    counters = {'BASE': 1, 'WALL': 1, 'FILLER': 1, 'APPL': 1, 'TALL': 1}
    prefix_map = {'BASE': 'A', 'WALL': 'U', 'FILLER': 'K', 'APPL': 'E', 'TALL': 'B'}
    
    for cab in all_cabs:
        cab.code = f"{cab.segment.name}{prefix_map.get(cab.kind, 'X')}{counters.get(cab.kind, 1)}"
        counters[cab.kind] = counters.get(cab.kind, 1) + 1
        cab.save()

def fill_base_gap(project, segment, start_x, gap_width, module_list):
    filler, mods = solve_gap(gap_width, module_list)
    curr_x = start_x
    for m in mods:
        Cabinet.objects.create(
            project=project, segment=segment,
            kind='BASE', start_mm=curr_x, width_mm=m,
            depth_mm=project.base_depth, height_mm=project.base_height,
            label=f"Alt Dolap {m}"
        )
        curr_x += m
    if filler >= 30: # rule: filler only if >= 30mm
        Cabinet.objects.create(
            project=project, segment=segment,
            kind='FILLER', start_mm=curr_x, width_mm=filler,
            depth_mm=project.base_depth, height_mm=project.base_height,
            label=f"Kör Parça {filler}"
        )

def fill_wall_gap(project, segment, start_x, gap_width, module_list):
    filler, mods = solve_gap(gap_width, module_list)
    curr_x = start_x
    for m in mods:
        Cabinet.objects.create(
            project=project, segment=segment,
            kind='WALL', start_mm=curr_x, width_mm=m,
            depth_mm=project.wall_depth, height_mm=project.wall_height,
            label=f"Üst Dolap {m}"
        )
        curr_x += m
    if filler >= 30:
        Cabinet.objects.create(
            project=project, segment=segment,
            kind='FILLER', start_mm=curr_x, width_mm=filler,
            depth_mm=project.wall_depth, height_mm=project.wall_height,  # wait, wall filler?
            label=f"Üst Kör Parça {filler}"
        )
