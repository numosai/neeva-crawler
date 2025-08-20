"""
Optimized accessibility analysis module that works with cached HTML content
"""
from pathlib import Path
from .base import BaseAnalyzer
from ..config.schemas import A11Y_SCHEMA


class OptimizedAccessibilityAnalyzer(BaseAnalyzer):
    """Handles accessibility analysis using cached HTML content"""
    
    def __init__(self):
        super().__init__()
        self.schema = A11Y_SCHEMA
    
    async def _analyze_html_content(self, html_content: str, url: str) -> dict:
        """Analyze HTML content for accessibility data"""
        # Extract data using CSS selectors on cached HTML
        raw_data = await self._extract_with_css_strategy(html_content, url, self.schema)
        
        if raw_data:
            # Convert list format to individual data if needed
            if isinstance(raw_data, list) and raw_data:
                raw_data = raw_data[0]
            
            # Analyze the extracted data
            analyzed_data = self._analyze_single_page_data(raw_data, url)
            return analyzed_data
        
        return {"url": url, "issues": [], "score": 100}
    
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
                "details": missing_alt_urls[:5],  # Limit to first 5 images for display
                "page_url": url
            })
        
        # Check for buttons without labels
        if buttons_without_labels > 0:
            issues.append({
                "type": "Unlabeled Buttons",
                "severity": "high",
                "description": f"{buttons_without_labels} buttons without accessible labels",
                "wcag_guideline": "WCAG 2.1 AA - 4.1.2 Name, Role, Value",
                "count": buttons_without_labels,
                "page_url": url
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
                "details": empty_link_urls[:5],  # Limit to first 5 links for display
                "page_url": url
            })
        
        # Check for missing language attribute
        html_lang = data.get("html_lang", "")
        if not html_lang:
            issues.append({
                "type": "Missing Language",
                "severity": "medium", 
                "description": "HTML document missing lang attribute",
                "wcag_guideline": "WCAG 2.1 AA - 3.1.1 Language of Page",
                "count": 1,
                "page_url": url
            })
        
        # Check heading hierarchy
        headings = data.get("headings_hierarchy", [])
        heading_issues = self._check_heading_hierarchy(headings, url)
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
    
    def _check_heading_hierarchy(self, headings: list, url: str) -> list:
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
                "count": 1,
                "page_url": url
            })
        
        # Check for skipped levels
        for i in range(1, len(heading_levels)):
            if heading_levels[i] - heading_levels[i-1] > 1:
                issues.append({
                    "type": "Heading Hierarchy",
                    "severity": "low",
                    "description": "Heading levels should not skip (e.g., h1 to h3)",
                    "wcag_guideline": "WCAG 2.1 AA - 1.3.1 Info and Relationships", 
                    "count": 1,
                    "page_url": url
                })
                break
        
        return issues
    
    def _create_multi_page_analysis(self, all_pages_data: list, base_url: str) -> dict:
        """Create comprehensive accessibility analysis from all pages"""
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
            # Issues already have page_url set
            all_issues.extend(page["issues"])
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
    
    def _get_output_filename(self) -> str:
        """Get output filename for accessibility analysis"""
        return "accessibility.json"