"""
Accessibility analysis module
"""
from pathlib import Path
from urllib.parse import urlparse
from crawl4ai import AsyncWebCrawler, CrawlerRunConfig, JsonCssExtractionStrategy
from ..config.schemas import A11Y_SCHEMA


class AccessibilityAnalyzer:
    """Handles accessibility analysis for web pages"""
    
    def __init__(self):
        self.schema = A11Y_SCHEMA
    
    async def analyze(self, url: str, output_dir: Path = None) -> bool:
        """Run accessibility analysis on a single URL"""
        if not output_dir:
            parsed = urlparse(url)
            domain = parsed.netloc.replace(":", "_")
            output_dir = Path("output") / domain
            
        raw_dir = output_dir / "raw"
        raw_dir.mkdir(parents=True, exist_ok=True)
        
        async with AsyncWebCrawler() as crawler:
            print(f"🔍 Running accessibility analysis on {url}")
            result = await crawler.arun(url, config=CrawlerRunConfig(
                extraction_strategy=JsonCssExtractionStrategy(self.schema)
            ))
            
            if result.extracted_content:
                with open(raw_dir / "accessibility.json", "w") as f:
                    f.write(result.extracted_content)
                print(f"✅ Accessibility report saved to {raw_dir / 'accessibility.json'}")
                return True
            else:
                print("❌ Failed to generate accessibility report")
                return False