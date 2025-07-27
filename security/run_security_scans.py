#!/usr/bin/env python3
import subprocess
import os
import logging
from datetime import datetime
import concurrent.futures

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger('security_scan')

class SecurityScanner:
    def __init__(self):
        self.scan_dir = os.path.dirname(os.path.abspath(__file__))
        self.reports_dir = os.path.join(self.scan_dir, "reports")
        os.makedirs(self.reports_dir, exist_ok=True)
    
    def run_zap_scan(self):
        """Run OWASP ZAP scan"""
        try:
            logger.info("Starting ZAP scan...")
            zap_script = os.path.join(self.scan_dir, "zap", "zap_scan.py")
            subprocess.run(["python", zap_script], check=True)
            logger.info("ZAP scan completed")
            return True
        except subprocess.CalledProcessError as e:
            logger.error(f"ZAP scan failed: {str(e)}")
            return False
    
    def run_burp_scan(self):
        """Run Burp Suite scan"""
        try:
            logger.info("Starting Burp Suite scan...")
            burp_script = os.path.join(self.scan_dir, "burp", "burp_scan.py")
            subprocess.run(["python", burp_script], check=True)
            logger.info("Burp Suite scan completed")
            return True
        except subprocess.CalledProcessError as e:
            logger.error(f"Burp scan failed: {str(e)}")
            return False
    
    def run_dependency_check(self):
        """Check dependencies for known vulnerabilities"""
        try:
            logger.info("Running dependency security check...")
            result = subprocess.run(
                ["safety", "check"],
                capture_output=True,
                text=True,
                check=True
            )
            
            report_path = os.path.join(
                self.reports_dir,
                f"dependency_check_{datetime.now().strftime('%Y%m%d_%H%M%S')}.txt"
            )
            
            with open(report_path, 'w') as f:
                f.write(result.stdout)
            
            logger.info(f"Dependency check completed. Report saved to: {report_path}")
            return True
        except subprocess.CalledProcessError as e:
            logger.error(f"Dependency check failed: {str(e)}")
            return False
    
    def run_bandit_scan(self):
        """Run Bandit static code analysis"""
        try:
            logger.info("Running Bandit static analysis...")
            report_path = os.path.join(
                self.reports_dir,
                f"bandit_report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
            )
            
            subprocess.run([
                "bandit",
                "-r", "..",  # Scan entire project
                "-f", "json",
                "-o", report_path
            ], check=True)
            
            logger.info(f"Bandit scan completed. Report saved to: {report_path}")
            return True
        except subprocess.CalledProcessError as e:
            logger.error(f"Bandit scan failed: {str(e)}")
            return False
    
    def run_all_scans(self):
        """Run all security scans in parallel where possible"""
        with concurrent.futures.ThreadPoolExecutor() as executor:
            # Run dynamic scans sequentially (they use same port)
            self.run_zap_scan()
            self.run_burp_scan()
            
            # Run static analysis tools in parallel
            futures = [
                executor.submit(self.run_dependency_check),
                executor.submit(self.run_bandit_scan)
            ]
            
            concurrent.futures.wait(futures)

def main():
    scanner = SecurityScanner()
    scanner.run_all_scans()

if __name__ == "__main__":
    main()
