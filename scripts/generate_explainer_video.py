"""
OmniLead-AI Video Explainer Generator
======================================
Renders a 720p HD animated video explainer + optimized GIF showing how each
pipeline node works with high-contrast subtitles, live telemetry, and visual data flow.
"""
import math
import os
import subprocess
import sys
from pathlib import Path
from PIL import Image, ImageDraw, ImageFont

# Canvas dimensions
WIDTH = 1280
HEIGHT = 720
FPS = 25

# Colors (GitHub Dark modern theme)
BG_COLOR = (13, 17, 23)
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

# Load system fonts
FONT_DIR = "C:\\Windows\\Fonts"
font_title = ImageFont.truetype(os.path.join(FONT_DIR, "segoeui.ttf"), 22)
font_subtitle = ImageFont.truetype(os.path.join(FONT_DIR, "segoeui.ttf"), 18)
font_caption_bold = ImageFont.truetype(os.path.join(FONT_DIR, "segoeuib.ttf"), 17)
font_caption = ImageFont.truetype(os.path.join(FONT_DIR, "segoeui.ttf"), 17)
font_mono = ImageFont.truetype(os.path.join(FONT_DIR, "consola.ttf"), 15)
font_mono_bold = ImageFont.truetype(os.path.join(FONT_DIR, "consolab.ttf"), 15)
font_small = ImageFont.truetype(os.path.join(FONT_DIR, "segoeui.ttf"), 13)
font_badge = ImageFont.truetype(os.path.join(FONT_DIR, "segoeuib.ttf"), 12)

# Nodes definition
NODES = [
    {
        "id": 1,
        "name": "1. Ingestion",
        "sub": "Rate Limiter",
        "icon": "IN",
        "color": ACCENT_BLUE,
        "title": "Node 1: Input Ingestion & Token-Bucket Rate Limiter",
        "subtitle": "Step 1/5: Ingests CSV/JSON leads with an asynchronous Token-Bucket limiter to prevent rate limits and website bans.",
        "telemetry": [
            "[INIT] Ingesting source: sample_leads.csv (10 targets detected)",
            "[QUEUE] Concurrency limit initialized: max 5 simultaneous workers",
            "[RATE_LIMIT] Token bucket configured: 2.0 requests/sec with burst ceiling = 5",
            "[INPUT_RECORD] -> Target 1: GrowthStack (https://growthstack.io)",
            "[STATUS] Acquire semaphore slot #1 ... GRANTED (0.01s latency)",
        ]
    },
    {
        "id": 2,
        "name": "2. Crawler",
        "sub": "HTTPX + BS4",
        "icon": "WEB",
        "color": ACCENT_CYAN,
        "title": "Node 2: Asynchronous Web Crawler & Tech Stack Detector",
        "subtitle": "Step 2/5: Fetches homepage HTML asynchronously, extracts meta tags, detects tech stack (Shopify/React/HubSpot), & harvests socials.",
        "telemetry": [
            "[HTTPX] GET https://growthstack.io HTTP/2.0 (User-Agent: Mozilla/5.0 Win64)",
            "[RESPONSE] 200 OK | Size: 48.2 KB | Content-Type: text/html; charset=utf-8",
            "[PARSER] Stripping noise scripts/styles; extracting body content & meta tags",
            "[STACK_DETECTED] Technology signals found: ['HubSpot', 'React', 'Stripe', 'Google Analytics']",
            "[SOCIAL_HARVEST] Discovered: linkedin.com/company/growthstack | twitter.com/growthstack",
        ]
    },
    {
        "id": 3,
        "name": "3. Verifier",
        "sub": "DNS MX Check",
        "icon": "DNS",
        "color": ACCENT_YELLOW,
        "title": "Node 3: 3-Layer Email Deliverability & DNS MX Resolver",
        "subtitle": "Step 3/5: Runs RFC-5322 regex validation, checks 50+ disposable email blacklists, and queries live DNS MX records.",
        "telemetry": [
            "[EMAIL] Testing prospect: marcus@growthstack.io",
            "[LAYER_1] RFC-5322 regex syntax validation: PASS",
            "[LAYER_2] Disposable domain blacklist check (growthstack.io): CLEAN (Not disposable)",
            "[LAYER_3] Async DNS query for 'growthstack.io' MX records ...",
            "[DNS_RESOLVE] Found 5 MX records: ['aspmx.l.google.com', 'alt1.aspmx.l.google.com', ...]",
            "[RESULT] Deliverability Score: 92/100 | Risk Status: SAFE (Inbox Verified)",
        ]
    },
    {
        "id": 4,
        "name": "4. Gemini AI",
        "sub": "3.8 Flash Engine",
        "icon": "AI",
        "color": ACCENT_PURPLE,
        "title": "Node 4: Gemini 3.8 Flash AI Enrichment & Icebreaker Generator",
        "subtitle": "Step 4/5: Gemini AI ingests company data, scores ICP (0-100), extracts pain points, and drafts hyper-customized icebreakers.",
        "telemetry": [
            "[MODEL] Initializing google-genai client with model: gemini-3.8-flash",
            "[PROMPT] Context window: scraped title, page summary, tech stack, prospect role",
            "[RESPONSE] Structured JSON schema returned (latency: 340ms):",
            "  * ICP Match Score: 92/100 (HOT LEAD)",
            "  * Pain Points: ['CRM sync latency', 'Manual data entry 10h/wk', 'Duplicate pipelines']",
            "  * Icebreaker: 'Noticed GrowthStack integrates with both HubSpot & Salesforce...'",
            "  * Suggested CTA: 'Would it be worth a 15-min call to show what that looks like?'",
        ]
    },
    {
        "id": 5,
        "name": "5. Dispatcher",
        "sub": "Webhooks + CRM",
        "icon": "SYNC",
        "color": ACCENT_GREEN,
        "title": "Node 5: Resilient Dispatcher with Exponential Backoff",
        "subtitle": "Step 5/5: Exports structured UTF-8 CSV and pushes hot leads directly to GoHighLevel/HubSpot CRM & Slack alerts with auto-retry.",
        "telemetry": [
            "[CSV_EXPORT] Writing unified row to output/enriched_leads.csv (21 columns populated)",
            "[FILTER] Lead qualification check: ICP=92 >= 80 threshold -> MARKED HOT LEAD 🔥",
            "[DISPATCH] POST https://services.leadconnectorhq.com/hooks/ghl_inbound (Attempt 1/3)",
            "[CRM_RESPONSE] HTTP 200 OK — Contact & Custom Fields synced to GoHighLevel CRM",
            "[NOTIFICATION] Slack Webhook alert dispatched to #growth-alerts (HTTP 200 OK)",
            "[STATUS] Pipeline run COMPLETE for lead: marcus@growthstack.io",
        ]
    }
]

DURATION_PER_NODE = 3.5  # seconds
TOTAL_DURATION = len(NODES) * DURATION_PER_NODE
TOTAL_FRAMES = int(TOTAL_DURATION * FPS)

def draw_rounded_rect(draw, bbox, radius, fill=None, outline=None, width=1):
    x0, y0, x1, y1 = bbox
    draw.rounded_rectangle([x0, y0, x1, y1], radius=radius, fill=fill, outline=outline, width=width)

def render_frame(frame_idx: int) -> Image.Image:
    t = frame_idx / FPS
    current_node_idx = min(int(t / DURATION_PER_NODE), len(NODES) - 1)
    node_data = NODES[current_node_idx]
    node_local_t = (t % DURATION_PER_NODE) / DURATION_PER_NODE

    img = Image.new("RGB", (WIDTH, HEIGHT), BG_COLOR)
    draw = ImageDraw.Draw(img)

    # ── 1. Top Header Banner ──────────────────────────────────────────────────
    # Top badge
    draw_rounded_rect(draw, (30, 20, 230, 44), radius=6, fill=(33, 38, 45), outline=node_data["color"], width=1)
    draw.text((40, 24), "● LIVE PIPELINE FLOW", fill=node_data["color"], font=font_badge)

    # Title & Subtitle
    draw.text((250, 20), "OmniLead-AI  •  Architecture & Node Execution Flow", fill=TEXT_WHITE, font=font_title)
    draw.text((250, 48), "Autonomous B2B Lead Scraping, DNS Verification, Gemini AI & CRM Pipeline", fill=TEXT_MUTED, font=font_small)

    # ── 2. Node Pipeline Ribbon (Y: 85 to 195) ─────────────────────────────────
    node_w = 210
    node_h = 80
    gap = 25
    start_x = 30
    node_y = 90

    # Draw connectors first
    for i in range(len(NODES) - 1):
        x1 = start_x + i * (node_w + gap) + node_w
        x2 = start_x + (i + 1) * (node_w + gap)
        cy = node_y + node_h // 2
        # Track line
        draw.line([(x1, cy), (x2, cy)], fill=PANEL_BORDER, width=3)

        # Animated packet moving along line
        if i < current_node_idx:
            # Completed transition - line is filled
            draw.line([(x1, cy), (x2, cy)], fill=ACCENT_GREEN, width=3)
        elif i == current_node_idx:
            # Active transition packet
            packet_pct = (math.sin(node_local_t * math.pi * 3) + 1) / 2
            px = x1 + packet_pct * (x2 - x1)
            draw.ellipse([px - 4, cy - 4, px + 4, cy + 4], fill=node_data["color"])

    # Draw nodes
    for i, n in enumerate(NODES):
        nx = start_x + i * (node_w + gap)
        is_active = (i == current_node_idx)
        is_done = (i < current_node_idx)

        if is_active:
            # Glowing active node
            border_color = n["color"]
            fill_color = (25, 33, 44)
            badge_text = "PROCESSING"
            badge_color = n["color"]
            border_w = 2
        elif is_done:
            border_color = ACCENT_GREEN
            fill_color = (20, 30, 24)
            badge_text = "COMPLETE"
            badge_color = ACCENT_GREEN
            border_w = 1
        else:
            border_color = PANEL_BORDER
            fill_color = PANEL_BG
            badge_text = "IDLE"
            badge_color = TEXT_DIM
            border_w = 1

        draw_rounded_rect(draw, (nx, node_y, nx + node_w, node_y + node_h), radius=8, fill=fill_color, outline=border_color, width=border_w)

        # Status indicator dot
        draw.ellipse([nx + 12, node_y + 14, nx + 20, node_y + 22], fill=badge_color)
        draw.text((nx + 26, node_y + 11), badge_text, fill=badge_color, font=font_badge)

        # Node name & sub
        draw.text((nx + 12, node_y + 32), n["name"], fill=TEXT_WHITE, font=font_caption_bold)
        draw.text((nx + 12, node_y + 53), n["sub"], fill=TEXT_MUTED, font=font_small)

    # ── 3. Central Telemetry Console (Y: 195 to 570) ───────────────────────────
    term_x0, term_y0 = 30, 195
    term_x1, term_y1 = WIDTH - 30, 570
    draw_rounded_rect(draw, (term_x0, term_y0, term_x1, term_y1), radius=10, fill=PANEL_BG, outline=PANEL_BORDER, width=1)

    # Terminal header bar
    draw_rounded_rect(draw, (term_x0, term_y0, term_x1, term_y0 + 36), radius=10, fill=(28, 33, 40), outline=PANEL_BORDER, width=1)
    # macOS window controls
    draw.ellipse([term_x0 + 15, term_y0 + 13, term_x0 + 25, term_y0 + 23], fill=(248, 81, 73))
    draw.ellipse([term_x0 + 33, term_y0 + 13, term_x0 + 43, term_y0 + 23], fill=(210, 153, 34))
    draw.ellipse([term_x0 + 51, term_y0 + 13, term_x0 + 61, term_y0 + 23], fill=(46, 160, 67))

    # Terminal title
    draw.text((term_x0 + 75, term_y0 + 9), f"Live Telemetry Console  ::  {node_data['title']}", fill=TEXT_MUTED, font=font_small)

    # Terminal log lines
    log_y = term_y0 + 50
    lines = node_data["telemetry"]
    max_visible_lines = min(len(lines), int(node_local_t * (len(lines) + 1)) + 1)

    for line_idx in range(max_visible_lines):
        line = lines[line_idx]
        color = TEXT_WHITE
        if line.startswith("[INIT]") or line.startswith("[QUEUE]"):
            color = ACCENT_BLUE
        elif line.startswith("[HTTPX]") or line.startswith("[RESPONSE]"):
            color = ACCENT_CYAN
        elif line.startswith("[DNS_RESOLVE]") or line.startswith("[RESULT]"):
            color = ACCENT_YELLOW
        elif line.startswith("[MODEL]") or line.startswith("[PROMPT]"):
            color = ACCENT_PURPLE
        elif line.startswith("[DISPATCH]") or line.startswith("[CRM_RESPONSE]") or line.startswith("[NOTIFICATION]"):
            color = ACCENT_GREEN

        draw.text((term_x0 + 20, log_y), line, fill=color, font=font_mono)
        log_y += 32

    # Blinking terminal cursor
    if int(t * 3) % 2 == 0:
        draw.text((term_x0 + 20, log_y), "▌", fill=node_data["color"], font=font_mono_bold)

    # ── 4. Subtitle / Explainer Card (Y: 585 to 685) ───────────────────────────
    sub_x0, sub_y0 = 30, 585
    sub_x1, sub_y1 = WIDTH - 30, 685
    draw_rounded_rect(draw, (sub_x0, sub_y0, sub_x1, sub_y1), radius=10, fill=(22, 27, 34), outline=node_data["color"], width=2)

    # Left colored vertical pill
    draw_rounded_rect(draw, (sub_x0 + 10, sub_y0 + 12, sub_x0 + 16, sub_y1 - 12), radius=3, fill=node_data["color"])

    # Subtitle Header
    draw.text((sub_x0 + 28, sub_y0 + 14), "SUBTITLE / EXPLAINER:", fill=node_data["color"], font=font_badge)

    # Subtitle Body text
    draw.text((sub_x0 + 28, sub_y0 + 38), node_data["subtitle"], fill=TEXT_WHITE, font=font_caption)

    # ── 5. Bottom Timeline Progress Bar (Y: 710 to 716) ────────────────────────
    progress_pct = frame_idx / TOTAL_FRAMES
    draw.rectangle([0, HEIGHT - 6, WIDTH, HEIGHT], fill=(22, 27, 34))
    draw.rectangle([0, HEIGHT - 6, int(WIDTH * progress_pct), HEIGHT], fill=node_data["color"])

    return img


def main():
    assets_dir = Path("docs/assets")
    assets_dir.mkdir(parents=True, exist_ok=True)
    mp4_path = assets_dir / "explainer.mp4"
    gif_path = assets_dir / "explainer.gif"

    print(f"[1/3] Rendering {TOTAL_FRAMES} frames ({TOTAL_DURATION:.1f}s @ {FPS} fps)...")

    # Launch ffmpeg subprocess to receive raw RGB24 frames from stdin
    cmd = [
        "ffmpeg",
        "-y",
        "-f", "rawvideo",
        "-vcodec", "rawvideo",
        "-s", f"{WIDTH}x{HEIGHT}",
        "-pix_fmt", "rgb24",
        "-r", str(FPS),
        "-i", "-",
        "-c:v", "libx264",
        "-pix_fmt", "yuv420p",
        "-preset", "fast",
        "-crf", "22",
        str(mp4_path)
    ]

    proc = subprocess.Popen(cmd, stdin=subprocess.PIPE, stderr=subprocess.DEVNULL)

    for i in range(TOTAL_FRAMES):
        frame = render_frame(i)
        proc.stdin.write(frame.tobytes())
        if i % 50 == 0 or i == TOTAL_FRAMES - 1:
            print(f"  Frame {i}/{TOTAL_FRAMES} ({i/TOTAL_FRAMES*100:.1f}%)", flush=True)

    proc.stdin.close()
    proc.wait()

    if proc.returncode != 0:
        print(f"FFmpeg exited with error code {proc.returncode}")
        sys.exit(1)

    print(f"[2/3] MP4 video created successfully at: {mp4_path.resolve()} ({mp4_path.stat().st_size / 1024:.1f} KB)", flush=True)

    print("[3/3] Generating optimized looping GIF for GitHub README...", flush=True)
    # Convert MP4 to high quality lightweight GIF with palettegen
    gif_cmd = [
        "ffmpeg",
        "-y",
        "-i", str(mp4_path),
        "-vf", "fps=8,scale=800:-1:flags=lanczos,split[s0][s1];[s0]palettegen=max_colors=96[p];[s1][p]paletteuse=dither=bayer:bayer_scale=3",
        str(gif_path)
    ]
    subprocess.run(gif_cmd, check=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    print(f"GIF explainer created successfully at: {gif_path.resolve()} ({gif_path.stat().st_size / 1024:.1f} KB)")
    print("Done!")

if __name__ == "__main__":
    main()
