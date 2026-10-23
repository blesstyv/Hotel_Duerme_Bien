"use strict";

document.addEventListener(
  "DOMContentLoaded",
  function () {

    const filter =
      document.querySelector(
        "[data-room-view-filter]"
      );

    if (!filter) {
      return;
    }


    const roomCards =
      Array.from(
        document.querySelectorAll(
          "[data-room-card]"
        )
      );


    const emptyMessage =
      document.querySelector(
        "[data-room-view-empty]"
      );


    function applyFilter() {

      const selectedView =
        filter.value;

      let visibleRooms = 0;


      roomCards.forEach(
        function (card) {

          const matches =
            !selectedView
            ||
            card.dataset.vista
            ===
            selectedView;


          const roomCheckbox =
            card.querySelector(
              "[data-room-select]"
            );


          /*
           * Si el usuario cambia el filtro
           * después de seleccionar una habitación
           * incompatible, la desmarcamos.
           *
           * Esto evita que exista una habitación
           * seleccionada pero oculta.
           */

          if (
            !matches
            &&
            roomCheckbox
            &&
            roomCheckbox.checked
          ) {

            roomCheckbox.checked =
              false;


            roomCheckbox.dispatchEvent(
              new Event(
                "change",
                {
                  bubbles: true,
                }
              )
            );
          }


          card.hidden =
            !matches;


          if (matches) {
            visibleRooms += 1;
          }
        }
      );


      if (emptyMessage) {

        emptyMessage.hidden =
          visibleRooms !== 0;
      }
    }


    filter.addEventListener(
      "change",
      applyFilter
    );


    applyFilter();
  }
);