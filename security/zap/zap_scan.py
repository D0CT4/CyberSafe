#!/usr/bin/env python3
from zapv2 import ZAPv2
import time
import sys
import os
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger('zap_scan')

class ZAPScanner:
    def __init__(self, target_url, api_key=None):
        self.target_url = target_url
        # ZAP Python API client
        self.zap = ZAPv2(apikey=api_key,
                        proxies={'http': 'http://127.0.0.1:8080', 
                                'https': 'http://127.0.0.1:8080'})
    
    def setup_context(self):
        """Setup the scanning context and scope"""
        logger.info('Setting up ZAP context...')
        self.context_id = 1
        self.context_name = 'AI Bridge Context'
        
        # Create context
        self.zap.context.new_context(self.context_name)
        
        # Include target URL in context
        self.zap.context.include_in_context(self.context_name, f"^{self.target_url}.*$")
        
        # Enable all scanners
        self.zap.pscan.enable_all_scanners()
        
    def spider_target(self):
        """Spider the target to discover endpoints"""
        logger.info('Spidering target...')
        scan_id = self.zap.spider.scan(self.target_url)
        
        # Wait for spider to complete
        while int(self.zap.spider.status(scan_id)) < 100:
            logger.info(f'Spider progress: {self.zap.spider.status(scan_id)}%')
            time.sleep(2)
            
    def active_scan(self):
        """Run active scan against discovered endpoints"""
        logger.info('Starting active scan...')
        scan_id = self.zap.ascan.scan(self.target_url)
        
        # Wait for active scan to complete
        while int(self.zap.ascan.status(scan_id)) < 100:
            logger.info(f'Active scan progress: {self.zap.ascan.status(scan_id)}%')
            time.sleep(5)
            
    def generate_report(self):
        """Generate HTML report of findings"""
        logger.info('Generating report...')
        report_dir = "reports"
        os.makedirs(report_dir, exist_ok=True)
        
        # Generate HTML report
        report_path = os.path.join(report_dir, "zap_report.html")
        with open(report_path, 'w') as f:
            f.write(self.zap.core.htmlreport())
            
        # Get alerts
        alerts = self.zap.core.alerts()
        return alerts, report_path

def main():
    target_url = "http://localhost:5000"  # AI Bridge API server
    api_key = os.getenv('ZAP_API_KEY')  # Optional API key
    
    try:
        scanner = ZAPScanner(target_url, api_key)
        scanner.setup_context()
        scanner.spider_target()
        scanner.active_scan()
        alerts, report_path = scanner.generate_report()
        
        # Print summary
        logger.info(f"\nScan completed. Report saved to: {report_path}")
        logger.info(f"Total alerts found: {len(alerts)}")
        
        # Print high-risk findings
        high_risks = [a for a in alerts if a['risk'] == 'High']
        if high_risks:
            logger.warning("\nHigh Risk Findings:")
            for alert in high_risks:
                logger.warning(f"- {alert['name']}: {alert['url']}")
                
    except Exception as e:
        logger.error(f"Scan failed: {str(e)}")
        sys.exit(1)

if __name__ == "__main__":
    main()
