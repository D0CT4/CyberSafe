#!/usr/bin/env python3
import requests
import logging
import json
import os
from datetime import datetime

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger('burp_scan')

class BurpScanner:
    def __init__(self, burp_api_url, api_key):
        self.burp_api_url = burp_api_url
        self.headers = {
            'Authorization': f'Bearer {api_key}',
            'Content-Type': 'application/json'
        }
    
    def start_scan(self, target_url):
        """Start a Burp Suite scan"""
        scan_config = {
            "scope": {
                "include": [{"rule": target_url}],
                "type": "SimpleScope"
            },
            "scan_configurations": [
                {
                    "type": "NamedConfiguration",
                    "name": "Crawl strategy - fastest"
                }
            ],
            "urls": [target_url]
        }
        
        response = requests.post(
            f"{self.burp_api_url}/v0.1/scan",
            headers=self.headers,
            json=scan_config
        )
        
        if response.status_code == 201:
            scan_id = response.headers.get('Location').split('/')[-1]
            logger.info(f"Scan started with ID: {scan_id}")
            return scan_id
        else:
            raise Exception(f"Failed to start scan: {response.text}")
    
    def get_scan_status(self, scan_id):
        """Get the current status of a scan"""
        response = requests.get(
            f"{self.burp_api_url}/v0.1/scan/{scan_id}",
            headers=self.headers
        )
        
        if response.status_code == 200:
            return response.json()
        else:
            raise Exception(f"Failed to get scan status: {response.text}")
    
    def get_scan_issues(self, scan_id):
        """Get all issues found in a scan"""
        response = requests.get(
            f"{self.burp_api_url}/v0.1/scan/{scan_id}/issues",
            headers=self.headers
        )
        
        if response.status_code == 200:
            return response.json()
        else:
            raise Exception(f"Failed to get scan issues: {response.text}")
    
    def generate_report(self, scan_id):
        """Generate HTML report for a scan"""
        report_config = {
            "format": "HTML",
            "filters": {
                "severity": ["high", "medium"]
            }
        }
        
        response = requests.post(
            f"{self.burp_api_url}/v0.1/scan/{scan_id}/report",
            headers=self.headers,
            json=report_config
        )
        
        if response.status_code == 200:
            report_dir = "reports"
            os.makedirs(report_dir, exist_ok=True)
            
            report_path = os.path.join(
                report_dir, 
                f"burp_report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.html"
            )
            
            with open(report_path, 'wb') as f:
                f.write(response.content)
            
            return report_path
        else:
            raise Exception(f"Failed to generate report: {response.text}")

def main():
    burp_api_url = os.getenv('BURP_API_URL', 'http://localhost:1337')
    burp_api_key = os.getenv('BURP_API_KEY')
    target_url = "http://localhost:5000"  # AI Bridge API server
    
    if not burp_api_key:
        logger.error("BURP_API_KEY environment variable not set")
        return
    
    try:
        scanner = BurpScanner(burp_api_url, burp_api_key)
        
        # Start scan
        scan_id = scanner.start_scan(target_url)
        
        # Monitor scan status
        while True:
            status = scanner.get_scan_status(scan_id)
            if status['scan_status'] == 'succeeded':
                break
            logger.info(f"Scan progress: {status.get('scan_metrics', {}).get('completed_percentage', 0)}%")
            time.sleep(30)
        
        # Get issues
        issues = scanner.get_scan_issues(scan_id)
        
        # Generate report
        report_path = scanner.generate_report(scan_id)
        
        # Print summary
        logger.info(f"\nScan completed. Report saved to: {report_path}")
        logger.info(f"Total issues found: {len(issues)}")
        
        # Print high severity issues
        high_severity = [i for i in issues if i['severity'] == 'high']
        if high_severity:
            logger.warning("\nHigh Severity Issues:")
            for issue in high_severity:
                logger.warning(f"- {issue['issue_type']}: {issue['url']}")
                
    except Exception as e:
        logger.error(f"Scan failed: {str(e)}")

if __name__ == "__main__":
    main()
