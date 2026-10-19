import type { ChatSession, DocumentChunk, DocumentItem, IngestionJob } from "./types"

const HOUR = 60 * 60 * 1000
const DAY = 24 * HOUR
const ago = (ms: number) => new Date(Date.now() - ms).toISOString()

export const SEED_DOCUMENTS: DocumentItem[] = [
  {
    document_id: "doc_q3fin",
    filename: "Q3_2026_Financial_Report.pdf",
    file_size: 2_516_582,
    page_count: 14,
    created_at: ago(2 * DAY),
  },
  {
    document_id: "doc_handbook",
    filename: "Employee_Handbook_2026.pdf",
    file_size: 5_347_737,
    page_count: 42,
    created_at: ago(6 * DAY),
  },
  {
    document_id: "doc_security",
    filename: "Information_Security_Policy.pdf",
    file_size: 1_258_291,
    page_count: 18,
    created_at: ago(9 * DAY),
  },
  {
    document_id: "doc_api",
    filename: "Platform_API_Integration_Guide.pdf",
    file_size: 3_984_588,
    page_count: 27,
    created_at: ago(12 * DAY),
  },
]

export const SEED_JOBS: IngestionJob[] = [
  {
    job_id: "job_vendor",
    document_id: "doc_vendor",
    status: "PROCESSING",
    progress: 38,
    error_message: null,
    filename: "Vendor_Contracts_Q4.pdf",
    file_size: 1_887_437,
  },
  {
    job_id: "job_scan",
    document_id: "doc_scan",
    status: "FAILED",
    progress: 62,
    error_message: "Text extraction failed on page 9: the page is an image-only scan with no OCR layer.",
    filename: "Board_Minutes_Scanned.pdf",
    file_size: 8_703_181,
  },
]

export const SEED_CHUNKS: DocumentChunk[] = [
  {
    chunk_id: "chk_fin_1",
    document_id: "doc_q3fin",
    page_numbers: [2],
    heading: "Executive Summary",
    content:
      "Q3 2026 total revenue reached $48.2M, up 23% year-over-year and 7% quarter-over-quarter, driven primarily by enterprise subscription expansion in North America and EMEA. Annual recurring revenue (ARR) closed the quarter at $186.5M. Platform revenue now represents 64% of total revenue, compared with 57% a year ago.",
    snippet: "Q3 2026 total revenue reached $48.2M, up 23% year-over-year and 7% quarter-over-quarter",
  },
  {
    chunk_id: "chk_fin_2",
    document_id: "doc_q3fin",
    page_numbers: [5, 6],
    heading: "Profitability",
    content:
      "Gross margin improved to 78.4% from 75.1% in Q2, reflecting infrastructure cost optimizations and a higher mix of platform revenue. Operating margin was 12.6%, the third consecutive quarter of positive non-GAAP operating income. Free cash flow for the quarter was $9.8M, and the company ended the period with $212M in cash and equivalents.",
    snippet: "Gross margin improved to 78.4% from 75.1% in Q2",
  },
  {
    chunk_id: "chk_fin_3",
    document_id: "doc_q3fin",
    page_numbers: [8],
    heading: "Customer Metrics",
    content:
      "Net revenue retention was 118%, with gross retention holding at 94%. The company added 312 net new customers in the quarter, bringing the total to 4,870. Customers contributing more than $100K in ARR grew 31% year-over-year to 412.",
    snippet: "Net revenue retention was 118%, with gross retention holding at 94%.",
  },
  {
    chunk_id: "chk_fin_4",
    document_id: "doc_q3fin",
    page_numbers: [12],
    heading: "Outlook",
    content:
      "For Q4 2026, management expects revenue between $51.0M and $52.5M and full-year revenue of $184M to $186M. Hiring will remain focused on go-to-market and AI research teams, with operating margin expected to remain above 10%.",
    snippet: "management expects revenue between $51.0M and $52.5M",
  },
  {
    chunk_id: "chk_hb_1",
    document_id: "doc_handbook",
    page_numbers: [17],
    heading: "Paid Time Off",
    content:
      "Full-time employees accrue 1.67 days of paid time off (PTO) per month, totaling 20 days per year. Up to 5 unused days may be carried over into the following calendar year; any additional unused days are forfeited on December 31. Part-time employees accrue PTO on a pro-rated basis.",
    snippet: "accrue 1.67 days of paid time off (PTO) per month, totaling 20 days per year",
  },
  {
    chunk_id: "chk_hb_2",
    document_id: "doc_handbook",
    page_numbers: [18, 19],
    heading: "Parental Leave",
    content:
      "All employees with at least 90 days of tenure are eligible for 16 weeks of fully paid parental leave, regardless of gender or path to parenthood. Leave may be taken continuously or split into up to two blocks within 12 months of the birth or placement. A phased return at 60% schedule is available for up to four weeks afterward.",
    snippet: "eligible for 16 weeks of fully paid parental leave",
  },
  {
    chunk_id: "chk_hb_3",
    document_id: "doc_handbook",
    page_numbers: [19],
    heading: "Sick Leave",
    content:
      "Employees receive 10 paid sick days per year, which do not roll over. Absences longer than three consecutive working days require a note from a licensed healthcare provider. Sick leave may also be used to care for an immediate family member.",
    snippet: "Employees receive 10 paid sick days per year, which do not roll over.",
  },
  {
    chunk_id: "chk_hb_4",
    document_id: "doc_handbook",
    page_numbers: [21],
    heading: "Requesting Leave",
    content:
      "PTO requests should be submitted through the HR portal at least two weeks in advance for absences of three days or more. Managers are expected to respond within two business days. Company-wide holidays are published each November for the following year.",
    snippet: "submitted through the HR portal at least two weeks in advance",
  },
  {
    chunk_id: "chk_hb_5",
    document_id: "doc_handbook",
    page_numbers: [3],
    heading: "About This Handbook",
    content:
      "This handbook describes the policies, benefits, and expectations that apply to all employees of Northwind Labs, including compensation, time off, remote work, equipment, and professional conduct. Where local law provides greater benefits, local law takes precedence.",
    snippet: "describes the policies, benefits, and expectations that apply to all employees",
  },
  {
    chunk_id: "chk_sec_1",
    document_id: "doc_security",
    page_numbers: [4],
    heading: "Access Control",
    content:
      "Access to production systems is granted on a least-privilege basis and must be approved by both the system owner and the employee's manager. Access reviews are performed quarterly, and dormant accounts are disabled automatically after 30 days of inactivity.",
    snippet: "granted on a least-privilege basis and must be approved by both the system owner and the employee's manager",
  },
  {
    chunk_id: "chk_sec_2",
    document_id: "doc_security",
    page_numbers: [7],
    heading: "Authentication Requirements",
    content:
      "Multi-factor authentication (MFA) is mandatory for all company accounts. Passwords must be at least 14 characters long and must not be reused across services. Hardware security keys are required for all administrators and anyone with production access.",
    snippet: "Multi-factor authentication (MFA) is mandatory for all company accounts.",
  },
  {
    chunk_id: "chk_sec_3",
    document_id: "doc_security",
    page_numbers: [11, 12],
    heading: "Incident Response",
    content:
      "Suspected security incidents must be reported to security@northwind.dev or via the #sec-incidents channel within 1 hour of discovery. Do not attempt to investigate, power off, or wipe affected devices; disconnect them from the network and wait for the on-call responder, who will preserve evidence and coordinate next steps.",
    snippet: "must be reported to security@northwind.dev or via the #sec-incidents channel within 1 hour of discovery",
  },
  {
    chunk_id: "chk_sec_4",
    document_id: "doc_security",
    page_numbers: [13],
    heading: "Severity Classification",
    content:
      "Incidents are classified from SEV-1 (customer data exposure or full outage) to SEV-4 (minor policy deviation). SEV-1 incidents trigger executive notification within 30 minutes and customer communication within 72 hours where required by law.",
    snippet: "SEV-1 incidents trigger executive notification within 30 minutes",
  },
  {
    chunk_id: "chk_api_1",
    document_id: "doc_api",
    page_numbers: [4],
    heading: "Authentication",
    content:
      "All API requests must include a bearer token in the Authorization header. Tokens are issued via the OAuth 2.0 client credentials flow at POST /oauth/token and expire after 60 minutes. Store client secrets in a secrets manager and never commit them to source control.",
    snippet: "Tokens are issued via the OAuth 2.0 client credentials flow at POST /oauth/token and expire after 60 minutes.",
  },
  {
    chunk_id: "chk_api_2",
    document_id: "doc_api",
    page_numbers: [6],
    heading: "Making Requests",
    content:
      "The base URL for all endpoints is https://api.northwind.dev/v2. Requests and responses use JSON. Include the header Content-Type: application/json for any request with a body, and pass an Idempotency-Key header on POST requests to make retries safe.",
    snippet: "pass an Idempotency-Key header on POST requests to make retries safe",
  },
  {
    chunk_id: "chk_api_3",
    document_id: "doc_api",
    page_numbers: [9],
    heading: "Rate Limits",
    content:
      "The default rate limit is 600 requests per minute per organization. Responses include X-RateLimit-Remaining and X-RateLimit-Reset headers. When a 429 status is returned, clients should retry with exponential backoff starting at 1 second, up to a maximum of 5 attempts.",
    snippet: "The default rate limit is 600 requests per minute per organization.",
  },
  {
    chunk_id: "chk_api_4",
    document_id: "doc_api",
    page_numbers: [15],
    heading: "Webhooks",
    content:
      "Webhook payloads are signed with HMAC-SHA256 using your endpoint secret. Verify the X-Signature header against the raw request body before processing, and reject any event whose timestamp is older than 5 minutes to prevent replay attacks.",
    snippet: "signed with HMAC-SHA256 using your endpoint secret",
  },
]

export interface SeedConversation {
  session: ChatSession
  question: string
}

export const SEED_CONVERSATIONS: SeedConversation[] = [
  {
    session: {
      id: "ses_q3",
      title: "Q3 revenue and margin analysis",
      created_at: ago(2 * HOUR),
      updated_at: ago(2 * HOUR),
    },
    question: "Summarize key financial metrics from Q3 report",
  },
  {
    session: {
      id: "ses_leave",
      title: "Parental leave eligibility",
      created_at: ago(5 * HOUR),
      updated_at: ago(5 * HOUR),
    },
    question: "What are the employee leave policies?",
  },
  {
    session: {
      id: "ses_api",
      title: "API authentication flow",
      created_at: ago(DAY + 3 * HOUR),
      updated_at: ago(DAY + 3 * HOUR),
    },
    question: "How do I authenticate with the platform API?",
  },
  {
    session: {
      id: "ses_incident",
      title: "Security incident escalation",
      created_at: ago(3 * DAY),
      updated_at: ago(3 * DAY),
    },
    question: "What should I do during a security incident?",
  },
  {
    session: {
      id: "ses_rate",
      title: "Handling 429 rate limit errors",
      created_at: ago(5 * DAY),
      updated_at: ago(5 * DAY),
    },
    question: "How should we handle API rate limits?",
  },
]

export const PROMPT_STARTERS = [
  { title: "Summarize key financial metrics", subtitle: "from the Q3 report", prompt: "Summarize key financial metrics from Q3 report" },
  { title: "What are the employee leave policies?", subtitle: "PTO, sick, and parental leave", prompt: "What are the employee leave policies?" },
  { title: "How do I authenticate with the API?", subtitle: "with a working code sample", prompt: "How do I authenticate with the platform API?" },
  { title: "What should I do during a security incident?", subtitle: "reporting and escalation steps", prompt: "What should I do during a security incident?" },
]
