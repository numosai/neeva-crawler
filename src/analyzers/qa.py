"""
QA test generation module
"""
import json
import yaml
from pathlib import Path
from urllib.parse import urlparse
import networkx as nx
from crawl4ai import AsyncWebCrawler, CrawlerRunConfig, LLMExtractionStrategy, LLMConfig
from ..config.prompts import QA_PROMPT
from schema import QATestFile


class QAAnalyzer:
    """Handles QA test plan generation"""
    
    def __init__(self):
        self.prompt = QA_PROMPT
    
    async def analyze_from_crawl_data(self, url: str, crawled_pages: list, flows: list, 
                                    model: str = "google/gemini-flash-2.5", output_dir: Path = None) -> bool:
        """Generate QA test plans from crawled data"""
        if not output_dir:
            parsed = urlparse(url)
            domain = parsed.netloc.replace(":", "_")
            output_dir = Path("output") / domain
            
        raw_dir = output_dir / "raw"
        raw_dir.mkdir(parents=True, exist_ok=True)
        
        qa_input = {
            "pages": crawled_pages,
            "flows": flows
        }
        
        async with AsyncWebCrawler() as crawler:
            print(f"🧪 Generating QA test plan using {model}...")
            result = await crawler.arun(
                url,
                config=CrawlerRunConfig(
                    extraction_strategy=LLMExtractionStrategy(
                        llm_config=LLMConfig(provider=model),
                        prompt=self.prompt + f"\n\nData:\n{json.dumps(qa_input, indent=2)}",
                        schema={"type": "array", "items": QATestFile.model_json_schema()}
                    )
                )
            )
            
            if result.extracted_content:
                return self._write_test_files(result.extracted_content, raw_dir)
            else:
                print("❌ Failed to generate QA plan")
                return False
    
    async def analyze_from_existing_data(self, url: str, model: str = "google/gemini-flash-2.5", 
                                       output_dir: Path = None) -> bool:
        """Regenerate QA test plan using existing crawled data"""
        if not output_dir:
            parsed = urlparse(url)
            domain = parsed.netloc.replace(":", "_")
            output_dir = Path("output") / domain
        
        raw_dir = output_dir / "raw"
        flows_file = raw_dir / "flows.json"
        if not flows_file.exists():
            print(f"❌ No crawled data found. Please run full crawl first: python main.py {url}")
            return False
        
        # Load existing crawled data
        with open(flows_file, "r") as f:
            flow_data = json.load(f)
        
        # Reconstruct crawled pages from flow data
        crawled_pages = []
        graph = nx.DiGraph()
        
        # Rebuild graph from saved data
        for node, data in flow_data["nodes"]:
            graph.add_node(node, **data)
            if isinstance(node, str) and node.startswith("page_"):
                crawled_pages.append({
                    "id": node,
                    "url": data.get("url", ""),
                    "title": data.get("title", ""),
                    "markdown": data.get("markdown", "")
                })
        
        for edge in flow_data["edges"]:
            graph.add_edge(edge["from"], edge["to"], label=edge.get("label", ""))
        
        # Find navigation paths
        candidate_paths = []
        nodes = list(graph.nodes)
        for start in nodes[:5]:
            for end in nodes[:5]:
                if start != end:
                    try:
                        paths = nx.all_simple_paths(graph, source=start, target=end, cutoff=5)
                        for p in list(paths)[:2]:
                            candidate_paths.append(p)
                    except nx.NetworkXNoPath:
                        continue
        
        selected_flows = candidate_paths[:5]
        
        # Load screenshots if available
        screenshot_dir = raw_dir / "screenshots"
        screenshots = []
        if screenshot_dir.exists():
            for jpg_file in sorted(screenshot_dir.glob("*.jpg")):
                screenshots.append(jpg_file.name)
        
        qa_input = {
            "pages": crawled_pages,
            "flows": selected_flows,
            "screenshots_available": screenshots
        }
        
        async with AsyncWebCrawler() as crawler:
            print(f"🧪 Regenerating QA test plan using {model}...")
            result = await crawler.arun(
                url,
                config=CrawlerRunConfig(
                    extraction_strategy=LLMExtractionStrategy(
                        llm_config=LLMConfig(provider=model),
                        prompt=self.prompt + f"\n\nData:\n{json.dumps(qa_input, indent=2)}",
                        schema={"type": "array", "items": QATestFile.model_json_schema()}
                    )
                )
            )
            
            if result.extracted_content:
                return self._write_test_files(result.extracted_content, raw_dir)
            else:
                print("❌ Failed to generate QA plan")
                return False
    
    def _write_test_files(self, extracted_content: str, raw_dir: Path) -> bool:
        """Write QA test files as YAML"""
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
                        test_data['name'] = f"test_{idx + 1}"
                    if 'qa_plan' not in test_data:
                        # If old format (direct QAPlan), wrap it
                        test_data = {'name': f"test_{idx + 1}", 'qa_plan': test_data}
                    
                    # Validate through schema
                    validated_test = QATestFile(**test_data)
                    
                    # Generate filename from test name
                    filename = validated_test.name.lower().replace(' ', '_').replace('-', '_')
                    filename = ''.join(c if c.isalnum() or c == '_' else '' for c in filename)
                    if not filename:
                        filename = f"test_{idx + 1}"
                    
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
                    print(f"✅ Test saved: {yaml_path.name}")
                    
                except Exception as e:
                    print(f"⚠️ Validation error for test {idx + 1}: {e}")
            
            print(f"📊 Generated {test_count} test files with {total_phases} total phases in {tests_dir}")
            return test_count > 0
            
        except Exception as e:
            print(f"❌ Error processing QA test data: {e}")
            return False