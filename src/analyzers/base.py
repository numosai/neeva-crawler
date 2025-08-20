"""
Base analyzer class for working with cached HTML content
"""
import json
from pathlib import Path
from crawl4ai import AsyncWebCrawler, CrawlerRunConfig, JsonCssExtractionStrategy, LLMExtractionStrategy, LLMConfig


class BaseAnalyzer:
    """Base class for analyzers that work with cached HTML content"""
    
    def __init__(self):
        self.name = self.__class__.__name__
    
    async def analyze_cached_pages(self, base_url: str, output_dir: Path) -> bool:
        """Run analysis on all cached pages from flows.json"""
        raw_dir = output_dir / "raw"
        flows_file = raw_dir / "flows.json"
        
        if not flows_file.exists():
            print("❌ No flows.json found. Run full crawl first.")
            return False
        
        # Load flows data to get all crawled pages
        with open(flows_file, 'r') as f:
            flows_data = json.load(f)
        
        # Extract pages with cached HTML content
        pages_to_analyze = []
        for node in flows_data.get('nodes', []):
            if isinstance(node, list) and len(node) >= 2:
                if isinstance(node[0], str) and node[0].startswith('page_'):
                    # This is a page node with data
                    page_data = node[1]
                    if isinstance(page_data, dict) and 'url' in page_data:
                        # Look for corresponding HTML file
                        page_id = node[0]  # e.g., "page_1"
                        page_num = page_id.split('_')[1]
                        html_file = raw_dir / f"page_{page_num}_content.html"
                        
                        if html_file.exists():
                            pages_to_analyze.append({
                                'url': page_data['url'],
                                'html_file': html_file,
                                'page_id': page_id
                            })
        
        if not pages_to_analyze:
            print("❌ No cached HTML files found")
            return False
        
        print(f"🔍 Running {self.name} analysis on {len(pages_to_analyze)} cached pages")
        all_pages_data = []
        
        for i, page_info in enumerate(pages_to_analyze, 1):
            try:
                print(f"📄 Analyzing page {i}/{len(pages_to_analyze)}: {page_info['url']}")
                
                # Read cached HTML content
                with open(page_info['html_file'], 'r', encoding='utf-8') as f:
                    html_content = f.read()
                
                # Analyze the HTML content
                page_data = await self._analyze_html_content(html_content, page_info['url'])
                if page_data:
                    all_pages_data.append(page_data)
                    
            except Exception as e:
                print(f"⚠️  Error analyzing {page_info['url']}: {e}")
                continue
        
        if not all_pages_data:
            print(f"❌ No pages were successfully analyzed by {self.name}")
            return False
        
        # Create comprehensive analysis
        analyzed_data = self._create_multi_page_analysis(all_pages_data, base_url)
        
        # Save analyzed data
        output_file = self._get_output_filename()
        with open(raw_dir / output_file, "w") as f:
            json.dump(analyzed_data, f, indent=2)
        
        print(f"✅ {self.name} report saved for {len(all_pages_data)} pages to {raw_dir / output_file}")
        return True
    
    async def _analyze_html_content(self, html_content: str, url: str) -> dict:
        """Analyze HTML content - to be implemented by subclasses"""
        raise NotImplementedError("Subclasses must implement _analyze_html_content")
    
    def _create_multi_page_analysis(self, all_pages_data: list, base_url: str) -> dict:
        """Create comprehensive analysis from all pages - to be implemented by subclasses"""
        raise NotImplementedError("Subclasses must implement _create_multi_page_analysis")
    
    def _get_output_filename(self) -> str:
        """Get output filename for this analyzer - to be implemented by subclasses"""
        raise NotImplementedError("Subclasses must implement _get_output_filename")
    
    async def _extract_with_css_strategy(self, html_content: str, url: str, schema: dict) -> dict:
        """Helper method to extract data using CSS selectors on cached HTML"""
        # Create a temporary crawler that can process the HTML directly
        from crawl4ai.extraction_strategy import JsonCssExtractionStrategy
        import tempfile
        import os
        
        # Create temporary HTML file
        with tempfile.NamedTemporaryFile(mode='w', suffix='.html', delete=False, encoding='utf-8') as f:
            f.write(html_content)
            temp_file = f.name
        
        try:
            async with AsyncWebCrawler() as crawler:
                # Use file:// URL to process local HTML file
                file_url = f"file://{temp_file}"
                result = await crawler.arun(
                    file_url,
                    config=CrawlerRunConfig(
                        extraction_strategy=JsonCssExtractionStrategy(schema)
                    )
                )
                
                if result.extracted_content:
                    return json.loads(result.extracted_content)
                return {}
        finally:
            # Clean up temp file
            os.unlink(temp_file)
    
    async def _extract_with_llm_strategy(self, html_content: str, url: str, prompt: str, schema: dict, model: str = "gemini/gemini-2.5-flash") -> dict:
        """Helper method to extract data using LLM on cached HTML"""
        import tempfile
        import os
        
        # Create temporary HTML file
        with tempfile.NamedTemporaryFile(mode='w', suffix='.html', delete=False, encoding='utf-8') as f:
            f.write(html_content)
            temp_file = f.name
        
        try:
            async with AsyncWebCrawler() as crawler:
                # Use file:// URL to process local HTML file
                file_url = f"file://{temp_file}"
                result = await crawler.arun(
                    file_url,
                    config=CrawlerRunConfig(
                        extraction_strategy=LLMExtractionStrategy(
                            llm_config=LLMConfig(provider=model),
                            prompt=prompt,
                            schema=schema
                        )
                    )
                )
                
                if result.extracted_content:
                    return json.loads(result.extracted_content)
                return {}
        finally:
            # Clean up temp file
            os.unlink(temp_file)