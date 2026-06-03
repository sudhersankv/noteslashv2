"use client";

import Link from "next/link";
import { useParams } from "next/navigation";
import { useEffect, useState } from "react";
import { api, InsightsResponse, ProjectStatus } from "@/lib/api";
import { insightLabels } from "@/lib/labels";
import { InsightCard } from "@/components/insight-card";
import { ChatPanel } from "@/components/chat-panel";
import { VoicePanel } from "@/components/voice-panel";
import { ReportPanel } from "@/components/report-panel";
import { Badge } from "@/components/ui/badge";
import { Spinner } from "@/components/ui/spinner";

type Tab = "overview" | "chat" | "voice" | "report";

export default function WorkspacePage() {
  const { id } = useParams<{ id: string }>();
  const [tab, setTab] = useState<Tab>("overview");
  const [status, setStatus] = useState<ProjectStatus | null>(null);
  const [insights, setInsights] = useState<InsightsResponse | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    if (!id) return;
    Promise.all([api.status(id), api.insights(id)])
      .then(([s, ins]) => {
        setStatus(s);
        setInsights(ins);
      })
      .catch((e) => setError(e.message))
      .finally(() => setLoading(false));
  }, [id]);

  const labels = insightLabels(insights?.content_type || status?.content_type);

  const tabs: { id: Tab; label: string }[] = [
    { id: "overview", label: "Overview" },
    { id: "chat", label: "Chat" },
    { id: "voice", label: "Voice" },
    { id: "report", label: "Report" },
  ];

  if (loading) {
    return (
      <div className="flex min-h-screen items-center justify-center">
        <Spinner />
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-neutral-50">
      <header className="border-b border-neutral-200 bg-white">
        <div className="mx-auto flex max-w-5xl flex-wrap items-center justify-between gap-4 px-6 py-4">
          <div>
            <Link href="/" className="text-xs text-neutral-500 hover:underline">
              Noteslash
            </Link>
            <h1 className="text-lg font-semibold">Your library</h1>
            <div className="mt-1 flex flex-wrap items-center gap-2">
              {status && (
                <p className="text-sm text-neutral-500">
                  {status.transcript_count} sources · {status.insight_count} insights
                </p>
              )}
              {(insights?.content_type || status?.content_type) && (
                <Badge>{insights?.content_type || status?.content_type}</Badge>
              )}
              {(insights?.tags || status?.tags)?.slice(0, 3).map((t) => (
                <Badge key={t} className="bg-neutral-200">
                  {t}
                </Badge>
              ))}
            </div>
          </div>
        </div>
        <nav className="mx-auto flex max-w-5xl gap-1 px-6">
          {tabs.map((t) => (
            <button
              key={t.id}
              onClick={() => setTab(t.id)}
              className={`border-b-2 px-4 py-2 text-sm font-medium ${
                tab === t.id
                  ? "border-neutral-900 text-neutral-900"
                  : "border-transparent text-neutral-500 hover:text-neutral-700"
              }`}
            >
              {t.label}
            </button>
          ))}
        </nav>
      </header>

      <main className="mx-auto max-w-5xl px-6 py-8">
        {error && <p className="mb-4 text-sm text-red-600">{error}</p>}

        {tab === "overview" && insights && (
          <div className="space-y-8">
            <section>
              <h2 className="text-lg font-semibold">Summary</h2>
              <p className="mt-2 text-neutral-700">{insights.summary}</p>
            </section>
            <Section title={labels.themes} items={insights.themes} />
            <Section title={labels.pains} items={insights.pain_points} />
            <Section title={labels.features} items={insights.feature_requests} />
          </div>
        )}

        {tab === "chat" && id && <ChatPanel projectId={id} />}
        {tab === "voice" && id && <VoicePanel projectId={id} />}
        {tab === "report" && id && <ReportPanel projectId={id} />}
      </main>
    </div>
  );
}

function Section({
  title,
  items,
}: {
  title: string;
  items: InsightsResponse["themes"];
}) {
  if (!items.length) return null;
  return (
    <section>
      <h3 className="mb-3 font-semibold">{title}</h3>
      <div className="grid gap-3 md:grid-cols-2">
        {items.map((i) => (
          <InsightCard key={i.id} item={i} />
        ))}
      </div>
    </section>
  );
}
