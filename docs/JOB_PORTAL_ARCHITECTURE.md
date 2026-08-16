# Job Portal Architecture

This document describes the architectural design for integrating job portals (like Indeed, Naukri, Internshala) into the existing ingestion subsystem.

## Design Principles

1.  **Generic Ingestion Compatibility**: Job portal integration must not break or interfere with the existing generic ATS/Careers page ingestion.
2.  **Explicit Domain Matching**: `JobPortalAdapter` is an abstract base class. It does not act as a generic domain router. Each concrete portal adapter (e.g., `IndeedAdapter`) is responsible for explicitly claiming its domain via `can_handle(url)`.
3.  **Structured Result Objects**: The ingestion system now strictly uses structured objects instead of position-based tuples.
    *   `FetchResult`: Contains `jobs` (list of `NormalizedJob`) and `diagnostics`.
    *   `IngestionDiagnostics`: Contains granular feedback on the extraction process (`status`, `adapter`, `http_status`, `extraction_method`, `jobs_found`, `execution_time_ms`, `errors`, `warnings`, `metadata`).

## Components

### `JobPortalAdapter`

The abstract base class (`core/ingestion/base_portal.py`) extends `JobSourceAdapter`. It requires subclasses to implement:
*   `parse_search_config(url: str) -> Dict[str, Any]`: Parses the URL into canonical search parameters (query, location) and places unrecognized parameters into `raw_params`.
*   `validate_source() -> bool`: Verifies if the source configuration is valid for the specific portal.
*   `fetch_jobs(url: str) -> FetchResult`: Executes the actual job fetching.

### `IndeedAdapter`

The concrete implementation for Indeed (`core/ingestion/adapters/indeed.py`).
*   **Domain Matching**: Claims `indeed.com` and subdomains (`in.indeed.com`).
*   **Configuration Parsing**: Maps `q` to `query` and `l` to `location`.
*   **Anti-Bot Handling**: Currently returns a structured `ACCESS_BLOCKED` status via `IngestionDiagnostics` because headless environments are blocked by Cloudflare. It does not falsely report "0 jobs found" or attempt bypasses.

## Diagnostic States

The system differentiates between various outcomes to avoid masking errors as "0 jobs found":
*   `SUCCESS`: Jobs successfully extracted.
*   `NO_JOBS_FOUND`: The source was accessed successfully, but no matching jobs were present.
*   `ACCESS_BLOCKED`: The portal actively blocked access (e.g., 403 Cloudflare challenge).
*   `UNSUPPORTED_PORTAL_ACCESS`: Attempted to access a portal without a supported mechanism/API.
*   `FETCH_ERROR`: Network/Timeout error.
*   `EXTRACTION_ERROR`: HTML/JSON structure changed.

## Frontend Integration

The user dashboard supports `JOB_PORTAL` as a source type. When an Indeed URL is pasted, the frontend client-side parses the URL, populating the corresponding "Keywords" and "Location" fields, while preserving all other parameters in the `raw_params` of the configuration payload. This ensures complete data is sent to the backend without hardcoding all possible Indeed parameters.
