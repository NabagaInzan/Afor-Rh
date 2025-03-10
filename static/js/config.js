// Configuration de l'application
const config = {
    // L'URL de base de l'API sera différente en production et en développement
    apiBaseUrl: window.location.hostname === 'localhost' || window.location.hostname === '127.0.0.1'
        ? '' // En développement local, utiliser des chemins relatifs
        : window.location.origin // En production, utiliser l'URL complète
};
