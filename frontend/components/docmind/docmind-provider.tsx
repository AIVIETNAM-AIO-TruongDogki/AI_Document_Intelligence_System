"use client"

import { createContext, useCallback, useContext, useEffect, useMemo, useRef, useState } from "react"
import { toast } from "sonner"
import { createId, deriveSessionTitle } from "@/lib/docmind/format"
import { buildSeedConversations, checkHealth, registerDocumentChunks, streamChat } from "@/lib/docmind/mock-api"
import { SEED_DOCUMENTS, SEED_JOBS } from "@/lib/docmind/seed"
import type {
  ApiStatus,
  ChatMessage,
  ChatSession,
  CitationSource,
  ContextScope,
  DocumentItem,
  IngestionJob,
} from "@/lib/docmind/types"

const MAX_UPLOAD_BYTES = 50 * 1024 * 1024

type GenerationPhase = "retrieving" | "streaming"

interface DocMindContextValue {
  documents: DocumentItem[]
  jobs: IngestionJob[]
  sessions: ChatSession[]
  messages: ChatMessage[]
  activeSession: ChatSession | null
  activeSessionId: string | null
  scope: ContextScope
  selectedDocIds: string[]
  contextDocuments: DocumentItem[]
  apiStatus: ApiStatus
  generation: { messageId: string; phase: GenerationPhase } | null
  newChat: () => void
  selectSession: (id: string) => void
  renameSession: (id: string, title: string) => void
  deleteSession: (id: string) => void
  uploadFiles: (files: FileList | File[]) => void
  dismissJob: (jobId: string) => void
  clearFinishedJobs: () => void
  deleteDocument: (documentId: string) => void
  setScope: (scope: ContextScope) => void
  toggleDocument: (documentId: string) => void
  sendMessage: (text: string) => void
  stopGeneration: () => void
}

const DocMindContext = createContext<DocMindContextValue | null>(null)

export function useDocMind() {
  const ctx = useContext(DocMindContext)
  if (!ctx) throw new Error("useDocMind must be used within DocMindProvider")
  return ctx
}

const seed = buildSeedConversations()

export function DocMindProvider({ children }: { children: React.ReactNode }) {
  const [documents, setDocuments] = useState<DocumentItem[]>(SEED_DOCUMENTS)
  const [jobs, setJobsState] = useState<IngestionJob[]>(SEED_JOBS)
  const jobsRef = useRef<IngestionJob[]>(SEED_JOBS)
  const failurePlan = useRef(new Map<string, number>())
  const [sessions, setSessions] = useState<ChatSession[]>(seed.sessions)
  const [messagesBySession, setMessagesBySession] = useState<Record<string, ChatMessage[]>>(seed.messages)
  const [activeSessionId, setActiveSessionId] = useState<string | null>(null)
  const [scope, setScopeState] = useState<ContextScope>("all")
  const [selectedDocIds, setSelectedDocIds] = useState<string[]>([])
  const [apiStatus, setApiStatus] = useState<ApiStatus>({ state: "checking" })
  const [generation, setGeneration] = useState<DocMindContextValue["generation"]>(null)
  const abortRef = useRef<AbortController | null>(null)

  const setJobs = useCallback((next: IngestionJob[]) => {
    jobsRef.current = next
    setJobsState(next)
  }, [])

  useEffect(() => {
    let cancelled = false
    const ping = async () => {
      try {
        const res = await checkHealth()
        if (!cancelled) setApiStatus(res.ok ? { state: "connected", latency: res.latency } : { state: "offline" })
      } catch {
        if (!cancelled) setApiStatus({ state: "offline" })
      }
    }
    const initial = setTimeout(ping, 700)
    const interval = setInterval(ping, 15000)
    return () => {
      cancelled = true
      clearTimeout(initial)
      clearInterval(interval)
    }
  }, [])

  const hasActiveJobs = jobs.some((j) => j.status === "PENDING" || j.status === "PROCESSING")

  useEffect(() => {
    if (!hasActiveJobs) return
    const interval = setInterval(() => {
      const finished: DocumentItem[] = []
      const failed: IngestionJob[] = []

      const next = jobsRef.current.map((job): IngestionJob => {
        if (job.status === "PENDING") {
          return Math.random() > 0.45 ? { ...job, status: "PROCESSING", progress: 3 } : job
        }
        if (job.status !== "PROCESSING") return job

        const progress = Math.min(100, job.progress + Math.round(4 + Math.random() * 9))
        const failAt = failurePlan.current.get(job.job_id)
        if (failAt !== undefined && progress >= failAt) {
          const failedJob: IngestionJob = {
            ...job,
            status: "FAILED",
            progress: failAt,
            error_message: "Embedding service timed out while indexing chunks. Please retry the upload.",
          }
          failed.push(failedJob)
          return failedJob
        }
        if (progress >= 100) {
          finished.push({
            document_id: job.document_id,
            filename: job.filename,
            file_size: job.file_size,
            page_count: Math.max(1, Math.round(job.file_size / 160_000)),
            created_at: new Date().toISOString(),
          })
          return { ...job, status: "COMPLETED", progress: 100 }
        }
        return { ...job, progress }
      })

      setJobs(next)

      if (finished.length > 0) {
        finished.forEach(registerDocumentChunks)
        setDocuments((prev) => [...finished, ...prev])
        finished.forEach((doc) =>
          toast.success("Document indexed", { description: `${doc.filename} is ready to query.` }),
        )
      }
      failed.forEach((job) => toast.error("Ingestion failed", { description: job.filename }))
    }, 500)
    return () => clearInterval(interval)
  }, [hasActiveJobs, setJobs])

  const uploadFiles = useCallback(
    (fileList: FileList | File[]) => {
      const files = Array.from(fileList)
      const accepted: IngestionJob[] = []

      for (const file of files) {
        const isPdf = file.type === "application/pdf" || file.name.toLowerCase().endsWith(".pdf")
        if (!isPdf) {
          toast.error("Unsupported file type", { description: `${file.name} is not a PDF.` })
          continue
        }
        if (file.size > MAX_UPLOAD_BYTES) {
          toast.error("File too large", { description: `${file.name} exceeds the 50 MB limit.` })
          continue
        }
        const job: IngestionJob = {
          job_id: createId("job"),
          document_id: createId("doc"),
          status: "PENDING",
          progress: 0,
          error_message: null,
          filename: file.name,
          file_size: file.size,
        }
        if (Math.random() < 0.12) failurePlan.current.set(job.job_id, 40 + Math.round(Math.random() * 40))
        accepted.push(job)
      }

      if (accepted.length > 0) {
        setJobs([...accepted, ...jobsRef.current])
        toast(`Uploading ${accepted.length} file${accepted.length > 1 ? "s" : ""}`, {
          description: "Ingestion jobs queued for processing.",
        })
      }
    },
    [setJobs],
  )

  const dismissJob = useCallback(
    (jobId: string) => setJobs(jobsRef.current.filter((j) => j.job_id !== jobId)),
    [setJobs],
  )

  const clearFinishedJobs = useCallback(
    () => setJobs(jobsRef.current.filter((j) => j.status === "PENDING" || j.status === "PROCESSING")),
    [setJobs],
  )

  const deleteDocument = useCallback(
    (documentId: string) => {
      const doc = documents.find((d) => d.document_id === documentId)
      setDocuments((prev) => prev.filter((d) => d.document_id !== documentId))
      setSelectedDocIds((prev) => prev.filter((id) => id !== documentId))
      if (doc) toast.success("Document deleted", { description: doc.filename })
    },
    [documents],
  )

  const setScope = useCallback((next: ContextScope) => {
    setScopeState(next)
  }, [])

  const toggleDocument = useCallback((documentId: string) => {
    setScopeState("selected")
    setSelectedDocIds((prev) =>
      prev.includes(documentId) ? prev.filter((id) => id !== documentId) : [...prev, documentId],
    )
  }, [])

  const contextDocuments = useMemo(
    () => (scope === "all" ? documents : documents.filter((d) => selectedDocIds.includes(d.document_id))),
    [documents, scope, selectedDocIds],
  )

  const stopGeneration = useCallback(() => {
    abortRef.current?.abort()
  }, [])

  const newChat = useCallback(() => {
    abortRef.current?.abort()
    setActiveSessionId(null)
  }, [])

  const selectSession = useCallback((id: string) => {
    abortRef.current?.abort()
    setActiveSessionId(id)
  }, [])

  const renameSession = useCallback((id: string, title: string) => {
    const trimmed = title.trim()
    if (!trimmed) return
    setSessions((prev) => prev.map((s) => (s.id === id ? { ...s, title: trimmed } : s)))
  }, [])

  const deleteSession = useCallback(
    (id: string) => {
      if (id === activeSessionId) {
        abortRef.current?.abort()
        setActiveSessionId(null)
      }
      setSessions((prev) => prev.filter((s) => s.id !== id))
      setMessagesBySession((prev) => {
        const { [id]: _removed, ...rest } = prev
        return rest
      })
      toast.success("Chat deleted")
    },
    [activeSessionId],
  )

  const sendMessage = useCallback(
    async (text: string) => {
      const query = text.trim()
      if (!query || generation) return

      const now = new Date().toISOString()
      let sessionId = activeSessionId
      if (!sessionId) {
        const session: ChatSession = { id: createId("ses"), title: deriveSessionTitle(query), created_at: now, updated_at: now }
        sessionId = session.id
        setSessions((prev) => [session, ...prev])
        setActiveSessionId(session.id)
      } else {
        const id = sessionId
        setSessions((prev) => prev.map((s) => (s.id === id ? { ...s, updated_at: now } : s)))
      }

      const sid = sessionId
      const assistantId = createId("msg")
      const userMessage: ChatMessage = { id: createId("msg"), role: "user", content: query, created_at: now }
      const assistantMessage: ChatMessage = { id: assistantId, role: "assistant", content: "", sources: null, created_at: now }

      const patchAssistant = (patch: Partial<ChatMessage>) =>
        setMessagesBySession((prev) => ({
          ...prev,
          [sid]: (prev[sid] ?? []).map((m) => (m.id === assistantId ? { ...m, ...patch } : m)),
        }))

      setMessagesBySession((prev) => ({ ...prev, [sid]: [...(prev[sid] ?? []), userMessage, assistantMessage] }))
      setGeneration({ messageId: assistantId, phase: "retrieving" })

      const controller = new AbortController()
      abortRef.current = controller
      let streamed = ""

      try {
        await streamChat({
          query,
          documents: contextDocuments,
          signal: controller.signal,
          onSources: (sources: CitationSource[]) => {
            patchAssistant({ sources })
            setGeneration({ messageId: assistantId, phase: "streaming" })
          },
          onDelta: (content) => {
            streamed = content
            patchAssistant({ content })
          },
        })
      } catch (error) {
        if (error instanceof DOMException && error.name === "AbortError") {
          patchAssistant({ content: streamed ? `${streamed}\n\n_Generation stopped._` : "_Generation stopped before a response was produced._" })
        } else {
          patchAssistant({ content: "Something went wrong while generating a response. Please try again." })
          toast.error("Generation failed")
        }
      } finally {
        if (abortRef.current === controller) abortRef.current = null
        setGeneration(null)
      }
    },
    [activeSessionId, contextDocuments, generation],
  )

  const value = useMemo<DocMindContextValue>(
    () => ({
      documents,
      jobs,
      sessions,
      messages: activeSessionId ? (messagesBySession[activeSessionId] ?? []) : [],
      activeSession: sessions.find((s) => s.id === activeSessionId) ?? null,
      activeSessionId,
      scope,
      selectedDocIds,
      contextDocuments,
      apiStatus,
      generation,
      newChat,
      selectSession,
      renameSession,
      deleteSession,
      uploadFiles,
      dismissJob,
      clearFinishedJobs,
      deleteDocument,
      setScope,
      toggleDocument,
      sendMessage,
      stopGeneration,
    }),
    [
      documents,
      jobs,
      sessions,
      messagesBySession,
      activeSessionId,
      scope,
      selectedDocIds,
      contextDocuments,
      apiStatus,
      generation,
      newChat,
      selectSession,
      renameSession,
      deleteSession,
      uploadFiles,
      dismissJob,
      clearFinishedJobs,
      deleteDocument,
      setScope,
      toggleDocument,
      sendMessage,
      stopGeneration,
    ],
  )

  return <DocMindContext.Provider value={value}>{children}</DocMindContext.Provider>
}
