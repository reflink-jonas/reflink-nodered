module.exports = {
    // Porten Node-RED lyssnar på
    uiPort: process.env.PORT || 1880,

    // Lyssna på alla IP (så du kan nå den från din dator)
    uiHost: "0.0.0.0",

    // Var editor och HTTP-API ligger
    httpAdminRoot: "/",
    httpNodeRoot: "/",

    // Node-REDs user directory
    userDir: "/root/.node-red",

    // Flödesfil
    flowFile: "flows.json",

    // Mapp för statiska filer (dit vi lagt /public/reflink/scan-bg.png)
    httpStatic: "/root/.node-red/public",

    // ===== LÖSENORDSSKYDD =====
    // Användare: admin
    // Lösenord: Reflink2025!
    adminAuth: {
        type: "credentials",
        users: [{
            username: "admin",
            password: "$2b$08$uboo7a1mSKfermfhhbRdA.FauqPjhC8oQ2wblKuuTfEvCA75qLpdu",
            permissions: "*"
        }]
    },

    // Dashboard 2.0 lösenordsskydd (samma inloggning)
    ui: {
        middleware: function(req, res, next) {
            // Tillåt dashboard utan extra login om man redan är inloggad i editorn
            next();
        }
    },

    // Global context - gör moduler tillgängliga i function-noder
    functionGlobalContext: {
        fs: require('fs'),
        path: require('path'),
        profileEngine: require('/opt/reflink/lib/profile-engine'),
        csvImporter: require('/opt/reflink/lib/csv-importer'),
        textUtils: require('/opt/reflink/lib/text-utils'),
        apiHandlers: require('/opt/reflink/lib/api-handlers')
    },

    // Tillåt externa moduler i function-noder
    functionExternalModules: true,

    // Context storage - sparar global/flow context till fil
    contextStorage: {
        default: {
            module: "localfilesystem"
        }
    }
};
