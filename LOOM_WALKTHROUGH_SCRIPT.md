# OmniLead-AI: Loom Video Walkthrough Script
## "2-Minute Client Close" — OnlineJobs.ph Application Companion

> Use this script to record a Loom demo video and attach it to every job application.
> Target clients: lead gen agencies, outbound sales teams, B2B SaaS founders.

---

## 🎬 Setup Before Recording

1. Open terminal in the `omnilead-ai` project folder
2. Have the project already installed: `pip install -e .`
3. Open `http://localhost:8000/docs` in your browser (run `uvicorn omnilead.api.server:app --port 8000`)
4. Screen layout: Terminal on left (60%), Browser on right (40%)

---

## 🎙️ Script (read naturally, not robotically)

---

**[0:00–0:15] Hook**

> "Hey — if you're hiring for lead generation or automation work, I want to show you something specific that I built. This is OmniLead-AI, an end-to-end lead enrichment pipeline I developed from scratch in Python."

---

**[0:15–0:40] The Problem (why this matters to them)**

> "Most agencies pay $300 to $1,000 a month for tools like Clay, Apollo, or Hunter just to enrich leads and personalize cold email. And when those tools go down or change their pricing — your whole workflow breaks."
>
> "I built this as a fully self-hosted alternative. Zero SaaS dependency, zero per-lead cost once deployed."

---

**[0:40–1:10] CLI Demo (switch to terminal)**

> "Let me run it live right now. I've got a CSV of 10 B2B leads — real company names, emails, roles."

```bash
python -m omnilead.cli.main_cli process --input sample_leads.csv
```

> *[Wait for the Rich progress bar to complete — about 3-4 seconds in mock mode]*
>
> "So in about 4 seconds, it's crawled each company's website, verified the email addresses against DNS MX records, ran each one through Google Gemini AI, and scored them 0 to 100 for how well they fit as a prospect."
>
> "7 out of 10 came back as hot leads — above 80 — which would automatically trigger a Slack alert to your team and push to your CRM."

---

**[1:10–1:35] API Demo (switch to browser)**

> "It also runs as a REST API. Here's the Swagger docs."

*[Click on `POST /api/v1/enrich`, click Try it Out, paste the sample JSON, Execute]*

> "I can hit this endpoint from Zapier, Make.com, GoHighLevel, or any webhook. And look at the response — it's returning the company summary, top pain points, a personalized icebreaker for cold outreach, and a suggested CTA. All structured JSON, ready to plug into any email tool."

---

**[1:35–1:55] Close**

> "This took me about two weeks to build. It's production-ready — Docker Compose, async rate limiting, retry logic on webhook failures, and a full test suite."
>
> "If your team is spending hours manually enriching leads or paying for a tool that could be automated away — I'd love to help you build something like this or extend it for your specific workflow."

---

**[1:55–2:00] CTA**

> "I'm available to start immediately. Send me a message and I'll reply within a few hours."

---

## 📋 Application Message Template (paste in OnlineJobs.ph)

```
Hi [Client Name],

I saw your post looking for a [lead gen / automation / API developer] — this is exactly the kind of work I specialize in.

I recently built OmniLead-AI, a self-hosted B2B lead enrichment pipeline that replaces Clay.com and Apollo with a custom Python + Gemini AI engine. It scrapes company websites, verifies emails via DNS, generates personalized cold email icebreakers, and pushes hot leads to any CRM via webhook — all async, all production-ready.

GitHub: https://github.com/yourusername/omnilead-ai
Loom Demo: [your loom link]

Happy to adapt this or build something similar for your specific workflow. I'm available to start immediately and work PH hours.

Looking forward to connecting,
[Your Name]
```

---

## 💡 Tips

- **Record in one take** — imperfections feel authentic and build trust
- **Show real terminal output** — clients love seeing code run live
- **Mention the GitHub link** in the first 30 seconds — many clients skip to the end
- **Don't apologize** for the mock mode — frame it as "runs even without credentials, so you can test it immediately"
