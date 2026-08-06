from __future__ import annotations

from dataclasses import dataclass, asdict
from pathlib import Path
import json
import requests
import time
import logging

from core.config import Settings

logger = logging.getLogger(__name__)


@dataclass(frozen=True)
class PaperRecord:
    paper_id: str
    title: str
    summary: str
    authors: list[str]
    categories: list[str]
    primary_category: str
    published: str
    updated: str
    abs_url: str
    pdf_url: str
    comment: str


def parse_date(date_obj: dict | None) -> str:
    """Helper để parse cấu trúc date-parts của Crossref thành chuỗi YYYY-MM-DD."""
    if not date_obj or "date-parts" not in date_obj:
        return ""
    parts = date_obj["date-parts"]
    if not parts or not parts[0]:
        return ""
    date_part = parts[0]
    try:
        if len(date_part) >= 3:
            return f"{int(date_part[0]):04d}-{int(date_part[1]):02d}-{int(date_part[2]):02d}"
        elif len(date_part) == 2:
            return f"{int(date_part[0]):04d}-{int(date_part[1]):02d}-01"
        elif len(date_part) == 1:
            return f"{int(date_part[0]):04d}-01-01"
    except (ValueError, TypeError):
        return ""
    return ""


def parse_crossref_payload(payload: dict) -> list[PaperRecord]:
    """Parse Crossref payload thành list PaperRecord.

    Lọc chỉ lấy các bản ghi có đầy đủ tiêu đề và tóm tắt (abstract hoặc description).
    Giữ nguyên các thẻ JATS XML trong tóm tắt ở bước này.
    """
    records = []
    message = payload.get("message", {})
    items = message.get("items", []) if isinstance(message, dict) else []
    
    for item in items:
        # 1. DOI -> paper_id
        paper_id = item.get("DOI", "")
        if not paper_id:
            continue
            
        # 2. Title -> title (lấy phần tử đầu tiên)
        titles = item.get("title", [])
        title = titles[0].strip() if titles else ""
        
        # 3. Abstract / Description -> summary (giữ nguyên XML)
        abstract = item.get("abstract", "")
        description = item.get("description", "")
        summary = abstract if abstract else description
        summary = summary.strip() if summary else ""
        
        # Lọc dữ liệu thô: Yêu cầu bắt buộc có đầy đủ tiêu đề và tóm tắt
        if not title or not summary:
            continue
            
        # 4. Authors -> authors (ghép given + family)
        authors = []
        for auth in item.get("author", []):
            given = auth.get("given", "").strip()
            family = auth.get("family", "").strip()
            name = f"{given} {family}".strip()
            if name:
                authors.append(name)
                
        # 5. Categories -> categories (từ subject)
        categories = item.get("subject", [])
        if not isinstance(categories, list):
            categories = []
        categories = [c.strip() for c in categories if c]
        
        # 6. Primary Category -> primary_category
        primary_category = categories[0] if categories else "unknown"
        
        # 7. Dates -> published và updated
        published = ""
        for field in ["published-print", "published-online", "published", "issued", "created"]:
            val = parse_date(item.get(field))
            if val:
                published = val
                break
                
        updated = ""
        for field in ["indexed", "updated", "created"]:
            val = parse_date(item.get(field))
            if val:
                updated = val
                break
        if not updated:
            updated = published
            
        # 8. URLs -> abs_url và pdf_url
        abs_url = item.get("URL", "")
        if not abs_url:
            abs_url = f"https://doi.org/{paper_id}"
            
        pdf_url = ""
        for link_item in item.get("link", []):
            if link_item.get("content-type") == "application/pdf":
                pdf_url = link_item.get("URL", "")
                break
                
        # 9. Publisher -> comment
        comment = item.get("publisher", "")
        
        records.append(
            PaperRecord(
                paper_id=paper_id,
                title=title,
                summary=summary,
                authors=authors,
                categories=categories,
                primary_category=primary_category,
                published=published,
                updated=updated,
                abs_url=abs_url,
                pdf_url=pdf_url,
                comment=comment,
            )
        )
        
    return records


def fetch_source_records(settings: Settings) -> list[PaperRecord]:
    """Gọi source API, thực hiện retry & backoff, lưu raw response và parse thành records."""
    url = "https://api.crossref.org/works"
    
    # 1. Tạo params từ cấu hình
    params = {
        "query": settings.source_query,
        "filter": settings.source_filter,
        "rows": settings.max_results,
    }
    
    # Sử dụng email đã thỏa thuận để tham gia Polite Pool
    headers = {
        "User-Agent": "DataPipelineLab/1.0 (mailto:26ai.thangnv@vinuni.edu.vn)"
    }
    
    # 2. Gọi API với retry cho các status code như 429/503
    max_retries = 5
    backoff = 1.0
    response_json = None
    
    for attempt in range(max_retries):
        try:
            logger.info(f"Fetching from Crossref API (attempt {attempt + 1}/{max_retries})...")
            response = requests.get(url, params=params, headers=headers, timeout=30)
            
            if response.status_code == 200:
                response_json = response.json()
                break
            elif response.status_code in {429, 503}:
                logger.warning(
                    f"Crossref API returned temporary status {response.status_code}. "
                    f"Retrying in {backoff} seconds..."
                )
                time.sleep(backoff)
                backoff *= 2
            else:
                response.raise_for_status()
        except requests.RequestException as e:
            if attempt == max_retries - 1:
                logger.error(f"Failed to fetch records after {max_retries} attempts.")
                raise
            logger.warning(f"Request failed due to error: {e}. Retrying in {backoff} seconds...")
            time.sleep(backoff)
            backoff *= 2
            
    if response_json is None:
        raise RuntimeError("Failed to retrieve data from Crossref API.")
        
    # 3. Lưu raw response vào settings.paths.raw_api_response
    settings.paths.raw_api_response.parent.mkdir(parents=True, exist_ok=True)
    with open(settings.paths.raw_api_response, "w", encoding="utf-8") as f:
        json.dump(response_json, f, indent=2, ensure_ascii=False)
        
    # 4. Parse payload thành records
    records = parse_crossref_payload(response_json)
    
    # 5. Lưu records đã parse vào settings.paths.raw_records_json
    settings.paths.raw_records_json.parent.mkdir(parents=True, exist_ok=True)
    with open(settings.paths.raw_records_json, "w", encoding="utf-8") as f:
        json.dump([asdict(r) for r in records], f, indent=2, ensure_ascii=False)
        
    return records


def load_raw_records(path: Path) -> list[PaperRecord]:
    """Đọc JSON snapshot và map thành PaperRecord."""
    if not path.exists():
        logger.warning(f"Snapshot file not found at {path}")
        return []
        
    with open(path, "r", encoding="utf-8") as f:
        data = json.load(f)
        
    if not isinstance(data, list):
        raise ValueError(f"Expected a JSON list of records in {path}")
        
    return [PaperRecord(**item) for item in data]

