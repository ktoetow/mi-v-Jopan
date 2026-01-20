function initYandexMap() {
    var myMap = new ymaps.Map('maps', {
        center: [55.985599, 92.886043], 
        zoom: 12
    });
}

ymaps.ready(initYandexMap);