#!/usr/bin/env python3
"""
Reflink Actions Refactor Script
================================
Refaktorerar flows.json, flows-settings.json och flows-alarms-stats.json
för att införa konsekvent msg.action / msg.group system.

Skapar:
1. Universal Safe Handler subflow
2. Uppdaterar ui-button noder att sätta msg.action/msg.group
3. Lägger till Action Router switch-nod som best practice
4. Städar befintliga function-noder för konsekvent syntax

Av: Claude Opus 4.5 för Reflink OS
"""

import json
import copy
import uuid
from datetime import datetime

def generate_id():
    """Genererar ett unikt Node-RED ID"""
    return uuid.uuid4().hex[:16]

def load_flows(filepath):
    """Laddar flows från JSON-fil"""
    with open(filepath, 'r', encoding='utf-8') as f:
        return json.load(f)

def save_flows(filepath, flows):
    """Sparar flows till JSON-fil"""
    with open(filepath, 'w', encoding='utf-8') as f:
        json.dump(flows, f, indent=4, ensure_ascii=False)

# ============================================================================
# UNIVERSAL SAFE HANDLER - Function Node Template
# ============================================================================

SAFE_HANDLER_FUNC = '''// ═══════════════════════════════════════════════════════════════════════════
// UNIVERSAL SAFE HANDLER - Reflink Message Standard v1.0
// ═══════════════════════════════════════════════════════════════════════════
// Garanterar att msg.action och msg.group alltid är satta
// Skyddar mot null/undefined och TypeError

// 🛡️ VALIDATE INCOMING MESSAGE
msg = msg || {};

// 🎯 ACTION - Vad ska hända? (required)
// Giltiga värden: showControllers, showMachines, showAlarms, showNodes,
//                 showKylar, showFrysar, refresh, navigate, update, delete
if (!msg.action || typeof msg.action !== 'string') {
    // Försök härled från topic eller payload
    if (msg.topic && typeof msg.topic === 'string') {
        msg.action = msg.topic;
    } else if (msg.payload && typeof msg.payload === 'object' && msg.payload.action) {
        msg.action = msg.payload.action;
    } else {
        msg.action = 'unknown';
        node.warn('⚠️ msg.action saknas - satt till "unknown"');
    }
}

// 📦 GROUP - Vilken kategori? (required)
// Giltiga värden: Controllers, Kylar, Frysar, Machines, Alarms, Nodes, System
if (!msg.group || typeof msg.group !== 'string') {
    // Försök härled från action eller topic
    const actionToGroup = {
        'showControllers': 'Controllers',
        'showKylar': 'Kylar',
        'showFrysar': 'Frysar',
        'showMachines': 'Machines',
        'showAlarms': 'Alarms',
        'showNodes': 'Nodes',
        'showMachineGauges': 'Machines',
        'alarmSummary': 'Alarms',
        'latestAlarms': 'Alarms',
        'createAlarms': 'Alarms',
        'refresh': 'System',
        'navigate': 'System'
    };
    
    msg.group = actionToGroup[msg.action] || 'Unknown';
    
    if (msg.group === 'Unknown') {
        node.warn('⚠️ msg.group kunde inte härledas - satt till "Unknown"');
    }
}

// 📊 METADATA - Lägg till timestamp och source om saknas
msg._meta = msg._meta || {};
msg._meta.timestamp = msg._meta.timestamp || new Date().toISOString();
msg._meta.handler = 'UniversalSafeHandler';
msg._meta.version = '1.0';

// 🔒 SANITIZE payload - Garantera att payload existerar
if (msg.payload === null || msg.payload === undefined) {
    msg.payload = {};
}

// Status för debugging
node.status({ 
    fill: 'green', 
    shape: 'dot', 
    text: `${msg.action} → ${msg.group}` 
});

return msg;'''

# ============================================================================
# ACTION ROUTER - Switch Node för routing baserat på msg.action
# ============================================================================

ACTION_ROUTER_CONFIG = {
    "rules": [
        {"t": "eq", "v": "showControllers", "vt": "str"},
        {"t": "eq", "v": "showKylar", "vt": "str"},
        {"t": "eq", "v": "showFrysar", "vt": "str"},
        {"t": "eq", "v": "showMachines", "vt": "str"},
        {"t": "eq", "v": "showAlarms", "vt": "str"},
        {"t": "eq", "v": "showNodes", "vt": "str"},
        {"t": "eq", "v": "refresh", "vt": "str"},
        {"t": "eq", "v": "navigate", "vt": "str"},
        {"t": "else"}  # Fallback
    ]
}

# ============================================================================
# BEST PRACTICE EXAMPLES
# ============================================================================

BEST_PRACTICE_CONTROLLERS = '''// ═══════════════════════════════════════════════════════════════════════════
// BEST PRACTICE: Controllers Handler
// ═══════════════════════════════════════════════════════════════════════════
// Visar hur man använder msg.action/msg.group konsekvent

// 🛡️ SAFE HEADER - Alltid först i varje function-nod
msg.action = msg.action || 'showControllers';
msg.group = msg.group || 'Controllers';

// 📦 Hämta data från global context (med fallback)
const controllers = global.get('reflink.regulators') || [];

// 🔄 Filtrera baserat på action
let result = [];
switch (msg.action) {
    case 'showKylar':
        result = controllers.filter(c => {
            const sp = parseFloat((c.setpoint || '0').toString().replace(/[^0-9.-]/g, ''));
            return !isNaN(sp) && sp >= 0;
        });
        msg.group = 'Kylar';
        break;
        
    case 'showFrysar':
        result = controllers.filter(c => {
            const sp = parseFloat((c.setpoint || '0').toString().replace(/[^0-9.-]/g, ''));
            return !isNaN(sp) && sp < 0;
        });
        msg.group = 'Frysar';
        break;
        
    case 'showControllers':
    default:
        result = controllers;
        break;
}

// 📊 Bygg response
msg.controllers = result;
msg.payload = result;
msg.count = result.length;

// 📈 Status för debugging
node.status({ 
    fill: result.length > 0 ? 'green' : 'yellow', 
    shape: 'dot', 
    text: `${msg.action}: ${result.length} st` 
});

return msg;'''

BEST_PRACTICE_MACHINES = '''// ═══════════════════════════════════════════════════════════════════════════
// BEST PRACTICE: Machines Handler
// ═══════════════════════════════════════════════════════════════════════════

// 🛡️ SAFE HEADER
msg.action = msg.action || 'showMachines';
msg.group = msg.group || 'Machines';

// 📦 Hämta data
const maxHz = 70;
const machines = (global.get('reflink.machines') || []).map(m => ({
    ...m,
    freqHz: ((m.capacityPercent || 0) / 100 * maxHz).toFixed(1) + ' Hz',
    status: m.capacityPercent > 80 ? 'high' : (m.capacityPercent > 50 ? 'normal' : 'low')
}));

// 📊 Bygg response med konsekvent struktur
msg.machines = machines;
msg.payload = machines;
msg.count = machines.length;

// 📈 Status
node.status({ 
    fill: 'green', 
    shape: 'dot', 
    text: `${machines.length} maskiner` 
});

return msg;'''

BEST_PRACTICE_ALARMS = '''// ═══════════════════════════════════════════════════════════════════════════
// BEST PRACTICE: Alarms Handler
// ═══════════════════════════════════════════════════════════════════════════

// 🛡️ SAFE HEADER
msg.action = msg.action || 'showAlarms';
msg.group = msg.group || 'Alarms';

// 📦 Hämta larm från global context
const reflink = global.get('reflink') || {};
const alarms = reflink.alarms || { 
    active: [], 
    summary: { total: 0, critical: 0, warning: 0, info: 0 },
    history: []
};

// 🔄 Hantera olika actions
let result;
switch (msg.action) {
    case 'showAlarmSummary':
    case 'alarmSummary':
        const s = alarms.summary;
        result = s.total === 0 
            ? '✅ Inga aktiva larm'
            : `⚠️ ${s.total} larm • ${s.critical} kritiska • ${s.warning} varningar`;
        msg.payload = result;
        break;
        
    case 'latestAlarms':
        const sorted = [...alarms.active].sort((a, b) => 
            new Date(b.timestamp) - new Date(a.timestamp)
        );
        result = sorted.slice(0, 5);
        msg.payload = result;
        break;
        
    case 'showAlarms':
    default:
        result = alarms.active;
        msg.payload = result;
        break;
}

msg.alarms = alarms.active;
msg.alarmsSummary = alarms.summary;
msg.count = alarms.active.length;

// 📈 Status baserad på allvarlighetsgrad
const fill = alarms.summary.critical > 0 ? 'red' : 
             (alarms.summary.warning > 0 ? 'yellow' : 'green');
node.status({ fill, shape: 'dot', text: `${alarms.active.length} larm` });

return msg;'''

def create_universal_safe_handler_node(flow_id, x=100, y=100):
    """Skapar Universal Safe Handler function-nod"""
    return {
        "id": f"safe-handler-{generate_id()[:8]}",
        "type": "function",
        "z": flow_id,
        "name": "🛡️ Universal Safe Handler",
        "func": SAFE_HANDLER_FUNC,
        "outputs": 1,
        "timeout": 0,
        "noerr": 0,
        "initialize": "",
        "finalize": "",
        "libs": [],
        "x": x,
        "y": y,
        "wires": [[]]
    }

def create_action_router_node(flow_id, x=300, y=100):
    """Skapar Action Router switch-nod"""
    return {
        "id": f"action-router-{generate_id()[:8]}",
        "type": "switch",
        "z": flow_id,
        "name": "🔀 Action Router",
        "property": "action",
        "propertyType": "msg",
        "rules": ACTION_ROUTER_CONFIG["rules"],
        "checkall": "true",
        "repair": False,
        "outputs": len(ACTION_ROUTER_CONFIG["rules"]),
        "x": x,
        "y": y,
        "wires": [[] for _ in ACTION_ROUTER_CONFIG["rules"]]
    }

def create_best_practice_example_nodes(flow_id, start_x=100, start_y=300):
    """Skapar best practice example function-noder"""
    nodes = []
    
    # Controllers example
    nodes.append({
        "id": f"bp-controllers-{generate_id()[:8]}",
        "type": "function",
        "z": flow_id,
        "name": "📘 Best Practice: Controllers",
        "func": BEST_PRACTICE_CONTROLLERS,
        "outputs": 1,
        "timeout": 0,
        "noerr": 0,
        "initialize": "",
        "finalize": "",
        "libs": [],
        "x": start_x,
        "y": start_y,
        "wires": [[]]
    })
    
    # Machines example
    nodes.append({
        "id": f"bp-machines-{generate_id()[:8]}",
        "type": "function",
        "z": flow_id,
        "name": "📘 Best Practice: Machines",
        "func": BEST_PRACTICE_MACHINES,
        "outputs": 1,
        "timeout": 0,
        "noerr": 0,
        "initialize": "",
        "finalize": "",
        "libs": [],
        "x": start_x,
        "y": start_y + 80,
        "wires": [[]]
    })
    
    # Alarms example
    nodes.append({
        "id": f"bp-alarms-{generate_id()[:8]}",
        "type": "function",
        "z": flow_id,
        "name": "📘 Best Practice: Alarms",
        "func": BEST_PRACTICE_ALARMS,
        "outputs": 1,
        "timeout": 0,
        "noerr": 0,
        "initialize": "",
        "finalize": "",
        "libs": [],
        "x": start_x,
        "y": start_y + 160,
        "wires": [[]]
    })
    
    return nodes

def update_ui_button_for_actions(node):
    """Uppdaterar ui-button noder att använda msg.action/msg.group"""
    if node.get('type') != 'ui-button':
        return node
    
    # Mappa button labels till action/group
    label = node.get('label', '').lower()
    name = node.get('name', '').lower()
    
    action_map = {
        'kylar': ('showKylar', 'Kylar'),
        'frysar': ('showFrysar', 'Frysar'),
        'controllers': ('showControllers', 'Controllers'),
        'maskiner': ('showMachines', 'Machines'),
        'machines': ('showMachines', 'Machines'),
        'larm': ('showAlarms', 'Alarms'),
        'alarms': ('showAlarms', 'Alarms'),
        'refresh': ('refresh', 'System'),
        'uppdatera': ('refresh', 'System'),
        'serviceläge': ('toggleService', 'Service'),
        'snabbdiagnos': ('runDiagnostics', 'System'),
        'ping': ('pingTest', 'Network'),
        'port': ('portTest', 'Network'),
        'modbus': ('modbusTest', 'Modbus'),
        'börvärde': ('setSetpoint', 'Controllers'),
        'on/off': ('togglePower', 'Controllers'),
        'export': ('exportBackup', 'System'),
        'backup': ('exportBackup', 'System')
    }
    
    # Hitta matchande action
    action, group = 'unknown', 'Unknown'
    for key, (act, grp) in action_map.items():
        if key in label or key in name:
            action, group = act, grp
            break
    
    # Lägg till/uppdatera topic för enkel routing
    if 'topic' not in node or not node['topic']:
        node['topic'] = action
    
    return node

def add_safe_header_to_function(node):
    """Lägger till Safe Header om den saknas i function-noder"""
    if node.get('type') != 'function':
        return node
    
    func = node.get('func', '')
    
    # Kolla om redan har safe header
    if '🛡️ SAFE HEADER' in func or 'SAFE HEADER' in func:
        return node  # Redan uppdaterad
    
    # Försök identifiera lämplig action/group från nodnamn
    name = node.get('name', '').lower()
    
    action_map = {
        'kylar': ('showKylar', 'Kylar'),
        'frysar': ('showFrysar', 'Frysar'),
        'controller': ('showControllers', 'Controllers'),
        'maskin': ('showMachines', 'Machines'),
        'machine': ('showMachines', 'Machines'),
        'larm': ('showAlarms', 'Alarms'),
        'alarm': ('showAlarms', 'Alarms'),
        'nod': ('showNodes', 'Nodes'),
        'node': ('showNodes', 'Nodes'),
        'gauge': ('showMachineGauges', 'Machines'),
        'layout': ('showLayout', 'Layout'),
        'summary': ('showSummary', 'Summary'),
        'hämta': ('getData', 'Data'),
        'get': ('getData', 'Data'),
        'lägg till': ('addItem', 'Data'),
        'add': ('addItem', 'Data')
    }
    
    action, group = 'processData', 'Data'
    for key, (act, grp) in action_map.items():
        if key in name:
            action, group = act, grp
            break
    
    # Lägg till Safe Header i början av funktionen
    safe_header = f'''// 🛡️ SAFE HEADER - Reflink Message Standard
msg.action = msg.action || '{action}';
msg.group = msg.group || '{group}';

'''
    
    # Kolla om funktionen börjar med kommentar
    if func.strip().startswith('//'):
        # Hitta slutet av första kommentarsblocket
        lines = func.split('\n')
        insert_idx = 0
        for i, line in enumerate(lines):
            if line.strip() and not line.strip().startswith('//'):
                insert_idx = i
                break
            if line.strip().startswith('// ═'):
                # Är ett separator-block, fortsätt efter det
                continue
        
        lines.insert(insert_idx, safe_header)
        node['func'] = '\n'.join(lines)
    else:
        node['func'] = safe_header + func
    
    return node

def create_reflink_standards_comment_node(flow_id, x=100, y=50):
    """Skapar en comment-nod med dokumentation för Reflink Message Standard"""
    return {
        "id": f"reflink-std-doc-{generate_id()[:8]}",
        "type": "comment",
        "z": flow_id,
        "name": "📚 REFLINK MESSAGE STANDARD v1.0",
        "info": """# Reflink Message Standard v1.0

## Obligatoriska fält

| Fält | Typ | Beskrivning |
|------|-----|-------------|
| `msg.action` | string | Vad ska hända? t.ex. `showControllers`, `refresh` |
| `msg.group` | string | Vilken kategori? t.ex. `Controllers`, `Alarms` |

## Giltiga actions

### Controllers
- `showControllers` - Visa alla regulatorer
- `showKylar` - Visa endast kylar (setpoint >= 0)
- `showFrysar` - Visa endast frysar (setpoint < 0)
- `setSetpoint` - Ändra börvärde
- `togglePower` - Slå på/av

### Machines
- `showMachines` - Visa alla maskiner
- `showMachineGauges` - Visa maskin-gauges

### Alarms
- `showAlarms` - Visa aktiva larm
- `showAlarmSummary` - Visa larmsammanfattning
- `latestAlarms` - Visa senaste larm
- `acknowledgeAlarm` - Kvittera larm

### System
- `refresh` - Uppdatera data
- `navigate` - Navigera till sida
- `exportBackup` - Exportera backup

## Exempel

```javascript
// I inject-nod:
msg.action = 'showControllers';
msg.group = 'Controllers';

// I function-nod (Safe Header):
msg.action = msg.action || 'showControllers';
msg.group = msg.group || 'Controllers';
```

## Best Practices

1. **Alltid Safe Header** - Första raderna i varje function-nod
2. **Explicit action/group** - Sätt alltid båda, även om du tror de är satta
3. **Fallback-värden** - Använd `||` för säkra defaults
4. **Status-uppdatering** - Visa action och group i node.status()
""",
        "x": x,
        "y": y,
        "wires": []
    }

def create_examples_flow():
    """Skapar ett helt nytt flow med best practice exempel"""
    flow_id = "reflink-examples-flow"
    
    nodes = [
        # Flow tab
        {
            "id": flow_id,
            "type": "tab",
            "label": "📘 Reflink Examples",
            "disabled": False,
            "info": "Best practice exempel för Reflink Message Standard v1.0"
        },
        
        # Documentation
        create_reflink_standards_comment_node(flow_id, 100, 50),
        
        # Universal Safe Handler
        create_universal_safe_handler_node(flow_id, 100, 150),
        
        # Action Router
        create_action_router_node(flow_id, 350, 150),
        
        # Best Practice Examples
        *create_best_practice_example_nodes(flow_id, 100, 300),
        
        # Example inject nodes
        {
            "id": f"inject-controllers-{generate_id()[:8]}",
            "type": "inject",
            "z": flow_id,
            "name": "Show Controllers",
            "props": [
                {"p": "action", "v": "showControllers", "vt": "str"},
                {"p": "group", "v": "Controllers", "vt": "str"},
                {"p": "payload", "v": "", "vt": "date"}
            ],
            "repeat": "",
            "crontab": "",
            "once": False,
            "onceDelay": 0.1,
            "topic": "",
            "x": 130,
            "y": 500,
            "wires": [[]]
        },
        {
            "id": f"inject-machines-{generate_id()[:8]}",
            "type": "inject",
            "z": flow_id,
            "name": "Show Machines",
            "props": [
                {"p": "action", "v": "showMachines", "vt": "str"},
                {"p": "group", "v": "Machines", "vt": "str"},
                {"p": "payload", "v": "", "vt": "date"}
            ],
            "repeat": "",
            "crontab": "",
            "once": False,
            "onceDelay": 0.1,
            "topic": "",
            "x": 130,
            "y": 550,
            "wires": [[]]
        },
        {
            "id": f"inject-alarms-{generate_id()[:8]}",
            "type": "inject",
            "z": flow_id,
            "name": "Show Alarms",
            "props": [
                {"p": "action", "v": "showAlarms", "vt": "str"},
                {"p": "group", "v": "Alarms", "vt": "str"},
                {"p": "payload", "v": "", "vt": "date"}
            ],
            "repeat": "",
            "crontab": "",
            "once": False,
            "onceDelay": 0.1,
            "topic": "",
            "x": 130,
            "y": 600,
            "wires": [[]]
        }
    ]
    
    return nodes

def refactor_flows(filepath):
    """Huvudfunktion som refaktorerar alla flows i en fil"""
    print(f"📂 Laddar {filepath}...")
    flows = load_flows(filepath)
    
    modified_count = 0
    
    for i, node in enumerate(flows):
        original = copy.deepcopy(node)
        
        # Uppdatera ui-button noder
        if node.get('type') == 'ui-button':
            flows[i] = update_ui_button_for_actions(node)
            if flows[i] != original:
                modified_count += 1
                print(f"  ✏️ Uppdaterade ui-button: {node.get('name', node.get('label', 'unnamed'))}")
        
        # Lägg till Safe Header i function-noder
        elif node.get('type') == 'function':
            flows[i] = add_safe_header_to_function(node)
            if flows[i] != original:
                modified_count += 1
                print(f"  ✏️ Lade till Safe Header: {node.get('name', 'unnamed')}")
    
    # Lägg till examples flow om det inte redan finns
    has_examples = any(n.get('id') == 'reflink-examples-flow' for n in flows)
    if not has_examples:
        examples = create_examples_flow()
        flows.extend(examples)
        print(f"  ➕ Lade till Reflink Examples flow med {len(examples)} noder")
    
    # Spara
    save_flows(filepath, flows)
    print(f"✅ Sparade {filepath} ({modified_count} noder modifierade)")
    
    return modified_count

def main():
    print("=" * 70)
    print("🔧 REFLINK ACTIONS REFACTOR")
    print("   Inför konsekvent msg.action / msg.group system")
    print("=" * 70)
    print()
    
    files = [
        '/root/.node-red/flows.json',
        '/root/.node-red/flows-settings.json',
        '/root/.node-red/flows-alarms-stats.json'
    ]
    
    total_modified = 0
    
    for filepath in files:
        try:
            count = refactor_flows(filepath)
            total_modified += count
        except FileNotFoundError:
            print(f"⚠️ Kunde inte hitta {filepath}, hoppar över...")
        except Exception as e:
            print(f"❌ Fel vid bearbetning av {filepath}: {e}")
    
    print()
    print("=" * 70)
    print(f"✅ KLAR! Totalt {total_modified} noder modifierade")
    print()
    print("📋 Nästa steg:")
    print("   1. Granska ändringarna i Node-RED editorn")
    print("   2. Testa flödena")
    print("   3. Commit och push till GitHub:")
    print("      git add .")
    print('      git commit -m "refactor: Inför konsekvent msg.action/msg.group system"')
    print("      git push origin opus-actions-refactor")
    print("=" * 70)

if __name__ == '__main__':
    main()

