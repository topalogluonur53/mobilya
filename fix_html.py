with open('templates/index.html', encoding='utf-8', newline='') as f:
    content = f.read()

lines = content.split('\r\n')
print(f'Before: {len(lines)} lines')

# Remove lines 1261-1463 (0-indexed: 1260-1462)
# Line 1261 is the misplaced "// Draw Countertop" comment starting orphaned code
# Line 1463 is "        });" (duplicate forEach close)
# We keep line 1260 (which is "                });") and jump to 1464 ("") -> 1465 ("    // Draw Countertop")

del lines[1260:1463]  # Removes lines 1261-1463 inclusive (0-indexed 1260-1462)

print(f'After: {len(lines)} lines')

# Show what's now around that spot
print('=== Now around line 1259-1270 ===')
for i in range(1257, 1270):
    if i < len(lines):
        print(f'{i+1}: {lines[i][:100]}')

with open('templates/index.html', 'w', encoding='utf-8', newline='') as f:
    f.write('\r\n'.join(lines))
print('Saved.')
