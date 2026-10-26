# Flock Energy API

A small, read-only FastAPI proxy for meter search, meter location, meter energy,
and distribution-transformer data from the Urja Meter Ops portal. The portal
operations and response shapes described here were observed in UI-driven
browser requests. **Live portal authentication is not implemented or verified**,
so live requests may fail even when the configured base URL is correct.

## Requirements

- Python 3.10 or newer
- Network access to the portal for upstream requests

## Installation

Run these commands from the project directory in Windows PowerShell.

Create a virtual environment:

```powershell
python -m venv .venv
```

Install the project dependencies:

```powershell
.\.venv\Scripts\python.exe -m pip install -r requirements.txt
```

Create a local environment file:

```powershell
Copy-Item .env.example .env
```

## Configuration

Set the following values in `.env`. The username and password entries below
are placeholders; replace them locally if needed. Do not commit `.env` or share
credentials, cookies, or tokens.

```dotenv
PORTAL_BASE_URL=https://urja-ops.flockenergy.tech
PORTAL_USERNAME=operator@urja.local
PORTAL_PASSWORD=urja-ops-2026
```

`app.config` requires all three variables to be non-empty. The current client
uses only `PORTAL_BASE_URL`; it does not submit the username or password,
because the login response and session contract have not been verified.
Non-secret placeholder values can be used for local OpenAPI-only startup.

## Run

Start the development server from PowerShell:

```powershell
.\.venv\Scripts\python.exe -m uvicorn app.main:app --reload
```

- Interactive API documentation: [http://127.0.0.1:8000/docs](http://127.0.0.1:8000/docs)
- OpenAPI schema: [http://127.0.0.1:8000/openapi.json](http://127.0.0.1:8000/openapi.json)

The client uses a 10-second upstream timeout. **Successful live authenticated
portal requests have not been verified.**

## API endpoints

All endpoints are read-only. Search and transformer pagination use `page`
(default `1`, minimum `1`). Meter search also accepts `q` (default empty
string).

| Method | Local path | Behavior |
| --- | --- | --- |
| GET | `/meters?q={query}&page={page}` | Search meters |
| GET | `/meters/{meter_id}/geo` | Retrieve observed location fields |
| GET | `/meters/{meter_id}/energy` | Retrieve observed energy readings |
| GET | `/transformers?page={page}` | List distribution transformers |

There is no hierarchy endpoint or combined meter-detail endpoint. The
observed meter-search response does not include hierarchy or geo, and no
hierarchy API contract was verified.

### Examples

```text
GET /meters?q=J100003&page=1
GET /meters/J100003/geo
GET /meters/J100003/energy
GET /transformers?page=1
```

Response property names preserve the observed portal schema. For example,
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
  non-success status is currently surfaced as a generic HTTP 502 by this
  service.

## Tests

Run the complete test suite from PowerShell:

```powershell
.\.venv\Scripts\python.exe -m pytest
```

Tests use the supplied meter-export fixture for export parsing and mocked HTTP
transports for API/client behavior; they do not depend on live portal access.

## Known limitations

- The observed login is a form-encoded `POST /login` with string fields
  `email` and `password`. A subsequent meter-search request included a Cookie
  header and no Authorization header. The login response status/schema and
  whether it sets a cookie remain unverified. The client does not authenticate.
- No hierarchy endpoint or response contract was found. Hierarchy data is
  present in the supplied meter export, but it is not retrieved by this API
  proxy.
- Meter energy date-range options and empty live responses are unverified.
- Portal non-200 behavior has not been observed; the service's error mapping
  is defensive behavior, not a claim about portal error formats.
- The portal's visible export action was not inspected.

See [PROTOCOL.md](PROTOCOL.md) for the portal evidence record and
[REFLECTION.md](REFLECTION.md) for implementation decisions and limitations.
