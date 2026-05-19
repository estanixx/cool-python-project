import { api } from "@/lib/api-client";
import { DictionaryEntry, DictionaryEntryRaw, normalizeEntry } from "@/types/api";
import HomeNav from "@/components/home-nav";
import DictionaryClient from "@/components/dictionary-client";

async function fetchEntries(): Promise<{
  entries: DictionaryEntry[];
  error: boolean;
}> {
  try {
    const data = await api<{ entries: DictionaryEntryRaw[] }>(
      "/dictionary?operation=list"
    );
    return { entries: (data.entries ?? []).map(normalizeEntry), error: false };
  } catch {
    return { entries: [], error: true };
  }
}

export default async function DictionaryPage() {
  const { entries, error: fetchError } = await fetchEntries();

  return (
    <main className="min-h-screen bg-background p-6">
      <div className="max-w-2xl mx-auto space-y-6">
        <HomeNav />
        <h1 className="text-2xl font-semibold tracking-tight">Dictionary</h1>
        <DictionaryClient initialEntries={entries} initialError={fetchError} />
      </div>
    </main>
  );
}
