import typing

def solve_gap(gap_width, module_list):
    gap_w = int(gap_width)
    if gap_w < 300:
        return gap_w, []

    if not module_list:
        module_list = [900, 800, 600, 500, 450, 400, 300]
    
    mods_int = [int(m) for m in module_list]

    INF = 9999999
    # Initialize subset sum DP. dp[w] stores (cost, current modular sum, choice)
    dp = [(INF, INF) for _ in range(gap_w + 1)]
    dp[0] = (0, 0)
    choice = [-1 for _ in range(gap_w + 1)]
    
    for w in range(1, gap_w + 1):
        best_cost = INF
        best_num = INF
        best_choice = -1
        
        for mod in mods_int:
            if w >= mod:
                prev_cost, prev_num = dp[w - mod] # type: ignore
                if prev_cost != INF:
                    current_cost = prev_cost + 10 # 10 cost per module
                    
                    if mod < 400:
                        current_cost += 5 # Penaltize small modules
                        
                    if current_cost < best_cost:
                        best_cost = current_cost
                        best_num = prev_num + 1
                        best_choice = mod
                        
        dp[w] = (best_cost, best_num)
        choice[w] = best_choice
        
    best_total_cost = INF
    best_width = 0
    
    for w in range(gap_w + 1):
        if dp[w][0] != INF:
            filler = gap_w - w
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
    while curr > 0: # type: ignore
        c = choice[curr]
        if c == -1:
            break
        mods.append(c) # type: ignore
        curr -= c # type: ignore
        
    final_filler = gap_w - sum(mods)
    return final_filler, mods

print(solve_gap(700, [600, 400, 300])) # expects filler=100, mods=[300,300] or filler=100 mods=[600]
print(solve_gap(1200, [600, 400, 300])) # 600, 600
print(solve_gap(710, [600, 400, 300])) # filler=110 mods=[600]
