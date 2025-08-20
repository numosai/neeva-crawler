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
    
    async def analyze_all_pages(self, base_url: str, output_dir: Path) -> bool:
        """Run SEO analysis on all crawled pages from flows.json"""
        raw_dir = output_dir / "raw"
        flows_file = raw_dir / "flows.json"
        
        if not flows_file.exists():
            print("❌ No flows.json found. Run full crawl first.")
            return False
        
        # Load flows data to get all crawled pages
        with open(flows_file, 'r') as f:
            flows_data = json.load(f)
        
        # Extract URLs from flows data
        urls_to_analyze = []
        for node in flows_data.get('nodes', []):
            if isinstance(node, list) and len(node) >= 2:
                if isinstance(node[0], str) and node[0].startswith('page_'):
                    # This is a page node with URL in the data
                    page_data = node[1]
                    if isinstance(page_data, dict) and 'url' in page_data:
                        urls_to_analyze.append(page_data['url'])
                elif isinstance(node[0], str) and node[0].startswith('http'):
                    # Direct URL node
                    urls_to_analyze.append(node[0])
        
        if not urls_to_analyze:
            print("❌ No URLs found in flows data")
            return False
        
        print(f"🔍 Running SEO analysis on {len(urls_to_analyze)} pages")
        all_pages_data = []
        
        async with AsyncWebCrawler() as crawler:
            for i, url in enumerate(urls_to_analyze, 1):
                try:
                    print(f"📄 Analyzing page {i}/{len(urls_to_analyze)}: {url}")
                    result = await crawler.arun(url, config=CrawlerRunConfig(
                        extraction_strategy=JsonCssExtractionStrategy(self.schema)
                    ))
                    
                    if result.extracted_content:
                        raw_data = json.loads(result.extracted_content)
                        if raw_data and isinstance(raw_data, list):
                            page_analysis = self._analyze_single_page_data(raw_data[0], url)
                            all_pages_data.append(page_analysis)
                    else:
                        print(f"⚠️  Failed to extract data from {url}")
                        
                except Exception as e:
                    print(f"⚠️  Error analyzing {url}: {e}")
                    continue
        
        if not all_pages_data:
            print("❌ No pages were successfully analyzed")
            return False
        
        # Create comprehensive analysis
        analyzed_data = self._create_multi_page_analysis(all_pages_data, base_url)
        
        # Save analyzed data
        with open(raw_dir / "seo.json", "w") as f:
            json.dump(analyzed_data, f, indent=2)
        
        print(f"✅ SEO report saved for {len(all_pages_data)} pages to {raw_dir / 'seo.json'}")
        return True
    
    def _analyze_seo_data(self, raw_data: list, url: str) -> dict:
        """Analyze raw SEO data and identify issues (legacy single-page method)"""
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
        
        page_analysis = self._analyze_single_page_data(raw_data[0], url)
        
        return {
            "pages": [page_analysis],
            "summary": {
                "total_pages": 1,
                "total_issues": len(page_analysis["issues"]),
                "avg_title_length": page_analysis["title_length"],
                "avg_desc_length": page_analysis["desc_length"],
                "avg_score": page_analysis["score"],
                "pages_with_h1": 1 if page_analysis["h1"] else 0,
                "total_h2_elements": page_analysis["h2_count"]
            }
        }
    
    def _analyze_single_page_data(self, data: dict, url: str) -> dict:
        """Analyze SEO data for a single page"""
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
        
        return {
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
    
    def _create_multi_page_analysis(self, all_pages_data: list, base_url: str) -> dict:
        """Create comprehensive analysis from all pages"""
        if not all_pages_data:
            return {
                "pages": [],
                "summary": {
                    "total_pages": 0,
                    "total_issues": 0,
                    "avg_title_length": 0,
                    "avg_desc_length": 0,
                    "avg_score": 0,
                    "pages_with_h1": 0,
                    "total_h2_elements": 0
                }
            }
        
        # Calculate summary statistics
        total_pages = len(all_pages_data)
        total_issues = sum(len(page["issues"]) for page in all_pages_data)
        total_title_length = sum(page["title_length"] for page in all_pages_data)
        total_desc_length = sum(page["desc_length"] for page in all_pages_data)
        total_score = sum(page["score"] for page in all_pages_data)
        pages_with_h1 = sum(1 for page in all_pages_data if page["h1"])
        total_h2_elements = sum(page["h2_count"] for page in all_pages_data)
        
        return {
            "pages": all_pages_data,
            "summary": {
                "total_pages": total_pages,
                "total_issues": total_issues,
                "avg_title_length": round(total_title_length / total_pages, 1),
                "avg_desc_length": round(total_desc_length / total_pages, 1),
                "avg_score": round(total_score / total_pages, 1),
                "pages_with_h1": pages_with_h1,
                "total_h2_elements": total_h2_elements
            }
        }