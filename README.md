<h1> **Support of HTTP QUERY in Web Application Firewalls** </h1>

<h2> **Short testing laboratory with QUERY and ModSecurity** </h2>

<h3> **Purpose:** </h3>
A prototype environment for methodology of HTTP/1.1, QUERY and WAF analysis.

<h3> **Architecture:** </h3>
- Client --> Flask-Backend on localhost:5000 --> SQLite Database as baseline for backend
- Client --> ModSecurity/CRS/NGINX on localhost:8080 --> Flask-Backend on localhost:5000 --> SQLite Database

**ALLOWED HTTP-Methods:**
GET, POST, QUERY, HEAD, OPTIONS

**Used HTTP-Methods:**
GET, POST, QUERY

<h3> **Versions:** </h3>
- HTTP/1.1
- ModSecurity 3.0.16
- ModSecurity-nginx 1.0.4
- OWASP CRS 3.3.10

<h3> **Attack Classes:** </h3>
- Benign Requests
- XSS
- Obfuscated XSS
- SQL-Injection

<h3> **Observed:** </h3>
- Benign GET-, POST- and QUERY-Requests are accepted whether it is directly to the Backend on :5000 or first through ModSecurity on :8080 resulting in 200.
- JSON-Body is parsed successfully by WAF on :8080 and Backend on :5000 for POST- and QUERY-Requests.
- Malicious GET-, POST- and QUERY-Requests reach Backend if sent directly to Backend on :5000.
- Malicious GET-, POST- and QUERY-Requests do not reach Backend if sent first to WAF on :8080 due to mutliple CRS rules resulting in 403.

<h3> **CRS rules triggered:** </h3>
XSS via POST, QUERY: ruleId: 941100 (+5), 941110 (+5), 941160  (+5), 949110 (no additional rule triggered just anomaly-score exceeded) (curl.exe -X <"either POST or QUERY"> -H "Content-Type: application/json" --data-binary "@../payloads/xss.json" http://localhost:8080/search) resulting in a total of 15 and therefore a BLOCK.
Obfuscated XSS via POST, QUERY: ruleId: 941100 (+5), 941110 (+5), 941160  (+5), 949110 (no additional rule triggered just anomaly-score exceeded) (curl.exe -X <"either POST or QUERY"> -H "Content-Type: application/json" --data-binary "@../payloads/obfuscated\_xss.json" http://localhost:8080/search) resulting in a total of 15 and therefore a BLOCK.
SQL-Injection via GET: ruleId: 942100 (SQL-Injection detected via libinjection - +5), 949110 (no additional rule triggered just anomaly-score exceeded) (curl.exe "http://localhost:8080/search?id=1%20OR%201=1") resulting in a total of 5 and therefore a BLOCK.
SQL-Injection via POST, QUERY: ruleId: 942100 (SQL-Injection detected via libinjection - +5), 949110 (no additional rule triggered just anomaly-score exceeded) resulting in a total fo 5 and therefore in a BLOCK.

<h3> **Notes:** </h3>
Whereas the XSS-Tests show the WAFs ability to detect the XSS-Payload, they do not demonstrate a successful execution of its payload in a browser, as the backend is not able to render the submitted input as HTML.
All sensitive information shared in this project, for example passwords or usernames are entirely made up and fictional for testing purposes only. 
