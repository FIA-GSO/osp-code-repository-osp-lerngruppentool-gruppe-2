# Lerngruppentool

> Originales Projekt mit allen Git-Commits: [MoritzAufGithub/Lerngruppentool](https://github.com/MoritzAufGithub/Lerngruppentool/branches)

Tool zur Bildung von digitalen Lerngruppen am GSO. Schüler sollen klassenübergreifende Lerngruppen auf einer Webseite erstellen und diesen beitreten können.

Ein webbasiertes System zur Bildung und Verwaltung von digitalen Lerngruppen am GSO. Die Plattform ermöglicht es Schülern, klassenübergreifende Gruppen für die Prüfungsvorbereitung zu erstellen, zu verwalten und diesen beizutreten.

## Projektziel

Das Tool nutzt das Prinzip des aktiven Lernens. Schüler können gezielt Mitstreiter suchen, um Lernstoff durch gegenseitiges Erklären und Diskutieren zu vertiefen. Ein exklusiver Zugang über GSO-Mailadressen stellt dabei den Datenschutz und die Relevanz der Inhalte sicher.

## Funktionen

- Erstellung von zeitlich begrenzten Lerngruppengesuchen mit wenigen Klicks
- Klassenübergreifende Suche nach interessierten Teilnehmern
- Automatisches Schließen von Gruppen bei Erreichen der Kapazitätsgrenze
- Bearbeitungs- und Löschfunktion für eigene Einträge
- Zugangsbeschränkung auf offizielle GSO-Schulmailadressen

## Technische Architektur

Das Projekt ist als Full-Stack-Webanwendung konzipiert:

- **Frontend:** Umsetzung mit HTML5, CSS3 und nativem JavaScript. Die Kommunikation mit dem Server erfolgt asynchron über Fetch-API-Aufrufe an die REST-Schnittstelle.
- **Backend:** Eine Python-basierte REST API auf Basis des Flask-Frameworks. Diese verarbeitet die Logik, die Authentifizierung und die Datenbankanbindung.

## Installation & Projekt starten

Kopiere den passenden Block und führe ihn im Terminal aus, um die nötigen Bibliotheken aus `requirements.txt` zu installieren.

### Option 1 – Globale Installation

```powershell
pip install -r requirements.txt
```

### Option 2 – Installation in einer Virtual Environment

```powershell
# Lokale Skripte aktivieren
Set-ExecutionPolicy -ExecutionPolicy Bypass -Scope Process

# Virtual Environment aktivieren und Abhängigkeiten installieren
.\venv\Scripts\activate
pip install -r requirements.txt
```

### Projekt ausführen

1. Führe `backend/app.py` aus.
2. Öffne `frontend/register.html` mit einem Live-Server (VS Code Extension: `ritwickdey.LiveServer`).

## Interaktion mit dem System

In der `main` von `app.py` wird `setup_db(True)` ausgeführt. Dadurch werden Testdatensätze sowie ein Admin-Account angelegt. Den Parameter auf `False` setzen, um keine Testdaten zu generieren.

Der Admin-Account ist sofort verwendbar:

| Feld     | Wert                        |
|----------|-----------------------------|
| E-Mail   | `admin@gso.schule.koeln`    |
| Passwort | `fabo_boss`                 |
