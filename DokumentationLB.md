---

title: LB 234 - Dev Ops Anwenden
author: Straub Alexander
repository: https://github.com/Keinstein0/HomeserverCentral

---

# Handlungsziel 1:
## 1. Was ist Dev Ops?
Dev Ops (Development Operations) ist der bereich der sich mit dem Prozess der Softwarentwicklung befasst. Das heisst den entwicklern, die den tatsächlichen code schreiben, eine effiziente umgebung zu geben. So ist das Konfigurieren der IDE, das definieren von Versionierungsprozessen, die Anforderungs und Qualitätssicherung des geschriebenen codes sowie das Deployment des finalen projektes alles teile des bereichs Dev Ops. So zieht Dev Ops eine brücke zwischen den Entwicklern, die den Code schreiben, und dem Betrieb, der den Code laufen lässt.

### Warum braucht es Dev Ops?
Dev Ops erlaubt entwicklern in vielen art und weisen effizienter zu arbeiten. So beschleunigt es die Time to Market von individuellen Features, die mittels CI/CD automatisch getestet und Deployed werden können. Es garantiert auch die qualitätssicherung, denn dank automatisierten Unit&Integrationstests kann sichergestellt werden, dass ein feature nicht den bereits existierenden code lahmlegt. Auch strukturiert und dokumentiert es den Entwicklungsprozess klarer. Statt mündlicher chaotischer desk to desk kommunkation à "Kannst du mir den neuen Code schnell per mail schicken" sort dev ops für einen nachvollziehbaren entwicklungsprozess über standardisierte schnittstellen.

### Wichtige wörter:

- **Anforderung**: Eigenschaft die das fertige Süstem zwingend besitzen muss. ("Die texte auf der webseite sollen für personen ohne technisches wissen bearbeitbar sein")
- **Anforderungserhebung**: Der prozess in dem (z.b durch Interviews) die Wünsche und Bedürfnisse der nutzer in Konkrete anforderungen übersetzt werden
- **Anforderungsverwaltung**: Das Strukturieren, Dokumentieren, Prioritisieren und Nachverfolgen von Anforderungen über den gesamten Projektverlauf
- **Issue/Ticket**: Ein eintrag in einem Verwaltungstool für ein Feature, Bug oder eine generelle Aufgabe
- **Milestone**: Ein Zielpunkt/Zwischenstand im Projekt (z.b "UI prototyp (ohne daten) fertiggestellt ama 27. Oktober")
- **MVP** (minimum viable product): Erste funktionsfähige Version die man dem Nutzer zeigen kann.
- **Product Owner**: Verantwortlicher im Team für die vertretung der Interessen des Kunden/Marktes 
- **Requirements Management Plan** : Ein Dokument, das festlegt, wie anforderungen im Projekt erfasst, bewertet, geändert und verwaltet werden.
- **Rückverfolgbarkeit**: Die möglichkeit eine Anforderung von ihrer Entstehung zum finalen code nachzuverfolgen.
- **User Story**: Ein schema für eine anforderung aus der sicht eines Anwenders: "Als [Rolle] mächte ich [Ziel], um [Nutzen]
- **Vorlage** (für issues): Eine vordefinierte Struktur für neue Tickets mit pflichtfeldern (z.B dazugehörige Anforderung, Priorität, etc. )
- **Zuständige Person**: Person die für ein Ticket verwantwortlich ist
- **IaC** (infrastructure as code): Der code beschreibt die infrastruktur statt clicks in einem Gui (z.b Docker)


## 2. Anforderungsverwaltung
Für meine Anforderungsverwaltung fand ich relativ schnell zwei effektive Tools die mit bei der Anforderungsverwaltung helfen könnten:
- Github Issues
- Trello

Zu beginn des Projektes verglich ich diese miteinander um herauszufinden, welches für mein Projekt am besten geeignet wäre. 

So hatte Github klar den Vorteil da es schon in meine Versionierungssoftware eingebaut ist. Mit Github Issues kann ich einfach branches und commits an eine Anforderung anhängen. So könnte ich die Entwicklung im nachhinein Nachvollziehen. 

Der Vorteil von Trello hingegen war die starke modularität mittels extensions. Mit diesen könnte ich eben wie bei github Commits und Branches an sogenannte Karten anhängen. Ein weiterer Vorteil von trello war auch, dass ich mich damit bereits bei start des Projektes auskannte und daher recht effizient von beginn an entwickeln konnte. 

Schlussendlich entschied ich mich für Trello, da damit schon vertraut war. 
![alt text](documentationAssets/trello.png)
Ich modifizierte es zudem mit der GitHub erweiterung, um die prinzipien der Nachvollziehbaren entwicklung umzusetzen, sowie der Subtask extension, da ich so meine anforderungen hierarchisch sortieren konnte. 

Reflexiv betrachtet funktionierte trello schlechter als erwartet für mein Projekt. Aufgrund davon dass es ein externes tool war vergas ich oft das Board zu updaten. Auch war das ahnängen der jeweiligen Commits eine sehr zeitaufwändige sache verglichen mit wie github issues es gemacht hätte. Auch waren die Subtasks eher nachteilhaft implementiert. Ich hoffte dadurch die individuellen anforderungen auf themenbereiche zu unterteilen, jedoch führte das netto jedoch nur zu mehr chaos. 

Darauf basierend werde ich das nächste mal entweder mit Github Issues arbeiten, oder versuchen eine automatisiertere und strukturiertere lösung mit trello umzusetzen.

# Handlungsziel 2:
## 1. Meine IDE
Für meine IDE verwende ich Visual Studio Code, da es mit seinem System von Extensions eine sehr angenehme und modifizierbare Umgebung bietet. Um die Entwicklungsumgebung für alle Beteiligten zu standardisieren und zu automatisieren, befindet sich das gesamte Projekt in einem DevContainer. Das bedeutet, dass jeder Entwickler exakt dieselbe Umgebung nutzt, ohne manuell Libraries oder Tools installieren zu müssen. Die extensions die ich verwende sind die Folgenden:

### Sprachsupport für die Sprachen des Projekts (Python, Go, Svelte etc.)
Dank VSCs extensiven supports für erweiterungen kann ich synthaxhighlighting und linting direkt in der IDE machen. Dank des Devcontainers kann auch jeder der dieses Repo klont mit diesen tools arbeiten. 
### Github Actions:
Erlaubt mir von VSC aus zu sehen, wie meine automatisierte CI/CD pipeline läuft ohne im browser in github zu schauen.
### Devcontainer
Die grundlegende erweiterung, um die isolierte und reproduzierbare Entwicklungsumgebung auszuführen.
### Helpers wie "Path Intellisense" und "Add to .gitignore"
Kleine hilfreiche helfer die mir ärgerliche aufgaben mit einem click erleichtern. 
### Cline (KI integration):
Modulare Extension für Vibecoding. Unabhängig vom modell (auch wenn ich hautptsächlich glm-5.2/3-flash und gemini-3.8 verwende) und entwicklerorientiert. Sie unterstützt mich effizient beim Generieren von Boilerplate code und Beispielcode.

*Ergänzende Tests*
Zuvor versuchte ich statt Cline einige MCP servers zu installieren, jedoch stellte sich dies als nicht besonders effizient heraus, da die Cline extension schlussendlich doch eine direktere integration mit dem code hatte als alle MCPs zusammen. Auch versuchte ich zu beginn die Trello extension zu verwenden, jedoch bot diese nicht mehr Automation oder effizienz als die normale applikation wesshalb ich mich dagegen entschied diese weiter zu verwenden.


# Handlungsziel 3:
## 1. Versionierung
Um meinen code zu versionieren gibt es einige möglichkeiten. So kann man beispielsweise das ganze projekt in ein .zip file packen oder code snippets manuell sichern. Jedoch führen diese mittel sehr schnell zu sehr viel chaos. Weiter gibt es dedizierte Versionierungssysteme wie git, Subversion oder Perforce welche klarere strukturen bieten. Insbesondere git sticht hier heraus, da es heutzutage der klare industriestandard ist für solche projekte. Zudem ist git ein Verteiltes Versionierungssystem. Das heisst das auch wenn git server down wäre könnte ich immer noch auf die alten versionen meines codes zugreifen.

Ich verwende git in Kombination mit GitHub, da sich auf meinem github alle meine bisherigen privaten projekte befinden und das backup so sicher in der cloud gespeichert wird.

## 2. Arbeiten mit git in diesem Projekt
Um in meinem repository so strukturiert wie möglich zu arbeiten, sind alle relevanten elemente auf sogennantem feature branches. Der main branch agiert so als ein "source of all truth" backup mit dem erst alle änderungen mittels PRs vereint werden sobald sie vollständig und korrekt implementiert sind. 

Dieses modell funktioniert auch in softwareprojekten mit mehreren mitgliedern, denn so entwickelt jeder entwickler auf einem branch ohne sich gegenseitig in den weg zu kommen. 

Die Pull Requests erlauben mir zudem präzise zu verwalten was auf den Main branch darf und was nicht. Die automatisierten tests via GitHub actions bestätigen ausserdem dass die PR sicher ist um mit dem main branch vereint zu werden.
![alt text](documentationAssets/git.png)
Im bild sieht man die interaktion zwischen den unterschiedlichen feature branches und dem main branch.

## 3. Artefaktverwaltung
Artefakte (also die generierten produkte des codes) werden im "Build" schritt der deployment pipeline automatisch generiert und auf dem ghcr als container publiziert die mein homeserver später einfach herunterladen kann. 

Statt semantic versioning verwende ich den commit hash als die version des containers, da ich so zurückverfolgen kann auf welchem stand der code jetzt genau ist, und es direkt mit dem repository abgleichen kann.

# Handlungsziel 4:
## 1. Testfälle

Da ich die Anforderungen direkt als Tickets (Issues) im Projektmanagement-Tool gepflegt habe, beziehen sich meine Testfälle direkt auf diese Komponenten und deren Schnittstellen.

Für die Integrationstests habe ich eine strukturierte Test-Suite aufgebaut, die das Zusammenspiel der Container prüft:

| Scenario ID | Component / Area | Test Scenario | Description / Verification | Expected Result |
|---|---|---|---|---|
| **INT-CAD-01** | Caddy | Ingress & Startup Health | Verify Caddy parses Caddyfile and starts without syntax errors. Probe `GET /_matrix/client/.well-known/matrix/client`. | HTTP 200 OK with valid Matrix discovery JSON payload. |
| **INT-CAD-02** | Caddy | Public Static Assets | Request public files (`/login.html`, `/assets/*`). | HTTP 200 OK; no forward_auth redirection triggered. |
| **INT-CAD-03** | Caddy | Forward Auth Redirection | Request a protected route without session cookies (e.g. `/` or protected `/status`). | HTTP 302 Redirect to `/login.html?redirect=...`. |
| **INT-CAD-04** | Caddy | Header Security | Inspect response headers from Caddy on `localhost`. | `X-Frame-Options: DENY`, `X-Content-Type-Options: nosniff`, `Server` header stripped. |
| **INT-AUT-01** | Auth Gateway | Gateway Self-Health | Probe `GET http://matrix-auth-gateway:5000/healthz` (or via Caddy `/healthz` if mapped). | HTTP 200 OK; response status `"ok"`. |
| **INT-AUT-02** | Auth Gateway | Valid Login Flow | `POST /login` with valid credentials of a user belonging to the required room (against `tuwunel-mock`). | HTTP 302 redirect with valid signed session cookie in `Set-Cookie`. |
| **INT-AUT-03** | Auth Gateway | Invalid Credentials | `POST /login` with incorrect password or invalid username. | HTTP 302 redirect to `/login.html?error=1` (or 401/403); no session cookie issued. |
| **INT-AUT-04** | Auth Gateway | Unauthorized Member (403) | Attempt access to protected route with session of a user NOT in the required room. | Forward auth returns HTTP 403 Forbidden; Caddy displays `403.html`. |
| **INT-AUT-05** | Auth Gateway | Logout Flow | `GET /logout` with an active session cookie. | Session invalidated in gateway; `Set-Cookie` expired; subsequent protected requests redirect to `/login.html`. |
| **INT-STA-01** | Status API | Service Self-Health | Probe `GET http://localhost:5001/healthz`. | HTTP 200 OK; status indicates Status API is running. |
| **INT-STA-02** | Status API | Service Discovery | Probe `GET /services` on Status API. | HTTP 200 OK; returns array of registered service IDs (`auth-gateway`, `tuwunel`, `homepage`, `caddy`). |
| **INT-STA-03** | Status API | Live Status Probe (Healthy) | Probe `GET /services/auth-gateway` and `GET /services/tuwunel` with mock running. | HTTP 200 OK; `"status": "UP"` with recorded response time. |
| **INT-STA-04** | Status API | Live Status Probe (Degraded/Down) | Temporarily simulate downstream failure on mock homeserver and query `GET /services/tuwunel`. | HTTP 200 OK; `"status": "DOWN"` or `"DEGRADED"`. |
| **INT-STA-05** | Status API | Cache Buffer & Burst Protection | Send 10 concurrent requests to `/services/auth-gateway` within TTL buffer window (N seconds). | All requests return identical cached `last_checked` timestamp; downstream service pinged only once. |
| **INT-STA-06** | Status API | Protected Status Access | Attempt to access Status API through Caddy protected route without login cookie. | HTTP 302 Redirect to `/login.html`. Access granted with valid session cookie. |
| **INT-HOM-01** | Homepage | Static Build Delivery | Caddy serves static production build of Homepage from `/apps/homepage`. | HTTP 200 OK for `index.html`; static assets load with correct MIME types (`text/html`, `application/javascript`). |
| **INT-CMP-01** | Docker Compose | Compose Config Validation | Run `docker compose config` and `docker compose --profile test config`. | Configuration validates with exit code 0; volume/network references resolve cleanly. |
| **INT-CMP-02** | Docker Compose | Healthcheck Cascading | Verify startup order: `caddy` and `status-api` wait until `matrix-auth-gateway` reports `healthy`. | Services transition to `healthy` state without restarting or crashing. |

---

Unit-Tests liegen dezentral direkt im Quellcode-Verzeichnis der jeweiligen Microservices/Komponenten (da sie nah am Code geschrieben und mit ihm weiterentwickelt werden), während die zentralen Integrationstests das Zusammenspiel aller Container im Docker-Compose-Netzwerk prüfen.

## 2. Automatisierung via GitHub Actions (CI Pipeline)
Der gesamte Testprozess ist vollständig automatisiert und läuft über GitHub Actions (scripts/ci.sh):

1. **Unit Tests & Linting:** Nach jedem Push auf einen Branch werden parallel die Unit-Tests der einzelnen Komponenten ausgeführt und das Linting geprüft (Einhaltung syntaktischer und stylischer Konventionen).

2. **Integration Tests:** Nur wenn die Unit-Tests und das Linting erfolgreich waren, wird das spezialisierte Test-Profil der docker-compose.yml gestartet. Dieses führt die in der Tabelle definierten Integrationstests vollautomatisch aus, um sicherzustellen, dass die Services fehlerfrei miteinander kommunizieren.

# Handlungsziel 5:
## Automatisierter Deployment Prozess
Oft will man nicht jedes mal wenn es ein kleines code update gibt sich in den server ssh-en nur um dann das update manuell zu patchen. Hierfür gibt es automatische Deployment prozesse genannt CD. Diese arbeiten direkt mit git zusammen um den aktuellsten/stabilsten code automatisch zu kompilieren/verpacken und auf dem server zum laufen zu bekommen. Um dies umzusetzen gibt es einige möglichkeiten:
- **Eingebauter Service**: Viele hoster erlauben einem direkt das git repository zu verlinken und so direkt die files zu hosten wenn es ein update gibt
- **Docker**: Bei services die auf Docker basieren kann man github direkt sagen dass es einen container als artefakt produzieren soll, der dann auf dem server simpel geupdated werden kann
- **Git**: Man kann es auch einfach machen indem man das repository bei jedem update neu pullt und dann den ganzen stack wieder aufbaut. Das führt jedoch zu ein wenig downtime da der server so alles von grund auf selber bauen muss. 

So dass der server jedoch weis wann ein update nötig ist gibt es auch wieder einige optionen:
- **Manuell**: Die simpelste lösung ist klar das manuelle ausführen der update datei. Dies funktioniert gut wenn man immer zugriff auf den server hat, skaliert jedoch bei grösseren projekten sehr nachteilhaft.
- **SSH** : Man kann github einen SSH key zum server geben, was github selbst erlaubt den server von aussen zu updaten. Das reduziert die komplexität des servers selbst, heisst jedoch dass man einen ssh port nach aussen öffnen muss, was ein potentielles sicherheitsrisiko ist.
- **Webhooks** : Die lösung mit der meisten komplexität liegt dabei einen WebHook server auf dem Server aufzusetzen. Das ist ein http endpunkt welchen github aufruft um zu sagen, dass der server geupdated werden muss. Auch hier muss man ein geheimes token einsetzen, so dass nicht jeder die ganze zeit den server anfragen kann um ihn zu updaten. 


## CD auf meinen Homeserver
Auf meinem homeserver werwende ich eine mischung aud *Docker* und *git* und löse die aktion mit einem *Webhook* aus. 

### Auslösung
Wenn ein feature branch in den main branch gemergt wird via einer passenden PR, wird ersteinmal gecheckt ob alle tests erfolgreich sind. Nur dann darf der merge ausgeführt werden. Danach werden die nötigen Docker container gebaut. So wird beispielsweise das svelte zu statischem html/css/js kompiliert, welches dann von nginx ausgeführt werden kann. Wenn dies fehlerfrei ausgeführt wurde wird eine http request an meinem homeserver geschickt.

### Webhook
Der Webhook service läuft auf dem host und checkt ob eine request zum updaten des servers reinkommt. Wenn das der Fall ist, wird gecheckt ob die request korrekt authorisiert ist und erst dann wird das updating skript ausgeführt.

### Sicherheit
Das updating skript `scripts/deploy.sh` sichert sich ersteinmal selbst. Es darf nur einmal ausgeführt werden und erstellt daher ersteinmal ein lock. Es ist auch so konfiguriert dass es bei einem fehler auf keinen fall silently-failt sondern einen error gibt. So kann ich darauf reagieren. 

Im ersten schritt wird dann das git repository geupdated mittels `git pull origin main` so dass alle dateien auf dem neusten stand sind.

### Docker
Danach werden die container geupdated. Das heisst sie werden erst einmal von ghcr heruntergeladen und ersetzen dann die aktuell laufenden container. Dies passiert für alle funktionalen services wie die homepage, auth und status. Einzig das Caddyfile verwendet eine andere logik

### Caddy
Da ich Caddy als meinen reverse proxy verwende, wäre es sehr nachteilhaft wenn caddy down wäre. Websocket verbindungen oder das matrix würden ihren state verlieren, was nicht katastrophal wäre, jedoch immer noch ärgerlich. Daher verwende ich hier eine 0-Downtime lösung die caddy schon selbst anbietet. der folgende block checkt ob ein update für caddy nötig ist und wenn ja führt es den eingebauten befehl zum 0-Downtime updaten des caddyfiles aus.

```shell
if docker compose -f "${COMPOSE_FILE}" ps --status running --format '{{.Service}}' | grep -q "^caddy$"; then
    docker compose -f "${COMPOSE_FILE}" exec -T caddy caddy reload --config /etc/caddy/Caddyfile
    echo "==> Caddy reloaded successfully."
else
    echo "==> Note: Caddy was not running; it has been started by docker compose up."
fi
```


