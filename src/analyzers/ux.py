"""
Optimized UX analysis module that works with cached HTML content
"""
from pathlib import Path
from .base import BaseAnalyzer
from ..config.prompts import UX_PROMPT


class UXAnalyzer(BaseAnalyzer):
    """Handles UX analysis using cached HTML content"""
    
    def __init__(self):
        super().__init__()
        self.prompt = UX_PROMPT
        self.schema = {"issues": ["string"], "recommendations": ["string"]}
    
    def _normalize_llm_response(self, issues_raw, recommendations_raw):
        """Normalize LLM response handling strings vs arrays consistently"""
        # Handle issues
        if isinstance(issues_raw, str):
            issues = [issues_raw]
        elif isinstance(issues_raw, list):
            issues = issues_raw
        else:
            issues = []
            
        # Handle recommendations
        if isinstance(recommendations_raw, str):
            recommendations = [recommendations_raw]
        elif isinstance(recommendations_raw, list):
            recommendations = recommendations_raw
        else:
            recommendations = []
            
        return issues, recommendations
    
    async def _analyze_html_content(self, html_content: str, url: str, model: str = "gemini/gemini-2.5-flash") -> dict:
        """Analyze HTML content for UX data"""
        # Extract data using LLM on cached HTML
        raw_data = await self._extract_with_llm_strategy(html_content, url, self.prompt, self.schema, model)
        
        if raw_data:
            # Add URL to the data regardless of format
            data_with_url = {
                'url': url,
                'raw_data': raw_data  # Store the original data
            }
            
            # Also flatten the data for easier processing
            if isinstance(raw_data, dict):
                data_with_url.update(raw_data)
            elif isinstance(raw_data, list):
                # Aggregate issues and recommendations from list items
                all_issues = []
                all_recommendations = []
                for item in raw_data:
                    if isinstance(item, dict):
                        issues, recommendations = self._normalize_llm_response(
                            item.get('issues', []), 
                            item.get('recommendations', [])
                        )
                        all_issues.extend(issues)
                        all_recommendations.extend(recommendations)
                            
                data_with_url['issues'] = all_issues
                data_with_url['recommendations'] = all_recommendations
            
            return data_with_url
        
        return {"url": url, "issues": [], "recommendations": []}
    
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
                issues, recommendations = self._normalize_llm_response(
                    page_data.get('issues', []),
                    page_data.get('recommendations', [])
                )
                    
            elif isinstance(page_data, list):
                # LLM returned a list of objects, aggregate them
                for item in page_data:
                    if isinstance(item, dict):
                        item_issues, item_recommendations = self._normalize_llm_response(
                            item.get('issues', []),
                            item.get('recommendations', [])
                        )
                        issues.extend(item_issues)
                        recommendations.extend(item_recommendations)
            
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
    
    def _get_output_filename(self) -> str:
        """Get output filename for UX analysis"""
        return "ux.json"
    
    async def analyze_cached_pages_with_model(self, base_url: str, model: str, output_dir: Path) -> bool:
        """Run UX analysis on all cached pages with specified model"""
        raw_dir = output_dir / "raw"
        flows_file = raw_dir / "flows.json"
        
        if not flows_file.exists():
            print("❌ No flows.json found. Run full crawl first.")
            return False
        
        # Load flows data to get all crawled pages
        import json
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
                
                # Analyze the HTML content with the specified model
                page_data = await self._analyze_html_content(html_content, page_info['url'], model)
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