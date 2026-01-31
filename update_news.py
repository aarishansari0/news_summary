import feedparser
import json
import hashlib
from datetime import datetime, timezone
import re
import ollama
import os
from newspaper import Article



articles = []
existing_summaries = {}

if os.path.exists("news.json"):
    with open("news.json", "r") as f:
        old = json.load(f)
        for a in old.get("articles", []):
            if "content_hash" in a and "ai_summary" in a:
                existing_summaries[a["content_hash"]] = a["ai_summary"]


RSS_FEEDS = {
    "Reuters": "https://feeds.reuters.com/reuters/topNews",
    "BBC": "http://feeds.bbci.co.uk/news/rss.xml",
    "Al Jazeera": "https://www.aljazeera.com/xml/rss/all.xml"
}

TAG_RULES = {
    "politics": {
        "government": 3,
        "election": 3,
        "minister": 2,
        "parliament": 3,
        "policy": 2,
        "law": 2,
        "vote": 2,
        "bjp": 3,
        "congress": 3
    },
    "business": {
        "market": 2,
        "economy": 3,
        "stock": 3,
        "company": 2,
        "trade": 2,
        "inflation": 3,
        "startup": 2,
        "gdp": 3,
        "revenue": 2
    },
    "technology": {
        "artificial intelligence": 3,
        "ai": 2,
        "software": 2,
        "technology": 2,
        "chip": 3,
        "data": 1,
        "cyber": 2
    },
    "sports": {
        "cricket": 3,
        "football": 3,
        "match": 2,
        "tournament": 2,
        "league": 2,
        "goal": 2,
        "ipl": 3,
        "finals":3
    },
    "conflict": {
        "war": 3,
        "attack": 2,
        "missile": 3,
        "military": 2,
        "strike": 2,
        "killed": 2
    }
}


PROMPT_TEMPLATE = """
Extract ONLY factual bullet points from the text below.

STRICT RULES:
- Output ONLY bullet points
- No introductions, no explanations, no notes
- Do NOT say how many points there are
- Do NOT mention limitations
- Each bullet must be one factual statement
- If facts are limited, output fewer bullets

Text:
{article}
"""

def make_id(title, source):
    return hashlib.sha1(f"{title}{source}".encode()).hexdigest()

def content_hash(text):
    return hashlib.sha1(text.encode("utf-8")).hexdigest()

def extract_image(entry):
    if "media_content" in entry:
        return entry.media_content[0].get("url")

    if "media_thumbnail" in entry:
        return entry.media_thumbnail[0].get("url")

    if "enclosures" in entry and entry.enclosures:
        return entry.enclosures[0].get("href")

    summary = entry.get("summary", "")
    match = re.search(r'<img[^>]+src="([^">]+)"', summary)
    if match:
        return match.group(1)

    return None

def chunk_text(text, max_chars=1500):
    chunks = []
    start = 0

    while start < len(text):
        end = start + max_chars
        chunk = text[start:end]
        chunks.append(chunk)
        start = end

    return chunks[:3]  # HARD CAP (important)

def fetch_full_article(url):
    try:
        article = Article(url)
        article.download()
        article.parse()

        text = article.text.strip()
        if len(text) < 500:
            return None

        return text
    except Exception as e:
        print("Failed to fetch article:", e)
        return None

def choose_model(article):
    text_len = len(article["text"])
    tag = article.get("primary_tag", "general")

    if text_len > 900:
        return "llama3.2:3b"
    if tag in ["politics", "conflict"]:
        return "llama3.2:3b"

    return "llama3.2:1b"

def clean_ai_summary(text):
    lines = text.splitlines()
    bullets = []

    for line in lines:
        line = line.strip()

        if line.startswith(("•", "-", "*", "1.", "2.", "3.", "4.", "5.")):
            line = re.sub(r"^[\d\.\-\*\•\s]+", "", line)
            bullets.append(f"• {line}")

    return "\n".join(bullets)

def summarize(article_text, model):
    response = ollama.chat(
        model=model,
        messages=[
            {
                "role": "user",
                "content": PROMPT_TEMPLATE.format(article=article_text)
            }
        ],
        options={
            "temperature": 0.2
        }
    )
    return response["message"]["content"].strip()

def summarize_chunks(chunks, model):
    partials = []

    for chunk in chunks:
        raw = summarize(chunk, model)
        cleaned = clean_ai_summary(raw)

        if cleaned:
            partials.append(cleaned)

    return "\n".join(partials)

def merge_summaries(partial_summary, model):
    raw = summarize(partial_summary, model)
    return clean_ai_summary(raw)

def extract_tags(title, summary):
    title_text = title.lower()
    summary_text = summary.lower() if summary else ""

    def clean(text):
        text = re.sub(r"<[^>]+>", " ", text)
        return re.sub(r"[^a-z0-9\s]", " ", text)

    title_text = clean(title_text)
    summary_text = clean(summary_text)

    scores = {}

    for tag, keywords in TAG_RULES.items():
        score = 0

        for kw, weight in keywords.items():
            pattern = rf"\b{re.escape(kw)}\b"

            if re.search(pattern, title_text):
                score += weight + 1   # title boost
            elif re.search(pattern, summary_text):
                score += weight

        if score > 0:
            scores[tag] = score

    if not scores:
        return ["general"]

    # sort tags by score
    ranked = sorted(scores.items(), key=lambda x: x[1], reverse=True)

    primary_tag, primary_score = ranked[0]
    tags = [primary_tag]

    # optional secondary tag
    if len(ranked) > 1:
        second_tag, second_score = ranked[1]
        if second_score >= primary_score * 0.7:
            tags.append(second_tag)

    return tags

for source, url in RSS_FEEDS.items():
    feed = feedparser.parse(url)
    i=1
    for entry in feed.entries[:15]:  # limit per source

        published = entry.get("published", "")
        try:
            published_dt = datetime(*entry.published_parsed[:6], tzinfo=timezone.utc)
            published_iso = published_dt.isoformat()
        except:
            published_iso = None
        
        tags = extract_tags(entry.title, entry.get("summary", ""))
        primary_tag = tags[0] if tags else "general"

        rss_text = f"{entry.title}. {entry.get('summary', '')}"
        full_text = fetch_full_article(entry.link)

        if full_text:
            chunks = chunk_text(full_text)
            model = choose_model({
                "text": full_text,
                "primary_tag": primary_tag
            })
            partial = summarize_chunks(chunks, model)
            article_text = merge_summaries(partial, model)
        else:
            article_text = rss_text
        hash_value = content_hash(
            full_text if full_text else rss_text
        )




        article = {
            "id": make_id(entry.title, source),
            "title": entry.title,
            "link": entry.link,
            "summary": entry.get("summary", ""),
            "source": source,
            "publishedAt": published_iso,
            "tags": tags,
            "image":extract_image(entry),
            "content_hash": hash_value
        }

        # AI summary (cached)
        if hash_value in existing_summaries:
            article["ai_summary"] = existing_summaries[hash_value]
        else:
            if full_text:
                article["ai_summary"] = article_text  # already summarized
            else:
                model = choose_model({
                    "text": article_text,
                    "primary_tag": primary_tag
                })
                article["ai_summary"] = summarize(article_text, model)


        articles.append(article)
        print(f"done articlenumber {i}")
        i+=1




# sort newest first
articles.sort(
    key=lambda x: x["publishedAt"] or "",
    reverse=True
)

output = {
    "lastUpdated": datetime.now(timezone.utc).isoformat(),
    "articles": articles
}

with open("news.json", "w", encoding="utf-8") as f:
    json.dump(output, f, ensure_ascii=False, indent=2)

print(f"Saved {len(articles)} articles")
