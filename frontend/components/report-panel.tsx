"use client";

import { useEffect, useState } from "react";
import { api } from "@/lib/api";
import { Button } from "./ui/button";
import { Card } from "./ui/card";
import { Spinner } from "./ui/spinner";

export function ReportPanel({ projectId }: { projectId: string }) {
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [markdown, setMarkdown] = useState<string | null>(null);

  async function generate() {
    setLoading(true);
    setError(null);
    try {
      const res = await api.report(projectId);
      setMarkdown(res.markdown);
    } catch (e) {
      setError(e instanceof Error ? e.message : "Report generation failed");
    } finally {
      setLoading(false);
    }
  }

  useEffect(() => {
    api.latestReport(projectId).then((r) => setMarkdown(r.markdown)).catch(() => {});
  }, [projectId]);

  function download() {
    if (!markdown) return;
    const blob = new Blob([markdown], { type: "text/markdown" });
    const url = URL.createObjectURL(blob);
    const a = document.createElement("a");
    a.href = url;
    a.download = "research-report.md";
    a.click();
    URL.revokeObjectURL(url);
  }

  return (
    <div className="space-y-4">
      <p className="text-sm text-neutral-600">
        Generate an executive research report from your insights and quotes. Export as Markdown.
      </p>
      <div className="flex gap-2">
        <Button onClick={generate} disabled={loading}>
          {loading ? "Generating…" : "Generate report"}
        </Button>
        {markdown && (
          <Button variant="secondary" onClick={download}>
            Download .md
          </Button>
        )}
      </div>
      {error && <p className="text-sm text-red-600">{error}</p>}
      {loading && (
        <div className="flex justify-center py-8">
          <Spinner />
        </div>
      )}
      {markdown && !loading && (
        <Card>
          <pre className="max-h-[480px] overflow-auto whitespace-pre-wrap text-sm text-neutral-800">
            {markdown}
          </pre>
        </Card>
      )}
    </div>
  );
}
