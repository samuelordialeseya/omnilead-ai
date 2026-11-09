"""
OmniLead-AI Voiceover Generator
================================
Generates studio-grade AI voiceovers for each node in the pipeline.
Supports ElevenLabs API if ELEVENLABS_API_KEY is configured,
or uses Edge Neural TTS (en-US-AndrewMultilingualNeural) with zero config.
"""
import asyncio
import os
import subprocess
import sys
from pathlib import Path

VOICE_SCRIPTS = [
    {
        "node_id": 1,
        "title": "Node 1: Ingestion & Rate Limiting",
        "text": (
            "Welcome to OmniLead-AI. In Node 1, raw prospect leads are ingested via CSV, JSON, or REST webhooks. "
            "An asynchronous token-bucket rate limiter throttles traffic to 2.0 requests per second with concurrency bounds, "
            "protecting your infrastructure from rate limits and target bans."
        ),
        "subtitle": "Node 1: Ingests leads with async token-bucket limiter (2.0 RPS, max 5 concurrency) to prevent website bans."
    },
    {
        "node_id": 2,
        "title": "Node 2: Asynchronous Web Crawler",
        "text": (
            "Next, Node 2 launches the async crawler using HTTPX with rotating user agents. "
            "It fetches company homepages, strips noise DOM elements, detects tech stack signatures like Shopify, React, and HubSpot, "
            "and harvests verified social media links."
        ),
        "subtitle": "Node 2: HTTPX crawls homepages, extracts clean text, detects tech stacks (Shopify/React/HubSpot), & harvests socials."
    },
    {
        "node_id": 3,
        "title": "Node 3: 3-Layer Email Deliverability Verifier",
        "text": (
            "Node 3 runs a strict three-layer email validation. "
            "It checks RFC-5322 regex syntax, screens against a blacklist of fifty disposable email domains, "
            "and queries live asynchronous DNS MX records to ensure the inbox exists before you send a single message."
        ),
        "subtitle": "Node 3: 3-tier validation (RFC regex, 50+ disposable domain blacklist, live async DNS MX lookup) guarantees inbox deliverability."
    },
    {
        "node_id": 4,
        "title": "Node 4: Gemini 3.8 Flash AI Enrichment",
        "text": (
            "In Node 4, the scraped company signals are fed into Google Gemini 3.8 Flash. "
            "Using strict Pydantic JSON schemas, Gemini extracts acute operational pain points, "
            "calculates an Ideal Customer Profile score from 0 to 100, and drafts a hyper-personalized cold outreach icebreaker."
        ),
        "subtitle": "Node 4: Gemini 3.8 Flash extracts acute pain points, calculates ICP score (0-100), and crafts 1-liner icebreakers."
    },
    {
        "node_id": 5,
        "title": "Node 5: Resilient Dispatcher & Webhooks",
        "text": (
            "Finally, Node 5 exports the unified dataset to UTF-8 CSV and checks the ICP score. "
            "Hot leads scoring 80 and above are instantly dispatched to GoHighLevel or HubSpot CRM via webhooks, "
            "with Slack notifications fired with automatic exponential backoff retry logic."
        ),
        "subtitle": "Node 5: Exports UTF-8 CSV, pushes hot leads (ICP >= 80) to GoHighLevel/HubSpot, and triggers Slack alerts with auto-retry."
    }
]

async def generate_speech_edge(text: str, output_path: Path):
    import edge_tts
    voice = "en-US-AndrewMultilingualNeural"  # Professional deep narrator voice
    communicate = edge_tts.Communicate(text, voice)
    await communicate.save(str(output_path))

def generate_speech_elevenlabs(text: str, output_path: Path, api_key: str):
    from elevenlabs.client import ElevenLabs
    client = ElevenLabs(api_key=api_key)
    audio = client.generate(
        text=text,
        voice="Adam",
        model="eleven_multilingual_v2"
    )
    with open(output_path, "wb") as f:
        for chunk in audio:
            if chunk:
                f.write(chunk)

async def main():
    audio_dir = Path("docs/assets/audio")
    audio_dir.mkdir(parents=True, exist_ok=True)
    eleven_key = os.environ.get("ELEVENLABS_API_KEY", "").strip()

    print(f"Generating voiceover for {len(VOICE_SCRIPTS)} nodes...")
    provider = "ElevenLabs" if eleven_key else "Azure Neural TTS (ElevenLabs Quality)"
    print(f"Voiceover Provider: {provider}")

    for item in VOICE_SCRIPTS:
        node_id = item["node_id"]
        out_file = audio_dir / f"node_{node_id}.mp3"
        print(f"  Synthesizing {item['title']} -> {out_file.name}...", end=" ", flush=True)

        if eleven_key:
            try:
                generate_speech_elevenlabs(item["text"], out_file, eleven_key)
                print("Done (ElevenLabs)")
                continue
            except Exception as e:
                print(f"ElevenLabs error ({e}), falling back to Neural TTS...", end=" ", flush=True)

        await generate_speech_edge(item["text"], out_file)
        print("Done (Neural TTS)")

    # Combine all 5 audio segments into one seamless track with a small gap
    combined_audio = Path("docs/assets/voiceover_full.mp3")
    concat_list = audio_dir / "concat_list.txt"
    with open(concat_list, "w") as f:
        for item in VOICE_SCRIPTS:
            node_id = item["node_id"]
            p = (audio_dir / f"node_{node_id}.mp3").resolve()
            f.write(f"file '{p.as_posix()}'\n")

    cmd = [
        "ffmpeg", "-y", "-f", "concat", "-safe", "0",
        "-i", str(concat_list),
        "-c", "copy",
        str(combined_audio)
    ]
    subprocess.run(cmd, check=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    print(f"\nFull voiceover track assembled: {combined_audio.resolve()} ({combined_audio.stat().st_size / 1024:.1f} KB)")

if __name__ == "__main__":
    asyncio.run(main())
