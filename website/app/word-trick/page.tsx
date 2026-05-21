import HomeNav from "@/components/home-nav";
import WordTrickClient from "@/components/word-trick-client";

export default function WordTrickPage() {
  return (
    <main className="min-h-screen bg-background p-6">
      <div className="max-w-2xl mx-auto space-y-6">
        <HomeNav />
        <h1 className="text-2xl font-semibold tracking-tight">Word Trick</h1>
        <WordTrickClient />
      </div>
    </main>
  );
}
