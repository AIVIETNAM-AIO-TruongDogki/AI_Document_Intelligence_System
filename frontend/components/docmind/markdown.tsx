"use client"

import { memo, useMemo } from "react"
import ReactMarkdown, { type Components } from "react-markdown"
import rehypeHighlight from "rehype-highlight"
import remarkGfm from "remark-gfm"
import type { CitationSource } from "@/lib/docmind/types"
import { cn } from "@/lib/utils"
import { CitationBadge } from "./citation-badge"
import { CodeBlock } from "./code-block"

const CITE_PREFIX = "#cite-"

/** Turns `[n]` markers into links outside of code fences so they can render as citation badges. */
function linkCitations(content: string) {
  return content
    .split(/(```[\s\S]*?(?:```|$))/g)
    .map((part, i) => (i % 2 === 1 ? part : part.replace(/\[(\d{1,2})\](?!\()/g, `[$1](${CITE_PREFIX}$1)`)))
    .join("")
}

interface MarkdownProps {
  content: string
  sources: CitationSource[]
  streaming: boolean
  onOpenSource: (source: CitationSource) => void
}

export const Markdown = memo(function Markdown({ content, sources, streaming, onOpenSource }: MarkdownProps) {
  const processed = useMemo(() => linkCitations(content), [content])

  const components = useMemo<Components>(
    () => ({
      a({ href, children, ...props }) {
        if (href?.startsWith(CITE_PREFIX)) {
          const index = Number(href.slice(CITE_PREFIX.length))
          const source = sources.find((s) => s.source_index === index)
          if (source) return <CitationBadge source={source} onOpen={() => onOpenSource(source)} />
          return <sup className="text-muted-foreground">[{index}]</sup>
        }
        return (
          <a href={href} target="_blank" rel="noreferrer" {...props}>
            {children}
          </a>
        )
      },
      pre({ children }) {
        return <CodeBlock>{children}</CodeBlock>
      },
      table({ children }) {
        return (
          <div className="overflow-x-auto rounded-lg border border-border">
            <table>{children}</table>
          </div>
        )
      },
    }),
    [sources, onOpenSource],
  )

  return (
    <div className={cn("dm-prose", streaming && "dm-streaming")}>
      <ReactMarkdown remarkPlugins={[remarkGfm]} rehypePlugins={[[rehypeHighlight, { detect: false }]]} components={components}>
        {processed}
      </ReactMarkdown>
    </div>
  )
})
