"use client"

import { createContext, useCallback, useContext, useEffect, useMemo, useRef, useState } from "react"
import { toast } from "sonner"
import { createId, deriveSessionTitle } from "@/lib/docmind/format"
import { checkHealthStatus } from "@/src/api/health"
import { deleteDocument as apiDeleteDocument, listDocuments, uploadDocument } from "@/src/api/documents"
import { getJobStatus } from "@/src/api/jobs"
import {
  deleteChatSession as apiDeleteChatSession,
  getChatSessionDetail,
  listChatSessions,
  sendChatMessage,
} from "@/src/api/chat"
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

export function DocMindProvider({ children }: { children: React.ReactNode }) {
  const [documents, setDocuments] = useState<DocumentItem[]>([])
  const [jobs, setJobsState] = useState<IngestionJob[]>([])
  const jobsRef = useRef<IngestionJob[]>([])
  const [sessions, setSessions] = useState<ChatSession[]>([])
  const [messagesBySession, setMessagesBySession] = useState<Record<string, ChatMessage[]>>({})
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

  // 1. Kiểm tra trạng thái Backend theo chu kỳ
  useEffect(() => {
    let cancelled = false
    const ping = async () => {
      try {
        const res = await checkHealthStatus()
        if (!cancelled) {
          setApiStatus(res.ok ? { state: "connected", latency: res.latency } : { state: "offline" })
        }
      } catch {
        if (!cancelled) setApiStatus({ state: "offline" })
      }
    }

    const initial = setTimeout(ping, 200)
    const interval = setInterval(ping, 10000)
    return () => {
      cancelled = true
      clearTimeout(initial)
      clearInterval(interval)
    }
  }, [])

  // 2. Tải danh sách tài liệu và phiên chat từ Backend CSDL khi khởi chạy
  useEffect(() => {
    let cancelled = false
    const loadInitialData = async () => {
      try {
        const [docsRes, sessionsRes] = await Promise.allSettled([
          listDocuments(),
          listChatSessions(),
        ])

        if (!cancelled && docsRes.status === "fulfilled") {
          const mappedDocs: DocumentItem[] = docsRes.value.map((d) => ({
            document_id: d.document_id,
            filename: d.filename,
            file_size: d.file_size,
            page_count: d.page_count,
            created_at: new Date().toISOString(),
          }))
          setDocuments(mappedDocs)
        }

        if (!cancelled && sessionsRes.status === "fulfilled") {
          const mappedSessions: ChatSession[] = sessionsRes.value.map((s) => ({
            id: s.id,
            title: s.title,
            created_at: s.created_at,
            updated_at: s.updated_at,
          }))
          setSessions(mappedSessions)
        }
      } catch (e) {
        console.error("Không thể tải dữ liệu khởi tạo từ Backend:", e)
      }
    }

    loadInitialData()
    return () => {
      cancelled = true
    }
  }, [])

  // 3. Xử lý tải lên file PDF thật lên Backend API (hỗ trợ nền & polling)
  const uploadFiles = useCallback(
    async (fileList: FileList | File[]) => {
      const files = Array.from(fileList)

      for (const file of files) {
        const isPdf = file.type === "application/pdf" || file.name.toLowerCase().endsWith(".pdf")
        if (!isPdf) {
          toast.error("Định dạng không hỗ trợ", { description: `${file.name} không phải là tệp PDF.` })
          continue
        }
        if (file.size > MAX_UPLOAD_BYTES) {
          toast.error("Tệp quá lớn", { description: `${file.name} vượt quá giới hạn 50 MB.` })
          continue
        }

        const tempJobId = createId("job")
        const initialJob: IngestionJob = {
          job_id: tempJobId,
          document_id: "",
          status: "PENDING",
          progress: 5,
          error_message: null,
          filename: file.name,
          file_size: file.size,
        }

        setJobs([initialJob, ...jobsRef.current])
        toast.info(`Đang tải lên ${file.name}...`)

        try {
          const res = await uploadDocument(file)

          // Trường hợp 1: Backend xử lý bất đồng bộ (HTTP 202 trả về job_id)
          if ("job_id" in res) {
            const backendJobId = res.job_id
            const docId = res.document_id

            // Cập nhật job_id thật từ server
            setJobs(
              jobsRef.current.map((j) =>
                j.job_id === tempJobId
                  ? { ...j, job_id: backendJobId, document_id: docId, status: res.status, progress: 10 }
                  : j
              )
            )

            // Khởi chạy polling kiểm tra tiến độ mỗi 1.2s
            const pollInterval = 1200
            const maxAttempts = 150
            let attempts = 0

            const timer = setInterval(async () => {
              attempts++
              try {
                const jobStatus = await getJobStatus(backendJobId)

                setJobs(
                  jobsRef.current.map((j) =>
                    j.job_id === backendJobId
                      ? {
                          ...j,
                          status: jobStatus.status,
                          progress: jobStatus.progress,
                          error_message: jobStatus.error_message,
                        }
                      : j
                  )
                )

                if (jobStatus.status === "COMPLETED") {
                  clearInterval(timer)
                  try {
                    const freshDocs = await listDocuments()
                    setDocuments(
                      freshDocs.map((d) => ({
                        document_id: d.document_id,
                        filename: d.filename,
                        file_size: d.file_size,
                        page_count: d.page_count,
                        created_at: new Date().toISOString(),
                      }))
                    )
                  } catch (e) {
                    console.error("Không thể tải lại danh sách tài liệu sau khi hoàn thành:", e)
                  }
                  toast.success("Tài liệu đã lập chỉ mục thành công", {
                    description: `${file.name} đã sẵn sàng để tra cứu và hỏi đáp!`,
                  })
                } else if (jobStatus.status === "FAILED") {
                  clearInterval(timer)
                  toast.error("Lỗi xử lý tài liệu", {
                    description: jobStatus.error_message || "Xử lý tài liệu thất bại",
                  })
                } else if (attempts >= maxAttempts) {
                  clearInterval(timer)
                  setJobs(
                    jobsRef.current.map((j) =>
                      j.job_id === backendJobId
                        ? { ...j, status: "FAILED", error_message: "Quá thời gian xử lý (Timeout)" }
                        : j
                    )
                  )
                  toast.error("Quá thời gian xử lý", { description: `${file.name} xử lý quá lâu.` })
                }
              } catch {
                if (attempts >= maxAttempts) {
                  clearInterval(timer)
                }
              }
            }, pollInterval)
          } else {
            // Trường hợp 2: Backend xử lý đồng bộ (HTTP 201)
            const syncDoc = res
            const newDoc: DocumentItem = {
              document_id: syncDoc.document_id,
              filename: syncDoc.filename,
              file_size: file.size,
              page_count: syncDoc.page_count,
              created_at: new Date().toISOString(),
            }

            setDocuments((prev) => [newDoc, ...prev.filter((d) => d.document_id !== syncDoc.document_id)])
            setJobs(
              jobsRef.current.map((j) =>
                j.job_id === tempJobId
                  ? { ...j, status: "COMPLETED", progress: 100, document_id: syncDoc.document_id }
                  : j
              )
            )
            toast.success("Tài liệu đã lập chỉ mục thành công", {
              description: `${syncDoc.filename} (${syncDoc.page_count} trang, ${syncDoc.chunk_count} đoạn) đã sẵn sàng!`,
            })
          }
        } catch (err: unknown) {
          const message = err instanceof Error ? err.message : "Xử lý tài liệu thất bại"
          setJobs(
            jobsRef.current.map((j) =>
              j.job_id === tempJobId ? { ...j, status: "FAILED", error_message: message } : j
            )
          )
          toast.error("Lỗi tải lên tài liệu", { description: message })
        }
      }
    },
    [setJobs]
  )

  const dismissJob = useCallback(
    (jobId: string) => setJobs(jobsRef.current.filter((j) => j.job_id !== jobId)),
    [setJobs]
  )

  const clearFinishedJobs = useCallback(
    () => setJobs(jobsRef.current.filter((j) => j.status === "PENDING" || j.status === "PROCESSING")),
    [setJobs]
  )

  // 4. Xóa tài liệu thật từ CSDL Backend
  const deleteDocument = useCallback(
    async (documentId: string) => {
      const doc = documents.find((d) => d.document_id === documentId)
      try {
        await apiDeleteDocument(documentId)
        setDocuments((prev) => prev.filter((d) => d.document_id !== documentId))
        setSelectedDocIds((prev) => prev.filter((id) => id !== documentId))
        if (doc) toast.success("Đã xóa tài liệu", { description: doc.filename })
      } catch (err: unknown) {
        const message = err instanceof Error ? err.message : "Không thể xóa tài liệu"
        toast.error("Lỗi xóa tài liệu", { description: message })
      }
    },
    [documents]
  )

  const setScope = useCallback((next: ContextScope) => {
    setScopeState(next)
  }, [])

  const toggleDocument = useCallback((documentId: string) => {
    setScopeState("selected")
    setSelectedDocIds((prev) =>
      prev.includes(documentId) ? prev.filter((id) => id !== documentId) : [...prev, documentId]
    )
  }, [])

  const contextDocuments = useMemo(
    () => (scope === "all" ? documents : documents.filter((d) => selectedDocIds.includes(d.document_id))),
    [documents, scope, selectedDocIds]
  )

  const stopGeneration = useCallback(() => {
    abortRef.current?.abort()
  }, [])

  const newChat = useCallback(() => {
    abortRef.current?.abort()
    setActiveSessionId(null)
  }, [])

  // 5. Chọn phiên chat và tải tin nhắn lịch sử nếu chưa có trong bộ nhớ
  const selectSession = useCallback(
    async (id: string) => {
      abortRef.current?.abort()
      setActiveSessionId(id)

      if (!messagesBySession[id]) {
        try {
          const detail = await getChatSessionDetail(id)
          const mappedMessages: ChatMessage[] = (detail.messages || []).map((m) => ({
            id: m.id,
            role: m.role as "user" | "assistant",
            content: m.content,
            sources: m.sources as CitationSource[] | null,
            created_at: m.created_at,
          }))
          setMessagesBySession((prev) => ({ ...prev, [id]: mappedMessages }))
        } catch (err) {
          console.error("Không thể tải lịch sử tin nhắn:", err)
        }
      }
    },
    [messagesBySession]
  )

  const renameSession = useCallback((id: string, title: string) => {
    const trimmed = title.trim()
    if (!trimmed) return
    setSessions((prev) => prev.map((s) => (s.id === id ? { ...s, title: trimmed } : s)))
  }, [])

  // 6. Xóa phiên chat khỏi Backend CSDL
  const deleteSession = useCallback(
    async (id: string) => {
      if (id === activeSessionId) {
        abortRef.current?.abort()
        setActiveSessionId(null)
      }
      try {
        await apiDeleteChatSession(id)
        setSessions((prev) => prev.filter((s) => s.id !== id))
        setMessagesBySession((prev) => {
          const { [id]: _removed, ...rest } = prev
          return rest
        })
        toast.success("Đã xóa cuộc trò chuyện")
      } catch (err: unknown) {
        const message = err instanceof Error ? err.message : "Không thể xóa cuộc trò chuyện"
        toast.error("Lỗi xóa hội thoại", { description: message })
      }
    },
    [activeSessionId]
  )

  // 7. Gửi câu hỏi đến Backend RAG API thật
  const sendMessage = useCallback(
    async (text: string) => {
      const query = text.trim()
      if (!query || generation) return

      const now = new Date().toISOString()
      const initialSessionId = activeSessionId
      const tempSessionId = initialSessionId || createId("ses")

      if (!initialSessionId) {
        const newSessionItem: ChatSession = {
          id: tempSessionId,
          title: deriveSessionTitle(query),
          created_at: now,
          updated_at: now,
        }
        setSessions((prev) => [newSessionItem, ...prev])
        setActiveSessionId(tempSessionId)
      } else {
        setSessions((prev) =>
          prev.map((s) => (s.id === initialSessionId ? { ...s, updated_at: now } : s))
        )
      }

      const userMessage: ChatMessage = {
        id: createId("msg"),
        role: "user",
        content: query,
        created_at: now,
      }
      const assistantId = createId("msg")
      const assistantMessage: ChatMessage = {
        id: assistantId,
        role: "assistant",
        content: "",
        sources: null,
        created_at: now,
      }

      setMessagesBySession((prev) => ({
        ...prev,
        [tempSessionId]: [...(prev[tempSessionId] ?? []), userMessage, assistantMessage],
      }))
      setGeneration({ messageId: assistantId, phase: "retrieving" })

      const targetDocId =
        scope === "selected" && selectedDocIds.length > 0 ? selectedDocIds[0] : null

      try {
        const res = await sendChatMessage({
          query,
          document_id: targetDocId,
          session_id: initialSessionId || null,
        })

        const realSessionId = res.session_id
        const mappedSources: CitationSource[] = (res.sources || []).map((s) => {
          const foundDoc = documents.find((d) => d.document_id === s.document_id)
          return {
            source_index: s.source_index,
            chunk_id: s.chunk_id,
            document_id: s.document_id,
            filename: foundDoc?.filename,
            page_numbers: s.page_numbers,
            snippet: s.snippet,
          }
        })

        // Nếu tạo phiên mới, cập nhật ID thật từ Backend
        if (!initialSessionId && realSessionId !== tempSessionId) {
          setSessions((prev) =>
            prev.map((s) => (s.id === tempSessionId ? { ...s, id: realSessionId } : s))
          )
          setActiveSessionId(realSessionId)
          setMessagesBySession((prev) => {
            const prevMsgs = prev[tempSessionId] ?? [userMessage, assistantMessage]
            const updatedMsgs = prevMsgs.map((m) =>
              m.id === assistantId ? { ...m, content: res.answer, sources: mappedSources } : m
            )
            const { [tempSessionId]: _, ...rest } = prev
            return { ...rest, [realSessionId]: updatedMsgs }
          })
        } else {
          setMessagesBySession((prev) => ({
            ...prev,
            [realSessionId]: (prev[realSessionId] ?? []).map((m) =>
              m.id === assistantId ? { ...m, content: res.answer, sources: mappedSources } : m
            ),
          }))
        }
      } catch (error: unknown) {
        const errMessage =
          error instanceof Error ? error.message : "Không thể nhận phản hồi từ hệ thống RAG."
        setMessagesBySession((prev) => ({
          ...prev,
          [tempSessionId]: (prev[tempSessionId] ?? []).map((m) =>
            m.id === assistantId ? { ...m, content: `⚠️ **Lỗi:** ${errMessage}` } : m
          ),
        }))
        toast.error("Hỏi đáp thất bại", { description: errMessage })
      } finally {
        setGeneration(null)
      }
    },
    [activeSessionId, documents, generation, scope, selectedDocIds]
  )

  const value = useMemo<DocMindContextValue>(
    () => ({
      documents,
      jobs,
      sessions,
      messages: activeSessionId ? messagesBySession[activeSessionId] ?? [] : [],
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
    ]
  )

  return <DocMindContext.Provider value={value}>{children}</DocMindContext.Provider>
}
