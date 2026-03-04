def solve_gap(gap_width, module_list):
    if gap_width < 300:
        return gap_width, []

    if not module_list:
        module_list = [900, 800, 600, 500, 450, 400, 300]

    # Initialize subset sum DP. dp[w] stores (cost, current modular sum, choice)
    dp = [(float('inf'), 0)] * (gap_width + 1)
    dp[0] = (0, 0)
    choice = [-1] * (gap_width + 1)
    
    for w in range(1, gap_width + 1):
        best_cost = float('inf')
        best_num = float('inf')
        best_choice = -1
        
        for mod in module_list:
            if w >= mod:
                prev_cost, prev_num = dp[w - mod]
                if prev_cost != float('inf'):
                    current_cost = prev_cost + 10 # 10 cost per module
                    
                    if mod < 400:
                        current_cost += 5 # Penaltize small modules
                        
                    if current_cost < best_cost:
                        best_cost = current_cost
                        best_num = prev_num + 1
                        best_choice = mod
                        
        dp[w] = (best_cost, best_num)
        choice[w] = best_choice
        
    best_total_cost = float('inf')
    best_width = 0
    
    for w in range(gap_width + 1):
        if dp[w][0] != float('inf'):
            filler = gap_width - w
            count = dp[w][1]
            
            # Formulate the cost
            cost = filler * 1000 + dp[w][0]
            
            # Avoid fillers smaller than 30mm
            if 0 < filler < 30:
                cost += 50000
                
            if cost < best_total_cost:
                best_total_cost = cost
                best_width = w
                
    mods = []
    curr = best_width
    while curr > 0:
        c = choice[curr]
        if c == -1:
            break
        mods.append(c)
        curr -= c
        
    filler = gap_width - sum(mods)
    return filler, mods

print(solve_gap(700, [600, 400, 300])) # expects filler=100, mods=[300,300] or filler=100 mods=[600]
print(solve_gap(1200, [600, 400, 300])) # 600, 600
print(solve_gap(710, [600, 400, 300])) # filler=110 mods=[600]
