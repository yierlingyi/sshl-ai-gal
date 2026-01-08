import os
import json

def scan_backgrounds():
    bg_dir = "assets/bg"
    output_file = "assets/background_map.json"
    
    bg_map = {}
    
    if not os.path.exists(bg_dir):
        print(f"Directory not found: {bg_dir}")
        return

    # Iterate over files in bg folder
    for f in os.listdir(bg_dir):
        if not f.lower().endswith(('.jpg', '.png', '.jpeg')):
            continue
            
        # Key: filename without extension
        key = os.path.splitext(f)[0]
        # Path: relative path
        full_path = os.path.join(bg_dir, f).replace("\\", "/")
        
        bg_map[key] = {
            "file": full_path,
            "description": "Auto-scanned background"
        }

    # Save to JSON
    with open(output_file, "w", encoding="utf-8") as f:
        json.dump(bg_map, f, indent=4)
    
    print(f"Scanned {len(bg_map)} backgrounds. Saved to {output_file}")

if __name__ == "__main__":
    scan_backgrounds()
