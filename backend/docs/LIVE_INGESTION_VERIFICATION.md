# Live Ingestion Verification

This document summarizes the end-to-end live testing of the ingestion subsystem, verifying that the tuple-unpacking regression has been resolved and that the adapters correctly extract jobs and interact with the database.

## 1. Generic Source (Previously Working)
- **Test URL:** `https://thejobcompany.co.in/job-category/batch/2027`
- **Detected Adapter:** `GenericAdapter`
- **HTTP Status:** 200
- **Jobs Found:** 12
- **Extraction Method:** LLM
- **LLM Used:** Yes (`True`)
- **Database Persistence:** **FAILED** (Unique Constraint Violation)
- **Diagnostics & Limitations:** 
  The LLM successfully extracts all 12 jobs from the page text. However, because it extracts multiple jobs from a single URL, it defaults the `job_url` of each job to the source URL. The database enforces a `UNIQUE` constraint on `job_url` (`jobs_job_url_key`), causing a `PendingRollbackError` upon `db.commit()` when inserting the second job.

## 2. Deloitte Careers
- **Test URL:** `https://www.deloitte.com/in/en/careers.html`
- **Detected Adapter:** `GenericAdapter`
- **HTTP Status:** 200
- **Jobs Found:** 0
- **Extraction Method:** LLM
- **LLM Used:** Yes (`True`)
- **Database Persistence:** SUCCESS (No jobs to save)
- **Diagnostics & Limitations:**
  A Playwright trace and DOM inspection reveals that this is a static landing page, not a job board. There is no embedded `JSON-LD`, embedded `__NEXT_DATA__`, or XHR/GraphQL requests that fetch jobs. The page strictly contains marketing copy and a link redirecting to `https://southasiacareers.deloitte.com/`, which is their actual localized job search portal.
- **Recommended Adapters:** 
  Rather than attempting an LLM hack on a marketing landing page, a dedicated adapter should be built for `southasiacareers.deloitte.com` (which appears to be an Avature or Taleo instance).

## 3. Real Greenhouse Job Board
- **Test URL:** `https://boards.greenhouse.io/stripe`
- **Detected Adapter:** `GreenhouseAdapter`
- **HTTP Status:** 200
- **Jobs Found:** 567
- **Extraction Method:** Greenhouse API
- **LLM Used:** No (`False`)
- **Database Persistence:** SUCCESS (567 jobs added to the database successfully)
- **Diagnostics:** Successfully pulled the full catalog natively via the Greenhouse API without needing Playwright or AI.

## 4. Real Lever Job Board
- **Test URL:** `https://jobs.lever.co/spotify`
- **Detected Adapter:** `LeverAdapter`
- **HTTP Status:** 200
- **Jobs Found:** 100
- **Extraction Method:** Lever API
- **LLM Used:** No (`False`)
- **Database Persistence:** SUCCESS (100 jobs added to the database successfully)
- **Diagnostics:** Successfully mapped internal fields using the Lever API without AI fallback.

## 5. Invalid Greenhouse URL
- **Test URL:** `https://boards.greenhouse.io/invalid_company_123`
- **Detected Adapter:** `GreenhouseAdapter`
- **HTTP Status:** 404
- **Jobs Found:** 0
- **Extraction Method:** Greenhouse API
- **LLM Used:** No (`False`)
- **Database Persistence:** SUCCESS (No jobs to save)
- **Failures:** Diagnosed cleanly: `"Greenhouse board 'invalid_company_123' not found."`

## 6. Lever Corporate Homepage
- **Test URL:** `https://www.lever.co/`
- **Detected Adapter:** `GenericAdapter`
- **HTTP Status:** 200
- **Jobs Found:** 0
- **Extraction Method:** LLM
- **LLM Used:** Yes (`True`)
- **Database Persistence:** SUCCESS (No jobs to save)
- **Diagnostics & Limitations:** The ingestion manager correctly falls back to `GenericAdapter` since this is not a `jobs.lever.co` route. The Playwright scraper + LLM pipeline runs, detects no jobs on the corporate marketing page, logs a warning `"LLM returned no jobs or failed"`, and safely returns 0 jobs without crashing.
