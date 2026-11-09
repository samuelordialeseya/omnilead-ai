"""
OmniLead-AI Screen Recording & Voiceover Pipeline
=================================================
Synthesizes ElevenLabs / Azure Neural audio voiceovers for all 5 nodes,
measures exact durations, and renders a synchronized 720p HD screen recording
with animated terminal, node topology, dynamic audio waveforms, and subtitles.
"""
import asyncio
import math
import os
import subprocess
import sys
import time
from pathlib import Path
from PIL import Image, ImageDraw, ImageFont

WIDTH = 1280
HEIGHT = 720
FPS = 25

# Palette
BG_DARK = (13, 17, 23)
PANEL_BG = (22, 27, 34)
PANEL_BORDER = (48, 54, 61)
TEXT_WHITE = (240, 246, 252)
TEXT_MUTED = (139, 148, 158)
TEXT_DIM = (110, 118, 129)
ACCENT_BLUE = (88, 166, 255)
ACCENT_GREEN = (63, 185, 80)
ACCENT_YELLOW = (210, 153, 34)
ACCENT_PURPLE = (188, 140, 255)
ACCENT_CYAN = (57, 197, 207)
ACCENT_RED = (248, 81, 73)

FONT_DIR = "C:\\Windows\\Fonts"
font_title = ImageFont.truetype(os.path.join(FONT_DIR, "segoeuib.ttf"), 18)
font_caption_bold = ImageFont.truetype(os.path.join(FONT_DIR, "segoeuib.ttf"), 15)
font_caption = ImageFont.truetype(os.path.join(FONT_DIR, "segoeui.ttf"), 15)
font_subtitle = ImageFont.truetype(os.path.join(FONT_DIR, "segoeui.ttf"), 17)
font_mono = ImageFont.truetype(os.path.join(FONT_DIR, "consola.ttf"), 14)
font_mono_bold = ImageFont.truetype(os.path.join(FONT_DIR, "consolab.ttf"), 14)
font_small = ImageFont.truetype(os.path.join(FONT_DIR, "segoeui.ttf"), 12)
font_badge = ImageFont.truetype(os.path.join(FONT_DIR, "segoeuib.ttf"), 11)

NODES = [
    {
        "id": 1,
        "name": "1. Ingestion & Queue",
        "tech": "Token Bucket (2.0 RPS)",
        "color": ACCENT_BLUE,
        "script": (
            "Welcome to OmniLead-AI. In Node 1, raw prospect leads are ingested via CSV, JSON, or REST webhooks. "
            "An asynchronous token-bucket rate limiter throttles traffic to 2.0 requests per second with concurrency bounds, "
            "protecting your infrastructure from rate limits and target bans."
        ),
        "subtitle": "Node 1: Raw leads ingested via CSV/JSON/API; token-bucket limiter (2.0 RPS, max 5 workers) prevents bans.",
        "terminal_lines": [
            "$ python -m omnilead.cli.main_cli process --input sample_leads.csv",
            "┌─────────────────────────────────────────────────────────────┐",
            "│ OmniLead-AI  •  B2B Lead Enrichment Pipeline                │",
            "│ Mode: LIVE PIPELINE  |  Leads: 10  |  Concurrency: 5        │",
            "└─────────────────────────────────────────────────────────────┘",
            "[SYSTEM] Token-bucket initialized: 2.0 RPS | Max burst = 5",
            "[QUEUE] Parsed 10 prospects from sample_leads.csv",
            "[WORKER-1] Spawning async pipeline worker for lead #1...",
            "[WORKER-1] Target: GrowthStack (https://growthstack.io)",
            "[ACQUIRE] Semaphore slot 1/5 granted (latency: 12ms)",
        ]
    },
    {
        "id": 2,
        "name": "2. Async Web Crawler",
        "tech": "HTTPX + BeautifulSoup",
        "color": ACCENT_CYAN,
        "script": (
            "Next, Node 2 launches the async crawler using HTTPX with rotating user agents. "
            "It fetches company homepages, strips noise DOM elements, detects tech stack signatures like Shopify, React, and HubSpot, "
            "and harvests verified social media links."
        ),
        "subtitle": "Node 2: HTTPX crawls homepages, extracts clean text, detects tech stacks (Shopify/React/HubSpot), & harvests socials.",
        "terminal_lines": [
            "[CRAWLER] HTTPX GET https://growthstack.io (User-Agent: Chrome/128 Win64)",
            "[RESPONSE] 200 OK | Content-Type: text/html | Transfer-Size: 48.2 KB",
            "[PARSER] Stripping script, style, noscript, and iframe tags...",
            "[EXTRACT] Meta Title: 'GrowthStack | B2B Revenue Operations Platform'",
            "[EXTRACT] Meta Desc:  'GrowthStack automates RevOps workflows & CRM sync'",
            "[DETECTION] Tech stack heuristics analyzed:",
            "  -> Detected: [HubSpot, React, Stripe, Google Analytics]",
            "[HARVEST] Socials discovered:",
            "  -> LinkedIn: linkedin.com/company/growthstack",
            "  -> Twitter:  twitter.com/growthstack",
        ]
    },
    {
        "id": 3,
        "name": "3. 3-Layer Email Verifier",
        "tech": "DNS MX + RFC 5322",
        "color": ACCENT_YELLOW,
        "script": (
            "Node 3 runs a strict three-layer email validation. "
            "It checks RFC-5322 regex syntax, screens against a blacklist of fifty disposable email domains, "
            "and queries live asynchronous DNS MX records to ensure the inbox exists before you send a single message."
        ),
        "subtitle": "Node 3: 3-tier validation (RFC regex, 50+ disposable domain blacklist, live async DNS MX lookup) guarantees deliverability.",
        "terminal_lines": [
            "[VERIFIER] Inspecting contact: marcus@growthstack.io",
            "[TIER 1] RFC-5322 syntax validation: PASS (RFC-compliant)",
            "[TIER 2] Disposable blacklist lookup (domain: growthstack.io): CLEAN",
            "[TIER 3] Querying DNS MX records via asyncresolver...",
            "  -> MX 1: aspmx.l.google.com (priority: 1)",
            "  -> MX 2: alt1.aspmx.l.google.com (priority: 5)",
            "  -> MX 3: alt2.aspmx.l.google.com (priority: 5)",
            "[STATUS] Deliverability Score: 92/100 | Risk: SAFE",
            "[VERIFIED] Email verified valid. Proceeding to AI enrichment.",
        ]
    },
    {
        "id": 4,
        "name": "4. Gemini 3.8 Flash AI",
        "tech": "google-genai JSON Schema",
        "color": ACCENT_PURPLE,
        "script": (
            "In Node 4, the scraped company signals are fed into Google Gemini 3.8 Flash. "
            "Using strict Pydantic JSON schemas, Gemini extracts acute operational pain points, "
            "calculates an Ideal Customer Profile score from 0 to 100, and drafts a hyper-personalized cold outreach icebreaker."
        ),
        "subtitle": "Node 4: Gemini 3.8 Flash extracts acute pain points, calculates ICP score (0-100), and crafts 1-liner icebreakers.",
        "terminal_lines": [
            "[AI] Dispatching context payload to model: gemini-3.8-flash",
            "[INPUT] Payload: Company summary, tech stack, prospect title (VP Sales)",
            "[INFERENCE] Latency: 320ms | Tokens: 412 in / 168 out",
            "[OUTPUT] Structured JSON parsed successfully:",
            "  {",
            "    \"icp_score\": 92,",
            "    \"is_hot_lead\": true,",
            "    \"pain_points\": [\"Dual-CRM sync latency\", \"Manual field entry\"],",
            "    \"icebreaker\": \"Noticed GrowthStack integrates with HubSpot & SFDC...\",",
            "    \"suggested_cta\": \"Worth a 15-min call to see how we sync pipelines?\"",
            "  }",
        ]
    },
    {
        "id": 5,
        "name": "5. Resilient Webhook Dispatch",
        "tech": "Tenacity Retries + CRM",
        "color": ACCENT_GREEN,
        "script": (
            "Finally, Node 5 exports the unified dataset to UTF-8 CSV and checks the ICP score. "
            "Hot leads scoring 80 and above are instantly dispatched to GoHighLevel or HubSpot CRM via webhooks, "
            "with Slack notifications fired with automatic exponential backoff retry logic."
        ),
        "subtitle": "Node 5: Exports UTF-8 CSV, pushes hot leads (ICP >= 80) to GoHighLevel/HubSpot, and triggers Slack alerts with auto-retry.",
        "terminal_lines": [
            "[CSV] Writing enriched row to output/enriched_leads.csv (21 columns)",
            "[QUALIFY] Lead Score 92 >= 80 -> Flagged as HOT LEAD 🔥",
            "[DISPATCH] POST https://services.leadconnectorhq.com/hooks/ghl_inbound",
            "[RETRY_HANDLER] Tenacity exponential backoff (attempt 1/3) -> 200 OK",
            "[SLACK] Formatted webhook alert posted to #growth-hot-leads (200 OK)",
            "┌─────────────────────────────────────────────────────────────┐",
            "│ Summary: 10/10 Enriched  |  10 Hot Leads  |  0 Failures     │",
            "│ Output: ./output/enriched_20261109_120000.csv               │",
            "└─────────────────────────────────────────────────────────────┘",
        ]
    }
]

def draw_rounded_rect(draw, bbox, radius, fill=None, outline=None, width=1):
    draw.rounded_rectangle(bbox, radius=radius, fill=fill, outline=outline, width=width)

def get_audio_duration(path: Path) -> float:
    cmd = [
        "ffprobe", "-v", "error",
        "-show_entries", "format=duration",
        "-of", "default=noprint_wrappers=1:nokey=1",
        str(path)
    ]
    res = subprocess.check_output(cmd).decode("utf-8").strip()
    return float(res)

async def synthesize_all_voiceovers(audio_dir: Path):
    audio_dir.mkdir(parents=True, exist_ok=True)
    import edge_tts
    eleven_key = os.environ.get("ELEVENLABS_API_KEY", "").strip()

    for node in NODES:
        out_file = audio_dir / f"node_{node['id']}.mp3"
        if out_file.exists() and out_file.stat().st_size > 5000:
            print(f"  [Cache] {out_file.name} ready ({out_file.stat().st_size // 1024} KB)")
            continue

        print(f"  Synthesizing Node {node['id']}...", flush=True)
        if eleven_key:
            try:
                from elevenlabs.client import ElevenLabs
                client = ElevenLabs(api_key=eleven_key)
                audio = client.generate(text=node["script"], voice="Adam", model="eleven_multilingual_v2")
                with open(out_file, "wb") as f:
                    for chunk in audio:
                        if chunk: f.write(chunk)
                continue
            except Exception as e:
                print(f"  ElevenLabs fallback ({e})")

        # Retry loop for Edge Neural TTS
        for attempt in range(4):
            try:
                comm = edge_tts.Communicate(node["script"], "en-US-AndrewMultilingualNeural")
                await comm.save(str(out_file))
                break
            except Exception:
                time.sleep(1.0)

    # Concat all audio files
    combined_audio = audio_dir.parent / "voiceover_full.mp3"
    concat_list = audio_dir / "concat.txt"
    with open(concat_list, "w") as f:
        for node in NODES:
            nid = node["id"]
            p = (audio_dir / f"node_{nid}.mp3").resolve().as_posix()
            f.write(f"file '{p}'\n")

    cmd = ["ffmpeg", "-y", "-f", "concat", "-safe", "0", "-i", str(concat_list), "-c", "copy", str(combined_audio)]
    subprocess.run(cmd, check=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    return combined_audio

def render_screen_frame(t: float, current_node_idx: int, node_local_t: float, total_duration: float) -> Image.Image:
    node = NODES[current_node_idx]
    img = Image.new("RGB", (WIDTH, HEIGHT), BG_DARK)
    draw = ImageDraw.Draw(img)

    # ── 1. Top Header Bar (Y: 15 to 55) ──────────────────────────────────────
    # REC badge
    is_rec_blink = int(t * 2) % 2 == 0
    rec_dot_color = ACCENT_RED if is_rec_blink else (150, 40, 40)
    draw.ellipse([25, 26, 37, 38], fill=rec_dot_color)
    mins = int(t) // 60
    secs = int(t) % 60
    tot_m = int(total_duration) // 60
    tot_s = int(total_duration) % 60
    draw.text((45, 23), f"REC [{mins:02d}:{secs:02d} / {tot_m:02d}:{tot_s:02d}]", fill=TEXT_MUTED, font=font_badge)

    # Title
    draw.text((250, 22), "OmniLead-AI  •  Live Pipeline Architecture & Node Execution", fill=TEXT_WHITE, font=font_title)

    # Audio badge
    draw_rounded_rect(draw, (WIDTH - 300, 18, WIDTH - 25, 46), radius=6, fill=(28, 33, 40), outline=node["color"])
    draw.text((WIDTH - 288, 24), "🎙️ AI Voiceover: ElevenLabs / Neural", fill=node["color"], font=font_badge)

    # ── 2. Left Column: Topology Graph (X: 25 to 455, Y: 65 to 600) ──────────
    graph_x0, graph_y0 = 25, 65
    graph_x1, graph_y1 = 455, 600
    draw_rounded_rect(draw, (graph_x0, graph_y0, graph_x1, graph_y1), radius=10, fill=PANEL_BG, outline=PANEL_BORDER)

    # Graph header
    draw.text((graph_x0 + 16, graph_y0 + 14), "PIPELINE TOPOLOGY & DATA FLOW", fill=TEXT_MUTED, font=font_badge)

    node_box_w = 400
    node_box_h = 75
    node_gap = 25
    start_ny = graph_y0 + 42

    for i, n in enumerate(NODES):
        ny = start_ny + i * (node_box_h + node_gap)
        is_active = (i == current_node_idx)
        is_done = (i < current_node_idx)

        # Connector line to next node
        if i < len(NODES) - 1:
            line_x = graph_x0 + node_box_w // 2
            line_y1 = ny + node_box_h
            line_y2 = ny + node_box_h + node_gap
            draw.line([(line_x, line_y1), (line_x, line_y2)], fill=PANEL_BORDER, width=3)

            if is_done:
                draw.line([(line_x, line_y1), (line_x, line_y2)], fill=ACCENT_GREEN, width=3)
            elif is_active:
                pulse_y = line_y1 + ((math.sin(node_local_t * math.pi * 4) + 1) / 2) * node_gap
                draw.ellipse([line_x - 4, pulse_y - 4, line_x + 4, pulse_y + 4], fill=n["color"])

        # Node box
        nx0 = graph_x0 + 15
        nx1 = nx0 + node_box_w - 30

        if is_active:
            fill = (25, 33, 44)
            outline = n["color"]
            status_text = "● ACTIVE"
            status_color = n["color"]
            b_width = 2
        elif is_done:
            fill = (18, 27, 22)
            outline = ACCENT_GREEN
            status_text = "✓ COMPLETED"
            status_color = ACCENT_GREEN
            b_width = 1
        else:
            fill = (18, 22, 28)
            outline = PANEL_BORDER
            status_text = "○ STANDBY"
            status_color = TEXT_DIM
            b_width = 1

        draw_rounded_rect(draw, (nx0, ny, nx1, ny + node_box_h), radius=8, fill=fill, outline=outline, width=b_width)

        # Status text
        draw.text((nx1 - 85, ny + 10), status_text, fill=status_color, font=font_badge)

        # Node Name & tech sub
        draw.text((nx0 + 14, ny + 14), n["name"], fill=TEXT_WHITE, font=font_caption_bold)
        draw.text((nx0 + 14, ny + 40), n["tech"], fill=TEXT_MUTED, font=font_small)

    # ── 3. Right Column: Terminal Screen Recording (X: 475 to 1255, Y: 65 to 600)
    term_x0, term_y0 = 475, 65
    term_x1, term_y1 = 1255, 600
    draw_rounded_rect(draw, (term_x0, term_y0, term_x1, term_y1), radius=10, fill=(16, 20, 26), outline=PANEL_BORDER)

    # Terminal titlebar
    draw_rounded_rect(draw, (term_x0, term_y0, term_x1, term_y0 + 36), radius=10, fill=(28, 33, 40), outline=PANEL_BORDER)
    draw.ellipse([term_x0 + 16, term_y0 + 13, term_x0 + 26, term_y0 + 23], fill=(248, 81, 73))
    draw.ellipse([term_x0 + 34, term_y0 + 13, term_x0 + 44, term_y0 + 23], fill=(210, 153, 34))
    draw.ellipse([term_x0 + 52, term_y0 + 13, term_x0 + 62, term_y0 + 23], fill=(46, 160, 67))
    draw.text((term_x0 + 78, term_y0 + 10), f"Terminal — omnilead.pipeline :: {node['name']}", fill=TEXT_MUTED, font=font_small)

    # Terminal stream lines
    lines = node["terminal_lines"]
    max_visible = min(len(lines), int(node_local_t * (len(lines) + 1)) + 1)
    ty = term_y0 + 50

    for idx in range(max_visible):
        line = lines[idx]
        color = TEXT_WHITE
        if line.startswith("$"):
            color = ACCENT_YELLOW
        elif line.startswith("[CRAWLER]") or line.startswith("[HTTPX]") or line.startswith("[EXTRACT]"):
            color = ACCENT_CYAN
        elif line.startswith("[VERIFIER]") or line.startswith("[STATUS]") or line.startswith("[VERIFIED]"):
            color = ACCENT_GREEN
        elif line.startswith("[AI]") or line.startswith("[INFERENCE]") or line.startswith("[OUTPUT]"):
            color = ACCENT_PURPLE
        elif line.startswith("[DISPATCH]") or line.startswith("[SLACK]") or line.startswith("[QUALIFY]"):
            color = ACCENT_GREEN
        elif line.startswith("┌") or line.startswith("│") or line.startswith("└"):
            color = ACCENT_BLUE

        draw.text((term_x0 + 18, ty), line, fill=color, font=font_mono)
        ty += 28

    if int(t * 3) % 2 == 0:
        draw.text((term_x0 + 18, ty), "▌", fill=node["color"], font=font_mono_bold)

    # ── 4. Bottom Subtitle & Audio Waveform Card (Y: 612 to 706) ──────────────
    sub_x0, sub_y0 = 25, 612
    sub_x1, sub_y1 = WIDTH - 25, 706
    draw_rounded_rect(draw, (sub_x0, sub_y0, sub_x1, sub_y1), radius=10, fill=PANEL_BG, outline=node["color"], width=2)

    # Waveform equalizer (8 animated bars)
    wave_x = sub_x0 + 18
    wave_y_center = sub_y0 + 22
    for b in range(10):
        bar_h = int(5 + 14 * abs(math.sin((t * 6) + b * 0.8)))
        bx = wave_x + b * 6
        draw.line([(bx, wave_y_center - bar_h // 2), (bx, wave_y_center + bar_h // 2)], fill=node["color"], width=3)

    draw.text((sub_x0 + 85, sub_y0 + 13), f"AI VOICEOVER & SUBTITLE  ::  {node['name'].upper()}", fill=node["color"], font=font_badge)
    draw.text((sub_x0 + 20, sub_y0 + 44), node["subtitle"], fill=TEXT_WHITE, font=font_subtitle)

    # ── 5. Bottom Timeline Bar ────────────────────────────────────────────────
    draw.rectangle([0, HEIGHT - 6, WIDTH, HEIGHT], fill=(22, 27, 34))
    draw.rectangle([0, HEIGHT - 6, int(WIDTH * (t / total_duration)), HEIGHT], fill=node["color"])

    return img


def main():
    assets_dir = Path("docs/assets")
    audio_dir = assets_dir / "audio"
    assets_dir.mkdir(parents=True, exist_ok=True)

    print("[1/4] Synthesizing / verifying voiceover audio...")
    combined_audio = asyncio.run(synthesize_all_voiceovers(audio_dir))

    # Measure exact durations
    durations = [get_audio_duration(audio_dir / f"node_{n['id']}.mp3") for n in NODES]
    total_duration = sum(durations)
    total_frames = int(total_duration * FPS)

    print(f"\n[2/4] Node Audio Durations:")
    for i, d in enumerate(durations):
        print(f"  Node {i+1}: {d:.2f}s ({int(d*FPS)} frames)")
    print(f"Total Video Duration: {total_duration:.2f}s ({total_frames} frames @ {FPS} fps)")

    # Render video stream
    raw_video = assets_dir / "temp_video.mp4"
    final_mp4 = assets_dir / "explainer.mp4"
    final_gif = assets_dir / "explainer.gif"

    print(f"\n[3/4] Rendering synchronized screen recording ({total_frames} frames)...")

    cmd = [
        "ffmpeg", "-y",
        "-f", "rawvideo", "-vcodec", "rawvideo",
        "-s", f"{WIDTH}x{HEIGHT}",
        "-pix_fmt", "rgb24",
        "-r", str(FPS),
        "-i", "-",
        "-c:v", "libx264", "-pix_fmt", "yuv420p",
        "-preset", "fast", "-crf", "20",
        str(raw_video)
    ]
    proc = subprocess.Popen(cmd, stdin=subprocess.PIPE, stderr=subprocess.DEVNULL)

    current_frame = 0
    accumulated_time = 0.0

    for node_idx, dur in enumerate(durations):
        node_frames = int(dur * FPS)
        for f in range(node_frames):
            t = accumulated_time + (f / FPS)
            node_local_t = f / max(node_frames, 1)
            frame_img = render_screen_frame(t, node_idx, node_local_t, total_duration)
            proc.stdin.write(frame_img.tobytes())
            current_frame += 1
            if current_frame % 50 == 0 or current_frame == total_frames - 1:
                pct = (current_frame / total_frames) * 100
                print(f"  Frame {current_frame}/{total_frames} ({pct:.1f}%)", flush=True)
        accumulated_time += dur

    proc.stdin.close()
    proc.wait()

    # Mux audio and video together
    print("\n[4/4] Muxing video and studio voiceover...")
    mux_cmd = [
        "ffmpeg", "-y",
        "-i", str(raw_video),
        "-i", str(combined_audio),
        "-c:v", "copy",
        "-c:a", "aac", "-b:a", "192k",
        "-shortest",
        str(final_mp4)
    ]
    subprocess.run(mux_cmd, check=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    if raw_video.exists():
        raw_video.unlink()

    print(f"✅ Final video with voiceover: {final_mp4.resolve()} ({final_mp4.stat().st_size / 1024:.1f} KB)")

    # Build optimized looping GIF
    print("Generating optimized looping GIF preview for GitHub README...", flush=True)
    gif_cmd = [
        "ffmpeg", "-y",
        "-i", str(final_mp4),
        "-vf", "fps=8,scale=800:-1:flags=lanczos,split[s0][s1];[s0]palettegen=max_colors=96[p];[s1][p]paletteuse=dither=bayer:bayer_scale=3",
        str(final_gif)
    ]
    subprocess.run(gif_cmd, check=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    print(f"✅ Loop GIF created: {final_gif.resolve()} ({final_gif.stat().st_size / 1024:.1f} KB)")
    print("All artifacts generated successfully!")

if __name__ == "__main__":
    main()
