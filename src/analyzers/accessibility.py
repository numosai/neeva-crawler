"""
Accessibility analysis module
"""
import json
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
                # Parse and analyze the extracted data
                raw_data = json.loads(result.extracted_content)
                analyzed_data = self._analyze_accessibility_data(raw_data, url)
                
                # Save analyzed data
                with open(raw_dir / "accessibility.json", "w") as f:
                    json.dump(analyzed_data, f, indent=2)
                print(f"✅ Accessibility report saved to {raw_dir / 'accessibility.json'}")
                return True
            else:
                print("❌ Failed to generate accessibility report")
                return False
    
    async def analyze_all_pages(self, base_url: str, output_dir: Path) -> bool:
        """Run accessibility analysis on all crawled pages from flows.json"""
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
        
        print(f"🔍 Running accessibility analysis on {len(urls_to_analyze)} pages")
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
        with open(raw_dir / "accessibility.json", "w") as f:
            json.dump(analyzed_data, f, indent=2)
        
        print(f"✅ Accessibility report saved for {len(all_pages_data)} pages to {raw_dir / 'accessibility.json'}")
        return True
    
    def _analyze_accessibility_data(self, raw_data: list, url: str) -> dict:
        """Analyze raw accessibility data and identify issues (legacy single-page method)"""
        if not raw_data or not isinstance(raw_data, list):
            return {"issues": [], "summary": {"total_issues": 0, "score": 100}}
        
        page_analysis = self._analyze_single_page_data(raw_data[0], url)
        
        return {
            "issues": page_analysis["issues"],
            "summary": {
                "total_issues": len(page_analysis["issues"]),
                "score": page_analysis["score"],
                "total_images": page_analysis["total_images"],
                "total_links": page_analysis["total_links"],
                "total_buttons": page_analysis["total_buttons"],
                "url": url
            }
        }
    
    def _analyze_single_page_data(self, data: dict, url: str) -> dict:
        """Analyze accessibility data for a single page"""
        issues = []
        
        # Count elements from lists
        images_missing_alt_list = data.get("images_missing_alt", [])
        total_images_list = data.get("total_images", [])
        buttons_without_labels_list = data.get("buttons_without_labels", [])
        links_without_text_list = data.get("links_without_text", [])
        total_links_list = data.get("total_links", [])
        total_buttons_list = data.get("total_buttons", [])
        
        # Ensure lists are actually lists
        if not isinstance(images_missing_alt_list, list):
            images_missing_alt_list = []
        if not isinstance(total_images_list, list):
            total_images_list = []
        if not isinstance(buttons_without_labels_list, list):
            buttons_without_labels_list = []
        if not isinstance(links_without_text_list, list):
            links_without_text_list = []
        if not isinstance(total_links_list, list):
            total_links_list = []
        if not isinstance(total_buttons_list, list):
            total_buttons_list = []
        
        # Count elements
        images_missing_alt = len(images_missing_alt_list)
        total_images = len(total_images_list)
        buttons_without_labels = len(buttons_without_labels_list)
        links_without_text = len(links_without_text_list)
        total_links = len(total_links_list)
        total_buttons = len(total_buttons_list)
        
        # Check for missing alt text on images
        if images_missing_alt > 0:
            # Extract image URLs that are missing alt text
            missing_alt_urls = []
            for img in images_missing_alt_list:
                if isinstance(img, dict) and 'src' in img:
                    src = img['src']
                    # Clean up the URL for display
                    if src:
                        # Show just filename if it's a long URL
                        if len(src) > 50:
                            if '/' in src:
                                filename = src.split('/')[-1]
                                missing_alt_urls.append(f".../{filename}")
                            else:
                                missing_alt_urls.append(src[:47] + "...")
                        else:
                            missing_alt_urls.append(src)
            
            issues.append({
                "type": "Missing Alt Text",
                "severity": "high",
                "description": f"{images_missing_alt} out of {total_images} images missing alt text",
                "wcag_guideline": "WCAG 2.1 AA - 1.1.1 Non-text Content",
                "count": images_missing_alt,
                "details": missing_alt_urls[:5]  # Limit to first 5 images for display
            })
        
        # Check for buttons without labels
        if buttons_without_labels > 0:
            issues.append({
                "type": "Unlabeled Buttons",
                "severity": "high",
                "description": f"{buttons_without_labels} buttons without accessible labels",
                "wcag_guideline": "WCAG 2.1 AA - 4.1.2 Name, Role, Value",
                "count": buttons_without_labels
            })
        
        # Check for links without text
        if links_without_text > 0:
            # Extract URLs of links without text
            empty_link_urls = []
            for link in links_without_text_list:
                if isinstance(link, dict) and 'href' in link:
                    href = link['href']
                    if href:
                        # Clean up URL for display
                        if len(href) > 50:
                            if '/' in href:
                                filename = href.split('/')[-1]
                                empty_link_urls.append(f".../{filename}")
                            else:
                                empty_link_urls.append(href[:47] + "...")
                        else:
                            empty_link_urls.append(href)
            
            issues.append({
                "type": "Empty Links",
                "severity": "medium", 
                "description": f"{links_without_text} links without descriptive text",
                "wcag_guideline": "WCAG 2.1 AA - 2.4.4 Link Purpose",
                "count": links_without_text,
                "details": empty_link_urls[:5]  # Limit to first 5 links for display
            })
        
        # Check for missing language attribute
        html_lang = data.get("html_lang", "")
        if not html_lang:
            issues.append({
                "type": "Missing Language",
                "severity": "medium", 
                "description": "HTML document missing lang attribute",
                "wcag_guideline": "WCAG 2.1 AA - 3.1.1 Language of Page",
                "count": 1
            })
        
        # Check heading hierarchy
        headings = data.get("headings_hierarchy", [])
        heading_issues = self._check_heading_hierarchy(headings)
        issues.extend(heading_issues)
        
        # Calculate score
        total_issues = len(issues)
        critical_issues = len([i for i in issues if i["severity"] == "high"])
        score = max(0, 100 - (critical_issues * 20) - ((total_issues - critical_issues) * 10))
        
        return {
            "url": url,
            "issues": issues,
            "score": score,
            "total_images": total_images,
            "total_links": total_links,
            "total_buttons": total_buttons
        }
    
    def _create_multi_page_analysis(self, all_pages_data: list, base_url: str) -> dict:
        """Create comprehensive analysis from all pages"""
        if not all_pages_data:
            return {
                "issues": [],
                "summary": {
                    "total_issues": 0,
                    "score": 100,
                    "total_images": 0,
                    "total_links": 0,
                    "total_buttons": 0,
                    "total_pages": 0
                }
            }
        
        # Collect all issues from all pages
        all_issues = []
        total_images = 0
        total_links = 0
        total_buttons = 0
        total_score = 0
        
        for page in all_pages_data:
            # Add page context to issues
            for issue in page["issues"]:
                issue_with_page = issue.copy()
                issue_with_page["page_url"] = page["url"]
                all_issues.append(issue_with_page)
            
            total_images += page["total_images"]
            total_links += page["total_links"]
            total_buttons += page["total_buttons"]
            total_score += page["score"]
        
        # Calculate overall score
        total_pages = len(all_pages_data)
        avg_score = round(total_score / total_pages, 1) if total_pages > 0 else 100
        
        return {
            "issues": all_issues,
            "pages": all_pages_data,  # Include individual page data
            "summary": {
                "total_issues": len(all_issues),
                "score": avg_score,
                "total_images": total_images,
                "total_links": total_links,
                "total_buttons": total_buttons,
                "total_pages": total_pages
            }
        }
    
    def _check_heading_hierarchy(self, headings: list) -> list:
        """Check for proper heading hierarchy"""
        issues = []
        if not headings:
            return issues
        
        # Extract heading levels (assuming tag field exists)
        heading_levels = []
        for heading in headings:
            if isinstance(heading, dict) and "tag" in heading:
                tag = heading["tag"].lower()
                if tag in ["h1", "h2", "h3", "h4", "h5", "h6"]:
                    level = int(tag[1])
                    heading_levels.append(level)
        
        if not heading_levels:
            return issues
        
        # Check if starts with h1
        if heading_levels and heading_levels[0] != 1:
            issues.append({
                "type": "Heading Hierarchy",
                "severity": "medium",
                "description": "Page should start with h1 heading",
                "wcag_guideline": "WCAG 2.1 AA - 1.3.1 Info and Relationships",
                "count": 1
            })
        
        # Check for skipped levels
        for i in range(1, len(heading_levels)):
            if heading_levels[i] - heading_levels[i-1] > 1:
                issues.append({
                    "type": "Heading Hierarchy",
                    "severity": "low",
                    "description": "Heading levels should not skip (e.g., h1 to h3)",
                    "wcag_guideline": "WCAG 2.1 AA - 1.3.1 Info and Relationships", 
                    "count": 1
                })
                break
        
        return issues