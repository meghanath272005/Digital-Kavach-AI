# API documentation

Base URL: `http://127.0.0.1:8000`. All bodies are JSON (`Content-Type: application/json`) except image upload.
Maximum JSON body 64 KB. Rate limit: `DKA_RATE_LIMIT_PER_MIN` per IP (default 60; image endpoints use a quarter, minimum 5).

## Error format
```json
{"error": {"status": 422, "message": "Some fields need attention.", "fields": {"message": "Paste the message you want to check."}}}
```
| Status | Meaning |
|---|---|
| 400 | Invalid JSON / body is not an object |
| 404 | Unknown route, identity, account or report |
| 405 | Method not allowed |
| 409 | Duplicate (account already linked) |
| 411 / 413 | Missing Content-Length / body too large |
| 415 | Wrong Content-Type |
| 422 | Validation failed (`fields` maps field name to message) |
| 429 | Rate limited (`Retry-After` header) |
| 500 | Unexpected error (generic message; details are never returned) |

## General
| Method & path | Description |
|---|---|
| `GET /api/health` | `{"status":"ok","service":...,"ml_model_loaded":bool}` |
| `GET /api/dashboard/stats` | Real counts: `demo_identities`, `linked_accounts`, `reports_saved`, `checks_run{scam_messages,profiles,images}`, `ml_models_loaded` |
| `GET /api/meta` | Dropdown options (categories, platforms, report types, statuses) |
| `GET /api/samples` | Clearly-labelled demonstration inputs |
| `GET /api/recommendations` | Safety advice, helpline `1930`, portal `https://cybercrime.gov.in/` |

## Scam message detector
`POST /api/scam/check` body `{"message": "<1-5000 chars>"}`
Response: `category` (Low/Medium/High/Inconclusive), `rule_category`, `score`, `thresholds`, `findings[]` (`id,title,points,severity,explanation,evidence[]`),
`links[]` (`display` defanged, `reasons[]`), `ml` (`available`, and when available `label`, `probability`, `note`), `ml_raised_category`,
`recommendations[]`, `method`, `limitations[]`, `disclaimer`.
Rules decide High; ML can raise Low/Inconclusive to Medium only. Links are never opened.

## Fake profile checker
`POST /api/profile/check` body: `username` (required), `url`, `description`, `notes`, `account_age_days`, `followers`, `following`.
Response: `category`, `score`, `thresholds`, `findings[]` (`id,title,points,severity,detail,field`), `checks_passed[]`, `inputs_considered[]`,
`limited_information`, `recommendations[]`, `method`, `disclaimer` ("Risk assessment is preliminary and may be incorrect."). No network access is made.

## Image analysis
- `POST /api/image/analyse` - body = raw image bytes, `Content-Type: image/jpeg` or `image/png`. Max 5 MB; actual type verified from file content.
- `GET /api/image/sample` - synthetic JPEG (not a real person). `POST /api/image/analyse-sample` - analyses it.

Response: `verdict` ("Indicators found" / "Inconclusive" / "No indicators found by these limited checks"), `summary`, `findings[]` (`id,title,level,detail`),
`measurements` (`format,width,height,megapixels,file_size_kb,sha256,exif_present,camera,software_tag,faces_detected,face_detector_available,ela`),
`ela_heatmap` (PNG data URL, JPEG only), `method` (lists what was NOT performed), `guidance[]`, `disclaimer`, `stored:false`. No confidence or percentage is ever returned.

## Identity and linked accounts (simulation)
| Method & path | Body | Response |
|---|---|---|
| `POST /api/identity/start` | `{"alias":"optional","consent":true}` | 201: `id` (`DEMO-XXXXXXXX`), `status`, `steps[]`, `notice` ("Simulation only ..."), `never_collected[]` |
| `GET /api/identity/{id}` | | identity summary |
| `GET /api/identity/{id}/accounts` | | `{"accounts":[...]}` |
| `POST /api/identity/{id}/accounts` | `{"category","platform","handle"}` | 201 account with `pseudonym` (`pid_` + 20 hex of HMAC-SHA256) |
| `GET /api/identity/{id}/accounts/{aid}` | | account |
| `PATCH /api/identity/{id}/accounts/{aid}` | `{"status":"Active (demo)"|"Paused (demo)"}` | account |
| `DELETE /api/identity/{id}/accounts/{aid}` | | `{"removed":true}` |

Categories: personal, business, community, religious, organisation. Max 20 accounts per identity. The identity secret is never returned.

## Impersonation reports (local only)
| Method & path | Description |
|---|---|
| `POST /api/reports` | Fields: `reporter_name?`, `contact?`, `username`, `platform`, `profile_url?`, `report_type`, `description` (>=20 chars), `evidence_description?`. 201 returns `reference_id`, `status`, `timeline[]`, `sent_to_platform_or_authority:false`, `notice` |
| `GET /api/reports/{reference_id}` | Status and timeline only (never the report text, contact or evidence). 404 if unknown, 422 if malformed |
| `POST /api/reports/{reference_id}/simulate-next` | DEMO ONLY: moves to the next status (Submitted -> Under Review -> Additional Information Required -> Resolved) |

Reports are stored in the local SQLite database only. They are **not** sent to any platform or authority.

## Database tables
`demo_identities`, `linked_accounts`, `impersonation_reports`, `report_status_history`, plus `usage_counters` (feature name + count only; no content).
