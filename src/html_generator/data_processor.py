"""
Data processor for transforming raw analysis data into display-ready formats
"""
import json
import yaml
from pathlib import Path
from typing import Dict, List, Any, Optional
from urllib.parse import urlparse


class DataProcessor:
    """Processes raw analysis data for HTML template consumption"""
    
    def __init__(self, raw_dir: Path):
        self.raw_dir = raw_dir
        
    def process_all_data(self) -> Dict[str, Any]:
        """Process all available data into a comprehensive structure"""
        return {
            'overview': self.process_overview_data(),
            'seo': self.process_seo_data(),
            'accessibility': self.process_accessibility_data(),
            'qa_tests': self.process_qa_data(),
            'ux': self.process_ux_data(),
            'screenshots': self.process_screenshots_data(),
            'sitemap': self.process_sitemap_data()
        }
    
    def process_overview_data(self) -> Dict[str, Any]:
        """Generate overview statistics from all data sources"""
        stats = {
            'total_pages': 0,
            'total_tests': 0,
            'accessibility_issues': 0,
            'seo_issues': 0,
            'ux_recommendations': 0,
            'site_title': 'Website Analysis'
        }
        
        # Count pages from flows data
        flows_file = self.raw_dir / "flows.json"
        if flows_file.exists():
            with open(flows_file, 'r') as f:
                flows_data = json.load(f)
                page_nodes = [node for node, _ in flows_data.get('nodes', []) 
                            if isinstance(node, str) and node.startswith('page_')]
                stats['total_pages'] = len(page_nodes)
        
        # Count tests from YAML files
        tests_dir = self.raw_dir / "tests"
        if tests_dir.exists():
            for yaml_file in tests_dir.glob("*.yaml"):
                try:
                    with open(yaml_file, 'r') as f:
                        test_data = yaml.safe_load(f)
                        phases = test_data.get('qa_plan', {}).get('phases', [])
                        stats['total_tests'] += len(phases)
                except Exception:
                    continue
        
        # Count accessibility issues
        a11y_file = self.raw_dir / "accessibility.json"
        if a11y_file.exists():
            try:
                with open(a11y_file, 'r') as f:
                    a11y_data = json.load(f)
                    if isinstance(a11y_data, dict) and 'summary' in a11y_data:
                        stats['accessibility_issues'] = a11y_data['summary'].get('total_issues', 0)
            except Exception:
                pass
        
        # Count SEO issues
        seo_file = self.raw_dir / "seo.json"
        if seo_file.exists():
            try:
                with open(seo_file, 'r') as f:
                    seo_data = json.load(f)
                    if isinstance(seo_data, dict) and 'summary' in seo_data:
                        stats['seo_issues'] = seo_data['summary'].get('total_issues', 0)
            except Exception:
                pass
        
        # Count UX recommendations
        ux_file = self.raw_dir / "ux.json"
        if ux_file.exists():
            try:
                with open(ux_file, 'r') as f:
                    ux_data = json.load(f)
                    if isinstance(ux_data, dict):
                        recommendations = ux_data.get('recommendations', [])
                        stats['ux_recommendations'] = len(recommendations)
            except Exception:
                pass
        
        # Extract site title from SEO data
        if seo_file.exists():
            try:
                with open(seo_file, 'r') as f:
                    seo_data = json.load(f)
                    if isinstance(seo_data, dict) and 'pages' in seo_data and seo_data['pages']:
                        title = seo_data['pages'][0].get('title', '')
                        if title:
                            stats['site_title'] = title.split('|')[0].strip()
            except Exception:
                pass
                
        return stats
    
    def process_seo_data(self) -> Dict[str, Any]:
        """Process SEO analysis data"""
        seo_file = self.raw_dir / "seo.json"
        if not seo_file.exists():
            return {'pages': [], 'summary': {}}
        
        try:
            with open(seo_file, 'r') as f:
                raw_data = json.load(f)
            
            # Return analyzed format as-is
            if isinstance(raw_data, dict) and 'pages' in raw_data and 'summary' in raw_data:
                return raw_data
            
            return {'pages': [], 'summary': {}}
        except Exception:
            return {'pages': [], 'summary': {}}
            description = seo_data.get('meta_description', '')
            h1 = seo_data.get('h1', '')
            h2_elements = seo_data.get('h2', [])
            
            issues = []
            recommendations = []
            
            # Title analysis
            if not title:
                issues.append("Missing page title")
            elif len(title) < 30:
                issues.append(f"Title too short ({len(title)} chars)")
                recommendations.append("Expand title to 30-60 characters")
            elif len(title) > 60:
                issues.append(f"Title too long ({len(title)} chars)")
                recommendations.append("Shorten title to under 60 characters")
            
            # Description analysis  
            if not description:
                issues.append("Missing meta description")
                recommendations.append("Add meta description of 120-160 characters")
            elif len(description) < 120:
                issues.append(f"Meta description too short ({len(description)} chars)")
                recommendations.append("Expand meta description to 120-160 characters")
            elif len(description) > 160:
                issues.append(f"Meta description too long ({len(description)} chars)")
                recommendations.append("Shorten meta description to under 160 characters")
            
            # H1 analysis
            if not h1:
                issues.append("Missing H1 tag")
                recommendations.append("Add a descriptive H1 tag to the page")
            
            page_data = {
                'url': 'Homepage',  # We don't have URL in current data structure
                'title': title,
                'description': description,
                'h1': h1,
                'h2_count': len(h2_elements),
                'h2_elements': [h.get('text', '') for h in h2_elements],
                'issues': issues,
                'recommendations': recommendations,
                'score': max(0, 100 - len(issues) * 25)  # Simple scoring
            }
            
            summary = {
                'total_pages': 1,
                'total_issues': len(issues),
                'avg_title_length': len(title) if title else 0,
                'avg_desc_length': len(description) if description else 0,
                'pages_with_h1': 1 if h1 else 0,
                'total_h2_elements': len(h2_elements)
            }
            
            return {
                'pages': [page_data],
                'summary': summary
            }
            
        except Exception as e:
            print(f"Error processing SEO data: {e}")
            return {'pages': [], 'summary': {}}
    
    def process_accessibility_data(self) -> Dict[str, Any]:
        """Process accessibility analysis data"""
        a11y_file = self.raw_dir / "accessibility.json"
        if not a11y_file.exists():
            return {'summary': {}, 'issues': []}
        
        try:
            with open(a11y_file, 'r') as f:
                raw_data = json.load(f)
            
            # Return analyzed format as-is
            if isinstance(raw_data, dict) and 'issues' in raw_data and 'summary' in raw_data:
                return raw_data
                
            return {'summary': {}, 'issues': []}
        except Exception:
            return {'summary': {}, 'issues': []}
    
    
    def process_qa_data(self) -> Dict[str, Any]:
        """Process QA test data from YAML files"""
        tests_dir = self.raw_dir / "tests"
        if not tests_dir.exists():
            return {'test_files': [], 'summary': {}}
        
        test_files = []
        total_phases = 0
        total_assertions = 0
        
        for yaml_file in tests_dir.glob("*.yaml"):
            try:
                with open(yaml_file, 'r') as f:
                    test_data = yaml.safe_load(f)
                
                test_name = test_data.get('name', yaml_file.stem)
                qa_plan = test_data.get('qa_plan', {})
                phases = qa_plan.get('phases', [])
                
                # Process phases
                processed_phases = []
                phase_count = len(phases)
                assertion_count = 0
                
                for phase in phases:
                    assertions = phase.get('assertions', [])
                    assertion_count += len(assertions)
                    
                    processed_phases.append({
                        'phase_number': phase.get('phaseNumber', 0),
                        'objective': phase.get('objective', ''),
                        'assertions': [
                            {
                                'id': assertion.get('verificationId', ''),
                                'description': assertion.get('description', ''),
                                'status': 'pending'  # Default status
                            }
                            for assertion in assertions
                        ]
                    })
                
                test_files.append({
                    'filename': yaml_file.name,
                    'name': test_name,
                    'title': qa_plan.get('title', test_name),
                    'phases': processed_phases,
                    'phase_count': phase_count,
                    'assertion_count': assertion_count
                })
                
                total_phases += phase_count
                total_assertions += assertion_count
                
            except Exception as e:
                print(f"Error processing test file {yaml_file}: {e}")
                continue
        
        summary = {
            'total_test_files': len(test_files),
            'total_phases': total_phases,
            'total_assertions': total_assertions,
            'avg_phases_per_file': round(total_phases / max(len(test_files), 1), 1),
            'avg_assertions_per_file': round(total_assertions / max(len(test_files), 1), 1)
        }
        
        return {
            'test_files': test_files,
            'summary': summary
        }
    
    def process_ux_data(self) -> Dict[str, Any]:
        """Process UX analysis data"""
        ux_file = self.raw_dir / "ux.json"
        if not ux_file.exists():
            return {'issues': [], 'recommendations': [], 'summary': {}}
        
        try:
            with open(ux_file, 'r') as f:
                ux_data = json.load(f)
            
            # Handle both single object and list formats
            issues = []
            recommendations = []
            
            if isinstance(ux_data, list):
                # Merge all issues and recommendations from list
                for item in ux_data:
                    if isinstance(item, dict):
                        issues.extend(item.get('issues', []))
                        recommendations.extend(item.get('recommendations', []))
            else:
                # Single object format
                issues = ux_data.get('issues', [])
                recommendations = ux_data.get('recommendations', [])
            
            # Add priority levels to recommendations
            processed_recommendations = []
            for i, rec in enumerate(recommendations):
                priority = 'High' if i < len(recommendations) // 3 else 'Medium' if i < 2 * len(recommendations) // 3 else 'Low'
                processed_recommendations.append({
                    'text': rec,
                    'priority': priority,
                    'category': 'User Experience'
                })
            
            summary = {
                'total_issues': len(issues),
                'total_recommendations': len(recommendations),
                'high_priority': len([r for r in processed_recommendations if r['priority'] == 'High']),
                'medium_priority': len([r for r in processed_recommendations if r['priority'] == 'Medium']),
                'low_priority': len([r for r in processed_recommendations if r['priority'] == 'Low'])
            }
            
            return {
                'issues': issues,
                'recommendations': processed_recommendations,
                'summary': summary
            }
            
        except Exception as e:
            print(f"Error processing UX data: {e}")
            return {'issues': [], 'recommendations': [], 'summary': {}}
    
    def process_screenshots_data(self) -> List[Dict[str, Any]]:
        """Process screenshots data"""
        screenshots_dir = self.raw_dir / "screenshots"
        if not screenshots_dir.exists():
            return []
        
        screenshots = []
        for img_file in sorted(screenshots_dir.glob("*.jpg")):
            screenshots.append({
                'filename': img_file.name,
                'title': f"Page {img_file.stem.split('_')[-1]}",
                'path': f"assets/screenshots/{img_file.name}",
                'size': img_file.stat().st_size if img_file.exists() else 0
            })
        
        return screenshots
    
    def process_sitemap_data(self) -> Dict[str, Any]:
        """Process sitemap data"""
        sitemap_png = self.raw_dir / "sitemap.png"
        sitemap_txt = self.raw_dir / "sitemap.txt"
        flows_file = self.raw_dir / "flows.json"
        
        data = {
            'has_visual': sitemap_png.exists(),
            'has_text': sitemap_txt.exists(),
            'visual_path': 'assets/sitemap.png' if sitemap_png.exists() else None,
            'nodes': 0,
            'edges': 0
        }
        
        if flows_file.exists():
            try:
                with open(flows_file, 'r') as f:
                    flows_data = json.load(f)
                    data['nodes'] = len(flows_data.get('nodes', []))
                    data['edges'] = len(flows_data.get('edges', []))
            except Exception:
                pass
        
        return data