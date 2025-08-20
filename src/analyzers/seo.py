"""
SEO analysis module
"""
import json
from pathlib import Path
from urllib.parse import urlparse
from crawl4ai import AsyncWebCrawler, CrawlerRunConfig, JsonCssExtractionStrategy
from ..config.schemas import SEO_SCHEMA


class SEOAnalyzer:
    """Handles SEO analysis for web pages"""
    
    def __init__(self):
        self.schema = SEO_SCHEMA
    
    async def analyze(self, url: str, output_dir: Path = None) -> bool:
        """Run SEO analysis on a single URL"""
        if not output_dir:
            parsed = urlparse(url)
            domain = parsed.netloc.replace(":", "_")
            output_dir = Path("output") / domain
            
        raw_dir = output_dir / "raw"
        raw_dir.mkdir(parents=True, exist_ok=True)
        
        async with AsyncWebCrawler() as crawler:
            print(f"🔍 Running SEO analysis on {url}")
            result = await crawler.arun(url, config=CrawlerRunConfig(
                extraction_strategy=JsonCssExtractionStrategy(self.schema)
            ))
            
            if result.extracted_content:
                # Parse and analyze the extracted data
                raw_data = json.loads(result.extracted_content)
                analyzed_data = self._analyze_seo_data(raw_data, url)
                
                # Save analyzed data
                with open(raw_dir / "seo.json", "w") as f:
                    json.dump(analyzed_data, f, indent=2)
                print(f"✅ SEO report saved to {raw_dir / 'seo.json'}")
                return True
            else:
                print("❌ Failed to generate SEO report")
                return False
    
    def _analyze_seo_data(self, raw_data: list, url: str) -> dict:
        """Analyze raw SEO data and identify issues"""
        if not raw_data or not isinstance(raw_data, list):
            return {
                "pages": [],
                "summary": {
                    "total_pages": 0,
                    "total_issues": 0,
                    "avg_title_length": 0,
                    "avg_desc_length": 0
                }
            }
        
        data = raw_data[0]  # First page data
        issues = []
        
        # Analyze title
        title = data.get("title", "").strip()
        title_length = len(title) if title else 0
        
        if not title:
            issues.append("Missing title tag")
        elif title_length > 60:
            issues.append(f"Title too long ({title_length} chars)")
        elif title_length < 30:
            issues.append(f"Title too short ({title_length} chars)")
        
        # Analyze meta description
        meta_desc = data.get("meta_description", "").strip()
        desc_length = len(meta_desc) if meta_desc else 0
        
        if not meta_desc:
            issues.append("Missing meta description")
        elif desc_length > 160:
            issues.append(f"Meta description too long ({desc_length} chars)")
        elif desc_length < 120:
            issues.append(f"Meta description too short ({desc_length} chars)")
        
        # Analyze H1
        h1 = data.get("h1", "").strip()
        if not h1:
            issues.append("Missing H1 tag")
        elif len(h1) > 70:
            issues.append(f"H1 too long ({len(h1)} chars)")
        
        # Analyze H2 structure
        h2_tags = data.get("h2", [])
        h2_count = len(h2_tags) if isinstance(h2_tags, list) else 0
        
        if h2_count == 0:
            issues.append("No H2 tags found for content structure")
        elif h2_count > 10:
            issues.append(f"Too many H2 tags ({h2_count}) - consider consolidating content")
        
        # Check for keyword stuffing in title
        if title and title.lower().count('fuel') > 2:
            issues.append("Potential keyword stuffing in title")
        
        # Calculate SEO score
        total_issues = len(issues)
        score = max(0, 100 - (total_issues * 15))
        
        page_data = {
            "url": url,
            "title": title,
            "description": meta_desc,
            "h1": h1,
            "title_length": title_length,
            "desc_length": desc_length,
            "h2_count": h2_count,
            "issues": issues,
            "score": score
        }
        
        return {
            "pages": [page_data],
            "summary": {
                "total_pages": 1,
                "total_issues": total_issues,
                "avg_title_length": title_length,
                "avg_desc_length": desc_length,
                "avg_score": score,
                "pages_with_h1": 1 if h1 else 0,
                "total_h2_elements": h2_count
            }
        }