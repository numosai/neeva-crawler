"""
QA Analyzer - Enhanced multi-page user flow testing
"""
import json
import yaml
from pathlib import Path
from urllib.parse import urlparse
from .base import BaseAnalyzer
from ..config.prompts import USER_FLOW_DISCOVERY_PROMPT, MULTI_PAGE_QA_PROMPT
from schema import QATestFile


class UserFlowAnalyzer(BaseAnalyzer):
    """Phase 1: Discovers realistic user flows across multiple pages"""
    
    def __init__(self):
        super().__init__()
        self.prompt = USER_FLOW_DISCOVERY_PROMPT
    
    async def discover_user_flows(self, base_url: str, output_dir: Path, model: str = "gemini/gemini-2.5-flash") -> dict:
        """Discover user flows from crawled site data"""
        raw_dir = output_dir / "raw"
        flows_file = raw_dir / "flows.json"
        
        if not flows_file.exists():
            print("❌ No flows.json found. Run full crawl first.")
            return {}
        
        print(f"🔍 Discovering user flows using {model}...")
        
        # Load the actual site navigation data
        with open(flows_file, 'r') as f:
            site_data = json.load(f)
        
        # Create enhanced prompt with actual site data
        enhanced_prompt = self.prompt + f"\n\nActual Site Navigation Data:\n{json.dumps(site_data, indent=2)[:5000]}\n\nBase URL: {base_url}"
        
        # Use direct LLM call with enhanced prompt
        result_data = await self._call_llm_directly(enhanced_prompt, model)
        
        if result_data:
            # Handle Gemini's wrapped response format
            flows_data = {}
            
            if isinstance(result_data, list) and len(result_data) > 0:
                # Gemini returns: [{"flows": [...], "error": false}]
                first_item = result_data[0]
                if isinstance(first_item, dict) and 'flows' in first_item:
                    flows_data = {"flows": first_item['flows']}
                    # Check if there was an error in the response
                    if first_item.get('error', False):
                        print(f"⚠️ LLM reported error: {first_item.get('content', 'Unknown error')}")
                        flows_data = {"flows": []}
                else:
                    # Assume list items are flows directly
                    flows_data = {"flows": result_data}
            elif isinstance(result_data, dict):
                # Direct dict response
                if 'flows' in result_data:
                    flows_data = result_data
                else:
                    flows_data = {"flows": [result_data]}
            else:
                print(f"⚠️ Unexpected result format: {type(result_data)}")
                flows_data = {"flows": []}
            
            # Save user flows
            user_flows_file = raw_dir / "user_flows.json"
            with open(user_flows_file, 'w') as f:
                json.dump(flows_data, f, indent=2)
            
            flow_count = len(flows_data.get('flows', []))
            print(f"✅ Discovered {flow_count} user flows saved to {user_flows_file}")
            return flows_data
        else:
            print("❌ Failed to discover user flows")
            return {}
    
    async def _analyze_html_content(self, html_content: str, url: str) -> dict:
        """Not used in this analyzer"""
        return {}
    
    def _create_multi_page_analysis(self, all_pages_data: list, base_url: str) -> dict:
        """Not used in this analyzer"""
        return {}
    
    def _get_output_filename(self) -> str:
        """Not used in this analyzer"""
        return "user_flows.json"
    
    async def _call_llm_directly(self, prompt: str, model: str) -> dict:
        """Make direct LLM call using Google's Vertex AI"""
        try:
            import os
            import google.generativeai as genai
            
            # Configure with API key
            api_key = os.getenv('GOOGLE_API_KEY')
            if not api_key:
                print("❌ GOOGLE_API_KEY not found in environment")
                return None
                
            genai.configure(api_key=api_key)
            
            # Use the model name without the provider prefix
            model_name = model.replace('gemini/', '')
            llm = genai.GenerativeModel(model_name)
            
            response = llm.generate_content(prompt)
            
            if response and response.text:
                try:
                    # Try to parse as JSON
                    import json
                    return json.loads(response.text)
                except json.JSONDecodeError:
                    # If not valid JSON, try to extract JSON from text
                    text = response.text.strip()
                    if text.startswith('```json'):
                        text = text.replace('```json', '').replace('```', '').strip()
                    elif text.startswith('```'):
                        text = text.replace('```', '').strip()
                    
                    try:
                        return json.loads(text)
                    except json.JSONDecodeError:
                        return None
            else:
                return None
                
        except Exception as e:
            return None


class QAAnalyzer(BaseAnalyzer):
    """Generates comprehensive multi-page QA tests from user flows"""
    
    def __init__(self):
        super().__init__()
        self.prompt = MULTI_PAGE_QA_PROMPT
        self.user_flow_analyzer = UserFlowAnalyzer()
    
    
    async def analyze_cached_pages_with_model(self, url: str, model: str, output_dir: Path) -> bool:
        """Run QA analysis on cached pages with specified model - similar to UX analyzer pattern"""
        raw_dir = output_dir / "raw"
        
        # Start fresh - delete existing QA outputs
        tests_dir = raw_dir / "tests"
        user_flows_file = raw_dir / "user_flows.json"
        
        if tests_dir.exists():
            import shutil
            shutil.rmtree(tests_dir)
            print("🗑️ Cleared existing test files")
        
        if user_flows_file.exists():
            user_flows_file.unlink()
            print("🗑️ Cleared existing user flows")
        
        return await self.analyze_from_existing_data(url, model, output_dir)
    
    async def analyze_from_existing_data(self, url: str, model: str = "gemini/gemini-2.5-flash", 
                                       output_dir: Path = None) -> bool:
        """Regenerate QA test plan using existing crawled data"""
        if not output_dir:
            parsed = urlparse(url)
            domain = parsed.netloc.replace(":", "_")
            output_dir = Path("output") / domain
        
        raw_dir = output_dir / "raw"
        
        # Check if user flows already exist and are valid
        user_flows_file = raw_dir / "user_flows.json"
        user_flows_data = {}
        
        if user_flows_file.exists():
            try:
                with open(user_flows_file, 'r') as f:
                    potential_flows = json.load(f)
                
                # Validate the loaded data
                if isinstance(potential_flows, dict) and 'flows' in potential_flows and len(potential_flows['flows']) > 0:
                    # Check if flows contain errors
                    valid_flows = [f for f in potential_flows['flows'] if not f.get('error', False)]
                    if valid_flows:
                        print("📄 Using existing valid user flows...")
                        user_flows_data = {'flows': valid_flows}
                    else:
                        print("⚠️ Existing flows contain errors, regenerating...")
                        user_flows_data = {}
                else:
                    print("⚠️ Invalid user flows format, regenerating...")
                    user_flows_data = {}
            except (json.JSONDecodeError, KeyError):
                print("⚠️ Corrupted user flows file, regenerating...")
                user_flows_data = {}
        
        # Generate flows if we don't have valid ones
        if not user_flows_data or not user_flows_data.get('flows'):
            print("🔍 Discovering user flows from existing data...")
            user_flows_data = await self.user_flow_analyzer.discover_user_flows(url, output_dir, model)
        
        if not user_flows_data or not user_flows_data.get('flows'):
            print("❌ No user flows available")
            return False
        
        return await self._generate_flow_based_tests(url, user_flows_data, model, output_dir)
    
    async def _generate_flow_based_tests(self, url: str, user_flows_data: dict, model: str, output_dir: Path) -> bool:
        """Generate QA tests based on discovered user flows"""
        raw_dir = output_dir / "raw"
        flows_file = raw_dir / "flows.json"
        
        # Load cached page content (clean markdown)
        cached_content = {}
        for flow in user_flows_data.get('flows', []):
            for page_ref in flow.get('page_sequence', []):
                # Handle both page IDs (page_1) and URLs
                if page_ref.startswith('page_'):
                    # Use clean markdown content for better analysis
                    md_file = raw_dir / f"{page_ref}_content.md"
                    if md_file.exists():
                        with open(md_file, 'r', encoding='utf-8') as f:
                            cached_content[page_ref] = f.read()  # No truncation - markdown is clean
                    else:
                        print(f"⚠️ Cached markdown not found for {page_ref} at {md_file}")
                else:
                    # For URLs, try to find corresponding page_X file from flows.json
                    # Skip URLs as they're not in our cached content
                    print(f"⚠️ Skipping URL reference: {page_ref} (not in cached pages)")
        
        # Load screenshots if available
        screenshot_dir = raw_dir / "screenshots"
        screenshots = []
        if screenshot_dir.exists():
            screenshots = [f.name for f in sorted(screenshot_dir.glob("*.jpg"))]
        
        # Prepare comprehensive input for multi-page test generation
        qa_input = {
            'base_url': url,
            'user_flows': user_flows_data.get('flows', []),
            'cached_page_content': cached_content,
            'available_screenshots': screenshots,
            'generation_mode': 'multi_page_flow_testing'
        }
        
        print(f"🧪 Generating multi-page QA tests using {model}...")
        
        # Use direct LLM call for QA generation too  
        full_prompt = self.prompt + f"\n\nFlow-Based QA Generation Data:\n{json.dumps(qa_input, indent=2)}"
        result_data = await self._call_llm_directly(full_prompt, model)
        
        if result_data:
            # Convert result_data to JSON string for _write_test_files method
            result_json = json.dumps(result_data)
            return self._write_test_files(result_json, raw_dir)
        else:
            print("❌ Failed to generate flow-based QA tests")
            return False
    
    
    def _write_test_files(self, extracted_content: str, raw_dir: Path) -> bool:
        """Write QA test files as YAML (same as original QA analyzer)"""
        try:
            data = json.loads(extracted_content)
            
            # Create tests subdirectory for YAML files
            tests_dir = raw_dir / "tests"
            tests_dir.mkdir(exist_ok=True)
            
            # Handle both single test and multiple tests
            if not isinstance(data, list):
                data = [data]
            
            # Validate and write each test as a separate YAML file
            test_count = 0
            total_phases = 0
            for idx, test_data in enumerate(data):
                try:
                    # Ensure the test has the correct structure
                    if 'name' not in test_data:
                        test_data['name'] = f"flow_test_{idx + 1}"
                    if 'qa_plan' not in test_data:
                        test_data = {'name': f"flow_test_{idx + 1}", 'qa_plan': test_data}
                    
                    # Validate through schema
                    validated_test = QATestFile(**test_data)
                    
                    # Generate filename from test name
                    filename = validated_test.name.lower().replace(' ', '_').replace('-', '_')
                    filename = ''.join(c if c.isalnum() or c == '_' else '' for c in filename)
                    if not filename:
                        filename = f"flow_test_{idx + 1}"
                    
                    # Ensure unique filename
                    yaml_path = tests_dir / f"{filename}.yaml"
                    counter = 1
                    while yaml_path.exists():
                        yaml_path = tests_dir / f"{filename}_{counter}.yaml"
                        counter += 1
                    
                    # Write as YAML
                    with open(yaml_path, "w") as f:
                        yaml.dump(validated_test.model_dump(), f, default_flow_style=False, sort_keys=False)
                    
                    test_count += 1
                    total_phases += len(validated_test.qa_plan.phases)
                    print(f"✅ Multi-page test saved: {yaml_path.name}")
                    
                except Exception as e:
                    print(f"⚠️ Validation error for test {idx + 1}: {e}")
            
            print(f"📊 Generated {test_count} flow-based test files with {total_phases} total phases in {tests_dir}")
            return test_count > 0
            
        except Exception as e:
            print(f"❌ Error processing QA test data: {e}")
            return False
    
    async def _analyze_html_content(self, html_content: str, url: str) -> dict:
        """Not used in this analyzer"""
        return {}
    
    def _create_multi_page_analysis(self, all_pages_data: list, base_url: str) -> dict:
        """Not used in this analyzer"""
        return {}
    
    def _get_output_filename(self) -> str:
        """Not used in this analyzer"""
        return "qa_tests.json"
    
    async def _call_llm_directly(self, prompt: str, model: str) -> dict:
        """Make direct LLM call using Google's Vertex AI"""
        try:
            import os
            import google.generativeai as genai
            
            # Configure with API key
            api_key = os.getenv('GOOGLE_API_KEY')
            if not api_key:
                print("❌ GOOGLE_API_KEY not found in environment")
                return None
                
            genai.configure(api_key=api_key)
            
            # Use the model name without the provider prefix
            model_name = model.replace('gemini/', '')
            llm = genai.GenerativeModel(model_name)
            
            response = llm.generate_content(prompt)
            
            if response and response.text:
                try:
                    # Try to parse as JSON
                    import json
                    return json.loads(response.text)
                except json.JSONDecodeError:
                    # If not valid JSON, try to extract JSON from text
                    text = response.text.strip()
                    if text.startswith('```json'):
                        text = text.replace('```json', '').replace('```', '').strip()
                    elif text.startswith('```'):
                        text = text.replace('```', '').strip()
                    
                    try:
                        return json.loads(text)
                    except json.JSONDecodeError:
                        return None
            else:
                return None
                
        except Exception as e:
            return None