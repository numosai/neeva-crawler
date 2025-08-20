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
    
    def _analyze_accessibility_data(self, raw_data: list, url: str) -> dict:
        """Analyze raw accessibility data and identify issues"""
        if not raw_data or not isinstance(raw_data, list):
            return {"issues": [], "summary": {"total_issues": 0, "score": 100}}
        
        data = raw_data[0]  # First page data
        issues = []
        
        # Check for missing alt text on images
        images_missing_alt = data.get("images_missing_alt", 0)
        total_images = data.get("total_images", 0)
        if images_missing_alt > 0:
            issues.append({
                "type": "Missing Alt Text",
                "severity": "high",
                "description": f"{images_missing_alt} out of {total_images} images missing alt text",
                "wcag_guideline": "WCAG 2.1 AA - 1.1.1 Non-text Content",
                "count": images_missing_alt
            })
        
        # Check for buttons without labels
        buttons_without_labels = data.get("buttons_without_labels", 0)
        if buttons_without_labels > 0:
            issues.append({
                "type": "Unlabeled Buttons",
                "severity": "high",
                "description": f"{buttons_without_labels} buttons without accessible labels",
                "wcag_guideline": "WCAG 2.1 AA - 4.1.2 Name, Role, Value",
                "count": buttons_without_labels
            })
        
        # Check for links without text
        links_without_text = data.get("links_without_text", 0)
        if links_without_text > 0:
            issues.append({
                "type": "Empty Links",
                "severity": "medium",
                "description": f"{links_without_text} links without descriptive text",
                "wcag_guideline": "WCAG 2.1 AA - 2.4.4 Link Purpose",
                "count": links_without_text
            })
        
        # Check for missing language attribute
        missing_lang = data.get("missing_lang", 0)
        if missing_lang > 0:
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
            "issues": issues,
            "summary": {
                "total_issues": total_issues,
                "score": score,
                "total_images": total_images,
                "total_links": data.get("total_links", 0),
                "total_buttons": data.get("total_buttons", 0),
                "url": url
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