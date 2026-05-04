import re, os, glob, json
from collections import defaultdict

BASE = os.path.dirname(__file__)
VIEWS_DIR = os.path.join(BASE, 'frontend', 'src', 'views')
COMP_DIR = os.path.join(BASE, 'frontend', 'src', 'components')

def read_file(fpath):
    with open(fpath, 'r', encoding='utf-8') as f:
        return f.read()

def find_static_ids(content):
    ids = []
    for m in re.finditer(r'\bid=["\']([^"\']+)["\']', content):
        ids.append(m.group(1))
    return ids

def find_component_imports(content):
    imports = []
    for m in re.finditer(r'import\s+(\w+)\s+from\s+["\']([^"\']+\.vue)["\']', content):
        imports.append((m.group(1), m.group(2)))
    for m in re.finditer(r'components:\s*\{([^}]+)\}', content):
        for name in re.findall(r'(\w+)', m.group(1)):
            imports.append((name, f'auto:{name}'))
    return imports

def resolve_component_path(import_name, import_path, source_dir):
    if import_path.startswith('auto:'):
        for root, dirs, files in os.walk(COMP_DIR):
            for f in files:
                if f.lower() == import_name.lower() + '.vue':
                    return os.path.join(root, f)
        return None
    
    if import_path.startswith('.'):
        abs_path = os.path.normpath(os.path.join(source_dir, import_path))
    elif import_path.startswith('@/'):
        rel = import_path[2:]
        abs_path = os.path.join(BASE, 'frontend', 'src', rel)
    else:
        return None
    
    if not abs_path.endswith('.vue'):
        abs_path += '.vue'
    return abs_path if os.path.exists(abs_path) else None

all_vue_files = []
for d in [VIEWS_DIR, COMP_DIR]:
    all_vue_files.extend(glob.glob(os.path.join(d, '**', '*.vue'), recursive=True))

file_ids = {}
file_components = {}

for fpath in all_vue_files:
    content = read_file(fpath)
    rel = os.path.relpath(fpath, BASE)
    file_ids[rel] = find_static_ids(content)
    file_components[rel] = find_component_imports(content)

def get_all_ids_for_page(view_rel, visited=None):
    if visited is None:
        visited = set()
    if view_rel in visited:
        return []
    visited.add(view_rel)
    
    ids = list(file_ids.get(view_rel, []))
    source_dir = os.path.dirname(os.path.join(BASE, view_rel))
    
    for comp_name, comp_path_str in file_components.get(view_rel, []):
        resolved = resolve_component_path(comp_name, comp_path_str, source_dir)
        if resolved:
            comp_rel = os.path.relpath(resolved, BASE)
            ids.extend(get_all_ids_for_page(comp_rel, visited))
    
    return ids

print("=" * 80)
print("1. GLOBAL DUPLICATE IDS (same id used in multiple files)")
print("=" * 80)

id_to_files = defaultdict(list)
for rel, ids in file_ids.items():
    for id_val in ids:
        id_to_files[id_val].append(rel)

global_dupes = {k: v for k, v in id_to_files.items() if len(v) > 1}
for id_val, files in sorted(global_dupes.items()):
    print(f'\n  id="{id_val}" appears in {len(files)} files:')
    for f in files:
        print(f'    - {f}')

print(f'\n  Total global duplicate ids: {len(global_dupes)}')

print("\n" + "=" * 80)
print("2. PAGE-LEVEL DUPLICATE IDS (same id on same rendered page)")
print("=" * 80)

page_dupes = {}
view_files = glob.glob(os.path.join(VIEWS_DIR, '**', '*.vue'), recursive=True)

for vf in view_files:
    rel = os.path.relpath(vf, BASE)
    all_ids = get_all_ids_for_page(rel)
    id_counts = defaultdict(int)
    for id_val in all_ids:
        id_counts[id_val] += 1
    
    dupes = {k: v for k, v in id_counts.items() if v > 1}
    if dupes:
        page_dupes[rel] = dupes

for rel, dupes in sorted(page_dupes.items()):
    print(f'\n  {rel}:')
    for id_val, count in sorted(dupes.items()):
        print(f'    id="{id_val}" x{count}')

print(f'\n  Total pages with duplicate ids: {len(page_dupes)}')

print("\n" + "=" * 80)
print("3. COMPONENTS WITH STATIC IDS (risk of duplication if used multiple times)")
print("=" * 80)

comp_files = glob.glob(os.path.join(COMP_DIR, '**', '*.vue'), recursive=True)
for cf in comp_files:
    rel = os.path.relpath(cf, BASE)
    ids = file_ids.get(rel, [])
    if ids:
        print(f'\n  {rel}:')
        for id_val in ids:
            print(f'    id="{id_val}"')

print("\n" + "=" * 80)
print("SUMMARY")
print("=" * 80)
total_page_dupes = sum(len(d) for d in page_dupes.values())
print(f'  Global duplicate ids: {len(global_dupes)}')
print(f'  Pages with duplicate ids: {len(page_dupes)}')
print(f'  Total page-level duplicate instances: {total_page_dupes}')
