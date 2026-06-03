"use client";

import { InsightItem } from "@/lib/api";
import { Badge } from "./ui/badge";
import { Card } from "./ui/card";

export function InsightCard({ item }: { item: InsightItem }) {
  return (
    <Card className="space-y-2">
      <div className="flex items-start justify-between gap-2">
        <h4 className="font-medium">{item.title}</h4>
        {item.frequency != null && <Badge>{item.frequency} mentions</Badge>}
      </div>
      {item.description && (
        <p className="text-sm text-neutral-600">{item.description}</p>
      )}
      {item.evidence.length > 0 && (
        <ul className="mt-2 space-y-2 border-t border-neutral-100 pt-2">
          {item.evidence.slice(0, 2).map((e, i) => (
            <li key={i} className="text-sm">
              <span className="text-xs text-neutral-400">{e.filename || "transcript"}</span>
              <blockquote className="mt-0.5 border-l-2 border-neutral-300 pl-2 text-neutral-700 italic">
                &ldquo;{e.quote.slice(0, 220)}
                {e.quote.length > 220 ? "…" : ""}&rdquo;
              </blockquote>
            </li>
          ))}
        </ul>
      )}
    </Card>
  );
}
