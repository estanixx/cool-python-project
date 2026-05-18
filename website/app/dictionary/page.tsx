import { api } from "@/lib/api-client";
import { DictionaryEntry, DictionaryList } from "@/types/api";
import HomeNav from "@/components/home-nav";
import DictionaryClient from "@/components/dictionary-client";

async function fetchEntries(): Promise<DictionaryEntry[]> {
  try {
    const data = await api<DictionaryList>("/dictionary?operation=list");
    return data.entries ?? [];
  } catch {
    return [];
  }
}

export default async function DictionaryPage() {
  const entries = await fetchEntries();

  return (
    <main className="min-h-screen bg-background p-6">
      <div className="max-w-2xl mx-auto space-y-6">
        <HomeNav />
        <h1 className="text-2xl font-semibold tracking-tight">Dictionary</h1>
        <DictionaryClient initialEntries={entries} />
      </div>
    </main>
  );
}
