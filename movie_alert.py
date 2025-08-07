#!/usr/bin/env python3
"""
BookMyShow Movie Booking Alert System
A modern, robust application to monitor movie booking availability
"""

import os
import sys
import time
import json
import logging
import re
from datetime import datetime
from typing import Dict, List, Optional
from dataclasses import dataclass
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
import smtplib
import argparse

# Optional imports for enhanced functionality
try:
    from dotenv import load_dotenv
    DOTENV_AVAILABLE = True
except ImportError:
    DOTENV_AVAILABLE = False

try:
    from twilio.rest import Client as TwilioClient
    TWILIO_AVAILABLE = True
except ImportError:
    TWILIO_AVAILABLE = False
    print("Twilio not installed. SMS alerts disabled.")

try:
    import plyer
    DESKTOP_NOTIFICATIONS = True
except ImportError:
    DESKTOP_NOTIFICATIONS = False
    print("plyer not installed. Desktop notifications disabled.")

try:
    from selenium import webdriver
    from selenium.webdriver.chrome.options import Options
    from selenium.webdriver.chrome.service import Service
    from selenium.webdriver.common.by import By
    from selenium.webdriver.support.ui import WebDriverWait
    from selenium.webdriver.support import expected_conditions as EC
    from webdriver_manager.chrome import ChromeDriverManager
    SELENIUM_AVAILABLE = True
except ImportError:
    SELENIUM_AVAILABLE = False
    print("Selenium not installed. Browser automation disabled.")


@dataclass
class MovieConfig:
    """Configuration for a movie to monitor"""
    name: str
    url: str
    city: str = "chennai"
    check_interval: int = 300  # 5 minutes default
    enabled: bool = True


@dataclass
class AlertConfig:
    """Configuration for alert methods"""
    email_enabled: bool = False
    sms_enabled: bool = False
    desktop_enabled: bool = False
    sound_enabled: bool = True


class BookMyShowMonitor:
    """Main class for monitoring BookMyShow movie bookings"""
    
    def __init__(self, config_file: str = "config.json"):
        self.config_file = config_file
        self.setup_logging()
        self.load_environment()
        self.load_config()
        self.driver = None
        
    def setup_logging(self):
        """Configure logging"""
        # Get log level from environment variable, default to INFO
        log_level = os.getenv('LOG_LEVEL', 'INFO').upper()
        level = getattr(logging, log_level, logging.INFO)
        
        logging.basicConfig(
            level=level,
            format='%(asctime)s - %(levelname)s - %(message)s',
            handlers=[
                logging.FileHandler('movie_alerts.log'),
                logging.StreamHandler(sys.stdout)
            ]
        )
        self.logger = logging.getLogger(__name__)
        
    def load_environment(self):
        """Load environment variables from .env file if available"""
        if DOTENV_AVAILABLE:
            env_file = ".env"
            if os.path.exists(env_file):
                self.logger.info(f"Loading environment variables from {env_file}")
                load_dotenv(env_file)
            else:
                self.logger.info("No .env file found, using system environment variables")
        else:
            self.logger.info("python-dotenv not installed, using system environment variables only")
        
    def expand_env_vars(self, obj):
        """Recursively expand environment variables in configuration"""
        if isinstance(obj, dict):
            return {key: self.expand_env_vars(value) for key, value in obj.items()}
        elif isinstance(obj, list):
            return [self.expand_env_vars(item) for item in obj]
        elif isinstance(obj, str):
            # Replace ${VAR_NAME} with environment variable value
            def replace_env_var(match):
                var_name = match.group(1)
                env_value = os.getenv(var_name)
                if env_value is not None:
                    return env_value
                else:
                    self.logger.warning(f"Environment variable {var_name} not found")
                    return match.group(0)  # Keep original if env var not found
            return re.sub(r'\$\{([^}]+)\}', replace_env_var, obj)
        else:
            return obj
        
    def load_config(self):
        """Load configuration from file or create default"""
        try:
            with open(self.config_file, 'r') as f:
                config = json.load(f)
        except FileNotFoundError:
            self.logger.info("Config file not found. Creating default configuration.")
            config = self.create_default_config()
            self.save_config(config)
        
        # Expand environment variables in the config
        config = self.expand_env_vars(config)
        
        self.movies = [MovieConfig(**movie) for movie in config.get('movies', [])]
        self.alert_config = AlertConfig(**config.get('alerts', {}))
        self.notification_config = config.get('notifications', {})
        
    def create_default_config(self) -> Dict:
        """Create default configuration"""
        return {
            "movies": [
                {
                    "name": "Sample Movie",
                    "url": "https://in.bookmyshow.com/movies/sample-movie/ET00000000",
                    "city": "mumbai",
                    "check_interval": 300,
                    "enabled": False
                }
            ],
            "alerts": {
                "email_enabled": False,
                "sms_enabled": False,
                "desktop_enabled": True,
                "sound_enabled": True
            },
            "notifications": {
                "email": {
                    "smtp_server": "smtp.gmail.com",
                    "smtp_port": 587,
                    "username": "",
                    "password": "",
                    "to_email": ""
                },
                "twilio": {
                    "account_sid": "",
                    "auth_token": "",
                    "from_number": "",
                    "to_number": ""
                }
            }
        }
        
    def save_config(self, config: Dict):
        """Save configuration to file"""
        with open(self.config_file, 'w') as f:
            json.dump(config, f, indent=2)
            

    def check_booking_status(self, movie: MovieConfig) -> bool:
        """
        Check if booking is open for a movie using Selenium
        Returns True if booking is available, False otherwise
        """
        return self.check_booking_status_selenium(movie)

    def setup_selenium_driver(self):
        """Setup Selenium Chrome driver with anti-detection measures"""
        if not SELENIUM_AVAILABLE:
            return None
            
        try:
            options = Options()
            
            # Anti-detection measures
            options.add_argument('--user-agent=Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/138.0.0.0 Safari/537.36')
            options.add_argument('--disable-blink-features=AutomationControlled')
            options.add_experimental_option("excludeSwitches", ["enable-automation"])
            options.add_experimental_option('useAutomationExtension', False)
            
            # Standard options
            options.add_argument('--headless')
            options.add_argument('--no-sandbox')
            options.add_argument('--disable-dev-shm-usage')
            options.add_argument('--disable-gpu')
            options.add_argument('--window-size=1920,1080')
            
            service = Service(ChromeDriverManager().install())
            driver = webdriver.Chrome(service=service, options=options)
            
            # Execute script to remove webdriver property
            driver.execute_script("Object.defineProperty(navigator, 'webdriver', {get: () => undefined})")
            
            return driver
        except Exception as e:
            self.logger.error(f"Failed to setup Selenium driver: {e}")
            return None

    def check_booking_status_selenium(self, movie: MovieConfig) -> bool:
        """
        Use Selenium to check booking status by looking for red 'Book tickets' button specifically
        """
        if not SELENIUM_AVAILABLE:
            self.logger.error("Selenium not available - cannot check booking status")
            return False
            
        try:
            self.logger.info(f"Checking booking status for: {movie.name}")
            
            if not self.driver:
                self.driver = self.setup_selenium_driver()
                
            if not self.driver:
                self.logger.error("Failed to setup browser driver")
                return False
                
            # Navigate to the movie page
            self.logger.debug(f"Navigating to: {movie.url}")
            self.driver.get(movie.url)
            
            # Wait for page to load with better timeout and conditions
            try:
                WebDriverWait(self.driver, 15).until(
                    EC.presence_of_element_located((By.TAG_NAME, "body"))
                )
                self.logger.debug("Page body loaded successfully")
                
                # Wait a bit more for dynamic content to load
                time.sleep(3)
                
            except Exception as wait_e:
                self.logger.error(f"Timeout waiting for page to load: {wait_e}")
                return False
            
            # Debug: Log page title
            page_title = self.driver.title
            self.logger.info(f"Page title: {page_title}")
            
            # Check for Cloudflare blocking
            if 'cloudflare' in page_title.lower() or 'attention required' in page_title.lower():
                self.logger.warning(f"⚠️  Detected Cloudflare blocking for {movie.name}")
                self.logger.info("Waiting 10 seconds and retrying...")
                time.sleep(10)
                
                # Retry with page refresh
                self.driver.refresh()
                time.sleep(5)
                
                # Check again
                new_title = self.driver.title
                
                if 'cloudflare' in new_title.lower() or 'attention required' in new_title.lower():
                    self.logger.error(f"❌ Still blocked by Cloudflare for {movie.name}. Skipping this check.")
                    return False
                else:
                    self.logger.info("✅ Successfully bypassed Cloudflare protection")
                    page_title = new_title
            
            # Log basic page info
            self.logger.debug(f"Current URL: {self.driver.current_url}")
            
            # STRICT VALIDATION: Look specifically for red "Book tickets" button
            booking_open = False
            
            try:
                # Strategy 1: Look for "Book tickets" text with more comprehensive selectors
                book_tickets_buttons = self.driver.find_elements(By.XPATH, 
                    "//button[contains(text(), 'Book tickets')] | "
                    "//a[contains(text(), 'Book tickets')] | "
                    "//*[@role='button' and contains(text(), 'Book tickets')] | "
                    "//div[contains(text(), 'Book tickets')] | "
                    "//span[contains(text(), 'Book tickets')] | "
                    "//*[contains(@class, 'book') and contains(text(), 'tickets')] | "
                    "//*[contains(text(), 'Book tickets')]"
                )
                
                if book_tickets_buttons:
                    self.logger.debug(f"Found {len(book_tickets_buttons)} 'Book tickets' buttons")
                    
                    # Check if any of these buttons have red/pink background
                    for button in book_tickets_buttons:
                        try:
                            # Get computed styles
                            bg_color = button.value_of_css_property('background-color')
                            color = button.value_of_css_property('color')
                            is_displayed = button.is_displayed()
                            is_enabled = button.is_enabled()
                            
                            self.logger.debug(f"Button - BG: {bg_color}, Color: {color}, Displayed: {is_displayed}, Enabled: {is_enabled}")
                            
                            # Check for red/pink background colors (various formats)
                            red_indicators = [
                                'rgb(220, 53, 69)',  # Bootstrap danger red
                                'rgb(248, 77, 122)', # Pink
                                'rgb(231, 76, 60)',  # Red
                                'rgb(255, 99, 132)', # Light red
                                'rgb(220, 20, 60)',  # Crimson
                                'rgb(240, 101, 149)', # BookMyShow pink
                                'rgb(255, 105, 135)', # Coral pink
                                'rgb(255, 92, 132)',  # BookMyShow button color
                                'rgb(235, 87, 87)',   # Light coral
                                '#dc3545', '#f84d7a', '#e74c3c', '#ff6384', '#dc143c',
                                '#f06595', '#ff6987', '#ff5c84', '#eb5757'  # Additional pinks
                            ]
                            
                            # Also check for any red-ish color (RGB with high red component)
                            is_red_bg = False
                            if bg_color and 'rgb' in bg_color:
                                import re
                                rgb_match = re.search(r'rgb\((\d+),\s*(\d+),\s*(\d+)\)', bg_color)
                                if rgb_match:
                                    r, g, b = map(int, rgb_match.groups())
                                    # Red-ish if red component is high and significantly higher than green/blue
                                    if r > 180 and r > (g + 50) and r > (b + 50):
                                        is_red_bg = True
                            
                            # Check if background color matches any red indicator or is red-ish
                            bg_is_red = any(red_color in bg_color for red_color in red_indicators) or is_red_bg
                            
                            if is_displayed and is_enabled and bg_is_red:
                                self.logger.info(f"✅ Found valid red 'Book tickets' button! BG: {bg_color}")
                                booking_open = True
                                break
                                
                        except Exception as style_e:
                            self.logger.debug(f"Error checking button styles: {style_e}")
                            continue
                
                # Strategy 2: If no red button found, do a more nuanced check
                if not booking_open:
                    page_source = self.driver.page_source.lower()
                    
                    # Check for both "I'm interested" and "book tickets" presence
                    has_interested = "i'm interested" in page_source or "mark interested" in page_source
                    has_book_tickets = "book tickets" in page_source
                    
                    if has_interested and not has_book_tickets:
                        # Only "I'm interested" found - booking definitely NOT open
                        self.logger.info(f"❌ Only 'I'm interested' found - booking NOT open for {movie.name}")
                        return False
                    elif has_book_tickets and not has_interested:
                        # Only "book tickets" found but no red button - might be open but be cautious
                        self.logger.warning(f"⚠️  Found 'book tickets' text but no red button for {movie.name}")
                        # For now, still return False for strict validation unless we find the red button
                        return False
                    elif has_interested and has_book_tickets:
                        # Both found - mixed state, some shows might be open
                        self.logger.warning(f"⚠️  Mixed state detected for {movie.name}: both 'interested' and 'book tickets' found")
                        # Look for any clickable "book tickets" buttons even without strict color validation
                        fallback_buttons = self.driver.find_elements(By.XPATH, 
                            "//button[contains(text(), 'Book tickets')] | "
                            "//a[contains(text(), 'Book tickets')] | "
                            "//div[contains(text(), 'Book tickets')] | "
                            "//span[contains(text(), 'Book tickets')] | "
                            "//*[contains(text(), 'Book tickets')]"
                        )
                        for button in fallback_buttons:
                            try:
                                if button.is_displayed() and button.is_enabled():
                                    self.logger.info(f"✅ Found enabled 'Book tickets' button in mixed state for {movie.name}")
                                    return True
                            except:
                                continue
                        self.logger.info(f"❌ No enabled 'Book tickets' buttons found in mixed state for {movie.name}")
                        return False
                    else:
                        # Neither found clearly - unclear state
                        self.logger.warning(f"⚠️  Unclear booking state for {movie.name} - neither clear 'interested' nor 'book tickets' found")
                        return False
                
            except Exception as elem_e:
                self.logger.error(f"Error during strict booking validation: {elem_e}")
                return False
            
            if booking_open:
                self.logger.info(f"🎉 STRICT VALIDATION PASSED: Red 'Book tickets' button found for {movie.name}!")
                return True
            else:
                self.logger.info(f"❌ STRICT VALIDATION FAILED: No red 'Book tickets' button found for {movie.name}")
                return False
                
        except Exception as e:
            self.logger.error(f"Error checking {movie.name}: {e}")
            return False

    def cleanup(self):
        """Clean up resources"""
        if self.driver:
            try:
                self.driver.quit()
            except:
                pass
            
    def send_desktop_notification(self, title: str, message: str):
        """Send desktop notification"""
        if not DESKTOP_NOTIFICATIONS or not self.alert_config.desktop_enabled:
            return
            
        try:
            plyer.notification.notify(
                title=title,
                message=message,
                timeout=10
            )
        except Exception as e:
            self.logger.error(f"Failed to send desktop notification: {e}")
            
    def send_email_alert(self, movie: MovieConfig):
        """Send email alert"""
        if not self.alert_config.email_enabled:
            return
            
        try:
            email_config = self.notification_config.get('email', {})
            if not all([email_config.get('username'), email_config.get('password'), email_config.get('to_email')]):
                self.logger.warning("Email configuration incomplete")
                return
                
            msg = MIMEMultipart()
            msg['From'] = email_config['username']
            msg['To'] = email_config['to_email']
            msg['Subject'] = f"🎬 Booking Open: {movie.name}"
            
            body = f"""
            Great news! Booking is now open for {movie.name}!
            
            🎬 Movie: {movie.name}
            🏙️ City: {movie.city}
            🔗 Link: {movie.url}
            ⏰ Detected at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
            
            Hurry up and book your tickets!
            """
            
            msg.attach(MIMEText(body, 'plain'))
            
            server = smtplib.SMTP(email_config['smtp_server'], email_config['smtp_port'])
            server.starttls()
            server.login(email_config['username'], email_config['password'])
            server.send_message(msg)
            server.quit()
            
            self.logger.info(f"Email alert sent for {movie.name}")
            
        except Exception as e:
            self.logger.error(f"Failed to send email alert: {e}")
            
    def send_sms_alert(self, movie: MovieConfig):
        """Send SMS alert via Twilio"""
        if not TWILIO_AVAILABLE:
            self.logger.warning("Twilio not available - SMS disabled")
            return
            
        if not self.alert_config.sms_enabled:
            self.logger.warning("SMS alerts are disabled in configuration")
            return
            
        try:
            twilio_config = self.notification_config.get('twilio', {})
            
            # Check each required config item
            missing_config = []
            placeholder_config = []
            for key in ['account_sid', 'auth_token', 'from_number', 'to_number']:
                value = twilio_config.get(key)
                if not value:
                    missing_config.append(key)
                elif value.startswith('${') or value.startswith('YOUR_TWILIO_'):
                    placeholder_config.append(key)
            
            if missing_config:
                self.logger.error(f"Twilio configuration incomplete. Missing: {missing_config}")
                return
                
            if placeholder_config:
                self.logger.error(f"Twilio configuration contains unresolved placeholders: {placeholder_config}")
                self.logger.error("Please set the required environment variables in .env file or system environment:")
                for key in placeholder_config:
                    env_var = key.upper().replace('_', '_').replace('NUMBER', '_NUMBER')
                    if 'account' in key:
                        env_var = 'TWILIO_ACCOUNT_SID'
                    elif 'auth' in key:
                        env_var = 'TWILIO_AUTH_TOKEN'
                    elif 'from' in key:
                        env_var = 'TWILIO_FROM_NUMBER'
                    elif 'to' in key:
                        env_var = 'TWILIO_TO_NUMBER'
                    self.logger.error(f"  {env_var}=your_value_here")
                return
            
            client = TwilioClient(twilio_config['account_sid'], twilio_config['auth_token'])
            
            message = f"🎬 BOOKING OPEN! {movie.name} tickets are now available! Book now: {movie.url}"
            
            result = client.messages.create(
                body=message,
                from_=twilio_config['from_number'],
                to=twilio_config['to_number']
            )
            
            self.logger.info(f"✅ SMS alert sent for {movie.name}. Message SID: {result.sid}")
            
        except Exception as e:
            self.logger.error(f"❌ Failed to send SMS alert: {e}")
            self.logger.error(f"Error type: {type(e).__name__}")
            
    def play_alert_sound(self):
        """Play alert sound"""
        if not self.alert_config.sound_enabled:
            return
            
        try:
            # macOS specific sound
            os.system('afplay /System/Library/Sounds/Glass.aiff')
        except Exception as e:
            self.logger.error(f"Failed to play alert sound: {e}")
            
    def send_all_alerts(self, movie: MovieConfig):
        """Send all configured alerts"""
        self.logger.info(f"🚨 SENDING ALERTS for {movie.name}")
        
        # Desktop notification
        if self.alert_config.desktop_enabled:
            self.send_desktop_notification("🎬 BookMyShow Alert", f"Booking is now OPEN for {movie.name}!")
        
        # Sound alert
        if self.alert_config.sound_enabled:
            self.play_alert_sound()
        
        # Email alert
        if self.alert_config.email_enabled:
            self.send_email_alert(movie)
        
        # SMS alert
        if self.alert_config.sms_enabled:
            self.send_sms_alert(movie)
        
        print(f"\n{'='*50}")
        print(f"🎉 BOOKING OPEN: {movie.name}")
        print(f"🔗 URL: {movie.url}")
        print(f"⏰ Time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        print(f"{'='*50}\n")
        
    def monitor_movies(self, run_once: bool = False):
        """Main monitoring loop"""
        if not self.movies:
            self.logger.error("No movies configured for monitoring!")
            return
            
        enabled_movies = [m for m in self.movies if m.enabled]
        if not enabled_movies:
            self.logger.error("No movies enabled for monitoring!")
            return
            
        self.logger.info(f"Starting monitoring for {len(enabled_movies)} movies...")
        
        for movie in enabled_movies:
            self.logger.info(f"  - {movie.name} (checking every {movie.check_interval}s)")
            
        try:
            while True:
                for movie in enabled_movies:
                    if self.check_booking_status(movie):
                        self.send_all_alerts(movie)
                        
                        if run_once:
                            return
                            
                        # Wait 10 minutes before checking again to avoid spam
                        self.logger.info(f"Waiting 10 minutes before next check for {movie.name}")
                        time.sleep(600)
                    else:
                        time.sleep(movie.check_interval)
                        
                if run_once:
                    break
                    
        except KeyboardInterrupt:
            self.logger.info("Monitoring stopped by user")
        except Exception as e:
            self.logger.error(f"Unexpected error in monitoring loop: {e}")
        finally:
            self.cleanup()
            
    def add_movie(self, name: str, url: str, city: str = "mumbai", interval: int = 300):
        """Add a new movie to monitor"""
        new_movie = {
            "name": name,
            "url": url,
            "city": city,
            "check_interval": interval,
            "enabled": True
        }
        
        # Load current config
        try:
            with open(self.config_file, 'r') as f:
                config = json.load(f)
        except FileNotFoundError:
            config = self.create_default_config()
            
        config['movies'].append(new_movie)
        self.save_config(config)
        
        self.logger.info(f"Added movie: {name}")
        print(f"✅ Added '{name}' to monitoring list")
        
    def list_movies(self):
        """List all configured movies"""
        if not self.movies:
            print("No movies configured.")
            return
            
        print("\n📽️  Configured Movies:")
        print("-" * 60)
        for i, movie in enumerate(self.movies, 1):
            status = "✅ Enabled" if movie.enabled else "❌ Disabled"
            print(f"{i}. {movie.name}")
            print(f"   City: {movie.city}")
            print(f"   Interval: {movie.check_interval}s")
            print(f"   Status: {status}")
            print(f"   URL: {movie.url}")
            print()


def main():
    """Main function with CLI interface"""
    parser = argparse.ArgumentParser(description="BookMyShow Movie Booking Alert System")
    parser.add_argument('--config', default='config.json', help='Configuration file path')
    parser.add_argument('--add-movie', nargs=4, metavar=('NAME', 'URL', 'CITY', 'INTERVAL'),
                       help='Add a new movie to monitor')
    parser.add_argument('--list', action='store_true', help='List configured movies')
    parser.add_argument('--check-once', action='store_true', help='Check all movies once and exit')
    parser.add_argument('--monitor', action='store_true', help='Start continuous monitoring')
    
    args = parser.parse_args()
    
    monitor = BookMyShowMonitor(args.config)
    
    if args.add_movie:
        name, url, city, interval = args.add_movie
        monitor.add_movie(name, url, city, int(interval))
    elif args.list:
        monitor.list_movies()
    elif args.check_once:
        monitor.monitor_movies(run_once=True)
    elif args.monitor:
        monitor.monitor_movies()
    else:
        # Interactive mode
        print("🎬 BookMyShow Movie Booking Alert System")
        print("=" * 50)
        print("1. List movies")
        print("2. Add movie")
        print("3. Start monitoring")
        print("4. Check once")
        print("5. Exit")
        
        while True:
            choice = input("\nEnter your choice (1-5): ").strip()
            
            if choice == '1':
                monitor.list_movies()
            elif choice == '2':
                name = input("Movie name: ").strip()
                url = input("BookMyShow URL: ").strip()
                city = input("City (default: mumbai): ").strip() or "mumbai"
                interval = input("Check interval in seconds (default: 300): ").strip()
                interval = int(interval) if interval.isdigit() else 300
                monitor.add_movie(name, url, city, interval)
            elif choice == '3':
                print("Starting monitoring... Press Ctrl+C to stop")
                monitor.monitor_movies()
            elif choice == '4':
                monitor.monitor_movies(run_once=True)
            elif choice == '5':
                print("Goodbye! 👋")
                break
            else:
                print("Invalid choice. Please try again.")


if __name__ == "__main__":
    main()
