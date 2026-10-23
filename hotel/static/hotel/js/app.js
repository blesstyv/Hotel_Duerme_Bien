"use strict";

document.addEventListener("DOMContentLoaded", function () {

  const sidebarButton =
    document.querySelector("[data-sidebar-toggle]");

  function closeSidebar() {

    document.body.classList.remove(
      "sidebar-open"
    );

    if (sidebarButton) {
      sidebarButton.setAttribute(
        "aria-expanded",
        "false"
      );
    }
  }


  if (sidebarButton) {

    sidebarButton.addEventListener(
      "click",
      function () {

        const isOpen =
          document.body.classList.toggle(
            "sidebar-open"
          );

        sidebarButton.setAttribute(
          "aria-expanded",
          String(isOpen)
        );
      }
    );
  }


  document
    .querySelectorAll("[data-sidebar-close]")
    .forEach(function (element) {

      element.addEventListener(
        "click",
        closeSidebar
      );
    });


  document.addEventListener(
    "keydown",
    function (event) {

      if (event.key === "Escape") {
        closeSidebar();
      }
    }
  );


  document
    .querySelectorAll("[data-dismiss-alert]")
    .forEach(function (button) {

      button.addEventListener(
        "click",
        function () {

          const alert =
            button.closest(".alert");

          if (alert) {
            alert.remove();
          }
        }
      );
    });


  document
    .querySelectorAll("[data-password-toggle]")
    .forEach(function (button) {

      button.addEventListener(
        "click",
        function () {

          const input =
            button.parentElement.querySelector(
              "[data-password-input]"
            );

          const revealed =
            input.type === "password";

          input.type =
            revealed
              ? "text"
              : "password";

          button.setAttribute(
            "aria-pressed",
            String(revealed)
          );

          button.setAttribute(
            "aria-label",
            revealed
              ? "Ocultar contraseña"
              : "Mostrar contraseña"
          );
        }
      );
    });


  document
    .querySelectorAll("[data-percentage]")
    .forEach(function (chart) {

      const percentage = Math.max(
        0,
        Math.min(
          100,
          Number(
            chart.dataset.percentage.replace(
              ",",
              "."
            )
          ) || 0
        )
      );

      chart.style.setProperty(
        "--percentage",
        String(percentage)
      );
    });


  const dialog =
    document.querySelector(
      "[data-confirm-dialog]"
    );

  let pendingForm = null;
  let pendingButton = null;


  if (dialog) {

    document
      .querySelectorAll("form[data-confirm]")
      .forEach(function (form) {

        form.addEventListener(
          "submit",
          function (event) {

            if (
              typeof dialog.showModal
              !==
              "function"
            ) {

              if (
                !window.confirm(
                  form.dataset.confirm
                )
              ) {
                event.preventDefault();
              }

              return;
            }

            event.preventDefault();

            pendingForm = form;
            pendingButton =
              event.submitter;

            dialog.querySelector(
              "[data-confirm-title]"
            ).textContent =
              form.dataset.confirmTitle
              ||
              "Confirmar operación";

            dialog.querySelector(
              "[data-confirm-message]"
            ).textContent =
              form.dataset.confirm;

            dialog.querySelector(
              "[data-confirm-accept]"
            ).textContent =
              form.dataset.confirmTitle
              ||
              "Confirmar";

            dialog.showModal();

            dialog.querySelector(
              "[data-confirm-cancel]"
            ).focus();
          }
        );
      });


    dialog.querySelector(
      "[data-confirm-cancel]"
    ).addEventListener(
      "click",
      function () {

        dialog.close();

        if (pendingButton) {
          pendingButton.focus();
        }

        pendingForm = null;
      }
    );


    dialog.querySelector(
      "[data-confirm-accept]"
    ).addEventListener(
      "click",
      function () {

        if (pendingForm) {

          const form =
            pendingForm;

          pendingForm = null;

          dialog.close();

          form.submit();
        }
      }
    );


    dialog.addEventListener(
      "cancel",
      function () {
        pendingForm = null;
      }
    );
  }


  /*
   * FORMULARIO DE ASIGNACIÓN
   */

  const assignmentForm =
    document.querySelector(
      "[data-assignment-form]"
    );


  if (!assignmentForm) {
    return;
  }


  const roomCheckboxes =
    Array.from(
      assignmentForm.querySelectorAll(
        "[data-room-select]"
      )
    );


  const roomPanels =
    Array.from(
      assignmentForm.querySelectorAll(
        "[data-room-panel]"
      )
    );


  const responsible =
    assignmentForm.querySelector(
      "[data-responsable]"
    );


  function normalizeSearch(value) {

    return value
      .toLocaleLowerCase("es")
      .normalize("NFD")
      .replace(
        /[\u0300-\u036f]/g,
        ""
      )
      .replace(
        /[.\s]/g,
        ""
      );
  }


  function applyPassengerVisibility(
    panel
  ) {

    const searchInput =
      panel.querySelector(
        "[data-passenger-search]"
      );

    const search =
      normalizeSearch(
        searchInput
          ? searchInput.value
          : ""
      );


    panel
      .querySelectorAll(
        "[data-passenger-row]"
      )
      .forEach(function (row) {

        const taken =
          row.dataset.taken
          ===
          "true";

        const matchesSearch =
          normalizeSearch(
            row.dataset.searchText
          ).includes(search);

        /*
         * Un pasajero seleccionado en otra
         * habitación desaparece de la lista.
         */
        row.hidden =
          taken
          ||
          !matchesSearch;
      });
  }


  function refreshDistribution(
    preserveResponsible
  ) {

    const selectedRooms =
      new Set(
        roomCheckboxes
          .filter(function (input) {
            return input.checked;
          })
          .map(function (input) {
            return input.value;
          })
      );


    const selectedPassengers =
      new Set();


    roomPanels.forEach(
      function (panel) {

        const selected =
          selectedRooms.has(
            panel.dataset.roomPanel
          );

        panel.hidden =
          !selected;


        const checked =
          Array.from(
            panel.querySelectorAll(
              "[data-passenger-select]:checked"
            )
          );


        if (selected) {

          checked.forEach(
            function (input) {

              selectedPassengers.add(
                input.value
              );
            }
          );
        }


        const count =
          selected
            ? checked.length
            : 0;


        const capacity =
          Number(
            panel.dataset.capacity
          );


        const badge =
          panel.querySelector(
            "[data-room-count]"
          );


        badge.textContent =
          count
          +
          " / "
          +
          capacity;


        badge.className =
          "badge "
          +
          (
            count === capacity
              ? "badge-success"
              : count > capacity
                ? "badge-danger"
                : "badge-neutral"
          );


        badge.setAttribute(
          "aria-live",
          "polite"
        );
      }
    );


    /*
     * Evita la duplicidad visual.
     *
     * Si un pasajero ya fue seleccionado
     * en otra habitación:
     *
     * - queda deshabilitado;
     * - desaparece visualmente de la lista.
     */

    roomPanels.forEach(
      function (panel) {

        const selected =
          selectedRooms.has(
            panel.dataset.roomPanel
          );


        panel
          .querySelectorAll(
            "[data-passenger-select]"
          )
          .forEach(function (input) {

            const selectedElsewhere =
              !input.checked
              &&
              selectedPassengers.has(
                input.value
              );


            input.disabled =
              !selected
              ||
              selectedElsewhere;


            const row =
              input.closest(
                "[data-passenger-row]"
              );


            if (row) {

              row.dataset.taken =
                selectedElsewhere
                  ? "true"
                  : "false";
            }
          });


        if (selected) {
          applyPassengerVisibility(
            panel
          );
        }
      }
    );


    if (
      !preserveResponsible
      &&
      responsible.value
      &&
      !selectedPassengers.has(
        responsible.value
      )
    ) {

      responsible.value = "";
    }


    Array.from(
      responsible.options
    ).forEach(
      function (option) {

        if (!option.value) {
          return;
        }

        const available =
          selectedPassengers.has(
            option.value
          )
          ||
          option.selected;

        option.hidden =
          !available;

        option.disabled =
          !available;
      }
    );


    assignmentForm.querySelector(
      "[data-distribution-empty]"
    ).hidden =
      selectedRooms.size > 0;


    assignmentForm.querySelector(
      "[data-selected-rooms]"
    ).textContent =
      String(
        selectedRooms.size
      );


    assignmentForm.querySelector(
      "[data-selected-passengers]"
    ).textContent =
      String(
        selectedPassengers.size
      );
  }


  assignmentForm.addEventListener(
    "change",
    function (event) {

      if (
        !event.target.matches(
          "[data-room-select], "
          +
          "[data-passenger-select], "
          +
          "[data-responsable]"
        )
      ) {
        return;
      }


      refreshDistribution(
        false
      );


      const preview =
        assignmentForm.querySelector(
          "[data-assignment-preview]"
        );


      if (preview) {

        preview.querySelector(
          "[data-preview-recalculate]"
        ).hidden = false;


        preview.querySelector(
          "[data-confirm-assignment]"
        ).disabled = true;


        const readyMessage =
          preview.querySelector(
            ".preview-heading"
          );


        if (readyMessage) {
          readyMessage.hidden = true;
        }
      }
    }
  );


  assignmentForm
    .querySelectorAll(
      "[data-passenger-search]"
    )
    .forEach(function (input) {

      input.addEventListener(
        "input",
        function () {

          const panel =
            input.closest(
              "[data-room-panel]"
            );

          applyPassengerVisibility(
            panel
          );
        }
      );
    });


  refreshDistribution(
    true
  );


  const preview =
    assignmentForm.querySelector(
      "[data-assignment-preview]"
    );


  if (preview) {

    preview.scrollIntoView({
      behavior: "instant",
      block: "start",
    });
  }
});