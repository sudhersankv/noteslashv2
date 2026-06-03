const steps = [
  { n: 1, title: "Upload", desc: "Add podcasts, audiobooks, interviews, or text files." },
  { n: 2, title: "Process", desc: "Noteslash transcribes, categorizes, and indexes your content." },
  { n: 3, title: "Explore", desc: "Chat or talk with your library — every answer cites sources." },
  { n: 4, title: "Export", desc: "Download a structured report of topics and takeaways." },
];

export function StepGuide() {
  return (
    <ol className="grid gap-4 sm:grid-cols-2 lg:grid-cols-4">
      {steps.map((s) => (
        <li key={s.n} className="rounded-xl border border-neutral-200 bg-white p-4">
          <span className="flex h-8 w-8 items-center justify-center rounded-full bg-neutral-900 text-sm font-semibold text-white">
            {s.n}
          </span>
          <h3 className="mt-3 font-semibold">{s.title}</h3>
          <p className="mt-1 text-sm text-neutral-600">{s.desc}</p>
        </li>
      ))}
    </ol>
  );
}
