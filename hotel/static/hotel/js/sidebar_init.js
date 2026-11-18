/*
 * Restaura el estado del menú lateral antes de pintar la página,
 * para evitar el parpadeo al cambiar de pantalla.
 */
(function () {
    "use strict";
    try {
        if (window.localStorage.getItem("hdb_sidebar") === "collapsed") {
            document.documentElement.classList.add("sidebar-collapsed");
        }
    } catch (error) { /* almacenamiento no disponible: se ignora */ }
})();
