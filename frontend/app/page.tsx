import { AppShell } from "@/components/docmind/app-shell"
import { DocMindProvider } from "@/components/docmind/docmind-provider"

export default function Page() {
  return (
    <DocMindProvider>
      <AppShell />
    </DocMindProvider>
  )
}
