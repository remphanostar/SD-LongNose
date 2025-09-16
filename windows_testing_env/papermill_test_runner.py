#!/usr/bin/env python3
"""
Papermill automated notebook testing for Pinokio deployment
"""

import os
import sys
import json
import papermill as pm
from pathlib import Path
import traceback
from datetime import datetime

# Import our mock GPU environment
sys.path.append(os.path.dirname(os.path.abspath(__file__)))
import mock_gpu_env

class NotebookTester:
    """Automated notebook testing with papermill"""
    
    def __init__(self, notebook_path: str, output_dir: str = "test_outputs"):
        self.notebook_path = Path(notebook_path)
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(exist_ok=True)
        self.timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        
    def run_test(self, parameters: dict = None) -> dict:
        """Run notebook test with papermill"""
        output_notebook = self.output_dir / f"test_result_{self.timestamp}.ipynb"
        
        try:
            print(f"🧪 Testing notebook: {self.notebook_path}")
            print(f"📝 Output will be saved to: {output_notebook}")
            
            # Run notebook with papermill
            pm.execute_notebook(
                input_path=str(self.notebook_path),
                output_path=str(output_notebook),
                parameters=parameters or {},
                kernel_name='python3',
                progress_bar=True,
                log_output=True
            )
            
            # Analyze results
            results = self.analyze_results(output_notebook)
            results['status'] = 'success'
            results['output_notebook'] = str(output_notebook)
            
            return results
            
        except Exception as e:
            print(f"❌ Test failed: {e}")
            results = {
                'status': 'failed',
                'error': str(e),
                'traceback': traceback.format_exc(),
                'output_notebook': str(output_notebook) if output_notebook.exists() else None
            }
            return results
    
    def analyze_results(self, output_notebook: Path) -> dict:
        """Analyze notebook execution results"""
        try:
            with open(output_notebook, 'r', encoding='utf-8') as f:
                notebook_data = json.load(f)
            
            results = {
                'cells_total': 0,
                'cells_executed': 0,
                'cells_with_errors': 0,
                'errors': [],
                'outputs': []
            }
            
            for cell in notebook_data.get('cells', []):
                if cell.get('cell_type') == 'code':
                    results['cells_total'] += 1
                    
                    # Check if cell was executed
                    if cell.get('execution_count') is not None:
                        results['cells_executed'] += 1
                    
                    # Check for errors
                    outputs = cell.get('outputs', [])
                    for output in outputs:
                        if output.get('output_type') == 'error':
                            results['cells_with_errors'] += 1
                            error_info = {
                                'cell_index': notebook_data['cells'].index(cell),
                                'error_name': output.get('ename', 'Unknown'),
                                'error_value': output.get('evalue', ''),
                                'traceback': output.get('traceback', [])
                            }
                            results['errors'].append(error_info)
                        elif output.get('output_type') in ['stream', 'execute_result']:
                            # Capture output text for analysis
                            if 'text' in output:
                                results['outputs'].append(output['text'])
                            elif 'data' in output and 'text/plain' in output['data']:
                                results['outputs'].append(output['data']['text/plain'])
            
            return results
            
        except Exception as e:
            return {'analysis_error': str(e)}
    
    def create_test_report(self, results: dict) -> str:
        """Create human-readable test report"""
        report = ["="*60]
        report.append("🧪 NOTEBOOK TEST REPORT")
        report.append("="*60)
        report.append(f"📅 Timestamp: {self.timestamp}")
        report.append(f"📓 Notebook: {self.notebook_path}")
        report.append(f"📊 Status: {results.get('status', 'unknown').upper()}")
        
        if results['status'] == 'success':
            report.append("\n✅ EXECUTION SUMMARY:")
            report.append(f"  • Total cells: {results.get('cells_total', 0)}")
            report.append(f"  • Executed cells: {results.get('cells_executed', 0)}")
            report.append(f"  • Cells with errors: {results.get('cells_with_errors', 0)}")
            
            if results.get('errors'):
                report.append("\n❌ ERRORS FOUND:")
                for i, error in enumerate(results['errors'], 1):
                    report.append(f"  {i}. Cell {error['cell_index']}: {error['error_name']}")
                    report.append(f"     {error['error_value']}")
            else:
                report.append("\n🎉 NO ERRORS FOUND!")
                
        else:
            report.append(f"\n❌ EXECUTION FAILED:")
            report.append(f"  Error: {results.get('error', 'Unknown')}")
        
        return "\n".join(report)

def main():
    """Main test runner"""
    notebook_file = "Pinokio_Colab_Final(1).ipynb"
    
    if not Path(notebook_file).exists():
        print(f"❌ Notebook not found: {notebook_file}")
        return 1
    
    print("🧪 AUTOMATED NOTEBOOK TESTING")
    print("="*50)
    
    # Initialize mock environment
    print("🔧 Setting up mock GPU environment...")
    # Mock environment is already set up via import
    
    # Run test
    tester = NotebookTester(notebook_file)
    results = tester.run_test()
    
    # Generate report
    report = tester.create_test_report(results)
    print(report)
    
    # Save report
    report_file = tester.output_dir / f"test_report_{tester.timestamp}.txt"
    with open(report_file, 'w', encoding='utf-8') as f:
        f.write(report)
    
    print(f"\n📝 Report saved to: {report_file}")
    
    return 0 if results['status'] == 'success' else 1

if __name__ == "__main__":
    sys.exit(main())
