#!/usr/bin/env python3
"""
Uppdaterar inject-noder som saknar msg.action/msg.group
"""

import json

def load_flows(filepath):
    with open(filepath, 'r', encoding='utf-8') as f:
        return json.load(f)

def save_flows(filepath, flows):
    with open(filepath, 'w', encoding='utf-8') as f:
        json.dump(flows, f, indent=4, ensure_ascii=False)

def get_action_group_from_name(name):
    """Härled action och group från nodnamn"""
    name_lower = name.lower() if name else ''
    
    mappings = [
        ('fake freq maskin', 'updateMachine', 'Machines'),
        ('maskin', 'showMachines', 'Machines'),
        ('kylar', 'showKylar', 'Kylar'),
        ('frysar', 'showFrysar', 'Frysar'),
        ('controller', 'showControllers', 'Controllers'),
        ('regulator', 'showControllers', 'Controllers'),
        ('larm', 'showAlarms', 'Alarms'),
        ('alarm', 'showAlarms', 'Alarms'),
        ('nod', 'showNodes', 'Nodes'),
        ('node', 'showNodes', 'Nodes'),
        ('lägg till', 'addItem', 'Data'),
        ('visa alla', 'showAll', 'Data'),
        ('refboard', 'updateRefboard', 'Refboard'),
        ('startup', 'initData', 'System'),
    ]
    
    for keyword, action, group in mappings:
        if keyword in name_lower:
            return action, group
    
    return 'processData', 'Data'

def has_action_group(node):
    """Kontrollera om inject-nod redan har action och group"""
    props = node.get('props', [])
    has_action = any(p.get('p') == 'action' for p in props)
    has_group = any(p.get('p') == 'group' for p in props)
    return has_action and has_group

def add_action_group_to_inject(node):
    """Lägg till action och group till inject-nod"""
    if node.get('type') != 'inject':
        return node, False
    
    if has_action_group(node):
        return node, False
    
    name = node.get('name', '')
    action, group = get_action_group_from_name(name)
    
    props = node.get('props', [])
    
    # Kolla om redan finns (partial)
    has_action = any(p.get('p') == 'action' for p in props)
    has_group = any(p.get('p') == 'group' for p in props)
    
    if not has_action:
        props.append({
            "p": "action",
            "v": action,
            "vt": "str"
        })
    
    if not has_group:
        props.append({
            "p": "group",
            "v": group,
            "vt": "str"
        })
    
    node['props'] = props
    return node, True

def process_file(filepath):
    print(f"📂 Bearbetar {filepath}...")
    flows = load_flows(filepath)
    
    modified = 0
    for i, node in enumerate(flows):
        if node.get('type') == 'inject':
            flows[i], was_modified = add_action_group_to_inject(node)
            if was_modified:
                modified += 1
                print(f"  ✏️ {node.get('name', 'unnamed')}: action={node['props'][-2]['v']}, group={node['props'][-1]['v']}")
    
    if modified > 0:
        save_flows(filepath, flows)
        print(f"✅ Sparade {filepath} ({modified} inject-noder uppdaterade)")
    else:
        print(f"  ℹ️ Alla inject-noder har redan action/group")
    
    return modified

def main():
    print("=" * 60)
    print("🔧 UPDATE INJECT NODES")
    print("=" * 60)
    
    files = [
        '/root/.node-red/flows.json',
        '/root/.node-red/flows-settings.json',
        '/root/.node-red/flows-alarms-stats.json'
    ]
    
    total = 0
    for f in files:
        try:
            total += process_file(f)
        except FileNotFoundError:
            print(f"⚠️ {f} hittades inte")
        except Exception as e:
            print(f"❌ Fel: {e}")
    
    print()
    print(f"✅ Totalt {total} inject-noder uppdaterade")

if __name__ == '__main__':
    main()

