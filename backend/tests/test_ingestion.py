import pytest
from unittest.mock import patch, MagicMock
from core.ingestion.manager import IngestionManager
from core.ingestion.adapters.greenhouse import GreenhouseAdapter
from core.ingestion.adapters.lever import LeverAdapter
from core.ingestion.adapters.ashby import AshbyAdapter
from core.ingestion.adapters.generic import GenericAdapter
from core.ingestion.adapters.indeed import IndeedAdapter
from core.ingestion.base import FetchResult, IngestionDiagnostics, NormalizedJob

def test_manager_detects_indeed():
    manager = IngestionManager()
    
    adapter = manager.get_adapter("https://indeed.com")
    assert isinstance(adapter, IndeedAdapter)
    
    adapter = manager.get_adapter("https://in.indeed.com/jobs?q=test")
    assert isinstance(adapter, IndeedAdapter)

def test_manager_detects_greenhouse():
    manager = IngestionManager()
    
    adapter = manager.get_adapter("https://boards.greenhouse.io/openai")
    assert isinstance(adapter, GreenhouseAdapter)
    
    adapter = manager.get_adapter("https://boards-api.greenhouse.io/v1/boards/openai/jobs")
    assert isinstance(adapter, GreenhouseAdapter)
    
def test_manager_detects_lever():
    manager = IngestionManager()
    
    adapter = manager.get_adapter("https://jobs.lever.co/netflix")
    assert isinstance(adapter, LeverAdapter)
    
def test_manager_detects_ashby():
    manager = IngestionManager()
    
    adapter = manager.get_adapter("https://jobs.ashbyhq.com/ycombinator")
    assert isinstance(adapter, AshbyAdapter)
    
def test_manager_detects_generic():
    manager = IngestionManager()
    
    adapter = manager.get_adapter("https://www.metacareers.com")
    assert isinstance(adapter, GenericAdapter)
    
    adapter = manager.get_adapter("https://careers.google.com")
    assert isinstance(adapter, GenericAdapter)

def test_extract_token_greenhouse():
    adapter = GreenhouseAdapter()
    
    assert adapter._extract_token("https://boards.greenhouse.io/openai") == "openai"
    assert adapter._extract_token("https://boards-api.greenhouse.io/v1/boards/stripe/jobs?content=true") == "stripe"
    assert adapter._extract_token("https://boards.greenhouse.io/embed/job_board?for=anthropic") == "anthropic"

def test_extract_company_lever():
    adapter = LeverAdapter()
    
    assert adapter._extract_company("https://jobs.lever.co/figma") == "figma"
    assert adapter._extract_company("https://api.lever.co/v0/postings/notion?mode=json") == "notion"

def test_extract_company_ashby():
    adapter = AshbyAdapter()
    
    assert adapter._extract_company("https://jobs.ashbyhq.com/vercel") == "vercel"
    assert adapter._extract_company("https://api.ashbyhq.com/posting-api/job-board/linear") == "linear"

def test_utils_parse_salary():
    from core.ingestion.utils import parse_salary
    res = parse_salary("70,000-1,20,000/Month")
    assert res["salary_min"] == 70000
    assert res["salary_max"] == 120000
    assert res["period"] == "MONTH"
    assert res["currency"] == "INR"

def test_utils_parse_location():
    from core.ingestion.utils import parse_location
    res = parse_location("San Francisco, CA, USA, Remote")
    assert res["city"] == "San Francisco"
    assert res["state"] == "CA"
    assert res["country"] == "USA"
    assert res["remote"] is True

def test_lever_strictness():
    adapter = LeverAdapter()
    assert adapter.can_handle("https://jobs.lever.co/netflix") is True
    assert adapter.can_handle("https://www.lever.co/") is False

def test_greenhouse_strictness():
    adapter = GreenhouseAdapter()
    result = adapter.fetch_jobs("https://boards.greenhouse.io/")
    assert len(result.jobs) == 0
    assert len(result.diagnostics.errors) > 0

def test_indeed_parameter_parsing():
    adapter = IndeedAdapter()
    url = "https://in.indeed.com/jobs?q=software+engineer+fresher&l=Lucknow%2C+Uttar+Pradesh&from=searchOnHP%2Cwhatautocomplete%2CwhatautocompleteSourceStandard%2Cwhereautocomplete&vjk=c887eeb4fa3cd1ac"
    
    config = adapter.parse_search_config(url)
    assert config["query"] == "software engineer fresher"
    assert config["location"] == "Lucknow, Uttar Pradesh"
    assert config["raw_params"]["vjk"] == "c887eeb4fa3cd1ac"
    assert "from" in config["raw_params"]

def _create_mock_playwright(status_code, title, content, links=None, raise_exc=False):
    class MockRes:
        status = status_code
    class MockPage:
        def goto(self, *args, **kwargs):
            if raise_exc:
                raise Exception("Network failure")
            return MockRes()
        def title(self):
            return title
        def content(self):
            return content
        def evaluate(self, arg):
            if raise_exc:
                raise Exception("Evaluate failure")
            if "scrollTo" in arg:
                return None
            if "querySelectorAll('a')" in arg:
                return links or []
            if "innerText" in arg:
                return content
            return None
    class MockContext:
        def new_page(self): return MockPage()
    class MockBrowser:
        def new_context(self, **kwargs): return MockContext()
        def close(self): pass
    class MockChromium:
        def launch(self, **kwargs): return MockBrowser()
    class MockPlaywright:
        @property
        def chromium(self): return MockChromium()
        def __enter__(self): return self
        def __exit__(self, *args): pass
    return MockPlaywright()

@patch('playwright.sync_api.sync_playwright')
def test_indeed_http_403_access_blocked(mock_pw):
    mock_pw.return_value = _create_mock_playwright(403, "Access Denied", "Blocked")
    adapter = IndeedAdapter()
    result = adapter.fetch_jobs("https://in.indeed.com/jobs?q=test")
    assert result.diagnostics.status == "ACCESS_BLOCKED"

@patch('playwright.sync_api.sync_playwright')
def test_indeed_http_200_cloudflare_challenge(mock_pw):
    mock_pw.return_value = _create_mock_playwright(200, "Attention Required! | Cloudflare", "Please verify you are a human")
    adapter = IndeedAdapter()
    result = adapter.fetch_jobs("https://in.indeed.com/jobs?q=test")
    assert result.diagnostics.status == "ACCESS_BLOCKED"

@patch('playwright.sync_api.sync_playwright')
@patch('core.ingestion.base_portal.extract_jobs_from_text')
def test_indeed_http_200_success(mock_extract, mock_pw):
    mock_pw.return_value = _create_mock_playwright(200, "Indeed Jobs", "Software Engineer at Google", links=[{"text":"apply", "href":"https://indeed.com/viewjob?jk=123"}])
    mock_extract.return_value = [{"title": "Software Engineer", "company": "Google", "job_url": "https://indeed.com/viewjob?jk=123"}]
    adapter = IndeedAdapter()
    result = adapter.fetch_jobs("https://in.indeed.com/jobs?q=test")
    assert result.diagnostics.status == "SUCCESS"
    assert result.diagnostics.jobs_found == 1

@patch('playwright.sync_api.sync_playwright')
@patch('core.ingestion.base_portal.extract_jobs_from_text')
def test_indeed_http_200_no_jobs(mock_extract, mock_pw):
    mock_pw.return_value = _create_mock_playwright(200, "Indeed Jobs", "No jobs match your search", links=[])
    mock_extract.return_value = []
    adapter = IndeedAdapter()
    result = adapter.fetch_jobs("https://in.indeed.com/jobs?q=test")
    assert result.diagnostics.status == "NO_JOBS_FOUND"
    assert result.diagnostics.jobs_found == 0

@patch('playwright.sync_api.sync_playwright')
def test_indeed_network_error(mock_pw):
    mock_pw.return_value = _create_mock_playwright(None, "", "", raise_exc=True)
    adapter = IndeedAdapter()
    result = adapter.fetch_jobs("https://in.indeed.com/jobs?q=test")
    assert result.diagnostics.status == "FETCH_ERROR"

def test_fetch_result_structure():
    result = FetchResult(
        jobs=[],
        diagnostics=IngestionDiagnostics(
            status="SUCCESS",
            adapter="TestAdapter",
            jobs_found=0
        )
    )
    assert result.diagnostics.status == "SUCCESS"
    assert result.diagnostics.adapter == "TestAdapter"

# Acceptance Test for Job Deduplication / Updates
def test_acceptance_scan_sequence():
    from db.session import SessionLocal
    from models.job_source import JobSource
    from models.job import Job
    from models.user import User  # Required for SQLAlchemy mapper resolution
    from models.company import Company # Required for SQLAlchemy mapper resolution
    from models.canonical_job import CanonicalJob
    import datetime
    
    db = SessionLocal()
    
    # 1. Clean up
    db.query(Job).filter(Job.source_url == "https://thejobcompany.co.in/job-category/batch/2027").delete(synchronize_session=False)
    db.query(JobSource).filter(JobSource.url == "https://thejobcompany.co.in/job-category/batch/2027").delete()
    db.commit()
    
    # Create Source
    source = JobSource(url="https://thejobcompany.co.in/job-category/batch/2027", name="Test Co")
    db.add(source)
    db.commit()
    
    manager = IngestionManager()
    
    # Override fetch_source for the test to return mock data
    class MockGenericAdapter(GenericAdapter):
        def __init__(self):
            self.call_count = 0
            
        def fetch_jobs(self, url, db=None, source_id=None, force_heal=False):
            self.call_count += 1
            
            jobs = []
            if self.call_count == 1 or self.call_count == 2:
                # 12 jobs
                for i in range(12):
                    jobs.append(NormalizedJob(
                        external_id=f"job_{i}", title=f"Job {i}", company="Test", description="Desc",
                        application_url=f"http://test.com/{i}", source_url=url, source_type="Career Page", source_name="Test"
                    ))
            elif self.call_count == 3:
                # 13 jobs (1 new)
                for i in range(13):
                    jobs.append(NormalizedJob(
                        external_id=f"job_{i}", title=f"Job {i}", company="Test", description="Desc",
                        application_url=f"http://test.com/{i}", source_url=url, source_type="Career Page", source_name="Test"
                    ))
            elif self.call_count == 4:
                # 13 jobs (1 updated)
                for i in range(13):
                    title = f"Job {i} Updated" if i == 0 else f"Job {i}"
                    jobs.append(NormalizedJob(
                        external_id=f"job_{i}", title=title, company="Test", description="Desc",
                        application_url=f"http://test.com/{i}", source_url=url, source_type="Career Page", source_name="Test"
                    ))
            elif self.call_count == 5:
                # 12 jobs (1 removed)
                for i in range(1, 13):
                    jobs.append(NormalizedJob(
                        external_id=f"job_{i}", title=f"Job {i}", company="Test", description="Desc",
                        application_url=f"http://test.com/{i}", source_url=url, source_type="Career Page", source_name="Test"
                    ))
                    
            return FetchResult(jobs=jobs, diagnostics=IngestionDiagnostics(status="Mocked", adapter="MockAdapter"))

    # Inject mock adapter
    mock_adapter = MockGenericAdapter()
    manager.adapters = [mock_adapter]
    
    # 1. First scan
    summary1 = manager.process_source(db, source)
    assert summary1["new"] == 12
    assert summary1["updated"] == 0
    assert summary1["removed"] == 0
    
    # 2. Second identical scan
    summary2 = manager.process_source(db, source)
    assert summary2["new"] == 0
    assert summary2["updated"] == 0
    assert summary2["removed"] == 0
    
    # 3. Third scan (1 new)
    summary3 = manager.process_source(db, source)
    assert summary3["new"] == 1
    assert summary3["updated"] == 0
    assert summary3["removed"] == 0
    
    # 4. Fourth scan (1 updated)
    summary4 = manager.process_source(db, source)
    assert summary4["new"] == 0
    assert summary4["updated"] == 1
    assert summary4["removed"] == 0
    
    # 5. Fifth scan (1 removed)
    summary5 = manager.process_source(db, source)
    assert summary5["new"] == 0
    assert summary5["updated"] == 0
    assert summary5["removed"] == 1
    
    db.close()

def test_deloitte_regression():
    from core.ingestion.manager import IngestionManager
    manager = IngestionManager()
    
    class MockGenericAdapter(GenericAdapter):
        def fetch_jobs(self, url, db=None, source_id=None, force_heal=False):
            return FetchResult(jobs=[], diagnostics=IngestionDiagnostics(status="SUCCESS", adapter="MockAdapter"))
    manager.adapters = [MockGenericAdapter()]
    
    result = manager.fetch_source("https://www.deloitte.com/in/en/careers.html")
    assert result is not None
    assert isinstance(result.jobs, list)
    assert isinstance(result.diagnostics, IngestionDiagnostics)

def test_thejobcompany_generic_page():
    from core.ingestion.manager import IngestionManager
    manager = IngestionManager()
    
    class MockGenericAdapter(GenericAdapter):
        def fetch_jobs(self, url, db=None, source_id=None, force_heal=False):
            return FetchResult(jobs=[], diagnostics=IngestionDiagnostics(status="SUCCESS", adapter="MockAdapter"))
    manager.adapters = [MockGenericAdapter()]
    
    result = manager.fetch_source("https://thejobcompany.co.in/job-category/batch/2027")
    assert result is not None
    assert isinstance(result.jobs, list)
    assert isinstance(result.diagnostics, IngestionDiagnostics)
