/*
 * Efectos visuales únicamente.
 * No modifica validaciones, cálculo de costos, selección de pasajeros
 * ni el envío de formularios.
 */
(function () {
    "use strict";

    // Retroalimentación de carga al enviar: solo agrega una clase CSS,
    // sin deshabilitar el botón ni interferir con el envío.
    document.addEventListener("submit", function (event) {
        var form = event.target;
        if (!form || event.defaultPrevented || !form.querySelector) { return; }
        var button = event.submitter || form.querySelector("button[type=submit]");
        if (button && button.classList && !form.hasAttribute("data-confirm")) {
            window.setTimeout(function () { button.classList.add("is-loading"); }, 0);
        }
    }, false);

    // Si el usuario vuelve con "atrás", se retira el indicador.
    window.addEventListener("pageshow", function () {
        var loading = document.querySelectorAll(".btn.is-loading");
        for (var i = 0; i < loading.length; i += 1) { loading[i].classList.remove("is-loading"); }
    });
})();
