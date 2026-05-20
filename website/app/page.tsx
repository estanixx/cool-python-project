import Link from "next/link";
import { Button } from "@/components/ui/button";

export default function HomePage() {
  return (
    <main className="min-h-screen bg-background flex items-center justify-center">
      <div className="flex flex-col items-center gap-6">
        <h1 className="text-3xl font-semibold tracking-tight">
          Cool Python App by Estanixx #3
        </h1>
        <div className="flex flex-col gap-4">
          <Link href="/dictionary">
            <Button variant="outline" className="w-48">
              📖 Dictionary
            </Button>
          </Link>
          <Link href="/shopping">
            <Button variant="outline" className="w-48">
              🛒 Shopping
            </Button>
          </Link>
          <Link href="/word-trick">
            <Button variant="outline" className="w-48">
              🔤 Word Trick
            </Button>
          </Link>
        </div>
      </div>
    </main>
  );
}
