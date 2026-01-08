import os
import json
import re

def scan_sounds():
    sound_dir = "assets/sound"
    desc_file = os.path.join(sound_dir, "音效详情表.txt")
    output_file = "assets/sound_map.json"
    
    sound_map = {}
    
    # 1. Parse Description File
    descriptions = {}
    if os.path.exists(desc_file):
        try:
            with open(desc_file, "r", encoding="gb18030", errors="ignore") as f:
                lines = f.readlines()
                for line in lines:
                    line = line.strip()
                    # Match pattern "123. Description"
                    match = re.match(r"(\d+)\.\s*(.*)", line)
                    if match:
                        idx = int(match.group(1))
                        desc = match.group(2)
                        descriptions[idx] = desc
        except Exception as e:
            print(f"Error reading description file: {e}")
    else:
        print("Description file not found.")

    # 2. Scan Directory
    if not os.path.exists(sound_dir):
        print(f"Directory not found: {sound_dir}")
        return

    for f in os.listdir(sound_dir):
        if not f.lower().endswith(('.ogg', '.mp3', '.wav')):
            continue
            
        # Key: filename without extension
        key = os.path.splitext(f)[0]
        # Path: relative path
        full_path = os.path.join(sound_dir, f).replace("\\", "/")
        
        # Try to match with description
        # Extract number from filename "se001" -> 1, "se025-2" -> 25
        # Regex to find the first number
        num_match = re.search(r"se(\d+)", f, re.IGNORECASE)
        desc_text = "Auto-scanned sound"
        
        if num_match:
            idx = int(num_match.group(1))
            if idx in descriptions:
                base_desc = descriptions[idx]
                desc_text = base_desc
                # If file has sub-index like -2, append to description if possible?
                # The text file sometimes says "25-2 ...". 
                # For simplicity, we just use the main line description.
        
        sound_map[key] = {
            "file": full_path,
            "description": desc_text
        }

    # 3. Save to JSON
    with open(output_file, "w", encoding="utf-8") as f:
        json.dump(sound_map, f, indent=4, ensure_ascii=False)
    
    print(f"Scanned {len(sound_map)} sounds. Saved to {output_file}")

if __name__ == "__main__":
    scan_sounds()
