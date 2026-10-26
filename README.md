# Flock Energy API

A small FastAPI read-only proxy for meter search, meter location, meter energy,
and distribution-transformer data from the Urja Meter Ops portal. The portal
operations and response shapes documented here were observed in its UI-driven
browser requests; authentication is not yet implemented or verified.

## Requirements

- Python 3.10 or newer
- Network access to the portal for live requests

## Installation

From the project directory in PowerShell:

```powershell
python -m venv .venv
.\.venv\Scripts\python.exe -m pip install -r requirements.txt
Copy-Item .env.example .env
```

Set the following values in `.env`:

```dotenv
PORTAL_BASE_URL=https://urja-ops.flockenergy.tech
PORTAL_USERNAME=your-portal-username
PORTAL_PASSWORD=your-portal-password
```

`app.config` requires all three variables to be non-empty. The current client
uses only `PORTAL_BASE_URL`; username and password are not sent because the
login response/session contract is not verified and authentication is not
implemented. Use non-secret placeholder values for local OpenAPI-only startup,
or keep real credentials in your ignored local `.env` if needed for future
authentication work. Do not commit `.env` or share credentials, cookies, or
tokens.

## Run

```powershell
.\.venv\Scripts\python.exe -m uvicorn app.main:app --reload
```

Open `http://127.0.0.1:8000/docs` for the generated OpenAPI documentation.

The service uses a 10-second upstream timeout. Until portal authentication is
implemented, live requests may fail with an upstream error even when the
configured base URL is correct.

## API endpoints

All endpoints are read-only. Search and transformer pagination use `page`
(default `1`, must be at least `1`). Meter search also accepts `q` (default
empty string).

| Method | Local path | Behavior |
|---|---|---|
| GET | `/meters?q={query}&page={page}` | Search meters |
| GET | `/meters/{meter_id}/geo` | Retrieve observed location fields |
| GET | `/meters/{meter_id}/energy` | Retrieve observed energy readings |
| GET | `/transformers?page={page}` | List distribution transformers |

There is no hierarchy endpoint and no combined meter-detail endpoint: the
observed meter list does not include hierarchy or geo, and no hierarchy API
contract was identified.

### Examples

```text
GET /meters?q=J100003&page=1
GET /meters/J100003/geo
GET /meters/J100003/energy
GET /transformers?page=1
```

The response property names preserve the observed portal schema. For example,
meter search returns an envelope containing `data`, `total`, `page`, and
`pageSize`; each item contains `meterId`, `serialNo`, `make`, `phaseType`,
`installStatus`, and `dtCode`.

## Error handling

- Invalid local pagination input returns HTTP 422.
- Portal timeouts return HTTP 504.
- Other upstream HTTP errors, connection failures, and invalid response JSON
  or schemas return HTTP 502 with a generic detail. Upstream response bodies
  are not returned to callers.
- Portal error and authentication status behavior has not been observed. A
  non-success status is currently surfaced as a generic HTTP 502.

## Tests

Run the complete suite:

```powershell
.\.venv\Scripts\python.exe -m pytest
```

Tests use the real meter-export fixture for export parsing and mocked HTTP
transports for API/client behavior; they do not depend on live portal access.

## Known limitations

- Portal login is observed as a form-encoded `POST /login` with string fields
  `email` and `password`; subsequent meter search carries a Cookie header and
  no Authorization header. The login response status/schema and whether it
  sets a cookie remain unverified. The client does not authenticate.
- No hierarchy endpoint or response contract was found. Hierarchy is available
  in the supplied export fixture, not through this API proxy.
- Meter energy date-range options and empty live responses are unverified.
- Portal non-200 behavior has not been observed; error handling is defensive
  behavior in this service, not a claim about portal error formats.
- The portal's visible export action was not inspected.

See [PROTOCOL.md](PROTOCOL.md) for the evidence record and [REFLECTION.md](REFLECTION.md)
for implementation decisions and remaining work.
