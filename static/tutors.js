// Инициализация карты Яндекс на странице репетиторов
function initTutorsMap() {
  if (typeof ymaps === "undefined") return;
  const containerId = "tutorsMap";
  const container = document.getElementById(containerId);
  if (!container) return;

  const center = [56.01528, 92.89325]; // Красноярск, центр

  const map = new ymaps.Map(containerId, {
    center: center,
    zoom: 11,
    controls: ["zoomControl", "fullscreenControl"],
  });

  const placemark = new ymaps.Placemark(
    center,
    {
      balloonContent: "Район офлайн‑занятий TutorBook",
    },
    {
      preset: "islands#redDotIcon",
    }
  );

  map.geoObjects.add(placemark);
}

document.addEventListener("DOMContentLoaded", function () {
  if (typeof ymaps !== "undefined") {
    ymaps.ready(initTutorsMap);
  }
});
