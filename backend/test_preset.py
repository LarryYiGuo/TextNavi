#!/usr/bin/env python3
import os
import json

# Set up the environment
DATA_DIR = os.path.join(os.path.dirname(__file__), "data")

# Preset output mapping
PRESET_OUTPUTS = {
    "ft_SCENE_A_MS": "Sense_A_Finetuned.fixed.jsonl",
    "ft_SCENE_B_STUDIO": "Sense_B_Finetuned.fixed.jsonl", 
    "base_SCENE_A_MS": "Sence_A_4o.fixed.jsonl",
    "base_SCENE_B_STUDIO": "Sense_B_4o.fixed.jsonl"
}

def get_preset_output(provider: str, site_id: str) -> str:
    """Get preset output based on provider and site_id combination"""
    key = f"{provider.lower()}_{site_id}"
    filename = PRESET_OUTPUTS.get(key)
    print(f"🔍 Looking for preset output: key={key}, filename={filename}")
    
    if not filename:
        print(f"⚠️ No filename found for key: {key}")
        return "Welcome! Please take a photo to start exploring."
    
    filepath = os.path.join(DATA_DIR, filename)
    print(f"📁 Full filepath: {filepath}")
    
    try:
        with open(filepath, 'r', encoding='utf-8') as f:
            # Read first line (JSONL format)
            first_line = f.readline().strip()
            print(f"📖 First line: {first_line[:100]}...")
            
            if first_line:
                data = json.loads(first_line)
                output = data.get("output", "Welcome! Please take a photo to start exploring.")
                print(f"✅ Found output: {output[:100]}...")
                return output
            else:
                print("⚠️ Empty first line")
                return "Welcome! Please take a photo to start exploring."
    except Exception as e:
        print(f"⚠️ Failed to load preset output from {filename}: {e}")
        return "Welcome! Please take a photo to start exploring."

# Test the function
if __name__ == "__main__":
    print("🧪 Testing get_preset_output function...")
    print()
    
    # Test case 1: ft + SCENE_A_MS
    print("Test 1: ft + SCENE_A_MS")
    result1 = get_preset_output("ft", "SCENE_A_MS")
    print(f"Result: {result1[:100]}...")
    print()
    
    # Test case 2: base + SCENE_B_STUDIO
    print("Test 2: base + SCENE_B_STUDIO")
    result2 = get_preset_output("base", "SCENE_B_STUDIO")
    print(f"Result: {result2[:100]}...")
    print()
    
    # Test case 3: invalid combination
    print("Test 3: invalid combination")
    result3 = get_preset_output("invalid", "INVALID")
    print(f"Result: {result3}")
    print()
    
    print("✅ Test completed!")
