from config.config import LINKEDIN_EMAIL, LINKEDIN_PASSWORD
from Scraper.GroupsMembersScraper import GroupsMembersScraper



scraper = GroupsMembersScraper(LINKEDIN_EMAIL, LINKEDIN_PASSWORD)
scraper.startBrowser()
scraper.login()
group_url = "https://www.linkedin.com/groups/8571393/"
members = scraper.scrape_group_members(group_url)
print(members)
