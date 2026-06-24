#!/usr/bin/env python3
"""Fetch free RSS feeds and build data/news.json for Hermes News.
No third-party dependencies; safe for GitHub Actions.
"""
from __future__ import annotations
import datetime as dt
import email.utils
import hashlib
import html
import json
import re
import sys
import urllib.parse
import urllib.request
import xml.etree.ElementTree as ET
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / 'data' / 'news.json'
UA = 'HermesNewsBot/1.0 (+https://github.com/BassSG/Hermes_News)'

TOPICS = [
    ('Top Thailand', 'https://news.google.com/rss?hl=th&gl=TH&ceid=TH:th', 'thailand'),
    ('ข่าวด่วน ไทย', 'https://news.google.com/rss/search?q=' + urllib.parse.quote('ข่าวด่วน ไทย OR ข่าวดัง ไทย') + '&hl=th&gl=TH&ceid=TH:th', 'breaking'),
    ('การเมืองไทย', 'https://news.google.com/rss/search?q=' + urllib.parse.quote('การเมืองไทย OR รัฐบาล OR นายก OR สภา') + '&hl=th&gl=TH&ceid=TH:th', 'politics'),
    ('เศรษฐกิจไทย', 'https://news.google.com/rss/search?q=' + urllib.parse.quote('เศรษฐกิจไทย OR หุ้นไทย OR ค่าเงินบาท OR น้ำมัน OR ทองคำ') + '&hl=th&gl=TH&ceid=TH:th', 'business'),
    ('ต่างประเทศสำคัญ', 'https://news.google.com/rss/search?q=' + urllib.parse.quote('สงคราม OR ทรัมป์ OR จีน OR สหรัฐ OR รัสเซีย OR อิสราเอล OR ยูเครน') + '&hl=th&gl=TH&ceid=TH:th', 'world'),
    ('เทคโนโลยี', 'https://news.google.com/rss/search?q=' + urllib.parse.quote('AI OR เทคโนโลยี OR ไซเบอร์ OR มือถือ') + '&hl=th&gl=TH&ceid=TH:th', 'tech'),
]

CATEGORY_KEYWORDS = {
    'politics': ['รัฐบาล','นายก','รัฐมนตรี','สภา','เลือกตั้ง','พรรค','กฎหมาย','ศาลรัฐธรรมนูญ','มติ'],
    'business': ['หุ้น','เงินบาท','เศรษฐกิจ','ทอง','น้ำมัน','ธนาคาร','ตลาด','เงินเฟ้อ','ดอกเบี้ย','ภาษี'],
    'world': ['สหรัฐ','จีน','รัสเซีย','ยูเครน','อิสราเอล','ฮามาส','ทรัมป์','โลก','ต่างประเทศ','สงคราม'],
    'tech': ['AI','เอไอ','เทคโนโลยี','ไซเบอร์','มือถือ','ชิป','Google','Apple','Microsoft','OpenAI'],
    'culture': ['กีฬา','บอล','บันเทิง','ดารา','ซีรีส์','เพลง'],
}
BREAKING_WORDS = ['ด่วน','ล่าสุด','ช็อก','ใหญ่','จับตา','วิกฤต','เตือน','ประกาศ','เสียชีวิต','ถล่ม','ฉุกเฉิน']
TH_WORDS = ['ไทย','กทม','กรุงเทพ','จังหวัด','รัฐบาล','ตำรวจ','สภา','นายก','เงินบาท','หุ้นไทย']

def fetch(url: str) -> bytes:
    req = urllib.request.Request(url, headers={'User-Agent': UA})
    with urllib.request.urlopen(req, timeout=30) as r:
        return r.read()

def clean(text: str) -> str:
    text = html.unescape(re.sub(r'<[^>]+>', ' ', text or ''))
    text = re.sub(r'\s+', ' ', text).strip()
    return text

def parse_date(value: str) -> str:
    if not value:
        return dt.datetime.now(dt.timezone.utc).isoformat()
    try:
        parsed = email.utils.parsedate_to_datetime(value)
        if parsed.tzinfo is None:
            parsed = parsed.replace(tzinfo=dt.timezone.utc)
        return parsed.astimezone(dt.timezone.utc).isoformat()
    except Exception:
        return dt.datetime.now(dt.timezone.utc).isoformat()

def category_for(text: str, default: str) -> str:
    if default in {'politics','business','world','tech'}:
        return default
    for cat, words in CATEGORY_KEYWORDS.items():
        if any(w.lower() in text.lower() for w in words):
            return cat
    if any(w in text for w in TH_WORDS):
        return 'thailand'
    return 'general'

def score_story(title: str, summary: str, source: str, topic: str, published_at: str) -> int:
    text = f'{title} {summary}'
    score = 45
    if topic == 'breaking': score += 18
    if any(w in text for w in BREAKING_WORDS): score += 16
    if any(w in text for w in TH_WORDS): score += 12
    if topic in {'politics','business'}: score += 7
    if topic == 'world': score += 2
    if source in {'BBC News ไทย','Thai PBS','ประชาชาติธุรกิจ','กรุงเทพธุรกิจ','ไทยรัฐ','มติชน'}: score += 5
    try:
        age_hours = (dt.datetime.now(dt.timezone.utc) - dt.datetime.fromisoformat(published_at)).total_seconds() / 3600
        if age_hours < 3: score += 12
        elif age_hours < 8: score += 8
        elif age_hours < 24: score += 3
        else: score -= 8
    except Exception:
        pass
    return max(1, min(100, score))

def why_it_matters(cat: str, title: str) -> str:
    if cat == 'politics': return 'เกี่ยวกับการเมือง/นโยบายไทย อาจกระทบชีวิตประจำวัน กฎหมาย หรือทิศทางประเทศ'
    if cat == 'business': return 'เกี่ยวกับเศรษฐกิจ เงิน ตลาด หรือค่าครองชีพ ควรรู้ก่อนเริ่มวัน'
    if cat == 'world': return 'เป็นประเด็นต่างประเทศที่อาจส่งผลต่อภูมิรัฐศาสตร์ เศรษฐกิจโลก หรือ sentiment ในไทย'
    if cat == 'tech': return 'เป็นเทรนด์เทคโนโลยี/AI/ไซเบอร์ที่อาจกระทบการทำงานและธุรกิจ'
    return 'เป็นข่าวที่กำลังถูกพูดถึงสูงในรอบเช้าและควรรู้เพื่อไม่ตกกระแส'

def parse_feed(name: str, url: str, topic: str):
    raw = fetch(url)
    root = ET.fromstring(raw)
    items = []
    for item in root.findall('.//item')[:25]:
        title = clean(item.findtext('title'))
        link = clean(item.findtext('link'))
        desc = clean(item.findtext('description'))
        pub = parse_date(item.findtext('pubDate'))
        source_el = item.find('source')
        source = clean(source_el.text if source_el is not None else name)
        text = f'{title} {desc}'
        cat = category_for(text, topic)
        story_id = hashlib.sha1((re.sub(r'\W+', '', title.lower())[:80] + source).encode('utf-8')).hexdigest()[:12]
        summary = desc
        # Google descriptions often append publisher lists; keep it readable.
        if len(summary) > 260:
            summary = summary[:257].rsplit(' ', 1)[0] + '…'
        items.append({
            'id': story_id,
            'title': title,
            'summary': summary,
            'description': desc,
            'link': link,
            'source': source,
            'published_at': pub,
            'category': cat,
            'topic': topic,
            'country_focus': 'TH' if any(w in text for w in TH_WORDS) or topic != 'world' else 'GLOBAL',
            'is_breaking': topic == 'breaking' or any(w in text for w in BREAKING_WORDS),
        })
    return items

def build():
    stories = []
    errors = []
    for name, url, topic in TOPICS:
        try:
            stories.extend(parse_feed(name, url, topic))
        except Exception as e:
            errors.append({'source': name, 'error': str(e)})
    # Deduplicate by normalized title stem.
    seen = {}
    for s in stories:
        key = re.sub(r'[^\wก-๙]+', '', s['title'].lower())[:60]
        s['score'] = score_story(s['title'], s['summary'], s['source'], s['topic'], s['published_at'])
        s['why_it_matters'] = why_it_matters(s['category'], s['title'])
        if key not in seen or s['score'] > seen[key]['score']:
            seen[key] = s
    final = sorted(seen.values(), key=lambda s: (s['score'], s['published_at']), reverse=True)[:36]
    payload = {
        'generated_at': dt.datetime.now(dt.timezone.utc).isoformat(),
        'is_live': bool(final),
        'sources': [{'name': name, 'topic': topic, 'url': url} for name, url, topic in TOPICS],
        'errors': errors,
        'stories': final,
    }
    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding='utf-8')
    print(f'Wrote {OUT} with {len(final)} stories ({len(errors)} feed errors)')
    if errors:
        print(json.dumps(errors, ensure_ascii=False, indent=2), file=sys.stderr)

if __name__ == '__main__':
    build()
