import os
import sys

def remove_bom_from_file(file_path):
    try:
        with open(file_path, 'r', encoding='utf-8-sig') as f:
            content = f.read()

        with open(file_path, 'w', encoding='utf-8') as f:
            f.write(content)

        print(f"✓ Removed BOM from: {file_path}")
        return True
    except Exception as e:
        print(f"✗ Error processing {file_path}: {e}")
        return False

def check_and_remove_bom_in_directory(directory):
    count = 0
    for root, dirs, files in os.walk(directory):
        for file in files:
            if file.endswith('.py'):
                filepath = os.path.join(root, file)
                with open(filepath, 'rb') as f:
                    content = f.read()
                    if content.startswith(b'\xef\xbb\xbf'):
                        if remove_bom_from_file(filepath):
                            count += 1
    return count

if __name__ == "__main__":
    backend_dir = "backend"
    print(f"Scanning {backend_dir} for Python files with BOM...")
    count = check_and_remove_bom_in_directory(backend_dir)
    print(f"\nTotal files processed: {count}")
