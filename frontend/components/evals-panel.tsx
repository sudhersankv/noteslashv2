"use client";

import { useEffect, useState } from "react";
import { api, EvalResponse } from "@/lib/api";
import { Button } from "./ui/button";
import { Card } from "./ui/card";
import { Spinner } from "./ui/spinner";

export function EvalsPanel({ projectId }: { projectId: string }) {
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [evalResult, setEvalResult] = useState<EvalResponse | null>(null);

  async function runEval() {
    setLoading(true);
    setError(null);
    try {
      const res = await api.evaluate(projectId);
      setEvalResult(res);
    } catch (e) {
      setError(e instanceof Error ? e.message : "Evaluation failed");
    } finally {
      setLoading(false);
    }
  }

  useEffect(() => {
    api.latestEval(projectId).then(setEvalResult).catch(() => {});
  }, [projectId]);

  return (
    <div className="space-y-4">
      <p className="text-sm text-neutral-600">
        Verify that insights are backed by source passages from your library.
      </p>
      <Button onClick={runEval} disabled={loading}>
        {loading ? "Running…" : "Run evaluation"}
      </Button>
      {error && <p className="text-sm text-red-600">{error}</p>}
      {loading && (
        <div className="flex justify-center py-8">
          <Spinner />
        </div>
      )}
      {evalResult && !loading && (
        <Card>
          <div className="grid grid-cols-2 gap-4 sm:grid-cols-4">
            <Stat label="Insights" value={evalResult.metrics.insights_total} />
            <Stat label="Grounded" value={evalResult.metrics.grounded} />
            <Stat label="Unsupported" value={evalResult.metrics.unsupported} />
            <Stat
              label="Grounding score"
              value={`${evalResult.metrics.grounding_score}%`}
              highlight
            />
          </div>
          {evalResult.unsupported_items.length > 0 && (
            <ul className="mt-4 space-y-2 border-t pt-4">
              <li className="text-sm font-medium text-neutral-500">Unsupported items</li>
              {evalResult.unsupported_items.map((u, i) => (
                <li key={i} className="rounded-lg bg-red-50 p-3 text-sm">
                  <strong>{u.insight_title}</strong>
                  <p className="text-red-800">{u.reason}</p>
                </li>
              ))}
            </ul>
          )}
        </Card>
      )}
    </div>
  );
}

function Stat({
  label,
  value,
  highlight,
}: {
  label: string;
  value: string | number;
  highlight?: boolean;
}) {
  return (
    <div>
      <p className="text-xs text-neutral-500">{label}</p>
      <p className={`text-2xl font-semibold ${highlight ? "text-emerald-700" : ""}`}>{value}</p>
    </div>
  );
}
