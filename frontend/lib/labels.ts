export function insightLabels(contentType?: string) {
  if (contentType === "interview") {
    return {
      themes: "Top themes",
      pains: "Pain points",
      features: "Feature requests",
    };
  }
  return {
    themes: "Key topics",
    pains: "Notable quotes",
    features: "Takeaways",
  };
}
