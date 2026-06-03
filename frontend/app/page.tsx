"use client";

import Link from "next/link";
import { useRouter } from "next/navigation";
import { useState } from "react";
import { api } from "@/lib/api";
import { StepGuide } from "@/components/step-guide";
import { Button } from "@/components/ui/button";
import { Spinner } from "@/components/ui/spinner";

export default function Home() {
  const router = useRouter();
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  async function trySample() {
    setLoading(true);
    setError(null);
    try {
      const { project } = await api.createSample();
      localStorage.setItem("lastProjectId", project.id);
      router.push(`/project/${project.id}/processing?auto=1`);
    } catch (e) {
      setError(e instanceof Error ? e.message : "Failed to load sample");
      setLoading(false);
    }
  }

  return (
    <div className="min-h-screen">
      <header className="border-b border-neutral-200 bg-white">
        <div className="mx-auto flex max-w-5xl items-center justify-between px-6 py-4">
          <span className="text-xl font-bold tracking-tight">Noteslash</span>
        </div>
      </header>

      <main className="mx-auto max-w-5xl px-6 py-12">
        <section className="text-center">
          <p className="text-sm font-medium uppercase tracking-wide text-neutral-500">
            Your audio library, understood
          </p>
          <h1 className="mt-2 text-4xl font-bold tracking-tight text-neutral-900">
            Turn any audio into searchable, cited notes
          </h1>
          <p className="mx-auto mt-4 max-w-2xl text-lg text-neutral-600">
            Upload podcasts, audiobooks, interviews, or lectures. Noteslash transcribes, organizes,
            and lets you chat or talk with your content — with sources for every answer.
          </p>
          <div className="mt-8 flex flex-wrap justify-center gap-3">
            <Link href="/new">
              <Button size="lg">Start a library</Button>
            </Link>
            <Button size="lg" variant="secondary" onClick={trySample} disabled={loading}>
              {loading ? (
                <span className="flex items-center gap-2">
                  <Spinner className="h-4 w-4" /> Loading sample…
                </span>
              ) : (
                "Try sample content"
              )}
            </Button>
          </div>
          {error && <p className="mt-4 text-sm text-red-600">{error}</p>}
        </section>

        <section className="mt-16">
          <h2 className="mb-6 text-center text-xl font-semibold">How it works</h2>
          <StepGuide />
        </section>
      </main>
    </div>
  );
}
