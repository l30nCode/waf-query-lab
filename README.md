# Support of HTTP QUERY in Web Application Firewalls

## Short testing laboratory with QUERY and ModSecurity

### Purpose:

A prototype environment for methodology of HTTP/1.1, QUERY and WAF analysis.

### Architecture:

- Client --> Flask-Backend on localhost:5000 --> SQLite Database as baseline for backend
- Client --> ModSecurity/CRS/NGINX on localhost:8080 --> Flask-Backend on localhost:5000 --> SQLite Database

**ALLOWED HTTP-Methods:** GET, POST, QUERY, HEAD, OPTIONS

**Used HTTP-Methods:** GET, POST, QUERY

### Versions:

- **HTTP/1.1**
- **ModSecurity** 3.0.16
- **ModSecurity-nginx** 1.0.4
- **OWASP CRS** 3.3.10
- **Container image:** `owasp/modsecurity-crs:nginx@sha256:ccec5e3ecd1dcf6b48903268f4fe415fd17914e8bf30fc21263fd05cc7045f29`

### Attack Classes:

- Benign Requests
- XSS
- Obfuscated XSS
- SQL-Injection

### WAF-QUERY-Lab use:

#### 1. Versuchsaufbau vorbereiten

Die Anleitung und die Testbefehle beziehen sich auf Windows PowerShell. Voraussetzung sind Git, Python und ein laufendes Docker mit Docker Compose.

- GitHub Repo klonen und ein PowerShell-Terminal im Projektroot öffnen.
- Python Virtual Environment erzeugen, aktivieren und die Dependencies aus der im Projektroot liegenden `requirements.txt` installieren:

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install -r requirements.txt
```

- Im Projektroot die containerisierte WAF-Instanz mit NGINX und CRS starten und den Status prüfen:

```powershell
docker compose up -d
docker compose ps
```

- In das Verzeichnis `backend` wechseln, die Datenbank erzeugen und das Flask-Backend starten:

```powershell
cd backend
python init_db.py
python app.py
```

Das Terminal mit dem laufenden Flask-Backend geöffnet lassen.

#### 2. Testläufe starten

- Das Verzeichnis `payloads` stellt verschiedene Request-Payloads mit benign und malicious Content bereit.
- Die folgenden Befehle in einem zweiten PowerShell-Terminal im Verzeichnis `backend` ausführen. Dazu das Terminal im Projektroot öffnen und `cd backend` ausführen.
- Die Dateipfade `../payloads/...` beziehen sich auf dieses Arbeitsverzeichnis.
- Für POST und QUERY werden die JSON-Payloads im Request-Body gesendet. Für GET wird die entsprechende Eingabe als URL-Parameter übertragen.
- Die folgenden Befehle und Protokolle dokumentieren exemplarisch die QUERY-Testläufe. Die zusammenfassenden Angaben zu GET und POST stehen unter „Observed“ und „CRS rules triggered“.

##### 2.1 Genutzte Befehle in den Testläufen auf WAF (8080)

###### 2.1.1 - QUERY benign
```powershell
curl.exe -X QUERY `
   -H "Content-Type: application/json" `
   --data-binary "@../payloads/benign.json" `
   http://localhost:8080/search
```

```json
{
  "content_type": "application/json",
  "method": "QUERY",
  "raw_body": "{\"id\":\"1\"}",
  "result": [
    {
      "id": 1,
      "name": "Emil"
    }
  ],
  "search_id": "1",
  "sql": "\n        SELECT id, name\n        FROM users\n        WHERE id = 1\n    "
}
```

###### 2.1.2 - QUERY sqli
```powershell
curl.exe -X QUERY `
   -H "Content-Type: application/json" `
   --data-binary "@../payloads/sqli.json" `
   http://localhost:8080/search
```

```html
<html>
<head><title>403 Forbidden</title></head>
<body>
<center><h1>403 Forbidden</h1></center>
<hr><center>nginx</center>
</body>
</html>
```

##### 2.2 Genutzte Befehle in den Testläufen auf Backend (5000)

###### 2.2.1 - QUERY benign
```powershell
curl.exe -X QUERY `
   -H "Content-Type: application/json" `
   --data-binary "@../payloads/benign.json" `
   http://localhost:5000/search
```

```json
{
  "content_type": "application/json",
  "method": "QUERY",
  "raw_body": "{\"id\":\"1\"}",
  "result": [
    {
      "id": 1,
      "name": "Emil"
    }
  ],
  "search_id": "1",
  "sql": "\n        SELECT id, name\n        FROM users\n        WHERE id = 1\n    "
}
```

###### 2.2.2 - QUERY sqli
```powershell
curl.exe -X QUERY `
   -H "Content-Type: application/json" `
   --data-binary "@../payloads/sqli.json" `
   http://localhost:5000/search
```

```json
{
  "content_type": "application/json",
  "method": "QUERY",
  "raw_body": "{\"id\":\"1 OR 1=1\"}",
  "result": [
    {
      "id": 1,
      "name": "Emil"
    },
    {
      "id": 2,
      "name": "Frieda"
    },
    {
      "id": 3,
      "name": "Oskar"
    }
  ],
  "search_id": "1 OR 1=1",
  "sql": "\n        SELECT id, name\n        FROM users\n        WHERE id = 1 OR 1=1\n    "
}
```

#### Ergebnisübersicht der dokumentierten QUERY-Tests

| QUERY-Test | Direktes Backend (5000) | Über WAF (8080) |
|---|---|---|
| Benigne Eingabe | Erwarteter Datensatz | Erwarteter Datensatz, HTTP 200 |
| SQL-Injection | Alle drei Datensätze | HTTP 403; Erkennungsregel 942100, Score 5; Blockierregel 949110 |
| XSS-Payload | Keine Browserausführung nachgewiesen | HTTP 403; Erkennungsregeln 941100, 941110 und 941160, Score 15; Blockierregel 949110 |
| XSS mit veränderter Groß-/Kleinschreibung | Keine Browserausführung nachgewiesen | HTTP 403; Erkennungsregeln 941100, 941110 und 941160, Score 15; Blockierregel 949110 |

Die XSS-Tests belegen die Erkennung und Blockierung der Payloads durch die WAF, nicht ihre Ausführung im Browser.

#### 3. WAF-Log-Ausgaben:
##### 3.1 - QUERY benign:
```text
2026-10-03 10:22:25
```

```text
172.19.0.1 - - [03/Oct/2026:08:22:25 +0000] "QUERY /search HTTP/1.1" 200 267 "-" "curl/8.21.0" "-"
```

**The following Audit-Log delivers more precise processing information of the benign QUERY-Request**
```text
2026-10-03 11:41:26
```

```text
172.19.0.1 - - [03/Oct/2026:09:41:26 +0000] "QUERY /search HTTP/1.1" 200 267 "-" "curl/8.21.0" "-"
2026-10-03 11:41:26
```

```text
{"transaction":{"client_ip":"172.19.0.1","time_stamp":"Sat Oct  3 09:41:26 2026","server_id":"57f0466c74f66bff14231a0eb39806c36f88df69","client_port":43430,"host_ip":"172.19.0.2","host_port":8080,"unique_id":"179102048678.486973","is_interrupted":false,"request":{"method":"QUERY","http_version":"1.1","hostname":"localhost","uri":"/search","headers":{"Host":"localhost:8080","User-Agent":"curl/8.21.0","Accept":"*/*","Content-Type":"application/json","Content-Length":"10"}},"response":{"body":"","http_code":200,"headers":{"Server":"nginx\u0000","Date":"Sat, 03 Oct 2026 09:41:26 GMT","Content-Length":"267","Content-Type":"application/json","Connection":"keep-alive","Access-Control-Allow-Headers":"*"}},"producer":{"modsecurity":"ModSecurity v3.0.16 (Linux)","connector":"ModSecurity-nginx v1.0.4","secrules_engine":"Enabled","components":["OWASP_CRS/3.3.10\""]},"messages":[]}}
2026-10-03 11:41:26
```

```text
{"transaction":{"client_ip":"127.0.0.1","time_stamp":"Sat Oct  3 09:41:26 2026","server_id":"57f0466c74f66bff14231a0eb39806c36f88df69","client_port":50246,"host_ip":"127.0.0.1","host_port":8443,"unique_id":"179102048637.851910","is_interrupted":false,"request":{"method":"GET","http_version":"2.0","hostname":"localhost","uri":"/healthz","headers":{"user-agent":"healthcheck","accept":"*/*","host":"localhost:8443"}},"response":{"body":"OK","http_code":200,"headers":{"Server":"nginx\u0000","Date":"Sat, 03 Oct 2026 09:41:26 GMT","Content-Length":"2","Content-Type":"application/octet-stream","Content-Type":"text/plain","Connection":"close"}},"producer":{"modsecurity":"ModSecurity v3.0.16 (Linux)","connector":"ModSecurity-nginx v1.0.4","secrules_engine":"Enabled","components":["OWASP_CRS/3.3.10\""]},"messages":[]}}
```

##### 3.2 - QUERY sqli:
```text
2026-10-03 10:22:58
```

```text
2026/10/03 08:22:58 [error] 499#499: *152 [client 172.19.0.1] ModSecurity: Access denied with code 403 (phase 2). Matched "Operator `Ge' with parameter `5' against variable `TX:ANOMALY_SCORE' (Value: `5' ) [file "/etc/modsecurity.d/owasp-crs/rules/REQUEST-949-BLOCKING-EVALUATION.conf"] [line "81"] [id "949110"] [rev ""] [msg "Inbound Anomaly Score Exceeded (Total Score: 5)"] [data ""] [severity "2"] [ver "OWASP_CRS/3.3.10"] [maturity "0"] [accuracy "0"] [tag "modsecurity"] [tag "application-multi"] [tag "language-multi"] [tag "platform-multi"] [tag "attack-generic"] [hostname "localhost"] [uri "/search"] [unique_id "179101577880.976896"] [ref ""], client: 172.19.0.1, server: localhost, request: "QUERY /search HTTP/1.1", host: "localhost:8080"
2026-10-03 10:22:58
```

```text
172.19.0.1 - - [03/Oct/2026:08:22:58 +0000] "QUERY /search HTTP/1.1" 403 146 "-" "curl/8.21.0" "-"
```

```text
2026-10-03 10:22:58
```

```json
{"transaction":{"client_ip":"172.19.0.1","time_stamp":"Sat Oct  3 08:22:58 2026","server_id":"6d91e719e834024d1b433888f9fb5dcaf6213a65","client_port":43928,"host_ip":"172.19.0.2","host_port":8080,"unique_id":"179101577880.976896","is_interrupted":true,"request":{"method":"QUERY","http_version":"1.1","hostname":"localhost","uri":"/search","headers":{"Host":"localhost:8080","User-Agent":"curl/8.21.0","Accept":"*/*","Content-Type":"application/json","Content-Length":"17"}},"response":{"body":"<html>\r\n<head><title>403 Forbidden</title></head>\r\n<body>\r\n<center><h1>403 Forbidden</h1></center>\r\n<hr><center>nginx</center>\r\n</body>\r\n</html>\r\n","http_code":403,"headers":{"Server":"nginx\u0000","Date":"Sat, 03 Oct 2026 08:22:58 GMT","Content-Length":"146","Content-Type":"text/html","Access-Control-Allow-Origin":"*","Connection":"keep-alive","Access-Control-Max-Age":"3600","Access-Control-Allow-Methods":"GET, POST, PUT, DELETE, OPTIONS","Access-Control-Allow-Headers":"*"}},"producer":{"modsecurity":"ModSecurity v3.0.16 (Linux)","connector":"ModSecurity-nginx v1.0.4","secrules_engine":"Enabled","components":["OWASP_CRS/3.3.10\""]},"messages":[{"message":"SQL Injection Attack Detected via libinjection","details":{"match":"detected SQLi using libinjection.","reference":"v8,8","ruleId":"942100","file":"/etc/modsecurity.d/owasp-crs/rules/REQUEST-942-APPLICATION-ATTACK-SQLI.conf","lineNumber":"46","data":"Matched Data: 1&1 found within ARGS:json.id: 1 OR 1=1","severity":"2","ver":"OWASP_CRS/3.3.10","rev":"","tags":["application-multi","language-multi","platform-multi","attack-sqli","paranoia-level/1","OWASP_CRS","capec/1000/152/248/66","PCI/6.5.2"],"maturity":"0","accuracy":"0"}},{"message":"Inbound Anomaly Score Exceeded (Total Score: 5)","details":{"match":"Matched \"Operator `Ge' with parameter `5' against variable `TX:ANOMALY_SCORE' (Value: `5' )","reference":"","ruleId":"949110","file":"/etc/modsecurity.d/owasp-crs/rules/REQUEST-949-BLOCKING-EVALUATION.conf","lineNumber":"81","data":"","severity":"2","ver":"OWASP_CRS/3.3.10","rev":"","tags":["modsecurity","application-multi","language-multi","platform-multi","attack-generic"],"maturity":"0","accuracy":"0"}}]}}
```

##### 3.3 Verhalten gegenüber XSS:
###### 3.3.1 - QUERY xss
```powershell
curl.exe -X QUERY `
   -H "Content-Type: application/json" `
   --data-binary "@../payloads/xss.json" `
   http://localhost:8080/search
```

```html
<html>
<head><title>403 Forbidden</title></head>
<body>
<center><h1>403 Forbidden</h1></center>
<hr><center>nginx</center>
</body>
</html>
```

```text
2026-10-03 10:37:10
```

```text
2026/10/03 08:37:10 [error] 499#499: *194 [client 172.19.0.1] ModSecurity: Access denied with code 403 (phase 2). Matched "Operator `Ge' with parameter `5' against variable `TX:ANOMALY_SCORE' (Value: `15' ) [file "/etc/modsecurity.d/owasp-crs/rules/REQUEST-949-BLOCKING-EVALUATION.conf"] [line "81"] [id "949110"] [rev ""] [msg "Inbound Anomaly Score Exceeded (Total Score: 15)"] [data ""] [severity "2"] [ver "OWASP_CRS/3.3.10"] [maturity "0"] [accuracy "0"] [tag "modsecurity"] [tag "application-multi"] [tag "language-multi"] [tag "platform-multi"] [tag "attack-generic"] [hostname "localhost"] [uri "/search"] [unique_id "179101663035.272579"] [ref ""], client: 172.19.0.1, server: localhost, request: "QUERY /search HTTP/1.1", host: "localhost:8080"
2026-10-03 10:37:10
```

```text
172.19.0.1 - - [03/Oct/2026:08:37:10 +0000] "QUERY /search HTTP/1.1" 403 146 "-" "curl/8.21.0" "-"
```

```text
2026-10-03 10:37:10
```

```json
{"transaction":{"client_ip":"172.19.0.1","time_stamp":"Sat Oct  3 08:37:10 2026","server_id":"6d91e719e834024d1b433888f9fb5dcaf6213a65","client_port":49126,"host_ip":"172.19.0.2","host_port":8080,"unique_id":"179101663035.272579","is_interrupted":true,"request":{"method":"QUERY","http_version":"1.1","hostname":"localhost","uri":"/search","headers":{"Host":"localhost:8080","User-Agent":"curl/8.21.0","Accept":"*/*","Content-Type":"application/json","Content-Length":"34"}},"response":{"body":"<html>\r\n<head><title>403 Forbidden</title></head>\r\n<body>\r\n<center><h1>403 Forbidden</h1></center>\r\n<hr><center>nginx</center>\r\n</body>\r\n</html>\r\n","http_code":403,"headers":{"Server":"nginx\u0000","Date":"Sat, 03 Oct 2026 08:37:10 GMT","Content-Length":"146","Content-Type":"text/html","Access-Control-Allow-Origin":"*","Connection":"keep-alive","Access-Control-Max-Age":"3600","Access-Control-Allow-Methods":"GET, POST, PUT, DELETE, OPTIONS","Access-Control-Allow-Headers":"*"}},"producer":{"modsecurity":"ModSecurity v3.0.16 (Linux)","connector":"ModSecurity-nginx v1.0.4","secrules_engine":"Enabled","components":["OWASP_CRS/3.3.10\""]},"messages":[{"message":"XSS Attack Detected via libinjection","details":{"match":"detected XSS using libinjection.","reference":"v8,25t:utf8toUnicode,t:urlDecodeUni,t:htmlEntityDecode,t:jsDecode,t:cssDecode,t:removeNulls","ruleId":"941100","file":"/etc/modsecurity.d/owasp-crs/rules/REQUEST-941-APPLICATION-ATTACK-XSS.conf","lineNumber":"38","data":"Matched Data: XSS data found within ARGS:json.id: <script>alert(1)</script>","severity":"2","ver":"OWASP_CRS/3.3.10","rev":"","tags":["modsecurity","application-multi","language-multi","platform-multi","attack-xss","paranoia-level/1","OWASP_CRS","capec/1000/152/242"],"maturity":"0","accuracy":"0"}},{"message":"XSS Filter - Category 1: Script Tag Vector","details":{"match":"Matched \"Operator `Rx' with parameter `(?i)<script[^>]*>[\\s\\S]*?' against variable `ARGS:json.id' (Value: `<script>alert(1)</script>' )","reference":"o0,8v8,25t:utf8toUnicode,t:urlDecodeUni,t:htmlEntityDecode,t:jsDecode,t:cssDecode,t:removeNulls","ruleId":"941110","file":"/etc/modsecurity.d/owasp-crs/rules/REQUEST-941-APPLICATION-ATTACK-XSS.conf","lineNumber":"64","data":"Matched Data: <script> found within ARGS:json.id: <script>alert(1)</script>","severity":"2","ver":"OWASP_CRS/3.3.10","rev":"","tags":["modsecurity","application-multi","language-multi","platform-multi","attack-xss","paranoia-level/1","OWASP_CRS","capec/1000/152/242"],"maturity":"0","accuracy":"0"}},{"message":"NoScript XSS InjectionChecker: HTML Injection","details":{"match":"Matched \"Operator `Rx' with parameter `(?i:(?:<\\w[\\s\\S]*[\\s\\/]|['\\\"](?:[\\s\\S]*[\\s\\/])?)(?:on(?:d(?:e(?:vice(?:(?:orienta|mo)tion|proximity|found|light)|livery(?:success|error)|activate)|r(?:ag(?:e(?:n(?:ter|d)|xit)|(?:gestur|leav)e|start|d (3146 characters omitted)' against variable `ARGS:json.id' (Value: `<script>alert(1)</script>' )","reference":"o0,7v8,25t:utf8toUnicode,t:urlDecodeUni,t:htmlEntityDecode,t:jsDecode,t:cssDecode,t:removeNulls","ruleId":"941160","file":"/etc/modsecurity.d/owasp-crs/rules/REQUEST-941-APPLICATION-ATTACK-XSS.conf","lineNumber":"181","data":"Matched Data: <script found within ARGS:json.id: <script>alert(1)</script>","severity":"2","ver":"OWASP_CRS/3.3.10","rev":"","tags":["modsecurity","application-multi","language-multi","platform-multi","attack-xss","paranoia-level/1","OWASP_CRS","capec/1000/152/242"],"maturity":"0","accuracy":"0"}},{"message":"Inbound Anomaly Score Exceeded (Total Score: 15)","details":{"match":"Matched \"Operator `Ge' with parameter `5' against variable `TX:ANOMALY_SCORE' (Value: `15' )","reference":"","ruleId":"949110","file":"/etc/modsecurity.d/owasp-crs/rules/REQUEST-949-BLOCKING-EVALUATION.conf","lineNumber":"81","data":"","severity":"2","ver":"OWASP_CRS/3.3.10","rev":"","tags":["modsecurity","application-multi","language-multi","platform-multi","attack-generic"],"maturity":"0","accuracy":"0"}}]}}
```

###### 3.3.2 - QUERY obfuscated xss
```powershell
curl.exe -X QUERY `
   -H "Content-Type: application/json" `
   --data-binary "@../payloads/obfuscated_xss.json" `
   http://localhost:8080/search
```

```html
<html>
<head><title>403 Forbidden</title></head>
<body>
<center><h1>403 Forbidden</h1></center>
<hr><center>nginx</center>
</body>
</html>
```

```text
2026-10-03 10:37:39
```

```text
2026/10/03 08:37:39 [error] 500#500: *196 [client 172.19.0.1] ModSecurity: Access denied with code 403 (phase 2). Matched "Operator `Ge' with parameter `5' against variable `TX:ANOMALY_SCORE' (Value: `15' ) [file "/etc/modsecurity.d/owasp-crs/rules/REQUEST-949-BLOCKING-EVALUATION.conf"] [line "81"] [id "949110"] [rev ""] [msg "Inbound Anomaly Score Exceeded (Total Score: 15)"] [data ""] [severity "2"] [ver "OWASP_CRS/3.3.10"] [maturity "0"] [accuracy "0"] [tag "modsecurity"] [tag "application-multi"] [tag "language-multi"] [tag "platform-multi"] [tag "attack-generic"] [hostname "localhost"] [uri "/search"] [unique_id "179101665942.814314"] [ref ""], client: 172.19.0.1, server: localhost, request: "QUERY /search HTTP/1.1", host: "localhost:8080"
2026-10-03 10:37:39
```

```text
172.19.0.1 - - [03/Oct/2026:08:37:39 +0000] "QUERY /search HTTP/1.1" 403 146 "-" "curl/8.21.0" "-"
```

```text
2026-10-03 10:37:39
```

```json
{"transaction":{"client_ip":"172.19.0.1","time_stamp":"Sat Oct  3 08:37:39 2026","server_id":"6d91e719e834024d1b433888f9fb5dcaf6213a65","client_port":39524,"host_ip":"172.19.0.2","host_port":8080,"unique_id":"179101665942.814314","is_interrupted":true,"request":{"method":"QUERY","http_version":"1.1","hostname":"localhost","uri":"/search","headers":{"Host":"localhost:8080","User-Agent":"curl/8.21.0","Accept":"*/*","Content-Type":"application/json","Content-Length":"34"}},"response":{"body":"<html>\r\n<head><title>403 Forbidden</title></head>\r\n<body>\r\n<center><h1>403 Forbidden</h1></center>\r\n<hr><center>nginx</center>\r\n</body>\r\n</html>\r\n","http_code":403,"headers":{"Server":"nginx\u0000","Date":"Sat, 03 Oct 2026 08:37:39 GMT","Content-Length":"146","Content-Type":"text/html","Access-Control-Allow-Origin":"*","Connection":"keep-alive","Access-Control-Max-Age":"3600","Access-Control-Allow-Methods":"GET, POST, PUT, DELETE, OPTIONS","Access-Control-Allow-Headers":"*"}},"producer":{"modsecurity":"ModSecurity v3.0.16 (Linux)","connector":"ModSecurity-nginx v1.0.4","secrules_engine":"Enabled","components":["OWASP_CRS/3.3.10\""]},"messages":[{"message":"XSS Attack Detected via libinjection","details":{"match":"detected XSS using libinjection.","reference":"v8,25t:utf8toUnicode,t:urlDecodeUni,t:htmlEntityDecode,t:jsDecode,t:cssDecode,t:removeNulls","ruleId":"941100","file":"/etc/modsecurity.d/owasp-crs/rules/REQUEST-941-APPLICATION-ATTACK-XSS.conf","lineNumber":"38","data":"Matched Data: XSS data found within ARGS:json.id: <sCrIpT>alert(1)</ScRiPt>","severity":"2","ver":"OWASP_CRS/3.3.10","rev":"","tags":["modsecurity","application-multi","language-multi","platform-multi","attack-xss","paranoia-level/1","OWASP_CRS","capec/1000/152/242"],"maturity":"0","accuracy":"0"}},{"message":"XSS Filter - Category 1: Script Tag Vector","details":{"match":"Matched \"Operator `Rx' with parameter `(?i)<script[^>]*>[\\s\\S]*?' against variable `ARGS:json.id' (Value: `<sCrIpT>alert(1)</ScRiPt>' )","reference":"o0,8v8,25t:utf8toUnicode,t:urlDecodeUni,t:htmlEntityDecode,t:jsDecode,t:cssDecode,t:removeNulls","ruleId":"941110","file":"/etc/modsecurity.d/owasp-crs/rules/REQUEST-941-APPLICATION-ATTACK-XSS.conf","lineNumber":"64","data":"Matched Data: <sCrIpT> found within ARGS:json.id: <sCrIpT>alert(1)</ScRiPt>","severity":"2","ver":"OWASP_CRS/3.3.10","rev":"","tags":["modsecurity","application-multi","language-multi","platform-multi","attack-xss","paranoia-level/1","OWASP_CRS","capec/1000/152/242"],"maturity":"0","accuracy":"0"}},{"message":"NoScript XSS InjectionChecker: HTML Injection","details":{"match":"Matched \"Operator `Rx' with parameter `(?i:(?:<\\w[\\s\\S]*[\\s\\/]|['\\\"](?:[\\s\\S]*[\\s\\/])?)(?:on(?:d(?:e(?:vice(?:(?:orienta|mo)tion|proximity|found|light)|livery(?:success|error)|activate)|r(?:ag(?:e(?:n(?:ter|d)|xit)|(?:gestur|leav)e|start|d (3146 characters omitted)' against variable `ARGS:json.id' (Value: `<sCrIpT>alert(1)</ScRiPt>' )","reference":"o0,7v8,25t:utf8toUnicode,t:urlDecodeUni,t:htmlEntityDecode,t:jsDecode,t:cssDecode,t:removeNulls","ruleId":"941160","file":"/etc/modsecurity.d/owasp-crs/rules/REQUEST-941-APPLICATION-ATTACK-XSS.conf","lineNumber":"181","data":"Matched Data: <sCrIpT found within ARGS:json.id: <sCrIpT>alert(1)</ScRiPt>","severity":"2","ver":"OWASP_CRS/3.3.10","rev":"","tags":["modsecurity","application-multi","language-multi","platform-multi","attack-xss","paranoia-level/1","OWASP_CRS","capec/1000/152/242"],"maturity":"0","accuracy":"0"}},{"message":"Inbound Anomaly Score Exceeded (Total Score: 15)","details":{"match":"Matched \"Operator `Ge' with parameter `5' against variable `TX:ANOMALY_SCORE' (Value: `15' )","reference":"","ruleId":"949110","file":"/etc/modsecurity.d/owasp-crs/rules/REQUEST-949-BLOCKING-EVALUATION.conf","lineNumber":"81","data":"","severity":"2","ver":"OWASP_CRS/3.3.10","rev":"","tags":["modsecurity","application-multi","language-multi","platform-multi","attack-generic"],"maturity":"0","accuracy":"0"}}]}}
```

### Observed:

These observations apply only to the tested requests and the configuration used in this laboratory.

- Benign GET-, POST- and QUERY-Requests are accepted whether it is directly to the Backend on :5000 or first through ModSecurity on :8080 resulting in **200**.
- **JSON-Body is parsed successfully** by WAF on :8080 and Backend on :5000 for POST- and QUERY-Requests.
- Malicious GET-, POST- and QUERY-Requests **reach Backend** if sent directly to Backend on :5000.
- Malicious GET-, POST- and QUERY-Requests **do not reach Backend** if sent first to WAF on :8080 due to CRS rule matches and the blocking evaluation resulting in **403**.

### CRS rules triggered:

- **XSS via POST, QUERY:** ruleId: 941100 (+5), 941110 (+5), 941160 (+5), 949110 (blocking evaluation rule: checks the accumulated anomaly score and blocks when the threshold is reached; adds no attack score) (`curl.exe -X <"either POST or QUERY"> -H "Content-Type: application/json" --data-binary "@../payloads/xss.json" http://localhost:8080/search`) resulting in a total of **15** and therefore a **BLOCK**.

- **Obfuscated XSS via POST, QUERY:** ruleId: 941100 (+5), 941110 (+5), 941160 (+5), 949110 (blocking evaluation rule: checks the accumulated anomaly score and blocks when the threshold is reached; adds no attack score) (`curl.exe -X <"either POST or QUERY"> -H "Content-Type: application/json" --data-binary "@../payloads/obfuscated_xss.json" http://localhost:8080/search`) resulting in a total of **15** and therefore a **BLOCK**.

- **SQL-Injection via GET:** ruleId: 942100 (SQL-Injection detected via libinjection - +5), 949110 (blocking evaluation rule: checks the accumulated anomaly score and blocks when the threshold is reached; adds no attack score) (`curl.exe "http://localhost:8080/search?id=1%20OR%201=1"`) resulting in a total of **5** and therefore a **BLOCK**.

- **SQL-Injection via POST, QUERY:** ruleId: 942100 (SQL-Injection detected via libinjection - +5), 949110 (blocking evaluation rule: checks the accumulated anomaly score and blocks when the threshold is reached; adds no attack score) resulting in a total of **5** and therefore in a **BLOCK**.

### Notes:

Whereas the XSS-Tests show the WAFs ability to detect the XSS-Payload, they **do not demonstrate a successful execution of its payload in a browser**, as the backend is not able to render the submitted input as HTML.

All sensitive information shared in this project, for example passwords or usernames are **entirely made up and fictional for testing purposes only**.
