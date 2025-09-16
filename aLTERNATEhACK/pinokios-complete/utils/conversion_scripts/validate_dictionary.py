#!/usr/bin/env python3
"""
Dictionary Validation Script for Pinokio Apps
Validates dictionary entries against actual GitHub repositories and checks for Pinokio-specific files
"""

import requests
import json
import time
from typing import Dict, List, Tuple

class DictionaryValidator:
    def __init__(self):
        self.github_token = None  # Add GitHub token if needed for higher rate limits
        self.session = requests.Session()
        
    def load_dictionary(self, file_path: str) -> Dict:
        """Load the dictionary from the Python file"""
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()
        
        # Extract the PINOKIO_APPS dictionary
        start_marker = 'PINOKIO_APPS = {'
        end_marker = '\n}'
        
        start_idx = content.find(start_marker)
        if start_idx == -1:
            raise ValueError("Could not find PINOKIO_APPS dictionary")
        
        # Find the matching closing brace
        brace_count = 0
        end_idx = start_idx
        for i, char in enumerate(content[start_idx:], start_idx):
            if char == '{':
                brace_count += 1
            elif char == '}':
                brace_count -= 1
                if brace_count == 0:
                    end_idx = i + 1
                    break
        
        dict_str = content[start_idx:end_idx]
        
        # Clean up the dictionary string to make it valid JSON
        dict_str = dict_str.replace('PINOKIO_APPS = ', '')
        dict_str = dict_str.replace("'", '"')
        dict_str = dict_str.replace('True', 'true').replace('False', 'false')
        
        return json.loads(dict_str)
    
    def check_repo_exists(self, owner: str, repo: str) -> bool:
        """Check if a GitHub repository exists"""
        url = f"https://api.github.com/repos/{owner}/{repo}"
        headers = {'Accept': 'application/vnd.github.v3+json'}
        if self.github_token:
            headers['Authorization'] = f'token {self.github_token}'
        
        try:
            response = self.session.get(url, headers=headers)
            return response.status_code == 200
        except Exception as e:
            print(f"Error checking {owner}/{repo}: {e}")
            return False
    
    def check_pinokio_files(self, owner: str, repo: str) -> Dict[str, bool]:
        """Check for Pinokio-specific files in a repository"""
        files_to_check = [
            'install.js',
            'install.json', 
            'pinokio.js',
            'pinokio_meta.json'
        ]
        
        results = {}
        for file in files_to_check:
            url = f"https://api.github.com/repos/{owner}/{repo}/contents/{file}"
            headers = {'Accept': 'application/vnd.github.v3+json'}
            if self.github_token:
                headers['Authorization'] = f'token {self.github_token}'
            
            try:
                response = self.session.get(url, headers=headers)
                results[file] = response.status_code == 200
            except Exception as e:
                results[file] = False
            
            # Rate limiting
            time.sleep(0.1)
        
        return results
    
    def is_pinokio_app(self, files: Dict[str, bool]) -> bool:
        """Determine if a repo is a proper Pinokio app"""
        # Must have either install.js OR install.json, AND pinokio.js
        has_install = files.get('install.js', False) or files.get('install.json', False)
        has_pinokio = files.get('pinokio.js', False)
        return has_install and has_pinokio
    
    def validate_dictionary(self, dictionary: Dict) -> Dict:
        """Validate all entries in the dictionary"""
        results = {
            'valid_pinokio_apps': [],
            'basic_installers': [],
            'non_existent': [],
            'invalid_entries': [],
            'summary': {}
        }
        
        total_entries = len(dictionary)
        processed = 0
        
        print(f"Validating {total_entries} dictionary entries...")
        
        for app_id, app_data in dictionary.items():
            processed += 1
            print(f"[{processed}/{total_entries}] Checking {app_id}...")
            
            # Extract owner and repo from URLs
            repo_url = app_data.get('repo_url', '')
            if not repo_url or 'github.com' not in repo_url:
                results['invalid_entries'].append({
                    'app_id': app_id,
                    'reason': 'Invalid or missing repo_url',
                    'data': app_data
                })
                continue
            
            try:
                # Extract owner/repo from URL
                parts = repo_url.replace('https://github.com/', '').split('/')
                if len(parts) < 2:
                    results['invalid_entries'].append({
                        'app_id': app_id,
                        'reason': 'Cannot parse owner/repo from URL',
                        'data': app_data
                    })
                    continue
                
                owner, repo = parts[0], parts[1]
                
                # Check if repo exists
                if not self.check_repo_exists(owner, repo):
                    results['non_existent'].append({
                        'app_id': app_id,
                        'owner': owner,
                        'repo': repo,
                        'data': app_data
                    })
                    continue
                
                # Check for Pinokio files
                files = self.check_pinokio_files(owner, repo)
                
                entry = {
                    'app_id': app_id,
                    'owner': owner,
                    'repo': repo,
                    'files': files,
                    'data': app_data
                }
                
                if self.is_pinokio_app(files):
                    results['valid_pinokio_apps'].append(entry)
                else:
                    results['basic_installers'].append(entry)
                
                # Rate limiting
                time.sleep(0.5)
                
            except Exception as e:
                results['invalid_entries'].append({
                    'app_id': app_id,
                    'reason': f'Error processing: {str(e)}',
                    'data': app_data
                })
        
        # Generate summary
        results['summary'] = {
            'total_entries': total_entries,
            'valid_pinokio_apps': len(results['valid_pinokio_apps']),
            'basic_installers': len(results['basic_installers']),
            'non_existent': len(results['non_existent']),
            'invalid_entries': len(results['invalid_entries'])
        }
        
        return results
    
    def generate_report(self, results: Dict, output_file: str):
        """Generate a detailed validation report"""
        with open(output_file, 'w', encoding='utf-8') as f:
            f.write("# Pinokio Dictionary Validation Report\n\n")
            
            # Summary
            f.write("## Summary\n\n")
            summary = results['summary']
            f.write(f"- **Total Entries**: {summary['total_entries']}\n")
            f.write(f"- **Valid Pinokio Apps**: {summary['valid_pinokio_apps']}\n")
            f.write(f"- **Basic Installers**: {summary['basic_installers']}\n") 
            f.write(f"- **Non-existent Repos**: {summary['non_existent']}\n")
            f.write(f"- **Invalid Entries**: {summary['invalid_entries']}\n\n")
            
            # Valid Pinokio Apps
            f.write("## ✅ Valid Pinokio Apps\n\n")
            for app in results['valid_pinokio_apps']:
                files_list = [k for k, v in app['files'].items() if v]
                f.write(f"- **{app['app_id']}** ({app['owner']}/{app['repo']}) - Files: {', '.join(files_list)}\n")
            f.write("\n")
            
            # Basic Installers
            f.write("## 🔧 Basic Installers (Not Pinokio Apps)\n\n")
            for app in results['basic_installers']:
                files_list = [k for k, v in app['files'].items() if v]
                f.write(f"- **{app['app_id']}** ({app['owner']}/{app['repo']}) - Files: {', '.join(files_list)}\n")
            f.write("\n")
            
            # Non-existent
            f.write("## ❌ Non-existent Repositories\n\n")
            for app in results['non_existent']:
                f.write(f"- **{app['app_id']}** - {app['owner']}/{app['repo']} (does not exist)\n")
            f.write("\n")
            
            # Invalid entries
            f.write("## 🚫 Invalid Entries\n\n")
            for app in results['invalid_entries']:
                f.write(f"- **{app['app_id']}** - {app['reason']}\n")
            f.write("\n")
    
    def generate_cleaned_dictionary(self, results: Dict, output_file: str):
        """Generate a cleaned dictionary with only valid Pinokio apps"""
        cleaned_dict = {}
        
        for app in results['valid_pinokio_apps']:
            app_data = app['data'].copy()
            app_data['is_pinokio_app'] = True
            app_data['pinokio_files'] = app['files']
            cleaned_dict[app['app_id']] = app_data
        
        # Write the cleaned dictionary
        with open(output_file, 'w', encoding='utf-8') as f:
            f.write("# Cleaned Pinokio Apps Dictionary\n")
            f.write("# Contains only verified Pinokio applications with proper install methods\n\n")
            f.write("PINOKIO_APPS = ")
            json.dump(cleaned_dict, f, indent=2, ensure_ascii=False)
            f.write("\n")

def main():
    validator = DictionaryValidator()
    
    # Load dictionary
    dict_file = "267.py"
    print(f"Loading dictionary from {dict_file}...")
    dictionary = validator.load_dictionary(dict_file)
    print(f"Loaded {len(dictionary)} entries")
    
    # Validate dictionary
    results = validator.validate_dictionary(dictionary)
    
    # Generate reports
    validator.generate_report(results, "validation_report.md")
    validator.generate_cleaned_dictionary(results, "cleaned_dictionary.py")
    
    print("\nValidation complete!")
    print(f"- Valid Pinokio Apps: {results['summary']['valid_pinokio_apps']}")
    print(f"- Basic Installers: {results['summary']['basic_installers']}")
    print(f"- Non-existent Repos: {results['summary']['non_existent']}")
    print(f"- Invalid Entries: {results['summary']['invalid_entries']}")
    print("\nReports generated:")
    print("- validation_report.md")
    print("- cleaned_dictionary.py")

if __name__ == "__main__":
    main()
