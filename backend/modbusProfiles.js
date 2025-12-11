/**
 * Reflink OS - Modbus Profile Engine
 * OPUS CHANGE: Skapad 2025-12-11 - Hanterar CSV-profiler för Modbus-regulatorer
 * 
 * Läser CSV-filer från /modbus-profiles/ och konverterar till JavaScript-objekt
 * som kan användas för auto-mapping av Modbus-register.
 */

const fs = require('fs').promises;
const path = require('path');

// Sökväg till profil-mappen
const PROFILES_DIR = path.join(__dirname, '..', 'modbus-profiles');

/**
 * Parsar en CSV-rad till ett objekt
 * @param {string} line - CSV-rad
 * @param {string[]} headers - Kolumnnamn
 * @returns {Object} Parsad rad som objekt
 */
function parseCSVLine(line, headers) {
    const values = [];
    let current = '';
    let inQuotes = false;
    
    for (let char of line) {
        if (char === '"') {
            inQuotes = !inQuotes;
        } else if (char === ',' && !inQuotes) {
            values.push(current.trim());
            current = '';
        } else {
            current += char;
        }
    }
    values.push(current.trim());
    
    const obj = {};
    headers.forEach((header, i) => {
        obj[header] = values[i] || '';
    });
    
    return obj;
}

/**
 * Konverterar rå CSV-data till typade värden
 * @param {Object} row - Rå CSV-rad
 * @returns {Object} Typad parameter
 */
function convertTypes(row) {
    return {
        controller: row.controller || '',
        param_name: row.param_name || '',
        description: row.description || '',
        register: parseInt(row.register) || 0,
        fc: parseInt(row.fc) || 4,
        datatype: row.datatype || 'int16',
        scale: parseFloat(row.scale) || 1,
        unit: row.unit || '',
        tag: row.tag || '',
        rw: row.rw || 'r',
        // Beräknade fält
        isWritable: (row.rw || 'r').toLowerCase().includes('w'),
        isBoolean: (row.datatype || '').toLowerCase() === 'bool',
        registerType: getRegisterType(parseInt(row.fc) || 4)
    };
}

/**
 * Returnerar registertyp baserat på function code
 * @param {number} fc - Function code
 * @returns {string} Registertyp
 */
function getRegisterType(fc) {
    switch (fc) {
        case 1: return 'coil';
        case 2: return 'discrete_input';
        case 3: return 'holding_register';
        case 4: return 'input_register';
        default: return 'unknown';
    }
}

/**
 * Läser en enskild CSV-fil och returnerar profildata
 * @param {string} filePath - Sökväg till CSV-fil
 * @returns {Promise<Object>} Profildata
 */
async function readProfileCSV(filePath) {
    try {
        const content = await fs.readFile(filePath, 'utf8');
        const lines = content.split('\n').filter(line => line.trim());
        
        if (lines.length < 2) {
            throw new Error('CSV-filen måste ha minst header + 1 rad');
        }
        
        const headers = lines[0].split(',').map(h => h.trim());
        const parameters = [];
        
        for (let i = 1; i < lines.length; i++) {
            const raw = parseCSVLine(lines[i], headers);
            const param = convertTypes(raw);
            if (param.param_name && param.register > 0) {
                parameters.push(param);
            }
        }
        
        // Extrahera controller-namn från första parametern
        const controllerName = parameters.length > 0 ? parameters[0].controller : 'UNKNOWN';
        
        return {
            controller: controllerName,
            fileName: path.basename(filePath),
            filePath: filePath,
            parameterCount: parameters.length,
            parameters: parameters,
            // Gruppera parametrar efter typ
            byType: {
                temperatures: parameters.filter(p => p.unit === '°C' || p.unit === 'K'),
                pressures: parameters.filter(p => p.unit === 'bar' || p.unit === 'psi'),
                booleans: parameters.filter(p => p.isBoolean),
                setpoints: parameters.filter(p => p.isWritable && !p.isBoolean),
                readonly: parameters.filter(p => !p.isWritable && !p.isBoolean)
            },
            // Lookup-tabeller för snabb åtkomst
            byTag: Object.fromEntries(parameters.map(p => [p.tag, p])),
            byRegister: Object.fromEntries(parameters.map(p => [p.register, p])),
            byParamName: Object.fromEntries(parameters.map(p => [p.param_name, p])),
            loadedAt: new Date().toISOString()
        };
    } catch (error) {
        console.error(`Fel vid läsning av ${filePath}:`, error.message);
        throw error;
    }
}

/**
 * Läser alla CSV-profiler från profil-mappen
 * @returns {Promise<Object>} Alla profiler indexerade på controller-namn
 */
async function loadAllProfiles() {
    const profiles = {};
    const errors = [];
    
    try {
        // Kontrollera att mappen finns
        await fs.access(PROFILES_DIR);
    } catch {
        // Skapa mappen om den inte finns
        await fs.mkdir(PROFILES_DIR, { recursive: true });
        console.log('OPUS: Skapade modbus-profiles mapp');
        return { profiles: {}, errors: [], count: 0 };
    }
    
    try {
        const files = await fs.readdir(PROFILES_DIR);
        const csvFiles = files.filter(f => f.toLowerCase().endsWith('.csv'));
        
        console.log(`OPUS: Hittade ${csvFiles.length} CSV-profiler`);
        
        for (const file of csvFiles) {
            const filePath = path.join(PROFILES_DIR, file);
            try {
                const profile = await readProfileCSV(filePath);
                profiles[profile.controller] = profile;
                console.log(`OPUS: Laddade profil ${profile.controller} (${profile.parameterCount} parametrar)`);
            } catch (error) {
                errors.push({
                    file: file,
                    error: error.message
                });
                console.error(`OPUS: Kunde inte ladda ${file}: ${error.message}`);
            }
        }
        
        return {
            profiles: profiles,
            errors: errors,
            count: Object.keys(profiles).length,
            loadedAt: new Date().toISOString()
        };
    } catch (error) {
        console.error('OPUS: Fel vid läsning av profil-mappen:', error.message);
        throw error;
    }
}

/**
 * Listar alla tillgängliga profil-filer
 * @returns {Promise<string[]>} Lista med filnamn
 */
async function listProfileFiles() {
    try {
        const files = await fs.readdir(PROFILES_DIR);
        return files.filter(f => f.toLowerCase().endsWith('.csv'));
    } catch {
        return [];
    }
}

/**
 * Hämtar en specifik profil
 * @param {string} controllerName - Controller-namn (t.ex. "AK-PC-781")
 * @param {Object} allProfiles - Alla laddade profiler
 * @returns {Object|null} Profilen eller null
 */
function getProfile(controllerName, allProfiles) {
    return allProfiles[controllerName] || null;
}

/**
 * Söker efter en parameter i en profil
 * @param {Object} profile - Profilobjekt
 * @param {string} searchTerm - Sökterm (tag, param_name eller register)
 * @returns {Object|null} Hittad parameter eller null
 */
function findParameter(profile, searchTerm) {
    if (!profile) return null;
    
    // Sök på tag
    if (profile.byTag[searchTerm]) {
        return profile.byTag[searchTerm];
    }
    
    // Sök på param_name
    if (profile.byParamName[searchTerm]) {
        return profile.byParamName[searchTerm];
    }
    
    // Sök på register
    const regNum = parseInt(searchTerm);
    if (!isNaN(regNum) && profile.byRegister[regNum]) {
        return profile.byRegister[regNum];
    }
    
    return null;
}

/**
 * Genererar Modbus-read konfiguration för node-red-contrib-modbus
 * @param {Object} param - Parameter från profil
 * @param {number} unitId - Modbus unit ID
 * @returns {Object} Konfiguration för modbus-read nod
 */
function generateModbusReadConfig(param, unitId = 1) {
    // Konvertera register-adress till 0-baserad
    let address = param.register;
    if (address >= 40001) address -= 40001;
    else if (address >= 30001) address -= 30001;
    else if (address >= 10001) address -= 10001;
    
    // Bestäm quantity baserat på datatyp
    let quantity = 1;
    if (['int32', 'uint32', 'float'].includes(param.datatype)) {
        quantity = 2;
    }
    
    return {
        name: param.description || param.param_name,
        unitId: unitId,
        fc: param.fc,
        address: address,
        quantity: quantity,
        // Extra metadata för processing
        _param: param.param_name,
        _tag: param.tag,
        _scale: param.scale,
        _unit: param.unit,
        _datatype: param.datatype
    };
}

// Exportera funktioner
module.exports = {
    loadAllProfiles,
    readProfileCSV,
    listProfileFiles,
    getProfile,
    findParameter,
    generateModbusReadConfig,
    PROFILES_DIR
};

