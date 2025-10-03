import time
import random
from playwright.sync_api import Page
from typing import Optional, List, Tuple
import cv2
import numpy as np
from PIL import Image
import io
import base64


class CaptchaSolver:
    def __init__(self, page: Page):
        self.page = page
        
    def detect_captcha(self) -> bool:
        """Detect if captcha is present on the page"""
        captcha_selectors = [
            'iframe[src*="captcha"]',
            'div[id*="captcha"]',
            'div[class*="captcha"]',
            'div[class*="challenge"]',
            'div[class*="puzzle"]',
            'canvas[id*="captcha"]',
            'img[src*="captcha"]',
            '[data-test-id*="captcha"]',
            '.recaptcha-checkbox',
            '#recaptcha',
            'iframe[title*="reCAPTCHA"]',
            'div[class*="hcaptcha"]',
            'iframe[src*="hcaptcha"]'
        ]
        
        for selector in captcha_selectors:
            if self.page.query_selector(selector):
                print(f"Captcha detected with selector: {selector}")
                return True
        return False
    
    def solve_recaptcha_v2(self) -> bool:
        """Attempt to solve reCAPTCHA v2"""
        try:
            # Wait for reCAPTCHA iframe to load
            recaptcha_frame = self.page.wait_for_selector('iframe[src*="recaptcha"]', timeout=5000)
            if not recaptcha_frame:
                return False
            
            # Click the checkbox
            frame = recaptcha_frame.content_frame()
            checkbox = frame.wait_for_selector('.recaptcha-checkbox-border', timeout=5000)
            if checkbox:
                checkbox.click()
                self.page.wait_for_timeout(2000)
                
                # Check if challenge appears
                challenge_frame = self.page.query_selector('iframe[src*="bframe"]')
                if challenge_frame:
                    return self.solve_image_challenge(challenge_frame)
                
                return True
        except Exception as e:
            print(f"Error solving reCAPTCHA v2: {e}")
            return False
    
    def solve_image_challenge(self, challenge_frame) -> bool:
        """Solve image-based captcha challenges"""
        try:
            frame = challenge_frame.content_frame()
            
            # Wait for challenge to load
            self.page.wait_for_timeout(3000)
            
            # Look for challenge instructions
            instruction = frame.query_selector('.rc-imageselect-desc-wrapper')
            if instruction:
                instruction_text = instruction.inner_text()
                print(f"Challenge instruction: {instruction_text}")
                
                # Get challenge images
                images = frame.query_selector_all('.rc-image-tile-wrapper img')
                if images:
                    return self.solve_visual_challenge(frame, images, instruction_text)
            
            return False
        except Exception as e:
            print(f"Error solving image challenge: {e}")
            return False
    
    def solve_visual_challenge(self, frame, images: List, instruction: str) -> bool:
        """Solve visual challenges by analyzing images"""
        try:
            # Simple heuristic approach - click random images for now
            # In a real implementation, you'd use computer vision or AI
            
            target_objects = self.extract_target_from_instruction(instruction)
            if not target_objects:
                return False
            
            # Analyze each image and click relevant ones
            clicked_count = 0
            for i, img in enumerate(images):
                if self.should_click_image(img, target_objects):
                    img.click()
                    clicked_count += 1
                    self.page.wait_for_timeout(random.randint(500, 1000))
            
            # Submit the challenge
            verify_button = frame.query_selector('#recaptcha-verify-button')
            if verify_button:
                verify_button.click()
                self.page.wait_for_timeout(3000)
                return True
                
            return False
        except Exception as e:
            print(f"Error solving visual challenge: {e}")
            return False
    
    def extract_target_from_instruction(self, instruction: str) -> List[str]:
        """Extract target objects from challenge instruction"""
        instruction = instruction.lower()
        common_targets = [
            'traffic lights', 'cars', 'bicycles', 'crosswalks', 'buses',
            'motorcycles', 'trucks', 'fire hydrants', 'parking meters',
            'boats', 'bridges', 'mountains', 'trees', 'flowers'
        ]
        
        targets = []
        for target in common_targets:
            if target in instruction:
                targets.append(target)
        
        return targets
    
    def should_click_image(self, img_element, targets: List[str]) -> bool:
        """Determine if an image should be clicked based on targets"""
        # This is a simplified approach
        # In reality, you'd use computer vision to analyze the image content
        
        # Random selection with some intelligence
        if 'traffic' in ' '.join(targets):
            return random.random() < 0.3  # 30% chance for traffic-related
        elif 'vehicle' in ' '.join(targets) or 'car' in ' '.join(targets):
            return random.random() < 0.25  # 25% chance for vehicles
        else:
            return random.random() < 0.2   # 20% chance for other objects
    
    def solve_puzzle_captcha(self) -> bool:
        """Solve sliding puzzle captchas"""
        try:
            # Look for puzzle elements
            puzzle_container = self.page.query_selector('[class*="puzzle"], [id*="puzzle"]')
            if not puzzle_container:
                return False
            
            # Look for slider element
            slider = self.page.query_selector('div[class*="slider"], input[type="range"]')
            if slider:
                return self.solve_slider_puzzle(slider)
            
            # Look for drag and drop puzzle
            drag_element = self.page.query_selector('[class*="drag"], [draggable="true"]')
            if drag_element:
                return self.solve_drag_puzzle(drag_element)
            
            return False
        except Exception as e:
            print(f"Error solving puzzle captcha: {e}")
            return False
    
    def solve_slider_puzzle(self, slider_element) -> bool:
        """Solve slider-based puzzle captcha"""
        try:
            # Get slider bounds
            slider_box = slider_element.bounding_box()
            if not slider_box:
                return False
            
            # Simulate human-like sliding motion
            start_x = slider_box['x'] + 10
            start_y = slider_box['y'] + slider_box['height'] / 2
            
            # Calculate end position (usually around 80-90% of slider width)
            end_x = slider_box['x'] + slider_box['width'] * random.uniform(0.8, 0.95)
            
            # Perform human-like drag with multiple steps
            self.page.mouse.move(start_x, start_y)
            self.page.mouse.down()
            
            # Move in small increments to simulate human behavior
            steps = random.randint(15, 25)
            for i in range(steps):
                progress = i / steps
                current_x = start_x + (end_x - start_x) * progress
                # Add slight randomness to make it more human-like
                jitter = random.uniform(-2, 2)
                self.page.mouse.move(current_x + jitter, start_y)
                self.page.wait_for_timeout(random.randint(20, 50))
            
            self.page.mouse.up()
            self.page.wait_for_timeout(2000)
            
            return True
        except Exception as e:
            print(f"Error solving slider puzzle: {e}")
            return False
    
    def solve_drag_puzzle(self, drag_element) -> bool:
        """Solve drag and drop puzzle captcha"""
        try:
            # Find the target drop zone
            drop_zone = self.page.query_selector('[class*="drop"], [class*="target"]')
            if not drop_zone:
                return False
            
            # Get element positions
            drag_box = drag_element.bounding_box()
            drop_box = drop_zone.bounding_box()
            
            if not drag_box or not drop_box:
                return False
            
            # Perform drag and drop
            drag_center_x = drag_box['x'] + drag_box['width'] / 2
            drag_center_y = drag_box['y'] + drag_box['height'] / 2
            drop_center_x = drop_box['x'] + drop_box['width'] / 2
            drop_center_y = drop_box['y'] + drop_box['height'] / 2
            
            self.page.mouse.move(drag_center_x, drag_center_y)
            self.page.mouse.down()
            self.page.wait_for_timeout(random.randint(100, 300))
            self.page.mouse.move(drop_center_x, drop_center_y)
            self.page.mouse.up()
            self.page.wait_for_timeout(2000)
            
            return True
        except Exception as e:
            print(f"Error solving drag puzzle: {e}")
            return False
    
    def bypass_captcha_with_delays(self) -> bool:
        """Try to bypass captcha by waiting and refreshing"""
        try:
            print("Attempting to bypass captcha with delays...")
            
            # Wait for a random period
            wait_time = random.randint(10, 30)
            print(f"Waiting {wait_time} seconds...")
            self.page.wait_for_timeout(wait_time * 1000)
            
            # Try refreshing the page
            self.page.reload()
            self.page.wait_for_timeout(5000)
            
            # Check if captcha is still present
            if not self.detect_captcha():
                print("Captcha bypassed successfully!")
                return True
            
            # Try going back and forward
            self.page.go_back()
            self.page.wait_for_timeout(3000)
            self.page.go_forward()
            self.page.wait_for_timeout(5000)
            
            return not self.detect_captcha()
        except Exception as e:
            print(f"Error bypassing captcha: {e}")
            return False
    
    def solve_captcha(self) -> bool:
        """Main method to solve any detected captcha"""
        if not self.detect_captcha():
            return True
        
        print("Captcha detected! Attempting to solve...")
        
        # Try different solving strategies
        strategies = [
            self.solve_recaptcha_v2,
            self.solve_puzzle_captcha,
            self.bypass_captcha_with_delays
        ]
        
        for strategy in strategies:
            try:
                print(f"Trying strategy: {strategy.__name__}")
                if strategy():
                    print(f"Captcha solved using {strategy.__name__}")
                    return True
                self.page.wait_for_timeout(2000)
            except Exception as e:
                print(f"Strategy {strategy.__name__} failed: {e}")
                continue
        
        print("All captcha solving strategies failed")
        return False
    
    def wait_for_manual_solve(self, timeout: int = 60) -> bool:
        """Wait for user to manually solve captcha"""
        print(f"Please solve the captcha manually. Waiting {timeout} seconds...")
        
        start_time = time.time()
        while time.time() - start_time < timeout:
            if not self.detect_captcha():
                print("Captcha solved manually!")
                return True
            self.page.wait_for_timeout(1000)
        
        print("Timeout waiting for manual captcha solution")
        return False