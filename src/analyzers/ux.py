"""
UX analysis module
"""
import json
from pathlib import Path
from urllib.parse import urlparse
from crawl4ai import AsyncWebCrawler, CrawlerRunConfig, LLMExtractionStrategy, LLMConfig
from ..config.prompts import UX_PROMPT


class UXAnalyzer:
    """Handles UX analysis for web pages"""
    
    def __init__(self):
        self.prompt = UX_PROMPT
        self.schema = {"issues": ["string"], "recommendations": ["string"]}
    
    async def analyze(self, url: str, model: str = "google/gemini-flash-2.5", output_dir: Path = None) -> bool:
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
    
    async def analyze_all_pages(self, base_url: str, model: str = "google/gemini-flash-2.5", output_dir: Path = None) -> bool:
        """Run UX analysis on all crawled pages from flows.json"""
        if not output_dir:
            parsed = urlparse(base_url)
            domain = parsed.netloc.replace(":", "_")
            output_dir = Path("output") / domain
            
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
        
        print(f"🔍 Running UX analysis on {len(urls_to_analyze)} pages")
        all_pages_data = []
        
        async with AsyncWebCrawler() as crawler:
            for i, url in enumerate(urls_to_analyze, 1):
                try:
                    print(f"📄 Analyzing UX for page {i}/{len(urls_to_analyze)}: {url}")
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
                        try:
                            page_data = json.loads(result.extracted_content)
                            if page_data:
                                # Add URL to the data regardless of format
                                data_with_url = {
                                    'url': url,
                                    'raw_data': page_data  # Store the original data
                                }
                                
                                # Also flatten the data for easier processing
                                if isinstance(page_data, dict):
                                    data_with_url.update(page_data)
                                elif isinstance(page_data, list):
                                    # Aggregate issues and recommendations from list items
                                    all_issues = []
                                    all_recommendations = []
                                    for item in page_data:
                                        if isinstance(item, dict):
                                            all_issues.extend(item.get('issues', []))
                                            all_recommendations.extend(item.get('recommendations', []))
                                    data_with_url['issues'] = all_issues
                                    data_with_url['recommendations'] = all_recommendations
                                
                                all_pages_data.append(data_with_url)
                        except (json.JSONDecodeError, KeyError, TypeError) as e:
                            print(f"⚠️  Error parsing UX data for {url}: {e}")
                            continue
                    else:
                        print(f"⚠️  Failed to extract UX data from {url}")
                        
                except Exception as e:
                    print(f"⚠️  Error analyzing UX for {url}: {e}")
                    continue
        
        if not all_pages_data:
            print("❌ No pages were successfully analyzed for UX")
            return False
        
        # Create comprehensive UX analysis
        analyzed_data = self._create_multi_page_analysis(all_pages_data, base_url)
        
        # Save analyzed data
        with open(raw_dir / "ux.json", "w") as f:
            json.dump(analyzed_data, f, indent=2)
        
        print(f"✅ UX report saved for {len(all_pages_data)} pages to {raw_dir / 'ux.json'}")
        return True
    
    def _create_multi_page_analysis(self, all_pages_data: list, base_url: str) -> dict:
        """Create comprehensive UX analysis from all pages"""
        if not all_pages_data:
            return {
                "issues": [],
                "recommendations": [],
                "summary": {
                    "total_issues": 0,
                    "total_recommendations": 0,
                    "high_priority": 0,
                    "medium_priority": 0,
                    "low_priority": 0,
                    "total_pages": 0
                }
            }
        
        # Collect all issues and recommendations from all pages
        all_issues = []
        all_recommendations = []
        
        for page_data in all_pages_data:
            page_url = page_data.get('url', 'unknown')
            
            # Handle different response formats from LLM
            issues = []
            recommendations = []
            
            if isinstance(page_data, dict):
                issues = page_data.get('issues', [])
                recommendations = page_data.get('recommendations', [])
            elif isinstance(page_data, list):
                # LLM returned a list of objects, aggregate them
                for item in page_data:
                    if isinstance(item, dict):
                        issues.extend(item.get('issues', []))
                        recommendations.extend(item.get('recommendations', []))
            
            # Add page context to issues
            for issue in issues:
                all_issues.append({
                    "text": issue,
                    "page_url": page_url
                })
            
            # Add page context to recommendations  
            for recommendation in recommendations:
                all_recommendations.append({
                    "text": recommendation,
                    "page_url": page_url,
                    "priority": self._determine_priority(recommendation)
                })
        
        # Count priorities
        high_priority = len([r for r in all_recommendations if r['priority'] == 'high'])
        medium_priority = len([r for r in all_recommendations if r['priority'] == 'medium'])
        low_priority = len([r for r in all_recommendations if r['priority'] == 'low'])
        
        return {
            "issues": all_issues,
            "recommendations": all_recommendations,
            "pages": all_pages_data,  # Include individual page data
            "summary": {
                "total_issues": len(all_issues),
                "total_recommendations": len(all_recommendations),
                "high_priority": high_priority,
                "medium_priority": medium_priority,
                "low_priority": low_priority,
                "total_pages": len(all_pages_data)
            }
        }
    
    def _determine_priority(self, recommendation: str) -> str:
        """Determine priority level based on recommendation text"""
        recommendation_lower = recommendation.lower()
        
        # High priority keywords
        high_keywords = ['critical', 'urgent', 'immediately', 'broken', 'error', 'accessibility', 'security', 'conversion', 'revenue']
        if any(keyword in recommendation_lower for keyword in high_keywords):
            return 'high'
        
        # Low priority keywords
        low_keywords = ['minor', 'cosmetic', 'polish', 'nice to have', 'consider', 'optional']
        if any(keyword in recommendation_lower for keyword in low_keywords):
            return 'low'
        
        # Default to medium
        return 'medium'