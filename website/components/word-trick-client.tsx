"use client";

import { useState } from "react";
import { api } from "@/lib/api-client";
import { WordTrickResult } from "@/types/api";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Card, CardHeader, CardTitle, CardContent } from "@/components/ui/card";

export default function WordTrickClient() {
  const [sentence, setSentence] = useState("");
  const [result, setResult] = useState<WordTrickResult | null>(null);
  const [message, setMessage] = useState("");
  const [loading, setLoading] = useState(false);

  const handleProcess = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!sentence.trim()) return;
    setLoading(true);
    setResult(null);
    setMessage("");
    try {
      const data = await api<WordTrickResult>("/word-trick", {
        method: "POST",
        body: JSON.stringify({ sentence }),
      });
      setResult(data);
    } catch (err) {
      setMessage(
        err instanceof Error ? err.message : "Failed to process sentence."
      );
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="space-y-6">
      <Card>
        <CardHeader>
          <CardTitle>Process Sentence</CardTitle>
        </CardHeader>
        <CardContent>
          <form onSubmit={handleProcess} className="flex gap-2">
            <Input
              placeholder="Enter a sentence..."
              value={sentence}
              onChange={(e) => setSentence(e.target.value)}
            />
            <Button type="submit" disabled={loading || !sentence.trim()}>
              Process
            </Button>
          </form>
        </CardContent>
      </Card>

      {result && (
        <Card>
          <CardHeader>
            <CardTitle>Result</CardTitle>
          </CardHeader>
          <CardContent>
            <p className="text-sm text-muted-foreground mb-2">
              Original: {result.sentence}
            </p>
            <p className="font-medium">{result.result}</p>
          </CardContent>
        </Card>
      )}

      {message && (
        <p className="text-sm text-muted-foreground">{message}</p>
      )}
    </div>
  );
}
