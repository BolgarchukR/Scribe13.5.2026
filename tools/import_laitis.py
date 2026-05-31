import json
import os
import sys

def parse_laitis(save_json_path, output_path):
    with open(save_json_path, 'r', encoding='utf-8') as f:
        data = json.load(f)

    macros = []
    
    def process_node(node, current_context=None):
        nonlocal macros
        if not isinstance(node, dict):
            return

        # Check if node has "C" (Children/Categories)
        if "C" in node and isinstance(node["C"], list):
            for child in node["C"]:
                process_node(child, current_context)
                
        # Check if node has "P" (Pages/Profiles)
        if "P" in node and isinstance(node["P"], list):
            for child in node["P"]:
                process_node(child, current_context)

        # Check if node is a direct Command (has "A"ctions and "V"oice triggers)
        if "A" in node and "V" in node:
            voice_triggers = node.get("V", [])
            actions = node.get("A", [])
            
            if not isinstance(actions, list):
                actions = []
                
            macro_actions = []
            
            for index, a in enumerate(actions):
                t = a.get("T")
                p = a.get("P", [])
                
                if t == 10 and len(p) > 0:
                    # Application Filter context
                    current_context = p[0]
                    # We don't map it to an action, we skip or add context
                
                elif t == 2 and len(p) >= 2:
                    k = p[0]
                    act_type = str(p[1])
                    if act_type == '1':
                        macro_actions.append({"type": "key_down", "key": k})
                    elif act_type == '2':
                        macro_actions.append({"type": "key_up", "key": k})
                    elif act_type == '0':
                        if '+' in k:
                            macro_actions.append({"type": "hotkey", "keys": k.split('+')})
                        else:
                            macro_actions.append({"type": "key_press", "key": k})
                    else:
                        # Sometimes without '0', '1', '2' or string hotkey
                        macro_actions.append({"type": "hotkey", "keys": k.split('+')})

                elif t == 0 and len(p) >= 1:
                    path = p[0]
                    args = p[1] if len(p) > 1 else ""
                    macro_actions.append({"type": "run_app", "path": path, "args": args})

                elif t == 7 and len(p) >= 1:
                    # Open URL
                    url = p[0]
                    macro_actions.append({"type": "run_app", "path": url, "args": ""})

                elif t == 9 and len(p) >= 1:
                    # Delay
                    try:
                        ms = int(p[0])
                        macro_actions.append({"type": "delay", "ms": ms})
                    except:
                        pass
                
                elif t == 5 and len(p) >= 1:
                    # Type text
                    macro_actions.append({"type": "type_text", "text": p[0]})
                    
            if macro_actions and voice_triggers:
                # Discard purely voice variables without a trigger
                valid_triggers = [t for t in voice_triggers if isinstance(t, str) and "{" not in t]
                if valid_triggers:
                    macros.append({
                        "trigger": ", ".join(valid_triggers),
                        "actions": macro_actions,
                        "context": current_context
                    })

    # Start recursion from D.B
    if "D" in data and "B" in data["D"]:
        for root_cat in data["D"]["B"]:
            process_node(root_cat)

    print(f"Extracted {len(macros)} valid macros from Laitis.")
    
    # Write to macro_import.json
    out_data = {
        "ru": macros
    }
    with open(output_path, 'w', encoding='utf-8') as f:
        json.dump(out_data, f, ensure_ascii=False, indent=4)
    print(f"Saved into {output_path}")

if __name__ == '__main__':
    if len(sys.argv) < 3:
        print("Usage: python import_laitis.py <path_to_Save.json> <output_macros.json>")
        sys.exit(1)
        
    parse_laitis(sys.argv[1], sys.argv[2])
