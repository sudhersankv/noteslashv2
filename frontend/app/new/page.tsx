"use client";

import { useRouter } from "next/navigation";
import { useState } from "react";
import Link from "next/link";
import { api } from "@/lib/api";
import { Button } from "@/components/ui/button";
import { Card } from "@/components/ui/card";

export default function NewProjectPage() {
  const router = useRouter();
  const [name, setName] = useState("My Library");
  const [files, setFiles] = useState<FileList | null>(null);
  const [paste, setPaste] = useState("");
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  async function handleSubmit(e: React.FormEvent) {
    e.preventDefault();
    const fileArr = files ? Array.from(files) : [];
    if (fileArr.length === 0 && !paste.trim()) {
      setError("Add at least one audio/text file or paste content.");
      return;
    }
    setLoading(true);
    setError(null);
    try {
      const project = await api.createProject(name);
      await api.upload(project.id, fileArr, paste);
      localStorage.setItem("lastProjectId", project.id);
      router.push(`/project/${project.id}/processing`);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Failed to create library");
      setLoading(false);
    }
  }

  return (
    <div className="min-h-screen bg-neutral-50">
      <header className="border-b border-neutral-200 bg-white px-6 py-4">
        <Link href="/" className="text-sm text-neutral-500 hover:text-neutral-900">
          ← Noteslash
        </Link>
      </header>
      <main className="mx-auto max-w-xl px-6 py-10">
        <h1 className="text-2xl font-bold">New library</h1>
        <p className="mt-2 text-neutral-600">
          Upload podcasts, audiobooks, interviews, lectures, or text files.
        </p>
        <Card className="mt-6">
          <form onSubmit={handleSubmit} className="space-y-4">
            <div>
              <label className="text-sm font-medium">Library name</label>
              <input
                value={name}
                onChange={(e) => setName(e.target.value)}
                className="mt-1 w-full rounded-lg border border-neutral-300 px-3 py-2 text-sm"
                required
              />
            </div>
            <div>
              <label className="text-sm font-medium">Upload files</label>
              <input
                type="file"
                accept="audio/*,.txt,.mp3,.wav,.m4a,.webm,.ogg"
                multiple
                onChange={(e) => setFiles(e.target.files)}
                className="mt-1 w-full text-sm"
              />
              <p className="mt-1 text-xs text-neutral-500">
                Supported: mp3, wav, m4a, webm, ogg, txt (max 25MB per audio file)
              </p>
            </div>
            <div>
              <label className="text-sm font-medium">Or paste text</label>
              <textarea
                value={paste}
                onChange={(e) => setPaste(e.target.value)}
                rows={5}
                className="mt-1 w-full rounded-lg border border-neutral-300 px-3 py-2 text-sm"
              />
            </div>
            {error && <p className="text-sm text-red-600">{error}</p>}
            <Button type="submit" disabled={loading} className="w-full">
              {loading ? "Uploading…" : "Continue"}
            </Button>
          </form>
        </Card>
      </main>
    </div>
  );
}
