import csv,random,json
from urllib.parse import urljoin
from typing import Dict, List, Optional
from bs4 import BeautifulSoup
from playwright.sync_api import sync_playwright
from utils.headers import headers
from Scraper.CaptchaSolver import *



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
        self.page.on("dialog", lambda dialog: dialog.dismiss())



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
            
            captcha_solver = CaptchaSolver(self.page)
            if captcha_solver.detect_captcha():
                print("Captcha detected after login attempt!")
                
                if captcha_solver.solve_captcha():
                    print("Captcha solved automatically!")
                else:
                    print("Automatic captcha solving failed. Trying manual approach...")
                    if captcha_solver.wait_for_manual_solve(timeout=120):
                        print("Captcha solved manually!")
                    else:
                        raise Exception("Captcha solving failed - manual intervention required")

            self.page.wait_for_timeout(2000)
        except Exception as e:
            print(f"Login failed: {e}")



    def scroll_to_load_all_members(self):
        prev_height = 0

        while True:
            self.page.evaluate("window.scrollTo(0, document.body.scrollHeight);")
            self.page.wait_for_timeout(random.uniform(0.2, 0.5) * 1000)

            show_more_btn = self.page.query_selector('button:has-text("Show more results"), button:has-text("Afficher plus de résultats")')
            if show_more_btn:
                try:
                    show_more_btn.click()
                    self.page.wait_for_timeout(random.uniform(1.5, 3.0) * 1000)
                    print("Clicked 'Show more results' button")
                except:
                    pass

            new_height = self.page.evaluate("document.body.scrollHeight")
            if new_height == prev_height and not show_more_btn:
                break
            prev_height = new_height

        

    def get_members_urls(self, group_url,search=None) :
        self.page.goto(group_url)
        members_urls = []

        try:
            self.page.wait_for_timeout(2000)
            content = self.page.content()

            join_button = self.page.query_selector('button:has(span.a11y-text:has-text("Rejoindre le groupe"))')
            if join_button:
                join_button.click()
                self.page.wait_for_timeout(1000)
                continue_button = self.page.query_selector('button:has-text("Continue"), button:has-text("Continuer")')
                if continue_button:
                    continue_button.click()

            self.page.wait_for_timeout(2000)
            self.page.goto(urljoin(group_url, "members/"))
            self.page.wait_for_timeout(2000)
            
            if search:
                self.page.fill('input[placeholder="Search members"], input[placeholder="Chercher des membres"]', search)
                self.page.keyboard.press("Enter")
                self.page.wait_for_timeout(2000)

            self.scroll_to_load_all_members()
            content = self.page.content()
            soup = BeautifulSoup(content, 'html.parser')
            member_elements = soup.select_one('ul.artdeco-list.groups-members-list__results-list')

            for member in member_elements.find_all('li'):
                profile_url_elem = member.find('a',class_='ember-view ui-conditional-link-wrapper ui-entity-action-row__link')
                profile_url = urljoin(self.base_url, profile_url_elem['href']) if profile_url_elem else None
                if profile_url:
                    members_urls.append(profile_url)

            print(f"Scraped {len(members_urls)} members urls")

            return members_urls
        except Exception as e:
            print(f"Error scraping members: {e}")
            return members_urls
        


    def get_members_infos(self,members_urls):
        members = []

        for member_url in members_urls:
            try:
                self.page.goto(member_url)
                self.page.wait_for_timeout(2000)
                name = self.page.query_selector('h1.CoYQrHnsjyAPOaMMSxtfPHyUhTgTKmYomTM.inline.t-24.v-align-middle.break-words').inner_text().strip() if self.page.query_selector('h1.CoYQrHnsjyAPOaMMSxtfPHyUhTgTKmYomTM.inline.t-24.v-align-middle.break-words') else None
                headline = self.page.query_selector('div.text-body-medium.break-words').inner_text().strip() if self.page.query_selector('div.text-body-medium.break-words') else None
                country = self.page.query_selector('span.text-body-small.inline.t-black--light.break-words').inner_text().strip() if self.page.query_selector('span.text-body-small.inline.t-black--light.break-words') else None
                members.append({
                    'name': name,
                    'headline': headline,
                    'country': country,
                    'profile_url': member_url
                })
            except Exception as e:
                print(f"Error fetching member info from {member_url}: {e}")
                continue
        return members
 


    def save_to_csv(self, members, filename):
        if not members:
            print("No members to save.")
            return

        keys = members[0].keys()
        with open(filename, 'w', newline='', encoding='utf-8') as output_file:
            dict_writer = csv.DictWriter(output_file, fieldnames=keys)
            dict_writer.writeheader()
            dict_writer.writerows(members)
        print(f"Saved {len(members)} members to {filename}")



    def save_to_json(self, members, filename: str):
        with open(filename, 'w', encoding='utf-8') as output_file:
            json.dump(members, output_file, ensure_ascii=False, indent=4)
            print(f"Saved data to {filename}")
    


    def run(self, group_url, output_urls_file,output_members_file,search=None):
        try:
            self.startBrowser()
            self.login()
            members_urls = self.get_members_urls(group_url,search)
            if members_urls:
                self.save_to_json(members_urls, output_urls_file)
                members = self.get_members_infos(members_urls)
                if members:
                    self.save_to_csv(members, output_members_file)
                    self.save_to_json(members, output_members_file.replace('.csv', '.json'))
        finally:
            self.stop_browser()