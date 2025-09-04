"""
Main orchestrator for Neeva-Crawler operations
"""
import subprocess
from pathlib import Path
from urllib.parse import urlparse
from .utils import WebCrawler
from .analyzers import AccessibilityAnalyzer, SEOAnalyzer, QAAnalyzer, UXAnalyzer, SitemapAnalyzer, HTMLGeneratorAnalyzer


class CrawlerEngine:
    """Main orchestrator for website analysis operations"""
    
    def __init__(self, max_depth: int = 2, max_pages: int = 10):
        self.web_crawler = WebCrawler(max_depth, max_pages)
        # Use analyzers that work with cached HTML
        self.accessibility_analyzer = AccessibilityAnalyzer()
        self.seo_analyzer = SEOAnalyzer()
        self.ux_analyzer = UXAnalyzer()
        # Use enhanced multi-page QA analyzer
        self.qa_analyzer = QAAnalyzer()
        self.sitemap_analyzer = SitemapAnalyzer()
        self.html_generator = HTMLGeneratorAnalyzer()
    
    def _get_output_dir(self, url: str) -> Path:
        """Get output directory for a given URL"""
        parsed = urlparse(url)
        domain = parsed.netloc.replace(":", "_")
        return Path("output") / domain
    
    def _run_git_workflow(self, url: str) -> bool:
        """Run git add, commit, and push workflow"""
        try:
            parsed = urlparse(url)
            domain = parsed.netloc.replace("www.", "").replace(":", "_")
            
            print(f"🔄 Running git workflow for {domain}...")
            
            # Git add
            result = subprocess.run(["git", "add", "."], capture_output=True, text=True)
            if result.returncode != 0:
                print(f"❌ Git add failed: {result.stderr}")
                return False
            
            # Git commit
            commit_message = f"Updated analysis for {domain}"
            result = subprocess.run(["git", "commit", "-m", commit_message], 
                                  capture_output=True, text=True)
            if result.returncode != 0:
                # Check if it's just "nothing to commit" 
                if "nothing to commit" in result.stdout:
                    print("ℹ️ No changes to commit")
                else:
                    print(f"❌ Git commit failed: {result.stderr}")
                    return False
            else:
                print(f"✅ Committed: {commit_message}")
            
            # Git push
            result = subprocess.run(["git", "push", "origin", "main"], 
                                  capture_output=True, text=True)
            if result.returncode != 0:
                print(f"❌ Git push failed: {result.stderr}")
                return False
            
            print("✅ Successfully pushed to origin/main")
            return True
            
        except Exception as e:
            print(f"❌ Git workflow error: {e}")
            return False
    
    async def full_crawl_and_analyze(self, url: str, model: str = "gemini/gemini-2.5-flash", git_push: bool = False) -> bool:
        """Perform full website crawl and all analyses"""
        output_dir = self._get_output_dir(url)
        
        # Check if output directory already exists
        if output_dir.exists():
            print(f"⚠️  Output directory already exists: {output_dir}")
            print("Delete the directory if you want to recrawl and reanalyze.")
            return True  # Return True to indicate graceful completion
        
        # Crawl the website
        print(f"🚀 Starting full analysis of {url}")
        crawled_pages, _ = await self.web_crawler.crawl_site(url, output_dir)
        
        if not crawled_pages:
            print("❌ No pages were successfully crawled")
            return False
        
        # Run all analyses in parallel
        results = await self._run_all_analyses(url, model, output_dir, crawled_pages)
        
        success_count = sum(results)
        total_analyses = len(results)
        print(f"📊 Completed {success_count}/{total_analyses} analyses successfully")
        
        # Run git workflow if requested and analysis was successful
        if git_push and success_count > 0:
            self._run_git_workflow(url)
        
        return success_count > 0
    
    async def regenerate_sitemap_only(self, url: str) -> bool:
        """Regenerate sitemap only from existing crawl data"""
        output_dir = self._get_output_dir(url)
        raw_dir = output_dir / "raw"
        flows_file = raw_dir / "flows.json"
        
        if not flows_file.exists():
            print(f"❌ No crawl data found for {url}")
            print(f"Expected flows.json at: {flows_file}")
            return False
        
        print(f"🗺️ Regenerating sitemap for {url}")
        
        import json
        with open(flows_file, 'r') as f:
            flows_data = json.load(f)
        
        sitemap_success = self.sitemap_analyzer.generate_sitemap(
            [], flows_data, raw_dir
        )
        
        if sitemap_success:
            print("✅ Sitemap regenerated successfully")
        else:
            print("❌ Failed to regenerate sitemap")
        
        return sitemap_success
    
    async def analyze_and_html(self, url: str, model: str = "gemini/gemini-2.5-flash") -> bool:
        """Run all analyses and generate HTML from existing crawl data"""
        output_dir = self._get_output_dir(url)
        raw_dir = output_dir / "raw"
        flows_file = raw_dir / "flows.json"
        
        if not flows_file.exists():
            print(f"❌ No crawl data found for {url}")
            print(f"Expected flows.json at: {flows_file}")
            print("Run a full crawl first to generate crawl data")
            return False
        
        print(f"🔍 Running analyses and HTML generation for {url}")
        
        # Load flows data
        import json
        with open(flows_file, 'r') as f:
            flows_data = json.load(f)
        
        # Run all analyses (except QA which needs special handling)
        results = []
        
        # Accessibility Analysis (using cached HTML)
        a11y_success = await self.accessibility_analyzer.analyze_cached_pages(url, output_dir)
        results.append(a11y_success)
        
        # SEO Analysis (using cached HTML)
        seo_success = await self.seo_analyzer.analyze_cached_pages(url, output_dir)
        results.append(seo_success)
        
        # UX Analysis (using cached HTML)
        ux_success = await self.ux_analyzer.analyze_cached_pages_with_model(url, model, output_dir)
        results.append(ux_success)
        
        # QA Analysis (if crawl data exists)
        crawled_pages_file = raw_dir / "crawled_pages.json"
        if crawled_pages_file.exists():
            with open(crawled_pages_file, 'r') as f:
                crawled_pages = json.load(f)
            
            flows = flows_data.get('edges', [])
            qa_success = await self.qa_analyzer.analyze_from_crawl_data(
                url, crawled_pages, flows, model, output_dir
            )
            results.append(qa_success)
        
        # Sitemap Analysis
        sitemap_success = self.sitemap_analyzer.generate_sitemap(
            [], flows_data, raw_dir
        )
        results.append(sitemap_success)
        
        # HTML Site Generation
        html_success = self.html_generator.generate_site(url, raw_dir, output_dir / "html")
        results.append(html_success)
        
        success_count = sum(results)
        total_analyses = len(results)
        print(f"📊 Completed {success_count}/{total_analyses} analyses and HTML generation successfully")
        
        if html_success:
            print(f"✅ HTML site generated successfully!")
            print(f"📁 Output directory: {output_dir / 'html'}")
            print(f"🚀 Ready for deployment to GitHub Pages")
        
        return success_count > 0

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
    
    async def analyze_qa_only(self, url: str, model: str = "gemini/gemini-2.5-flash") -> bool:
        """Run QA analysis only from existing crawl data"""
        output_dir = self._get_output_dir(url)
        raw_dir = output_dir / "raw"
        
        if not raw_dir.exists():
            print(f"❌ No crawl data found for {url}")
            print(f"Expected data at: {raw_dir}")
            print("Run a full crawl first to generate data")
            return False
        
        print(f"🧪 Running QA analysis only for {url} using {model}")
        
        # QA Analysis using the same pattern as UX analyzer
        qa_success = await self.qa_analyzer.analyze_cached_pages_with_model(url, model, output_dir)
        
        if qa_success:
            print(f"✅ QA analysis completed successfully!")
            print(f"📁 Output directory: {output_dir / 'raw'}")
            print(f"🧪 QA tests: {output_dir / 'raw' / 'tests'}")
        else:
            print(f"❌ QA analysis failed")
        
        return qa_success
    
    async def _run_all_analyses(self, url: str, model: str, output_dir: Path, 
                               crawled_pages: list) -> list[bool]:
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
        
        # QA Analysis using cached pages pattern
        qa_success = await self.qa_analyzer.analyze_cached_pages_with_model(url, model, output_dir)
        results.append(qa_success)
        
        # Accessibility Analysis (using cached HTML)
        a11y_success = await self.accessibility_analyzer.analyze_cached_pages(url, output_dir)
        results.append(a11y_success)
        
        # SEO Analysis (using cached HTML)
        seo_success = await self.seo_analyzer.analyze_cached_pages(url, output_dir)
        results.append(seo_success)
        
        # UX Analysis (using cached HTML)
        ux_success = await self.ux_analyzer.analyze_cached_pages_with_model(url, model, output_dir)
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