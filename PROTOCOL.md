# Portal investigation record

Do not record credentials, cookies, authorization values, tokens, personal data,
or unredacted account/device identifiers. Record header names only. Replace
record-specific identifiers with placeholders (for example, `{meter_id}`).
Use only an authorized account and real UI actions; do not guess URLs or probe
undocumented paths.

## Collecting browser evidence

1. Open the portal in a browser where you are authorized to use it.
2. Open Developer Tools → **Network**, enable **Preserve log**, and filter to
   **Fetch/XHR**. Clear the log before each operation.
3. Perform one UI action at a time. Record the request method and path, relevant
   parameter names and non-sensitive values, status, and response structure.
   Use the browser's request/response details; do not share a raw HAR, copied
   cURL command, or unredacted headers/body.
4. Redact sensitive values before sharing. Keep field names and JSON types so
   the schema remains useful. For record-specific paths or values, use
   placeholders consistently.
5. Repeat for successful UI flows. Record an error only if it occurs naturally
   or can be triggered safely without risking account lockout or data changes.
6. Mark each observation as verified only after confirming it against the
   browser request and response. A UI observation alone does not establish an
   API contract.

### Capturing authentication safely

1. In your own authorized browser, open the portal and Developer Tools →
   **Network**. Enable **Preserve log** and clear the log. If already signed in,
   use the portal's normal **Sign out** control once, then clear the log again.
2. Sign in once through the visible portal form. Do not copy or share the
   password or any credential values.
3. In Network, select the request caused by submitting the sign-in form. In
   **Headers**, record only the HTTP method, path, status, and header names.
   From **Payload**, record field names and value types only. From **Response**
   or **Preview**, record JSON field names and types only. Record whether a
   `Set-Cookie` header is present, but never copy its value. Do not guess which
   request is the login request; identify it by the form submission and timing.
4. After the portal returns to the meters page, select its meter-search request
   in Network. Record the method, path, query parameter names, status, and
   response schema. In **Headers**, record whether `Cookie` and/or
   `Authorization` header names are present; do not copy their values.
5. Share the sanitized notes only. Never share a HAR, copied cURL command,
   complete request/response headers, credential values, cookies, tokens, or
   personal data. Avoid repeated failed sign-in attempts.

## Operations to investigate

### Authentication and session

- Evidence source / UI action: Signed in through the portal UI and reached the
  Meters page.
- Request method and path: The normal sign-in form submitted `POST /login`.
- Parameters (names; redact sensitive values): None observed in the URL.
- Request body schema (field names and types only): Form URL encoded fields
  `email` (string) and `password` (string). Values were not captured.
- Response status and schema (redacted): Login response status and response
  schema were not captured.
- Authentication/session behavior: The login request had no Cookie or
  Authorization request header. A subsequent `GET /portal/meters/search`
  included a Cookie header and no Authorization header. A normal sign-out
  action submitted `POST /api/auth/sign-out` with a Cookie header and returned
  HTTP 200 JSON with a boolean `success` field; the sign-out response included
  `Set-Cookie`. Cookie values were neither read nor recorded.
- Errors and status codes: No login error response was captured. No
  unauthorized API response was observed or deliberately triggered.
- Confidence / verification status: Login method/path, form content type and
  field names/types, and subsequent request header presence were observed.
  Login status/body, login `Set-Cookie` presence, cookie attributes/session
  lifetime, renewal, and unauthorized behavior remain unverified.

### Meter details

- Evidence source / UI action: Meter search and opening a meter from its
  visible result.
- Request method and path: `GET /portal/meters/search` (API request observed).
  The browser detail page is `/meters/{meter_id}`; its server-side data-loading
  contract was not separately identified.
- Parameters (use `{meter_id}` for identifiers): Search query keys are `q`
  and `page`; page values 1 and 2 were observed. No request body.
- Request body schema: None observed for search.
- Response status and schema (redacted): HTTP 200 JSON with top-level fields
  `data`, `total`, `page`, and `pageSize`. Each `data` item has string fields
  `meterId`, `serialNo`, `make`, `phaseType`, `installStatus`, and `dtCode`.
  The unfiltered result had 403 records total, 20 records per page, and 20
  records on each of pages 1 and 2. A UI search with no matches returned
  `total: 0`, `page: 1`, `pageSize: 20`, and an empty `data` array. The list
  response does not include the export's nested `hierarchy` or `geo` fields.
- Authentication/session behavior: See Authentication and session above.
- Errors and status codes: Only HTTP 200 responses were observed.
- Confidence / verification status: Method, path, query parameter names,
  pagination behavior, status, and response schema observed from UI-triggered
  fetches. Authentication details and error responses remain unverified.

#### Meter location

- Request method and path: `GET /portal/meters/{meter_id}/geo`.
- Parameters: Meter ID is a path segment; no query parameters or request body
  were observed.
- Response status and schema: HTTP 200 JSON with `data` containing string
  fields `latitude` and `longitude`.
- Confidence / verification status: Observed in the meter detail UI flow;
  authentication and error behavior remain unverified.

#### Meter consumption

- Request method and path: `GET /portal/meters/{meter_id}/energy`.
- Parameters: Meter ID is a path segment; no query parameters or request body
  were observed.
- Response status and schema: HTTP 200 JSON with `data` as an array of objects
  containing string fields `timestamp`, `kwh`, `kvah`, and `voltR`. Eight rows
  were shown for the inspected meter.
- Confidence / verification status: Observed in the meter detail UI flow;
  date-range support, empty results, authentication, and error behavior remain
  unverified.

### Consumption

- See the Meter consumption observation above. No date-range controls or
  additional consumption query parameters were observed in the UI.

### Transformers

- Evidence source / UI action: Opened the visible Transformers navigation item
  and used its Next/Previous pagination controls.
- Request method and path: `GET /portal/dts`.
- Parameters (use placeholders for identifiers): Query key `page`; values 1
  and 2 were observed. No request body.
- Request body schema: None observed.
- Response status and schema (redacted): HTTP 200 JSON with top-level fields
  `data`, `total`, `page`, and `pageSize`. Each `data` item has string fields
  `code`, `name`, and `feederCode`, and numeric `capacityKva`. The observed
  result had 40 records total, 20 per page, and two pages.
- Observed relationship to meters or hierarchy: Transformer rows expose a
  feeder code; meter export records expose a DT code. No transformer detail
  navigation or additional relationship request was observed.
- Authentication/session behavior: See Authentication and session above.
- Errors and status codes: Only HTTP 200 responses were observed. The visible
  export button was not activated.
- Confidence / verification status: Method, path, page query, pagination,
  status, and response schema observed from UI-triggered fetches.

### Hierarchy

- Evidence source / UI action: The meter detail page displayed a hierarchy
  breadcrumb.
- Request method and path: No dedicated hierarchy API request was identified.
- Parameters: Unknown.
- Request body schema: Unknown.
- Response status and schema (redacted): The UI displayed zone, circle,
  division, subdivision, substation, feeder, and DT labels; most displayed a
  name and code. The source response and schema were not captured.
- Observed hierarchy levels, identifiers, and parent/child relationships: The
  breadcrumb presents those levels in that order. No independent relationship
  contract was verified.
- Authentication/session behavior: See Authentication and session above.
- Errors and status codes: Not observed.
- Confidence / verification status: UI presentation observed; API endpoint,
  method, parameters, schema, and missing-node behavior remain unverified.

## Evidence status

| Operation | Evidence collected | Verified against request and response | Remaining questions |
|---|---|---|---|
| Authentication/session | Login form request and later search headers observed | Partially — request schema and Cookie/Authorization header presence | Login response status/schema, login Set-Cookie, cookie attributes/lifecycle, unauthorized response |
| Meter search | Yes | Yes — method/path, query names, 200 schema, pagination, empty result | Auth and error behavior |
| Meter location | Yes | Yes — method/path, 200 schema | Auth and error behavior |
| Meter consumption | Yes | Yes — method/path, 200 schema | Date-range support, empty result, auth and error behavior |
| Transformers | Yes | Yes — method/path, pagination, 200 schema | Auth and error behavior; export action not inspected |
| Hierarchy | UI breadcrumb only | Partially — displayed levels/order | API request/response contract and relationships |

## Service implementation status

The local FastAPI service exposes:

| Local route | Verified portal operation |
|---|---|
| `GET /meters?q={query}&page={page}` | `GET /portal/meters/search?q={query}&page={page}` |
| `GET /meters/{meter_id}/geo` | `GET /portal/meters/{meter_id}/geo` |
| `GET /meters/{meter_id}/energy` | `GET /portal/meters/{meter_id}/energy` |
| `GET /transformers?page={page}` | `GET /portal/dts?page={page}` |

Pydantic response models preserve the observed portal field names and reject
unexpected fields. The client uses a 10-second timeout, does not follow
redirects, and validates response JSON. Local invalid pagination returns 422;
upstream timeouts return 504; other upstream HTTP failures, connection errors,
and invalid response JSON/schema return a generic 502 without exposing the
upstream body. Only successful portal responses were observed; these failure
mappings describe local defensive behavior and not verified portal errors.

The client does not submit credentials or implement authentication. Configured
username/password values are currently validated by the existing configuration
module but are not sent upstream. Live access through this service is therefore
not verified. No hierarchy route is exposed because no hierarchy API contract
was identified.