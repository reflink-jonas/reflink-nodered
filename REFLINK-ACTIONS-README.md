# Reflink Message Standard v1.0

## Översikt

Detta dokument beskriver det standardiserade meddelandeformat som används i Reflink OS Node-RED flöden. Syftet är att eliminera `TypeError: Cannot read properties of null` och `"No group configured"` fel genom att garantera att `msg.action` och `msg.group` alltid är satta.

## Obligatoriska fält

| Fält | Typ | Beskrivning | Exempel |
|------|-----|-------------|---------|
| `msg.action` | string | Vad ska hända? | `showControllers`, `refresh`, `navigate` |
| `msg.group` | string | Vilken kategori? | `Controllers`, `Machines`, `Alarms` |

## Safe Header Pattern

**Varje function-nod MÅSTE börja med Safe Header:**

```javascript
// 🛡️ SAFE HEADER - Reflink Message Standard
msg.action = msg.action || 'defaultAction';
msg.group = msg.group || 'DefaultGroup';
```

## Giltiga Actions

### Controllers (Regulatorer)
| Action | Beskrivning |
|--------|-------------|
| `showControllers` | Visa alla regulatorer |
| `showKylar` | Visa endast kylar (setpoint >= 0°C) |
| `showFrysar` | Visa endast frysar (setpoint < 0°C) |
| `setSetpoint` | Ändra börvärde |
| `togglePower` | Slå på/av regulator |

### Machines (Maskiner/Aggregat)
| Action | Beskrivning |
|--------|-------------|
| `showMachines` | Visa alla maskiner |
| `showMachineGauges` | Visa maskin-gauges med frekvens |
| `toggleMachine` | Slå på/av maskin |

### Alarms (Larm)
| Action | Beskrivning |
|--------|-------------|
| `showAlarms` | Visa alla aktiva larm |
| `showAlarmSummary` | Visa sammanfattning |
| `latestAlarms` | Visa senaste 5 larm |
| `acknowledgeAlarm` | Kvittera larm |
| `createAlarms` | Skapa/initiera larm |

### Nodes (Konfiguration)
| Action | Beskrivning |
|--------|-------------|
| `showNodes` | Visa alla konfigurerade noder |
| `addNode` | Lägg till ny nod |
| `updateNode` | Uppdatera befintlig nod |
| `deleteNode` | Ta bort nod |

### System
| Action | Beskrivning |
|--------|-------------|
| `refresh` | Uppdatera data |
| `navigate` | Navigera till sida |
| `exportBackup` | Exportera konfiguration |
| `importBackup` | Importera konfiguration |

## Giltiga Groups

| Group | Beskrivning |
|-------|-------------|
| `Controllers` | Alla regulatorer |
| `Kylar` | Kylregulatorer |
| `Frysar` | Frysregulatorer |
| `Machines` | Maskiner/aggregat |
| `Alarms` | Larmsystem |
| `Nodes` | Nodkonfiguration |
| `System` | Systemfunktioner |
| `Network` | Nätverksfunktioner |

## Exempel

### Inject-nod (UI-button eller timer)

```json
{
  "props": [
    { "p": "action", "v": "showControllers", "vt": "str" },
    { "p": "group", "v": "Controllers", "vt": "str" },
    { "p": "payload", "v": "", "vt": "date" }
  ]
}
```

### Function-nod (Data Processing)

```javascript
// ═══════════════════════════════════════════════════════════════
// CONTROLLERS HANDLER
// ═══════════════════════════════════════════════════════════════

// 🛡️ SAFE HEADER
msg.action = msg.action || 'showControllers';
msg.group = msg.group || 'Controllers';

// Hämta data
const controllers = global.get('reflink.regulators') || [];

// Filtrera baserat på action
let result;
if (msg.action === 'showKylar') {
    result = controllers.filter(c => parseFloat(c.setpoint) >= 0);
    msg.group = 'Kylar';
} else if (msg.action === 'showFrysar') {
    result = controllers.filter(c => parseFloat(c.setpoint) < 0);
    msg.group = 'Frysar';
} else {
    result = controllers;
}

// Bygg response
msg.controllers = result;
msg.payload = result;
msg.count = result.length;

// Status
node.status({ 
    fill: 'green', 
    shape: 'dot', 
    text: `${msg.action}: ${result.length} st` 
});

return msg;
```

### Switch-nod (Action Router)

```
Property: msg.action
Rules:
  1. == showControllers → Output 1
  2. == showKylar → Output 2
  3. == showFrysar → Output 3
  4. == showMachines → Output 4
  5. == showAlarms → Output 5
  6. otherwise → Output 6 (error handler)
```

## Migrationsguide

### Före (Gammal kod)

```javascript
// DÅLIGT - Ingen validering
const data = msg.payload.controllers;
msg.payload = data;
return msg;
```

### Efter (Ny standard)

```javascript
// 🛡️ SAFE HEADER
msg.action = msg.action || 'showControllers';
msg.group = msg.group || 'Controllers';

// BRA - Validering och fallback
const data = (msg.payload && msg.payload.controllers) 
    ? msg.payload.controllers 
    : global.get('reflink.regulators') || [];

msg.controllers = data;
msg.payload = data;
msg.count = data.length;

return msg;
```

## Felsökning

### TypeError: Cannot read properties of null

**Orsak:** `msg.payload` eller annan property är `null`

**Lösning:** Lägg till Safe Header och validera alla inputs:
```javascript
msg.payload = msg.payload || {};
const value = msg.payload.someValue || 'default';
```

### "No group configured"

**Orsak:** `msg.group` saknas när UI-komponenter behöver den

**Lösning:** Sätt alltid `msg.group` i Safe Header eller inject-noden.

## Filstruktur

```
/root/.node-red/
├── flows.json                 # Huvudflöden (Kontrollrum, RefBoard)
├── flows-settings.json        # Settings-flöden
├── flows-alarms-stats.json    # Larm & Statistik
├── refactor-actions.py        # Refaktoreringsscript
└── REFLINK-ACTIONS-README.md  # Detta dokument
```

## Verktyg

### Refaktoreringsscript

Kör för att uppdatera alla flows:
```bash
cd /root/.node-red
python3 refactor-actions.py
```

## Changelog

### v1.0 (2025-12-08)
- Initial release
- Universal Safe Handler
- Action Router pattern
- Best practice examples för Controllers, Machines, Alarms

