"use client";

import { useParams, useRouter, useSearchParams } from "next/navigation";
import { useEffect, useState, Suspense } from "react";
import { api, ProjectStatus } from "@/lib/api";
import { Spinner } from "@/components/ui/spinner";

const STEPS = [
  "Transcribing audio",
  "Categorizing content",
  "Indexing library",
  "Extracting insights",
];

function ProcessingContent() {
  const { id } = useParams<{ id: string }>();
  const searchParams = useSearchParams();
  const router = useRouter();
  const auto = searchParams.get("auto") === "1";
  const [step, setStep] = useState(0);
  const [error, setError] = useState<string | null>(null);
  const [status, setStatus] = useState<ProjectStatus | null>(null);

  useEffect(() => {
    if (!id) return;
    let cancelled = false;
    let interval: ReturnType<typeof setInterval> | null = null;

    async function run() {
      try {
        const initial = await api.status(id);
        if (cancelled) return;
        if (initial.status === "ready") {
          router.replace(`/project/${id}`);
          return;
        }
        if (auto || initial.status === "pending" || initial.status === "empty") {
          setStep(0);
          await api.process(id);
        }
      } catch (e) {
        if (!cancelled) setError(e instanceof Error ? e.message : "Processing failed");
        return;
      }

      interval = setInterval(async () => {
        try {
          const s = await api.status(id);
          if (cancelled) return;
          setStatus(s);
          if (s.chunk_count > 0) setStep(2);
          if (s.insight_count > 0) setStep(3);
          if (s.content_type) setStep((prev) => Math.max(prev, 1));
          if (s.status === "ready") {
            if (interval) clearInterval(interval);
            router.replace(`/project/${id}`);
          }
          if (s.status === "failed") {
            if (interval) clearInterval(interval);
            setError(s.message || "Processing failed");
          }
        } catch {
          /* poll */
        }
      }, 1500);
    }

    run();
    return () => {
      cancelled = true;
      if (interval) clearInterval(interval);
    };
  }, [id, auto, router]);

  return (
    <div className="flex min-h-screen flex-col items-center justify-center px-6">
      <Spinner className="h-10 w-10" />
      <h1 className="mt-6 text-xl font-semibold">Processing your library</h1>
      <p className="mt-2 text-neutral-600">This may take a minute for audio files</p>
      <ul className="mt-8 space-y-2 text-sm">
        {STEPS.map((label, i) => (
          <li
            key={label}
            className={i <= step ? "font-medium text-neutral-900" : "text-neutral-400"}
          >
            {i <= step ? "✓" : "○"} {label}
          </li>
        ))}
      </ul>
      {status && (
        <p className="mt-4 text-xs text-neutral-500">
          {status.transcript_count} sources · {status.chunk_count} chunks ·{" "}
          {status.insight_count} insights
          {status.content_type ? ` · ${status.content_type}` : ""}
        </p>
      )}
      {error && <p className="mt-4 text-sm text-red-600">{error}</p>}
    </div>
  );
}

export default function ProcessingPage() {
  return (
    <Suspense
      fallback={
        <div className="flex min-h-screen items-center justify-center">
          <Spinner />
        </div>
      }
    >
      <ProcessingContent />
    </Suspense>
  );
}
