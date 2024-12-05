from app import create_app

app = create_app()

"""
TO DO:
- przypisywanie druzyn do turnieju(sprawdzenie czy druzyna istnieje, czy nie gra juz w jakims turnieju itp.)
- zarządzanie druzyną z poziomu trenera(ustawienie pozycji zawodników i nwm czy jeszcze coś)
- funkcje do bezpiecznego usuwania zawodników, druzyn, turniejow, coachów (tu są transakcje, wiec np. nie mozna 
usunąc druzyny, ktora bierze udzial w aktywnym turnieju, trzeba obgadac co robimy z historycznymi danymi przy usuwaniu czegos
tak samo z turniejem, nie mozna usunąc turnieju, a zostawic w druzynach przypianie do nieistniejącego turnieju i wiele innych)
- OBSŁUGA MECZÓW !!! (utworzenie meczu przez admina, interfejs wprowadzania wyników, zdarzeń)...
- ... MATCH EVENTY
- jakieś wyświetlanie stanu turnieju, jakieś tabeli ligowej, czy czegokolwiek


Rzeczy poboczne, które trzeba zrobić na koniec:
- dostęp do poszczególnych stron z poziomy url (tzn. jak wpiszesz sobie ściezke to z poziomy coacha dostaniesz się 
do funkcji admina, nie moze tak być i trzeba wykorzytać jakos flage, ktora jest tworzorzona przy sign-upie )
- szyfrowanie hasla i zeby ono sie nie wyswietlalo przy rejestracji
- 
"""