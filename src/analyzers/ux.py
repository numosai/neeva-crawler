"""
UX analysis module
"""
from pathlib import Path
from urllib.parse import urlparse
from crawl4ai import AsyncWebCrawler, CrawlerRunConfig, LLMExtractionStrategy, LLMConfig
from ..config.prompts import UX_PROMPT


class UXAnalyzer:
    """Handles UX analysis for web pages"""
    
    def __init__(self):
        self.prompt = UX_PROMPT
        self.schema = {"issues": ["string"], "recommendations": ["string"]}
    
    async def analyze(self, url: str, model: str = "openai/gpt-4o-mini", output_dir: Path = None) -> bool:
        """Run UX analysis on a single URL"""
        if not output_dir:
            parsed = urlparse(url)
            domain = parsed.netloc.replace(":", "_")
            output_dir = Path("output") / domain
            
        raw_dir = output_dir / "raw"
        raw_dir.mkdir(parents=True, exist_ok=True)
        
        async with AsyncWebCrawler() as crawler:
            print(f"🔍 Running UX analysis on {url}")
            result = await crawler.arun(
                url,
                config=CrawlerRunConfig(
                    extraction_strategy=LLMExtractionStrategy(
                        llm_config=LLMConfig(provider=model),
                        prompt=self.prompt,
                        schema=self.schema
                    )
                )
            )
            
            if result.extracted_content:
                with open(raw_dir / "ux.json", "w") as f:
                    f.write(result.extracted_content)
                print(f"✅ UX report saved to {raw_dir / 'ux.json'}")
                return True
            else:
                print("❌ Failed to generate UX report")
                return False