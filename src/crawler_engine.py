"""
Main orchestrator for Neeva-Crawler operations
"""
from pathlib import Path
from urllib.parse import urlparse
from .utils import WebCrawler
from .analyzers import AccessibilityAnalyzer, SEOAnalyzer, QAAnalyzer, UXAnalyzer, SitemapAnalyzer, HTMLGeneratorAnalyzer


class CrawlerEngine:
    """Main orchestrator for website analysis operations"""
    
    def __init__(self, max_depth: int = 2, max_pages: int = 10):
        self.web_crawler = WebCrawler(max_depth, max_pages)
        self.accessibility_analyzer = AccessibilityAnalyzer()
        self.seo_analyzer = SEOAnalyzer()
        self.qa_analyzer = QAAnalyzer()
        self.ux_analyzer = UXAnalyzer()
        self.sitemap_analyzer = SitemapAnalyzer()
        self.html_generator = HTMLGeneratorAnalyzer()
    
    def _get_output_dir(self, url: str) -> Path:
        """Get output directory for a given URL"""
        parsed = urlparse(url)
        domain = parsed.netloc.replace(":", "_")
        return Path("output") / domain
    
    async def full_crawl_and_analyze(self, url: str, model: str = "openai/gpt-4o-mini") -> bool:
        """Perform full website crawl and all analyses"""
        output_dir = self._get_output_dir(url)
        
        # Crawl the website
        print(f"🚀 Starting full analysis of {url}")
        crawled_pages, flows = await self.web_crawler.crawl_site(url, output_dir)
        
        if not crawled_pages:
            print("❌ No pages were successfully crawled")
            return False
        
        # Run all analyses in parallel
        results = await self._run_all_analyses(url, model, output_dir, crawled_pages, flows)
        
        success_count = sum(results)
        total_analyses = len(results)
        print(f"📊 Completed {success_count}/{total_analyses} analyses successfully")
        
        return success_count > 0
    
    async def analyze_accessibility_only(self, url: str) -> bool:
        """Run accessibility analysis only"""
        return await self.accessibility_analyzer.analyze(url)
    
    async def analyze_seo_only(self, url: str) -> bool:
        """Run SEO analysis only"""
        return await self.seo_analyzer.analyze(url)
    
    async def analyze_qa_only(self, url: str, model: str = "openai/gpt-4o-mini") -> bool:
        """Regenerate QA test plan from existing crawl data"""
        return await self.qa_analyzer.analyze_from_existing_data(url, model)
    
    async def generate_html_only(self, url: str) -> bool:
        """Generate HTML site from existing analysis data"""
        output_dir = self._get_output_dir(url)
        raw_dir = output_dir / "raw"
        html_dir = output_dir / "html"
        
        if not raw_dir.exists():
            print(f"❌ No analysis data found for {url}")
            print(f"Expected data at: {raw_dir}")
            print("Run a full analysis first to generate data")
            return False
        
        print(f"🌐 Generating HTML site from existing data for {url}")
        success = self.html_generator.generate_site(url, raw_dir, html_dir)
        
        if success:
            print(f"✅ HTML site generated successfully!")
            print(f"📁 Output directory: {html_dir}")
            print(f"🚀 Ready for deployment to GitHub Pages")
        
        return success
    
    async def _run_all_analyses(self, url: str, model: str, output_dir: Path, 
                               crawled_pages: list, flows: list) -> list[bool]:
        """Run all analyses and return success status for each"""
        results = []
        raw_dir = output_dir / "raw"
        
        # Read flows data for sitemap generation
        flows_file = raw_dir / "flows.json"
        flows_data = {}
        if flows_file.exists():
            import json
            with open(flows_file, 'r') as f:
                flows_data = json.load(f)
        
        # QA Analysis
        qa_success = await self.qa_analyzer.analyze_from_crawl_data(
            url, crawled_pages, flows, model, output_dir
        )
        results.append(qa_success)
        
        # Accessibility Analysis
        a11y_success = await self.accessibility_analyzer.analyze(url, output_dir)
        results.append(a11y_success)
        
        # SEO Analysis
        seo_success = await self.seo_analyzer.analyze(url, output_dir)
        results.append(seo_success)
        
        # UX Analysis
        ux_success = await self.ux_analyzer.analyze(url, model, output_dir)
        results.append(ux_success)
        
        # Sitemap Analysis
        sitemap_success = self.sitemap_analyzer.generate_sitemap(
            crawled_pages, flows_data, raw_dir
        )
        results.append(sitemap_success)
        
        # HTML Site Generation
        html_success = self.html_generator.generate_site(url, raw_dir, output_dir / "html")
        results.append(html_success)
        
        return results