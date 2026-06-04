# Noteslash — Video walkthrough script

Use with [ARCHITECTURE.md](./ARCHITECTURE.md) diagrams on a second monitor or paste into slides.

**Suggested length:** 3–4 minutes  
**Prereqs:** Railway backend live, frontend deployed, migration 003 applied.

---

## Opening (15 sec)

> “This is **Noteslash**—upload any audio or text, and get a searchable library you can **chat** or **talk** to, with answers tied to real quotes from your content.”

Show: production URL landing page.

---

## Problem + solution (20 sec)

> “Podcasts, audiobooks, and interviews pile up. Reading and searching them is slow. Noteslash transcribes audio, categorizes it, builds a semantic index, and surfaces themes and takeaways—with citations.”

Show: 4-step “How it works” on homepage.

---

## Demo path A — Sample content (90 sec)

1. Click **Try sample content**
2. Processing screen: mention four stages (categorize → index → insights)
3. **Overview** tab:
   - Summary paragraph
   - Content type badge (e.g. interview)
   - Cards with quoted evidence
4. **Chat** tab:
   - “What did users say about onboarding?”
   - Point at **Supporting quotes** under the answer
5. **Voice** tab (if Realtime enabled):
   - Start voice → allow mic
   - Ask one short question
   - Show live transcript log
6. **Report** tab:
   - Generate → Download `.md`

---

## Architecture bite (45 sec) — optional for technical audience

Open `docs/ARCHITECTURE.md` §2 (deployment) or §5 (pipeline):

> “Frontend is Next.js. API is FastAPI on Railway. Supabase Postgres stores chunks with **pgvector** embeddings. Upload uses **Whisper**; chat uses retrieval plus GPT. Voice uses OpenAI **Realtime** over WebRTC, but search runs on our API so content stays grounded.”

---

## Stack close (15 sec)

> “Stack: Next.js, FastAPI, Supabase, OpenAI Whisper, embeddings, chat, and Realtime. Repo is public at github.com/sudhersankv/noteslashv2.”

---

## Demo path B — Real audio (30 sec extra)

> “You can upload mp3, wav, or m4a—Whisper transcribes on upload, up to 25 megabytes per file.”

Show: `/new` → upload a short clip → processing → Overview.

---

## Troubleshooting lines (if live demo fails)

| Issue | Line |
|-------|------|
| Voice won’t connect | “Voice needs HTTPS and OpenAI Realtime access on the API key.” |
| Processing slow | “First run embeds every chunk—usually 30 to 60 seconds for three files.” |
| CORS error | “Frontend must point NEXT_PUBLIC_API_URL at the Railway URL.” |

---

## Checklist before recording

- [ ] Railway `/health` returns `noteslash`
- [ ] Sample flow works end-to-end
- [ ] Chat returns at least one citation
- [ ] Mic permission granted (for voice segment)
- [ ] Browser tab zoom 100%, dark/light mode consistent
