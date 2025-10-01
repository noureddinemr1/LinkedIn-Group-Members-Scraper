import requests,csv,random
from urllib.parse import urljoin
from typing import Dict, List, Optional
from bs4 import BeautifulSoup
from playwright.sync_api import sync_playwright
from utils.headers import headers



class GroupsMembersScraper:
    def __init__(self,email, password):
        self.email = email
        self.password = password
        self.base_url = "https://www.linkedin.com/"
        self.login_url = urljoin(self.base_url, "login")
        self.browser = None
        self.page = None

    def startBrowser(self):
        self.playwright = sync_playwright().start()
        self.browser = self.playwright.chromium.launch(headless=False)
        self.context = self.browser.new_context()
        self.page = self.context.new_page()

    def stop_browser(self):
        if self.browser:
            self.browser.close()
        if hasattr(self, "playwright"):
            self.playwright.stop()
    

    
    def login(self):
        try:
            self.page.goto(self.login_url)
            self.page.fill('input[name="session_key"]', self.email)
            self.page.fill('input[name="session_password"]', self.password)
            self.page.click('button[type="submit"]')
            self.page.wait_for_load_state('networkidle')
            print("Logged in successfully")
        except Exception as e:
            print(f"Login failed: {e}")

    def scroll_to_load_all_members(self):

        prev_height = 0

        while True:
            # Scroll to bottom
            self.page.evaluate("window.scrollTo(0, document.body.scrollHeight);")
            self.page.wait_for_timeout(random.uniform(0.2, 0.5) * 1000)

            # Click "Show more results" button if it exists
            show_more_btn = self.page.query_selector('button:has-text("Show more results")')
            
            if show_more_btn:
                try:
                    show_more_btn.click()
                    self.page.wait_for_timeout(random.uniform(1.5, 3.0) * 1000)
                    print("Clicked 'Show more results' button")
                except:
                    pass

            # Check if new content loaded
            new_height = self.page.evaluate("document.body.scrollHeight")
            if new_height == prev_height and not show_more_btn:
                # No new content and no button → done
                break
            prev_height = new_height


        
    def scrape_group_members(self, group_url) -> List[Dict[str, Optional[str]]]:
        self.page.goto(group_url)

        members = []

        try:
            self.page.wait_for_timeout(2000)
            content = self.page.content()

            join_button = self.page.query_selector('button:has-text("Join")')
            if join_button:
                join_button.click()

            self.page.wait_for_timeout(2000)
            self.page.goto(urljoin(group_url, "members/"))
            self.page.wait_for_timeout(2000)

            self.scroll_to_load_all_members()

            content = self.page.content()
            soup = BeautifulSoup(content, 'html.parser')
            member_elements = soup.select_one('ul.artdeco-list.groups-members-list__results-list')

            for member in member_elements.find_all('li'):
                name_elem = member.find('div',class_='artdeco-entity-lockup__title ember-view entity-action-title')
                profile_url_elem = member.find('a',class_='ember-view ui-conditional-link-wrapper ui-entity-action-row__link')
                
                name = name_elem.get_text(strip=True) if name_elem else None
                profile_url = urljoin(self.base_url, profile_url_elem['href']) if profile_url_elem else None
                
                members.append({
                    'name': name,
                    'profile_url': profile_url
                })

            print(f"Scraped {len(members)} members")
            return members
        except Exception as e:
            print(f"Error scraping members: {e}")
            return members


                
                    

                
            



