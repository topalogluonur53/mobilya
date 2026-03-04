def generate_cutlist(project):
    cabinets = project.cabinets.filter(kind__in=['BASE', 'WALL', 'FILLER']).order_by('segment__name', 'start_mm')
    t = project.panel_thickness
    
    parts = []
    part_id = 1
    
    for cab in cabinets:
        cab_code = f"[{cab.code}] " if cab.code else ""
        cab_name = f"{cab_code}{cab.segment.name}-{cab.label}"
        
        if cab.kind == 'FILLER':
            parts.append({
                'id': part_id,
                'cabinet': cab_name,
                'part_name': 'Kör Parça',
                'qty': 1,
                'length': cab.height_mm,
                'width': cab.width_mm,
                'thickness': t,
                'material': 'MDF 18mm'
            })
            part_id += 1
            continue
            
        # Side Panels
        parts.append({
            'id': part_id,
            'cabinet': cab_name,
            'part_name': 'Yan Tabla',
            'qty': 2,
            'length': cab.height_mm,
            'width': cab.depth_mm,
            'thickness': t,
            'material': 'MDF 18mm'
        })
        part_id += 1
        
        inner_width = cab.width_mm - 2 * t
        if inner_width <= 0:
            continue
            
        # Bottom Panel
        parts.append({
            'id': part_id,
            'cabinet': cab_name,
            'part_name': 'Alt Tabla',
            'qty': 1,
            'length': inner_width,
            'width': cab.depth_mm,
            'thickness': t,
            'material': 'MDF 18mm'
        })
        part_id += 1
        
        if cab.kind == 'BASE':
            # Top rail (100mm) instead of full panel
            parts.append({
                'id': part_id,
                'cabinet': cab_name,
                'part_name': 'Üst Kayıt',
                'qty': 2, # Wait, usually 2 top rails (front and back)
                'length': inner_width,
                'width': 100,
                'thickness': t,
                'material': 'MDF 18mm'
            })
            part_id += 1
        else: # WALL
            # Top Panel
            parts.append({
                'id': part_id,
                'cabinet': cab_name,
                'part_name': 'Üst Tabla',
                'qty': 1,
                'length': inner_width,
                'width': cab.depth_mm,
                'thickness': t,
                'material': 'MDF 18mm'
            })
            part_id += 1
            
        if getattr(cab, 'has_drawers', False) and cab.kind == 'BASE':
            # Drawer Faces (1 small, 2 large)
            parts.append({
                'id': part_id, 'cabinet': cab_name, 'part_name': 'Çekmece Klapası (Küçük)',
                'qty': 1, 'length': 140, 'width': cab.width_mm - 4,
                'thickness': t, 'material': 'MDF 18mm'
            })
            part_id += 1
            parts.append({
                'id': part_id, 'cabinet': cab_name, 'part_name': 'Çekmece Klapası (Büyük)',
                'qty': 2, 'length': 280, 'width': cab.width_mm - 4,
                'thickness': t, 'material': 'MDF 18mm'
            })
            part_id += 1
            # Drawer Boxes (Sides)
            parts.append({
                'id': part_id, 'cabinet': cab_name, 'part_name': 'Çekmece Yanı (Küçük)',
                'qty': 2, 'length': 100, 'width': cab.depth_mm - 50,
                'thickness': t, 'material': 'MDF 18mm'
            })
            part_id += 1
            parts.append({
                'id': part_id, 'cabinet': cab_name, 'part_name': 'Çekmece Yanı (Büyük)',
                'qty': 4, 'length': 200, 'width': cab.depth_mm - 50,
                'thickness': t, 'material': 'MDF 18mm'
            })
            part_id += 1
             # Drawer Boxes (Front/Back)
            drawer_inner_width = inner_width - 26 # 13mm slide clearance each side
            parts.append({
                'id': part_id, 'cabinet': cab_name, 'part_name': 'Çekmece Ön/Arka (Küçük)',
                'qty': 2, 'length': 100, 'width': drawer_inner_width - 2*t,
                'thickness': t, 'material': 'MDF 18mm'
            })
            part_id += 1
            parts.append({
                'id': part_id, 'cabinet': cab_name, 'part_name': 'Çekmece Ön/Arka (Büyük)',
                'qty': 4, 'length': 200, 'width': drawer_inner_width - 2*t,
                'thickness': t, 'material': 'MDF 18mm'
            })
            part_id += 1
        else:
            # Check if this is an appliance housing by label
            is_4_door = cab.door_style == '4' or (cab.door_style == 'AUTO' and cab.width_mm >= 1200)
            is_2_door = cab.door_style == '2' or (cab.door_style == 'AUTO' and cab.width_mm >= 600 and cab.width_mm < 1200)

            if "Evye" in cab_name:
                # Evye (Sink): Doors exist, but no top and no shelves.
                qty = 4 if is_4_door else (2 if is_2_door else 1)
                w_div = 4 if is_4_door else (2 if is_2_door else 1)
                
                parts.append({
                    'id': part_id, 'cabinet': cab_name, 'part_name': 'Kapak (Evye)',
                    'qty': qty,
                    'length': cab.height_mm - 4 if cab.kind == 'BASE' else cab.height_mm,
                    'width': (cab.width_mm / w_div) - 4,
                    'thickness': t, 'material': 'MDF 18mm'
                })
                part_id += 1
            elif "Fırın" in cab_name or "Bulaşık" in cab_name or "Buzdolabı" in cab_name:
                # OVEN / DW / FRIDGE: Generally these are just housing (sides, maybe bottom). No doors, no shelves.
                pass 
            else:
                # Standard Door & Shelves
                
                # Kapak Hesabı
                qty = 4 if is_4_door else (2 if is_2_door else 1)
                w_div = 4 if is_4_door else (2 if is_2_door else 1)
                if qty > 0:
                    parts.append({
                        'id': part_id,
                        'cabinet': cab_name,
                        'part_name': 'Kapak',
                        'qty': qty,
                        'length': cab.height_mm - 4 if cab.kind == 'BASE' else cab.height_mm,
                        'width': (cab.width_mm / w_div) - 4,
                        'thickness': t,
                        'material': 'MDF 18mm'
                    })
                    part_id += 1
                
                # Dikme ve Raf Hesabı
                p_style = getattr(cab, 'partition_style', 'AUTO')
                num_dividers = 0
                if p_style == '4':
                    num_dividers = 3
                elif p_style == '2':
                    num_dividers = 1
                elif p_style == '1':
                    num_dividers = 0
                else: # AUTO
                    num_dividers = 1 if is_4_door else 0
                
                if num_dividers > 0:
                    parts.append({
                        'id': part_id,
                        'cabinet': cab_name,
                        'part_name': 'Orta Dikme',
                        'qty': num_dividers,
                        'length': cab.height_mm - 2*t,
                        'width': cab.depth_mm - 20,
                        'thickness': t,
                        'material': 'MDF 18mm'
                    })
                    part_id += 1
                
                # Raflar
                num_shelf_compartments = num_dividers + 1
                shelf_qty = 2 if cab.kind == 'WALL' and cab.height_mm > 700 else 1
                total_shelf_qty = shelf_qty * num_shelf_compartments
                
                parts.append({
                    'id': part_id,
                    'cabinet': cab_name,
                    'part_name': 'Raf',
                    'qty': total_shelf_qty,
                    'length': (inner_width - (num_dividers * t)) / num_shelf_compartments,
                    'width': cab.depth_mm - 20,
                    'thickness': t,
                    'material': 'MDF 18mm'
                })
                part_id += 1
        
    return parts
