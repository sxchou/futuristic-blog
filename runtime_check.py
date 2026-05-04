import re, os, glob

dirs = [
    os.path.join(os.path.dirname(__file__), 'frontend', 'src', 'views'),
    os.path.join(os.path.dirname(__file__), 'frontend', 'src', 'components'),
]
files = []
for d in dirs:
    files.extend(glob.glob(os.path.join(d, '**', '*.vue'), recursive=True))
files = sorted(set(files))

issues_total = 0

def report(category, fpath, line, msg):
    global issues_total
    issues_total += 1
    rel = os.path.relpath(fpath, os.path.dirname(__file__))
    print(f'  [{category}] {rel} line {line}: {msg}')

for fpath in files:
    with open(fpath, 'r', encoding='utf-8') as f:
        content = f.read()
        lines = content.split('\n')
    
    # === 1. STATIC duplicate ids (same id appears multiple times in source) ===
    all_ids = {}
    for i, line in enumerate(lines, 1):
        for m in re.finditer(r'\bid=["\']([^"\']+)["\']', line):
            id_val = m.group(1)
            if id_val not in all_ids:
                all_ids[id_val] = []
            all_ids[id_val].append(i)
    for id_val, line_nums in all_ids.items():
        if len(line_nums) > 1:
            report('DUP-ID', fpath, line_nums[0], f'id="{id_val}" repeated on lines {line_nums}')
    
    # === 2. STATIC id inside v-for (will duplicate at runtime) ===
    # Find v-for blocks and check for static ids inside them
    vfor_pattern = re.compile(r'v-for="[^"]*"', re.IGNORECASE)
    for m in vfor_pattern.finditer(content):
        vfor_line = content[:m.start()].count('\n') + 1
        # Find the containing element's scope (to next sibling at same level)
        # Simple approach: find all static ids in the next ~50 lines after v-for
        start_pos = m.start()
        end_pos = min(start_pos + 3000, len(content))
        block = content[start_pos:end_pos]
        
        static_ids = re.findall(r'\bid=["\']([^"\']+)["\']', block)
        dynamic_ids = re.findall(r':id=', block)
        
        for sid in static_ids:
            if ':' not in sid and '+' not in sid and sid not in ('', ):
                report('VFOR-ID', fpath, vfor_line, f'Static id="{sid}" inside v-for will duplicate at runtime. Use :id="\'{sid}-\' + index"')
    
    # === 3. Form fields NOT inside <form> ===
    # Find all <form>...</form> ranges
    form_ranges = []
    for fm in re.finditer(r'<form\b[^>]*>(.*?)</form>', content, re.DOTALL):
        form_ranges.append((fm.start(), fm.end()))
    
    # Find all input/select/textarea elements
    field_pattern = re.compile(r'<(input|select|textarea)\b([^>]*?)(/?>)', re.DOTALL)
    for fm in field_pattern.finditer(content):
        tag = fm.group(1)
        attrs = fm.group(2)
        
        # Skip hidden, submit, button, radio, checkbox, file
        if re.search(r'type=["\'](?:hidden|submit|button|radio|checkbox|file)["\']', attrs):
            continue
        
        # Check if inside a <form>
        pos = fm.start()
        in_form = any(s <= pos <= e for s, e in form_ranges)
        
        if not in_form:
            line_num = content[:pos].count('\n') + 1
            # Get a short description
            v_model = re.search(r'v-model="([^"]+)"', attrs)
            desc = v_model.group(1) if v_model else tag
            report('NO-FORM', fpath, line_num, f'<{tag}> v-model="{desc}" is NOT inside a <form> element')
    
    # === 4. Form fields missing BOTH id and name ===
    for fm in field_pattern.finditer(content):
        tag = fm.group(1)
        attrs = fm.group(2)
        
        if re.search(r'type=["\'](?:hidden|submit|button|radio|checkbox|file)["\']', attrs):
            continue
        
        has_id = bool(re.search(r'\bid=', attrs))
        has_name = bool(re.search(r'\bname=', attrs))
        
        if not has_id and not has_name:
            line_num = content[:fm.start()].count('\n') + 1
            v_model = re.search(r'v-model="([^"]+)"', attrs)
            desc = v_model.group(1) if v_model else tag
            report('NO-ID-NAME', fpath, line_num, f'<{tag}> v-model="{desc}" has neither id nor name')
    
    # === 5. Password fields not in <form> ===
    for fm in re.finditer(r'type=["\']password["\']', content):
        pos = fm.start()
        in_form = any(s <= pos <= e for s, e in form_ranges)
        if not in_form:
            line_num = content[:pos].count('\n') + 1
            report('PWD-NO-FORM', fpath, line_num, 'Password field not inside <form>')
    
    # === 6. label for= without matching id ===
    all_file_ids = set(re.findall(r'\bid=["\']([^"\']+)["\']', content))
    # Also collect dynamic :id patterns (they generate ids at runtime)
    dynamic_id_patterns = re.findall(r":id=['\"]([^'\"]+)['\"]", content)
    
    for i, line in enumerate(lines, 1):
        for lm in re.finditer(r'<label\b[^>]*\bfor=["\']([^"\']+)["\']', line):
            for_val = lm.group(1)
            if for_val not in all_file_ids:
                # Check if a dynamic :id might generate this
                found_dynamic = False
                for pattern in dynamic_id_patterns:
                    if for_val in pattern or pattern.startswith(for_val):
                        found_dynamic = True
                        break
                if not found_dynamic:
                    report('LABEL-NO-ID', fpath, i, f'label for="{for_val}" has no matching field id')
    
    # === 7. v-for fields with static id but no dynamic index ===
    # More precise: find v-for blocks, then check each field inside
    # We already handle this in check #2, but let's also check for
    # fields inside v-for that have NO id at all (they need one for a11y)
    for vm in vfor_pattern.finditer(content):
        start_pos = vm.start()
        # Find the end of the v-for element (simplified: scan to next v-for or end)
        block_start = start_pos
        block_end = min(start_pos + 3000, len(content))
        block = content[block_start:block_end]
        
        # Find fields in this block
        for fm in re.finditer(r'<(input|select|textarea)\b([^>]*?)(/?>)', block, re.DOTALL):
            tag = fm.group(1)
            attrs = fm.group(2)
            
            if re.search(r'type=["\'](?:hidden|submit|button|radio|checkbox|file)["\']', attrs):
                continue
            
            has_id = bool(re.search(r'\bid=', attrs))
            has_dynamic_id = bool(re.search(r':id=', attrs))
            has_name = bool(re.search(r'\bname=', attrs))
            has_dynamic_name = bool(re.search(r':name=', attrs))
            
            line_num = content[:block_start + fm.start()].count('\n') + 1
            
            if not has_id and not has_dynamic_id and not has_name and not has_dynamic_name:
                v_model = re.search(r'v-model="([^"]+)"', attrs)
                desc = v_model.group(1) if v_model else tag
                report('VFOR-NO-ID', fpath, line_num, f'<{tag}> in v-for has no id/name (v-model="{desc}")')

print()
print('=' * 60)
if issues_total == 0:
    print('ALL CLEAN - No issues found!')
else:
    print(f'FOUND {issues_total} ISSUE(S) - See above')
print('=' * 60)
