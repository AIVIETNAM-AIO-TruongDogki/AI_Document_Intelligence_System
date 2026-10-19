import { SEED_CHUNKS, SEED_CONVERSATIONS, SEED_DOCUMENTS } from "./seed"
import type { ChatMessage, ChatSession, CitationSource, DocumentChunk, DocumentItem } from "./types"

/**
 * In-browser mock of the DocMind RAG backend. Each function mirrors an endpoint of the
 * real service and returns payloads that match the shared data contracts, so it can be
 * swapped for `fetch` calls without touching the UI.
 */

const chunkStore = new Map<string, DocumentChunk>(SEED_CHUNKS.map((c) => [c.chunk_id, c]))

export const API_BASE_URL = "https://api.docmind.dev/v1"

function sleep(ms: number, signal?: AbortSignal) {
  return new Promise<void>((resolve, reject) => {
    if (signal?.aborted) return reject(new DOMException("Aborted", "AbortError"))
    const timer = setTimeout(resolve, ms)
    signal?.addEventListener(
      "abort",
      () => {
        clearTimeout(timer)
        reject(new DOMException("Aborted", "AbortError"))
      },
      { once: true },
    )
  })
}

export function getChunk(chunkId: string) {
  return chunkStore.get(chunkId) ?? null
}

/** Simulates the chunking step that runs when an ingestion job completes. */
export function registerDocumentChunks(doc: DocumentItem) {
  const name = doc.filename.replace(/\.pdf$/i, "").replace(/[_-]+/g, " ")
  const sections = [
    {
      heading: "Overview",
      content: `${name} opens with an overview of its purpose, scope, and intended audience. It establishes the key definitions used throughout the document and summarizes the main obligations and decisions it covers.`,
      snippet: "an overview of its purpose, scope, and intended audience",
    },
    {
      heading: "Key Terms",
      content: `The core section of ${name} details the specific terms, figures, and responsibilities that apply. It lists effective dates, responsible parties, and the conditions under which the provisions can be amended or terminated.`,
      snippet: "details the specific terms, figures, and responsibilities that apply",
    },
    {
      heading: "Summary and Next Steps",
      content: `${name} closes with a summary of action items and next steps, including review deadlines and the contacts responsible for questions or escalations.`,
      snippet: "a summary of action items and next steps",
    },
  ]
  const pageStep = Math.max(1, Math.floor(doc.page_count / sections.length))
  sections.forEach((section, i) => {
    const chunk_id = `chk_${doc.document_id}_${i + 1}`
    chunkStore.set(chunk_id, {
      chunk_id,
      document_id: doc.document_id,
      page_numbers: [Math.min(doc.page_count, 1 + i * pageStep)],
      ...section,
    })
  })
}

interface ScriptedTopic {
  match: RegExp
  chunkIds: string[]
  content: string
}

const FENCE = "```"

const SCRIPTED_TOPICS: ScriptedTopic[] = [
  {
    match: /rate.?limit|429|throttl|backoff/i,
    chunkIds: ["chk_api_3", "chk_api_2"],
    content: [
      "The API allows **600 requests per minute per organization** by default. Every response includes `X-RateLimit-Remaining` and `X-RateLimit-Reset` headers you can use to pace traffic [1].",
      "",
      "When you receive a `429`, retry with **exponential backoff** starting at 1 second, up to 5 attempts [1]:",
      "",
      `${FENCE}ts`,
      "async function withBackoff(fn: () => Promise<Response>, attempts = 5) {",
      "  for (let i = 0; i < attempts; i++) {",
      "    const res = await fn()",
      "    if (res.status !== 429) return res",
      "    await new Promise((r) => setTimeout(r, 1000 * 2 ** i))",
      "  }",
      '  throw new Error("Rate limit retries exhausted")',
      "}",
      FENCE,
      "",
      "Pair retries on POST requests with an `Idempotency-Key` header so a retried write is never applied twice [2].",
    ].join("\n"),
  },
  {
    match: /financ|revenue|q3|metric|margin|earning|arr\b|cash/i,
    chunkIds: ["chk_fin_1", "chk_fin_2", "chk_fin_3", "chk_fin_4"],
    content: [
      "Here are the key financial metrics from the **Q3 2026 Financial Report**:",
      "",
      "### Growth",
      "- **Revenue:** $48.2M, up **23% YoY** and 7% QoQ, driven by enterprise expansion in North America and EMEA [1].",
      "- **ARR:** closed the quarter at **$186.5M**, with platform revenue now 64% of the total [1].",
      "",
      "### Profitability",
      "| Metric | Q3 2026 | Change |",
      "| --- | --- | --- |",
      "| Gross margin | 78.4% | +3.3 pts vs Q2 |",
      "| Operating margin | 12.6% | 3rd positive quarter |",
      "| Free cash flow | $9.8M | — |",
      "",
      "Margin gains came from infrastructure cost optimizations and a higher mix of platform revenue [2].",
      "",
      "### Customers",
      "Net revenue retention was **118%** with gross retention at 94%. The company added 312 net new customers (4,870 total), and $100K+ ARR customers grew 31% to 412 [3].",
      "",
      "### Outlook",
      "Q4 revenue guidance is **$51.0M–$52.5M**, implying full-year revenue of $184M–$186M, with operating margin expected to stay above 10% [4].",
    ].join("\n"),
  },
  {
    match: /leave|vacation|pto|time off|holiday|parental|maternity|paternity|sick/i,
    chunkIds: ["chk_hb_1", "chk_hb_3", "chk_hb_2", "chk_hb_4"],
    content: [
      "The **Employee Handbook 2026** defines three main types of leave:",
      "",
      "1. **Paid time off (PTO)** — Full-time employees accrue 1.67 days per month, or **20 days per year**. Up to 5 unused days carry over; the rest are forfeited on December 31 [1].",
      "2. **Sick leave** — **10 paid sick days** per year that do not roll over. Absences longer than three consecutive working days require a note from a healthcare provider, and sick days can be used to care for immediate family [2].",
      "3. **Parental leave** — After 90 days of tenure, employees are eligible for **16 weeks of fully paid leave**, which can be split into up to two blocks within 12 months. A phased return at a 60% schedule is available for four weeks [3].",
      "",
      "> **How to request:** submit PTO through the HR portal at least two weeks ahead for absences of three days or more. Managers should respond within two business days [4].",
    ].join("\n"),
  },
  {
    match: /api|authenticat|oauth|token|integrat|endpoint|webhook|sdk/i,
    chunkIds: ["chk_api_1", "chk_api_2", "chk_api_4"],
    content: [
      "The platform API uses the **OAuth 2.0 client credentials** flow. Exchange your client ID and secret at `POST /oauth/token` for a bearer token, which expires after **60 minutes** [1].",
      "",
      `${FENCE}ts`,
      'const tokenRes = await fetch("https://api.northwind.dev/oauth/token", {',
      '  method: "POST",',
      '  headers: { "Content-Type": "application/x-www-form-urlencoded" },',
      "  body: new URLSearchParams({",
      '    grant_type: "client_credentials",',
      "    client_id: process.env.NW_CLIENT_ID!,",
      "    client_secret: process.env.NW_CLIENT_SECRET!,",
      "  }),",
      "})",
      "const { access_token } = await tokenRes.json()",
      "",
      "// Use the token on every request to the v2 API",
      'const res = await fetch("https://api.northwind.dev/v2/projects", {',
      '  headers: { Authorization: "Bearer " + access_token },',
      "})",
      FENCE,
      "",
      "A few requirements from the guide:",
      "- All endpoints live under `https://api.northwind.dev/v2` and use JSON. Send an `Idempotency-Key` header on POST requests so retries are safe [2].",
      "- Store client secrets in a secrets manager and never commit them to source control [1].",
      "- If you consume webhooks, verify the `X-Signature` HMAC-SHA256 header against the raw body and reject events older than 5 minutes [3].",
    ].join("\n"),
  },
  {
    match: /security|incident|breach|phish|password|mfa|access|sev/i,
    chunkIds: ["chk_sec_3", "chk_sec_4", "chk_sec_2"],
    content: [
      "According to the **Information Security Policy**, follow these steps when you suspect a security incident:",
      "",
      "1. **Report within 1 hour** of discovery to `security@northwind.dev` or the `#sec-incidents` Slack channel [1].",
      "2. **Do not investigate, power off, or wipe** affected devices. Disconnect them from the network and wait for the on-call responder, who preserves evidence and coordinates next steps [1].",
      "3. **Expect a severity rating.** Incidents range from SEV-1 (customer data exposure or full outage) to SEV-4 (minor policy deviation). SEV-1 triggers executive notification within **30 minutes** and customer communication within 72 hours where legally required [2].",
      "",
      "As a preventive baseline, MFA is mandatory on every company account, passwords must be at least 14 characters, and administrators must use hardware security keys [3].",
    ].join("\n"),
  },
]

function toSources(chunks: DocumentChunk[], documents: DocumentItem[]): CitationSource[] {
  return chunks.map((chunk, i) => ({
    source_index: i + 1,
    chunk_id: chunk.chunk_id,
    document_id: chunk.document_id,
    filename: documents.find((d) => d.document_id === chunk.document_id)?.filename,
    page_numbers: chunk.page_numbers,
    snippet: chunk.snippet,
  }))
}

const STOP_WORDS = new Set(
  "a an and are as at be by can do does for from how i in is it me of on or our should the this to us we what when where which who why with you your".split(
    " ",
  ),
)

function tokenize(text: string) {
  return text
    .toLowerCase()
    .split(/[^a-z0-9$%]+/)
    .filter((t) => t.length > 2 && !STOP_WORDS.has(t))
}

function prettyName(filename: string) {
  return filename.replace(/\.pdf$/i, "").replace(/_/g, " ")
}

export function planAnswer(query: string, documents: DocumentItem[]): { content: string; sources: CitationSource[] } {
  if (documents.length === 0) {
    return {
      content:
        "There are no documents in the current context yet. Upload a PDF from the **Knowledge Base** panel, or switch the scope back to **All documents**, and I'll answer with citations from your files.",
      sources: [],
    }
  }

  const docIds = new Set(documents.map((d) => d.document_id))
  const chunksInScope = [...chunkStore.values()].filter((c) => docIds.has(c.document_id))

  if (/summar|overview|what.*(documents|files|knowledge)/i.test(query) && !/q3|financ|revenue/i.test(query)) {
    const picks = documents
      .map((d) => chunksInScope.find((c) => c.document_id === d.document_id))
      .filter((c): c is DocumentChunk => Boolean(c))
      .slice(0, 5)
    const lines = picks.map((chunk, i) => {
      const doc = documents.find((d) => d.document_id === chunk.document_id)!
      return `- **${prettyName(doc.filename)}** (${doc.page_count} pages): ${chunk.content.split(". ")[0]}. [${i + 1}]`
    })
    return {
      content: [
        `Your knowledge base currently has **${documents.length} document${documents.length === 1 ? "" : "s"}** in scope:`,
        "",
        ...lines,
        "",
        "Ask a follow-up about any of these and I'll pull the exact passages.",
      ].join("\n"),
      sources: toSources(picks, documents),
    }
  }

  for (const topic of SCRIPTED_TOPICS) {
    if (!topic.match.test(query)) continue
    const chunks = topic.chunkIds.map((id) => chunkStore.get(id)!).filter((c) => docIds.has(c.document_id))
    if (chunks.length === topic.chunkIds.length) {
      return { content: topic.content, sources: toSources(chunks, documents) }
    }
  }

  const queryTokens = new Set(tokenize(query))
  const ranked = chunksInScope
    .map((chunk) => {
      const tokens = tokenize(`${chunk.heading} ${chunk.content}`)
      const score = tokens.reduce((s, t) => s + (queryTokens.has(t) ? 1 : 0), 0)
      return { chunk, score }
    })
    .filter((r) => r.score > 0)
    .sort((a, b) => b.score - a.score)
    .slice(0, 3)
    .map((r) => r.chunk)

  if (ranked.length === 0) {
    return {
      content: [
        "I couldn't find passages in the selected documents that directly answer that question.",
        "",
        "Try rephrasing with terms that are likely to appear in the source files, or widen the context to **All documents**.",
      ].join("\n"),
      sources: [],
    }
  }

  const bullets = ranked.map((chunk, i) => `- **${chunk.heading}:** ${chunk.content} [${i + 1}]`)
  return {
    content: ["Here's what I found in your documents:", "", ...bullets].join("\n"),
    sources: toSources(ranked, documents),
  }
}

interface StreamChatOptions {
  query: string
  documents: DocumentItem[]
  signal: AbortSignal
  onSources: (sources: CitationSource[]) => void
  onDelta: (content: string) => void
}

/** Mirrors `POST /chat/stream`: retrieval first, then token-by-token generation. */
export async function streamChat({ query, documents, signal, onSources, onDelta }: StreamChatOptions) {
  await sleep(650 + Math.random() * 400, signal)
  const { content, sources } = planAnswer(query, documents)
  onSources(sources)

  const tokens = content.match(/\S+\s*|\s+/g) ?? []
  let acc = ""
  for (let i = 0; i < tokens.length; i += 2) {
    acc += tokens.slice(i, i + 2).join("")
    onDelta(acc)
    await sleep(22 + Math.random() * 18, signal)
  }
  return { content, sources }
}

export async function checkHealth(): Promise<{ ok: boolean; latency: number }> {
  const latency = Math.round(28 + Math.random() * 60)
  await sleep(latency)
  return { ok: true, latency }
}

export function buildSeedConversations(): { sessions: ChatSession[]; messages: Record<string, ChatMessage[]> } {
  const messages: Record<string, ChatMessage[]> = {}
  for (const { session, question } of SEED_CONVERSATIONS) {
    const answer = planAnswer(question, SEED_DOCUMENTS)
    messages[session.id] = [
      { id: `${session.id}_u`, role: "user", content: question, created_at: session.created_at },
      {
        id: `${session.id}_a`,
        role: "assistant",
        content: answer.content,
        sources: answer.sources,
        created_at: session.updated_at,
      },
    ]
  }
  return { sessions: SEED_CONVERSATIONS.map((c) => c.session), messages }
}
