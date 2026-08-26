# Jaszczur2137

Sterownik oświetlenia w terrarium na bazie zestawu uruchomieniowego ESP32.

# Możliwości

Urządzenie ma na celu sterowanie dwustanowe punktami świetlnymi lub ogrzewaniem w terrarium. Do ustalania reguł sterowania stworzony został prosty interpreter wyrażeń. Każdy z podłączonych czujników kojarzony jest ze zmienną, dostępną podczas tworzenia reguł sterowania.

Konfiguracja urządzenia odbywa się za pośrednictwem interfejsu webowego, przy czym urządzenie może pracować w trybie klienta lub punktu dostępowego Wi-Fi. Urządzenie wspiera bazową autoryzację `HTTP`, przy czym baza danych użytkowników przechowywana jest w pliku `etc/users.json` w postaci `user: sha1(pass)`. Wszystkie zależności są przechowywane lokalnie w katalogu `arch`.

Aplikacja bazuje na definicji wyprowadzeń oraz czujników. Wyprowadzenia definiowane są w pliku `etc/outs.json`, gdzie ustalana jest ich unikatowa nazwa oraz numer wyprowadzenia, a następnie w plikach `outs/nazwa.json` definiowane są ich dodatkowe atrybuty. Sensory definiowane są bezpośrednio w kodzie źródłowym, z uwagi na stosowanie różnego rodzaju interfejsów, przy czym ich dane zapisywane są w plikach `sens/nazwa.json`.

## Sterownik aplikacji

Sterownik aplikacji (`lib/driver.py`) koordynuje odczyt czujników, zapis danych historii na wykresie, logowanie zdarzeń, proces wyznaczania stanu wyjść oraz udostępnia interfejsy umożliwiające sterowanie nim poprzez serwer `HTTP`. Dodatkowo istnieje możliwość tworzenia jednorazowych zdarzeń, które w wybranej chwili ustawią stan wyjścia lub rodzaj sterowania.

## Serwer HTTP

Serwer `HTTP` (`lib/server.py`) umożliwia obsługę jednego klienta w danym czasie, z uwagi na ograniczone zasoby oraz występujące dawniej błędy w implementacji `Micropythona`. Ze względu na długi czas zestawiania połączenia oraz duże ilości wymaganej pamięci `RAM` obsługa `TLS` nie jest używana. Metoda `accept(wait, timeout)` serwera pozwala określić czas oczekiwania (`wait`) na klienta oraz maksymalny czas pojedynczej operacji wymiany danych (`timeout`). Zasoby, których nazwa kończy się na `.gz` są traktowane jako treść skompresowana, gdzie klient jest informowany o kodowaniu zasobu. Typ mime zasobu jest określany automatycznie na podstawie rozszerzenia. Zasoby są wczytywane jedynie z katalogu, który odpowiada typowi zasobu.

Serwer obsługuje dodatkowo:
- zapytania `GET` oraz `POST`,
- autoryzację użytkownika `WWW-Authenticate: Basic`,
- przekazywanie oraz weryfikację `ETag`,
- obsługę `Cache-Control` w zależności od zasobu,
- informacje o kodowaniu (`gzip` lub `identity`).

## Wyświetlacz LCD

Zastosowany w projekcie wyświetlacz (`lib/display.py`) umożliwia wyświetlanie stanu urządzenia, średniej temperatury oraz wilgotności dla predefiniowanych czujników `DHT22`. Można go usunąć lub przerobić na inną formę, w zależności od przeznaczenia urządzenia.

# Zależności

- [K-ESP-CTRL](https://github.com/Kuszki/K-ESP-CTRL) - zapożyczono serwer HTTP (GPL3)
- [Chart.js](https://github.com/chartjs/Chart.js) - biblioteka do tworzenia wykresów w JavaScript (MIT)
- [chartjs-plugin-zoom](https://github.com/chartjs/chartjs-plugin-zoom) - plugin do obsługi powiększania i przesuwania wykresów Chart.js (MIT)
- [CodeMirror](https://github.com/codemirror/dev) - edytor kodu w przeglądarce z obsługą składni i rozszerzeń (MIT)
- [Hammer.js](https://github.com/hammerjs/hammer.js) - biblioteka do obsługi gestów dotykowych i myszy (MIT)
- [jQuery](https://github.com/jquery/jquery) - biblioteka upraszczająca manipulację DOM, obsługę zdarzeń i zapytania AJAX (MIT)
- [Moment.js](https://github.com/moment/moment) - biblioteka do parsowania, formatowania i obsługi dat oraz czasu (MIT)

# Prototyp

Wykonany prototyp urządzenia dla 3 punktów świetlnych oraz 2 czujników `DHT22` zamontowano na terrarium przeznaczonym dla Gekona Lamparciego. Możliwe są inne implementacje oraz wdrożenia.

# Licencja 

Możesz kopiować, modyfikować i rozpowszechniać ten program zgodnie z warunkami licencji GNU GPL v3.0. W przypadku dystrybucji zmodyfikowanych wersji lub rozpowszechniania programu wraz z kodem źródłowym należy zachować postanowienia licencji GPLv3, w szczególności obowiązek udostępnienia kodu źródłowego oraz zachowania informacji o prawach autorskich i licencji.
