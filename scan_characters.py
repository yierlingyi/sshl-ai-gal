import os
import json
import re

def scan_characters():
    base_dir = "assets/fg"
    output_file = "assets/character_map.json"
    
    character_map = {}
    
    if not os.path.exists(base_dir):
        print(f"Directory not found: {base_dir}")
        return

    # Iterate over character folders
    for char_folder in os.listdir(base_dir):
        folder_path = os.path.join(base_dir, char_folder)
        if not os.path.isdir(folder_path):
            continue
            
        # Extract base name (e.g., chiguo_A1_0 -> chiguo)
        # Simple heuristic: take part before first underscore
        char_name_key = char_folder.split("_")[0]
        
        if char_name_key not in character_map:
            character_map[char_name_key] = {
                "body": "",
                "expressions": {}
            }
            
        # Scan files in folder
        files = os.listdir(folder_path)
        
        # 1. Find Body (heuristic: ends with _CF_A1_0.png or similar "big" file)
        # OR just take the largest file? 
        # Better heuristic based on file naming convention observed:
        # Body: {char}_CF_{ver}.png
        # Face: {char}_{ver}_face_{id}.png
        
        for f in files:
            if not f.endswith(".png"):
                continue
                
            full_path = os.path.join(folder_path, f).replace("\\", "/")
            
            if "_face_" in f:
                # It's a face
                # Use filename (without extension) as temporary key
                # User will map "happy" -> "filename" later, but for now we expose all
                face_id = f.replace(".png", "")
                # Try to make key shorter? e.g. just the ID at the end
                # chiguo_A1-2_0_face_041903a -> 041903a
                match = re.search(r"face_(.+)$", face_id)
                if match:
                    short_key = match.group(1)
                else:
                    short_key = face_id
                
                character_map[char_name_key]["expressions"][short_key] = full_path
                
            elif "_CF_" in f:
                # Likely body
                character_map[char_name_key]["body"] = full_path

    # Save to JSON
    with open(output_file, "w", encoding="utf-8") as f:
        json.dump(character_map, f, indent=4)
    
    print(f"Scanned {len(character_map)} characters. Saved to {output_file}")

if __name__ == "__main__":
    scan_characters()
