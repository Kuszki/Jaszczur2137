# Jaszczur2137

Sterownik oświetlenia w terrarium na bazie zestawu uruchomieniowego ESP32.

# Możliwości

Urządzenie ma na celu sterowanie dwustanowe punktami świetlnymi lub ogrzewaniem w terrarium. Do ustalania reguł sterowania stworzony został prosty interpreter wyrażeń. Każdy z podłączonych czujników kojarzony jest ze zmienną, dostępną podczas tworzenia reguł sterowania.

Konfiguracja urządzenia odbywa się za pośrednictwem interfejsu webowego, przy czym urządzenie może pracować w trybie klienta lub punktu dostępowego Wi-Fi.

Projekt znajduje się we wczesnej fazie rozwoju.

# Zależności

- [K-ESP-CTRL](https://github.com/Kuszki/K-ESP-CTRL) - zapożyczono serwer HTTP (GPL3)
- [Chart.js](https://github.com/chartjs/Chart.js) - biblioteka do tworzenia wykresów w JavaScript (MIT)
- [chartjs-plugin-zoom](https://github.com/chartjs/chartjs-plugin-zoom) - plugin do obsługi powiększania i przesuwania wykresów Chart.js (MIT)
- [CodeMirror](https://github.com/codemirror/dev) - edytor kodu w przeglądarce z obsługą składni i rozszerzeń (MIT)
- [Hammer.js](https://github.com/hammerjs/hammer.js) - biblioteka do obsługi gestów dotykowych i myszy (MIT)
- [jQuery](https://github.com/jquery/jquery) - biblioteka upraszczająca manipulację DOM, obsługę zdarzeń i zapytania AJAX (MIT)
- [Moment.js](https://github.com/moment/moment) - biblioteka do parsowania, formatowania i obsługi dat oraz czasu (MIT)

# Licencja 

Możesz kopiować, modyfikować i rozpowszechniać ten program zgodnie z warunkami licencji GNU GPL v3.0. W przypadku dystrybucji zmodyfikowanych wersji lub rozpowszechniania programu wraz z kodem źródłowym należy zachować postanowienia licencji GPLv3, w szczególności obowiązek udostępnienia kodu źródłowego oraz zachowania informacji o prawach autorskich i licencji.

