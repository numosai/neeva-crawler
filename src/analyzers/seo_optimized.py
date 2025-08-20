"""
Optimized SEO analysis module that works with cached HTML content
"""
from pathlib import Path
from .base import BaseAnalyzer
from ..config.schemas import SEO_SCHEMA


class OptimizedSEOAnalyzer(BaseAnalyzer):
    """Handles SEO analysis using cached HTML content"""
    
    def __init__(self):
        super().__init__()
        self.schema = SEO_SCHEMA
    
    async def _analyze_html_content(self, html_content: str, url: str) -> dict:
        """Analyze HTML content for SEO data"""
        # Extract data using CSS selectors on cached HTML
        raw_data = await self._extract_with_css_strategy(html_content, url, self.schema)
        
        if raw_data:
            # Convert list format to individual data if needed
            if isinstance(raw_data, list) and raw_data:
                raw_data = raw_data[0]
            
            # Analyze the extracted data
            analyzed_data = self._analyze_single_page_data(raw_data, url)
            return analyzed_data
        
        return {"url": url, "issues": [], "score": 0}
    
    def _analyze_single_page_data(self, data: dict, url: str) -> dict:
        """Analyze SEO data for a single page"""
        issues = []
        recommendations = []
        
        # Extract data
        title = data.get("title", "").strip()
        meta_description = data.get("meta_description", "").strip()
        h1 = data.get("h1", "").strip()
        h2_elements = data.get("h2", [])
        
        # Check title tag
        if not title:
            issues.append("Missing title tag")
        elif len(title) < 30:
            issues.append(f"Title too short ({len(title)} chars) - should be 30-60 characters")
            recommendations.append("Expand title tag to be more descriptive")
        elif len(title) > 60:
            issues.append(f"Title too long ({len(title)} chars) - should be 30-60 characters")
            recommendations.append("Shorten title tag to under 60 characters")
        
        # Check meta description
        if not meta_description:
            issues.append("Missing meta description")
            recommendations.append("Add meta description tag for better search snippets")
        elif len(meta_description) < 120:
            issues.append(f"Meta description too short ({len(meta_description)} chars)")
            recommendations.append("Expand meta description to 120-160 characters")
        elif len(meta_description) > 160:
            issues.append(f"Meta description too long ({len(meta_description)} chars)")
            recommendations.append("Shorten meta description to under 160 characters")
        
        # Check H1 tag
        if not h1:
            issues.append("Missing H1 tag")
            recommendations.append("Add H1 tag for better content structure")
        
        # Check H2 structure
        h2_count = len(h2_elements) if isinstance(h2_elements, list) else 0
        if h2_count == 0:
            issues.append("No H2 tags found")
            recommendations.append("Add H2 tags to improve content structure")
        
        # Calculate SEO score
        score = 100
        score -= len([i for i in issues if "Missing" in i]) * 25  # Major issues
        score -= len([i for i in issues if "too short" in i or "too long" in i]) * 10  # Minor issues
        score = max(0, score)
        
        return {
            "url": url,
            "title": title,
            "description": meta_description,
            "h1": h1,
            "h2_elements": [h.get("text", "") if isinstance(h, dict) else str(h) for h in h2_elements] if h2_elements else [],
            "h2_count": h2_count,
            "issues": issues,
            "recommendations": recommendations,
            "score": score
        }
    
    def _create_multi_page_analysis(self, all_pages_data: list, base_url: str) -> dict:
        """Create comprehensive SEO analysis from all pages"""
        if not all_pages_data:
            return {
                "pages": [],
                "summary": {
                    "total_pages": 0,
                    "total_issues": 0,
                    "avg_title_length": 0,
                    "avg_desc_length": 0,
                    "avg_score": 0
                }
            }
        
        total_issues = sum(len(page["issues"]) for page in all_pages_data)
        total_title_length = sum(len(page.get("title", "")) for page in all_pages_data)
        total_desc_length = sum(len(page.get("description", "")) for page in all_pages_data)
        total_score = sum(page.get("score", 0) for page in all_pages_data)
        total_pages = len(all_pages_data)
        
        return {
            "pages": all_pages_data,
            "summary": {
                "total_pages": total_pages,
                "total_issues": total_issues,
                "avg_title_length": round(total_title_length / total_pages) if total_pages > 0 else 0,
                "avg_desc_length": round(total_desc_length / total_pages) if total_pages > 0 else 0,
                "avg_score": round(total_score / total_pages, 1) if total_pages > 0 else 0
            }
        }
    
    def _get_output_filename(self) -> str:
        """Get output filename for SEO analysis"""
        return "seo.json"