# Modbus Profiler för Reflink

## CSV-format

Varje CSV-fil innehåller registerkartan för en specifik regulator.

### Kolumner:

| Kolumn | Beskrivning | Exempel |
|--------|-------------|---------|
| `controller` | Regulatormodell | AK-PC-781, IR33, IDPlus |
| `param_name` | Internt parameternamn (snake_case) | suction_pressure |
| `description` | Läsbar beskrivning (Svenska) | Sugtryck |
| `register` | Modbus registeradress | 30001, 40001, 10001 |
| `fc` | Function Code (2=coil, 3=holding, 4=input) | 4 |
| `datatype` | Datatyp | int16, uint16, int32, float, bool |
| `scale` | Skalningsfaktor | 0.1 (dela råvärde med 10) |
| `unit` | Enhet | °C, bar, %, K |
| `tag` | Kort tagg för identifiering | SUC_P, ROOM_T |
| `rw` | Läs/skriv | r=readonly, rw=read-write |

### Function Codes (FC):

- **FC 1**: Read Coils (digitala utgångar)
- **FC 2**: Read Discrete Inputs (digitala ingångar) 
- **FC 3**: Read Holding Registers (skrivbara register)
- **FC 4**: Read Input Registers (readonly register)

### Registeradresser:

Adresserna följer Modbus-konventionen:
- **10001-19999**: Discrete Inputs (FC 2)
- **30001-39999**: Input Registers (FC 4) 
- **40001-49999**: Holding Registers (FC 3)

### Datatyper:

- `bool` - Boolean (1 bit/register)
- `int16` - Signed 16-bit (-32768 till 32767)
- `uint16` - Unsigned 16-bit (0 till 65535)
- `int32` - Signed 32-bit (2 register)
- `uint32` - Unsigned 32-bit (2 register)
- `float` - 32-bit float (2 register)

### Skalning:

Råvärdet från Modbus multipliceras med `scale` för att få rätt värde.

**Exempel:** Temperatur = råvärde × 0.1
- Råvärde: 234 → Temperatur: 23.4°C

## Skapa egna profiler

1. Kopiera en befintlig CSV som mall
2. Ändra `controller` till din regulatormodell
3. Fyll i register enligt regulatorns dokumentation
4. Spara filen som `tillverkare_modell.csv`
5. Klicka "Ladda om profiler" i Node-RED

## Filer i denna mapp:

- `danfoss_AK-PC-781.csv` - Danfoss AK-PC 781 kylregulator
- `carel_IR33.csv` - Carel IR33 kylregulator  
- `eliwell_IDPlus.csv` - Eliwell ID Plus regulator
- `generic_refrigeration.csv` - Generisk mall för kylregulatorer

