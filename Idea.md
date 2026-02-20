# Was ich bauen möchte

Ich möchte einen automatisierten Entwicklungs-Workflow, bei dem KI-Agenten
(Claude Code) meine GitHub Issues selbstständig abarbeiten. Ich erstelle ein
Issue, schiebe es auf meinem Kanban-Board in die Spalte "Ready" — und ab da
übernimmt das System.

## Mein Kanban-Board

Ich nutze GitHub Projects V2 mit einem Kanban-Board. Die Spalten entsprechen
dem Standard-Status-Feld von GitHub:

- **Backlog** — Ideen und geplante Aufgaben
- **Ready** — Bereit für die Entwicklung
- **In Progress** — Wird gerade bearbeitet
- **In Review** — Code wird geprüft
- **Done** — Fertig

Wenn ich ein Issue nach "Ready" verschiebe, soll automatisch ein Developer-Agent
anfangen zu arbeiten. Das Board zeigt mir jederzeit, wo jedes Issue gerade steht.

## Die Agenten

Ich brauche drei Rollen:

**Orchestrator** — Der Koordinator. Er beobachtet das Board und entscheidet,
welcher Agent als nächstes dran ist. Er läuft nur auf GitHub, nicht bei mir
lokal.

**Developer** — Der Entwickler. Er liest das Issue, implementiert die Lösung,
schreibt Tests und erstellt einen Pull Request. Er läuft auf meinem eigenen
Server zu Hause.

**Reviewer** — Der Prüfer. Er schaut sich den Pull Request an, gibt Feedback
und entscheidet, ob der Code gut genug ist oder nachgebessert werden muss.
Auch er läuft auf meinem Server.

## Der Ablauf

1. Ich erstelle ein Issue mit einer Beschreibung, was ich brauche
2. Ich schiebe es nach "Ready"
3. Der Developer beginnt automatisch zu arbeiten und schiebt das Issue "In Progress"
4. Er erstellt einen Pull Request und das Issue wandert nach "In Review"
5. Der Reviewer prüft den Code
6. Bei Problemen geht es zurück an den Developer — automatisch. Status geht auf in Review
7. Wenn alles passt, wandert es nach "Done"
8. Ich schaue mir den fertigen PR an und merge ihn

## Wo soll das laufen?

Ich habe einen kleinen Server zu Hause (Beelink Mini-PC), der rund um die Uhr
läuft. Darauf sollen der Developer und der Reviewer arbeiten. Der Orchestrator
braucht keinen eigenen Server, der läuft direkt auf GitHub. Ich habe dir runner auf Github bereits eingerichtet.
- "runner-developer-1" mit dem label "agentic-developer"
- "runner-developer-2" mit dem label "agentic-developer"
- "runner-reviewer-1" mit dem label "agentic-reviewer"

alle runner mit dem Label "agentic-developer" sind für den Developer prozess gedacht und mit dem Label "agentic-reviewer" sind für den reviewer.

## Organisations-Ebene vs. Repository-Ebene

Ich möchte das System einmal für meine GitHub-Organisation einrichten. Das
bedeutet: Der Server, der Webhook und die grundlegenden Workflows werden einmal
aufgesetzt und gelten dann für alle meine Repositories.

Pro Repository muss ich dann nur noch beschreiben, wie die Agenten dort
arbeiten sollen — also welche Coding-Standards gelten, wie getestet wird und
welchen Charakter die Agenten haben sollen.

## Was die Agenten über sich wissen

Jeder Agent hat drei Dateien, die ihn beschreiben:

IDENTITY.md — Wer er ist, wie er kommuniziert, welche Werte er hat
TOOLS.md — Welche Build-, Test- und Lint-Befehle im Projekt gelten
MEMORY.md — Was er aus früheren Aufgaben gelernt hat (wächst mit der Zeit, soll aber regelmäßig bereinigt werden, wenn Wissen veraltet oder nicht mehr relevant ist)

Ergänzend zur MEMORY.md existiert ein logs/-Ordner. Darin wird pro Tag eine Markdown-Datei angelegt mit dem Namensschema [yyyy-MM-dd].md (z. B. 2025-06-15.md). Jede Log-Datei dokumentiert:

Was an dem Tag gemacht wurde — erledigte Aufgaben, Änderungen, Entscheidungen
Was wir uns für das Projekt merken sollten — offene Punkte, Erkenntnisse, Blocker, nächste Schritte

Regel für MEMORY.md: Zu Beginn jeder neuen Sitzung müssen die letzten drei Log-Dateien aus logs/ eingelesen werden, um den aktuellen Projektstand und Kontext zu kennen. Dieser Hinweis ist fest in der MEMORY.md verankert.