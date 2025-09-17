"""
Web crawling utilities
"""
import json
from pathlib import Path
from urllib.parse import urlparse, urljoin
import networkx as nx
from crawl4ai import AsyncWebCrawler, CrawlerRunConfig, BrowserConfig
from .screenshot import ScreenshotProcessor


class WebCrawler:
    """Handles web crawling and site mapping"""
    
    def __init__(self, max_depth: int = 5, max_pages: int = 30):
        self.max_depth = max_depth
        self.max_pages = max_pages
        self.screenshot_processor = ScreenshotProcessor()
    
    
    
    
    
    async def crawl_site(self, url: str, output_dir: Path, use_cdp: bool = False, cdp_port: int = 9222, additional_urls: list = None) -> tuple[list, list]:
        """
        Crawl a website and return pages and navigation flows
        
        Returns:
            tuple: (crawled_pages, selected_flows)
        """
        parsed = urlparse(url)
        
        # Prepare initial URLs to visit
        initial_urls = [url]
        if additional_urls:
            initial_urls.extend(additional_urls)
        
        seen, to_visit = set(), [(u, 0) for u in initial_urls]
        crawled_pages = []
        graph = nx.DiGraph()
        
        # Create directories
        raw_dir = output_dir / "raw"
        raw_dir.mkdir(parents=True, exist_ok=True)
        (raw_dir / "screenshots").mkdir(exist_ok=True)
        (output_dir / "html").mkdir(exist_ok=True)
        
        # Configure browser
        browser_config = None
        
        # CDP mode configuration
        if use_cdp:
            # Use the base CDP endpoint - Playwright will handle the browser ID
            cdp_url = f"http://localhost:{cdp_port}"
            browser_config = BrowserConfig(
                browser_mode="cdp",
                cdp_url=cdp_url,
                use_managed_browser=True,
                headless=False,
                viewport_width=1280,
                viewport_height=720,
                verbose=True
            )
            print(f"🔗 Connecting to existing Chrome browser via CDP")
            print(f"📡 CDP endpoint: {cdp_url}")
            print(f"💡 Make sure Chrome is running with: chrome --remote-debugging-port={cdp_port}")
            print(f"🔑 If you need to authenticate, do so in the browser before continuing.")
        
        async with AsyncWebCrawler(config=browser_config) as crawler:
            page_idx = 1
            while to_visit and len(crawled_pages) < self.max_pages:
                current_url, depth = to_visit.pop(0)
                if current_url in seen or depth > self.max_depth:
                    continue
                seen.add(current_url)
                
                print(f"🌐 Crawling {current_url}")
                
                # Build basic config for crawling
                config_params = {
                    "screenshot": True,
                    "only_text": False,
                    "wait_until": "networkidle",
                    "delay_before_return_html": 2.0,
                    "simulate_user": True,
                    "magic": True
                }
                
                result = await crawler.arun(
                    current_url,
                    config=CrawlerRunConfig(**config_params)
                )
                
                if not result.success:
                    continue
                
                # Process screenshot
                if result.screenshot:
                    screenshot_path = raw_dir / "screenshots" / f"page_{page_idx}.jpg"
                    self.screenshot_processor.save_compressed_screenshot(
                        result.screenshot, screenshot_path
                    )
                
                # Store raw HTML content for analyzers
                page_html_file = raw_dir / f"page_{page_idx}_content.html"
                if hasattr(result, 'html') and result.html:
                    with open(page_html_file, 'w', encoding='utf-8') as f:
                        f.write(result.html)
                
                # Store clean markdown content for QA test generation
                page_md_file = raw_dir / f"page_{page_idx}_content.md"
                if result.markdown:
                    with open(page_md_file, 'w', encoding='utf-8') as f:
                        f.write(result.markdown)
                
                # Add page data
                page_node = f"page_{page_idx}"
                crawled_pages.append({
                    "id": page_node,
                    "url": current_url,
                    "title": result.metadata.get("title") if result.metadata else "",
                    "markdown": result.markdown if hasattr(result, 'markdown') else "",
                    "html_file": f"page_{page_idx}_content.html"  # Reference to stored HTML
                })
                
                # Add to graph
                graph.add_node(
                    page_node, 
                    url=current_url,
                    title=result.metadata.get("title", ""),
                    markdown=result.markdown[:1000] if result.markdown else ""
                )
                
                # Process internal links for traditional link following
                for link in result.links.get("internal", []):
                    href = link.get("href")
                    if not href or href in ["", "#", "javascript:void(0)", "javascript:"]:
                        continue
                    full_url = urljoin(current_url, href)
                    link_netloc = urlparse(full_url).netloc
                    
                    # Check if domains match (handle www subdomain differences)
                    base_domain = parsed.netloc.replace("www.", "")
                    link_domain = link_netloc.replace("www.", "")
                    
                    if link_netloc in ["", parsed.netloc] or link_domain == base_domain:
                        graph.add_edge(page_node, full_url, label=link.get("text", "").strip())
                        if full_url not in seen and depth < self.max_depth:
                            to_visit.append((full_url, depth + 1))
                
                page_idx += 1
        
        # Save graph data
        flows = [{"from": u, "to": v, "label": d.get("label", "")} for u, v, d in graph.edges(data=True)]
        with open(raw_dir / "flows.json", "w") as f:
            json.dump({"nodes": list(graph.nodes(data=True)), "edges": flows}, f, indent=2)
        
        # Generate navigation paths
        selected_flows = self._find_navigation_paths(graph)
        
        return crawled_pages, selected_flows
    
    def _find_navigation_paths(self, graph: nx.DiGraph) -> list:
        """Find interesting navigation paths through the site"""
        candidate_paths = []
        nodes = list(graph.nodes)
        
        for start in nodes:
            for end in nodes:
                if start != end:
                    try:
                        paths = nx.all_simple_paths(graph, source=start, target=end, cutoff=5)
                        for path in paths:
                            candidate_paths.append(path)
                    except nx.NetworkXNoPath:
                        continue
        
        return candidate_paths[:3]  # Return top 3 paths