Der GitHub-Link zum originalen Projekt, um alle Git-Commits usw. nachzuverfolgen: 
https://github.com/MoritzAufGithub/Lerngruppentool/branches

# Lerngruppentool
Tool zur Bildung von digitalen Lerngruppen am GSO. Schüler sollen klassenübergreifende Lerngruppen auf einer Webseite erstellen und diesen beitreten können.


Ein webbasiertes System zur Bildung und Verwaltung von digitalen Lerngruppen am GSO. Die Plattform ermöglicht es Schülern, klassenübergreifende Gruppen für die Prüfungsvorbereitung zu erstellen, zu verwalten und diesen beizutreten.

Projektziel
Das Tool nutzt das Prinzip des aktiven Lernens. Schüler können gezielt Mitstreiter suchen, um Lernstoff durch gegenseitiges Erklären und Diskutieren zu vertiefen. Ein exklusiver Zugang über GSO-Mailadressen stellt dabei den Datenschutz und die Relevanz der Inhalte sicher.

Funktionen
Erstellung von zeitlich begrenzten Lerngruppengesuchen mit wenigen Klicks.
Klassenübergreifende Suche nach interessierten Teilnehmern.
Automatisches Schließen von Gruppen bei Erreichen der Kapazitätsgrenze.
Bearbeitungs- und Löschfunktion für eigene Einträge.
Zugangsbeschränkung auf offizielle GSO-Schulmailadressen.

Technische Architektur
Das Projekt ist als Full-Stack-Webanwendung konzipiert:

    Frontend: Umsetzung mit HTML5, CSS3 und nativem JavaScript. Die Kommunikation mit dem Server erfolgt asynchron über Fetch-API-Aufrufe an die REST-Schnittstelle.
    Backend: Eine Python-basierte REST API auf Basis des Flask-Frameworks. Diese verarbeitet die Logik, die Authentifizierung und die Datenbankanbindung.



Wie bekomme ich das Projekt zum Laufen?
--> Den unteren Block kopieren und im Terminal ausführen, um nötige Bibliotheken aus requirements.txt zu installieren.
Wenn keine virtual environment angelegt wurde, den 1. Block kopieren um die Pakete global zu installieren.
Andernfalls den 2. Block.

Block 1 --------------------------------------------------

# Globale Installation (
pip install -r requirements.txt
# )

Block 2 --------------------------------------------------

# Installation im Virtual Environment (
# Lokale Skripte aktivieren:
Set-ExecutionPolicy -ExecutionPolicy Bypass -Scope Process

# Skript aktivieren und Abhängigkeiten installieren:
.\venv\Scripts\activate
pip install -r requirements.txt
# )

----------------------------------------------------------

Nun kann das Programm ausgeführt werden. Hierzu die Datei app.py ausführen.
Dann mit einem Live-Server (Extension: "ritwickdey.LiveServer") die register.html öffnen.



Interaktion mit dem System:
In der main von app.py wird "setup_db(True) ausgeführt.
Dadurch werden Testdatensätze erzeugt als auch ein Admin-Rollen-Account.
Den Methodenparameter kann man auf "False" setzen, wenn man keine Testdaten haben will.

Mit dem Admin-Account kann man sich sofort anmelden mit den Daten:
email: "admin@gso.schule.koeln"
passwort: "fabo_boss"
