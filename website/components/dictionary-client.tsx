"use client";

import { useState } from "react";
import { api } from "@/lib/api-client";
import { DictionaryEntry } from "@/types/api";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Card, CardHeader, CardTitle, CardContent } from "@/components/ui/card";
import {
  Table,
  TableHeader,
  TableBody,
  TableRow,
  TableHead,
  TableCell,
} from "@/components/ui/table";

interface DictionaryClientProps {
  initialEntries: DictionaryEntry[];
}

export default function DictionaryClient({
  initialEntries,
}: DictionaryClientProps) {
  const [entries, setEntries] = useState<DictionaryEntry[]>(initialEntries);
  const [newWord, setNewWord] = useState("");
  const [newDefinition, setNewDefinition] = useState("");
  const [searchWord, setSearchWord] = useState("");
  const [searchResult, setSearchResult] = useState<DictionaryEntry | null>(
    null
  );
  const [message, setMessage] = useState("");
  const [loading, setLoading] = useState(false);

  const handleAdd = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!newWord.trim() || !newDefinition.trim()) return;
    setLoading(true);
    setMessage("");
    try {
      await api<unknown>("/dictionary", {
        method: "POST",
        body: JSON.stringify({ word: newWord, definition: newDefinition }),
      });
      setNewWord("");
      setNewDefinition("");
      setMessage(`"${newWord}" added successfully.`);
      // Refresh list
      const data = await api<{ entries: DictionaryEntry[] }>(
        "/dictionary?operation=list"
      );
      setEntries(data.entries ?? []);
    } catch (err) {
      setMessage(err instanceof Error ? err.message : "Failed to add entry.");
    } finally {
      setLoading(false);
    }
  };

  const handleSearch = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!searchWord.trim()) return;
    setLoading(true);
    setSearchResult(null);
    setMessage("");
    try {
      const result = await api<DictionaryEntry>(`/dictionary/${searchWord}`);
      setSearchResult(result);
    } catch (err) {
      setMessage(
        err instanceof Error ? err.message : `Entry "${searchWord}" not found.`
      );
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="space-y-6">
      {/* Add Entry Form */}
      <Card>
        <CardHeader>
          <CardTitle>Add Entry</CardTitle>
        </CardHeader>
        <CardContent>
          <form onSubmit={handleAdd} className="space-y-3">
            <div className="flex gap-2">
              <Input
                placeholder="Word"
                value={newWord}
                onChange={(e) => setNewWord(e.target.value)}
              />
              <Input
                placeholder="Definition"
                value={newDefinition}
                onChange={(e) => setNewDefinition(e.target.value)}
              />
              <Button type="submit" disabled={loading}>
                Add
              </Button>
            </div>
          </form>
        </CardContent>
      </Card>

      {/* Lookup Form */}
      <Card>
        <CardHeader>
          <CardTitle>Lookup</CardTitle>
        </CardHeader>
        <CardContent>
          <form onSubmit={handleSearch} className="flex gap-2">
            <Input
              placeholder="Search word..."
              value={searchWord}
              onChange={(e) => setSearchWord(e.target.value)}
            />
            <Button type="submit" disabled={loading}>
              Search
            </Button>
          </form>
          {searchResult && (
            <Card className="mt-3">
              <CardContent className="pt-4">
                <p className="font-semibold">{searchResult.word}</p>
                <p className="text-muted-foreground">{searchResult.definition}</p>
              </CardContent>
            </Card>
          )}
        </CardContent>
      </Card>

      {/* Entries List */}
      <Card>
        <CardHeader>
          <CardTitle>Entries</CardTitle>
        </CardHeader>
        <CardContent>
          {entries.length === 0 ? (
            <p className="text-muted-foreground text-sm">No entries yet.</p>
          ) : (
            <Table>
              <TableHeader>
                <TableRow>
                  <TableHead>Word</TableHead>
                  <TableHead>Definition</TableHead>
                </TableRow>
              </TableHeader>
              <TableBody>
                {entries.map((entry) => (
                  <TableRow key={entry.word}>
                    <TableCell className="font-medium">{entry.word}</TableCell>
                    <TableCell>{entry.definition}</TableCell>
                  </TableRow>
                ))}
              </TableBody>
            </Table>
          )}
        </CardContent>
      </Card>

      {message && (
        <p className="text-sm text-muted-foreground">{message}</p>
      )}
    </div>
  );
}
