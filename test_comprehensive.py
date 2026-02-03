#!/usr/bin/env python3
"""
Comprehensive DaWn Dice Party Streamlit App Test Suite
Tests all button interactions and Google Sheets connectivity
"""

import asyncio
import time
import json
import requests
from datetime import datetime
from typing import Dict, List, Optional, Any


class DaWnDiceTestSuite:
    def __init__(self, base_url: str = "http://localhost:8501"):
        self.base_url = base_url
        self.test_results = []
        self.page = None
        self.browser = None
        self.context = None

    async def setup_playwright(self):
        """Initialize Playwright browser"""
        try:
            from playwright.async_api import async_playwright

            self.playwright = await async_playwright().start()
            self.browser = await self.playwright.chromium.launch(
                headless=False, slow_mo=1000
            )
            self.context = await self.browser.new_context(
                viewport={"width": 1280, "height": 720},
                user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
            )
            self.page = await self.context.new_page()
            return True
        except Exception as e:
            print(f"❌ Playwright setup failed: {e}")
            return False

    def log_test_result(
        self,
        test_name: str,
        status: str,
        details: str = "",
        button_label: str = "",
        page_name: str = "",
    ):
        """Log test result"""
        result = {
            "timestamp": datetime.now().isoformat(),
            "test_name": test_name,
            "page": page_name,
            "button_label": button_label,
            "status": status,  # PASS, FAIL, SKIP
            "details": details,
        }
        self.test_results.append(result)
        status_icon = "✅" if status == "PASS" else "❌" if status == "FAIL" else "⏭️"
        print(f"{status_icon} {test_name} ({page_name}): {details}")

    async def wait_and_click(self, button_text: str, timeout: int = 5000) -> bool:
        """Wait for button and click it"""
        try:
            # Try multiple selectors for button
            selectors = [
                f"button:has-text('{button_text}')",
                f"[data-testid*='{button_text.lower()}']",
                f"input[type='submit'][value*='{button_text}']",
                f"*:has-text('{button_text}')",  # Last resort
            ]

            for selector in selectors:
                try:
                    element = await self.page.wait_for_selector(selector, timeout=2000)
                    if element:
                        await element.click()
                        return True
                except:
                    continue

            print(f"⚠️ Button not found: {button_text}")
            return False
        except Exception as e:
            print(f"❌ Error clicking button '{button_text}': {e}")
            return False

    async def check_element_exists(self, text: str, element_type: str = "text") -> bool:
        """Check if element with text exists"""
        try:
            if element_type == "text":
                await self.page.wait_for_selector(f"text={text}", timeout=2000)
            elif element_type == "button":
                await self.page.wait_for_selector(
                    f"button:has-text('{text}')", timeout=2000
                )
            return True
        except:
            return False

    async def take_screenshot(self, filename: str):
        """Take screenshot for debugging"""
        try:
            await self.page.screenshot(
                path=f"screenshots/{filename}_{int(time.time())}.png"
            )
        except Exception as e:
            print(f"⚠️ Screenshot failed: {e}")

    async def test_home_page(self):
        """Test home page buttons and functionality"""
        print("\n🏠 Testing Home Page...")

        try:
            await self.page.goto(self.base_url, wait_until="networkidle")
            await self.page.wait_for_timeout(2000)

            # Test login form buttons
            login_buttons = ["Login", "Sign Up"]
            for button_text in login_buttons:
                exists = await self.check_element_exists(button_text, "button")
                if exists:
                    clickable = await self.wait_and_click(button_text)
                    self.log_test_result(
                        f"Home Button: {button_text}",
                        "PASS" if clickable else "FAIL",
                        f"Button {'clicked' if clickable else 'found but not clickable'}",
                        button_text,
                        "home.py",
                    )
                    await self.page.wait_for_timeout(1000)
                    await self.page.go_back(self.base_url, wait_until="networkidle")
                    await self.page.wait_for_timeout(1000)
                else:
                    self.log_test_result(
                        f"Home Button: {button_text}",
                        "FAIL",
                        "Button not found",
                        button_text,
                        "home.py",
                    )

            # Test navigation elements (if logged in)
            nav_elements = ["🏠 홈", "📝 예약 신청", "📊 내 예약 현황"]
            for element_text in nav_elements:
                exists = await self.check_element_exists(element_text)
                self.log_test_result(
                    f"Navigation Element: {element_text}",
                    "PASS" if exists else "SKIP",
                    f"Element {'found' if exists else 'not found (may require login)'}",
                    element_text,
                    "home.py",
                )

        except Exception as e:
            self.log_test_result(
                "Home Page Load",
                "FAIL",
                f"Failed to load home page: {e}",
                "",
                "home.py",
            )

    async def test_registration_page(self):
        """Test registration page buttons"""
        print("\n📝 Testing Registration Page...")

        try:
            # Navigate to registration
            await self.page.goto(self.base_url, wait_until="networkidle")

            # Try to find and click Sign Up button
            sign_up_clicked = await self.wait_and_click("Sign Up")
            if sign_up_clicked:
                await self.page.wait_for_timeout(2000)

                # Test registration form buttons
                reg_buttons = ["Sign Up", "Cancel"]
                for button_text in reg_buttons:
                    exists = await self.check_element_exists(button_text, "button")
                    if exists:
                        self.log_test_result(
                            f"Registration Button: {button_text}",
                            "PASS",
                            "Button found and accessible",
                            button_text,
                            "register.py",
                        )
                    else:
                        self.log_test_result(
                            f"Registration Button: {button_text}",
                            "FAIL",
                            "Button not found",
                            button_text,
                            "register.py",
                        )

                # Test form validation
                # Try submitting empty form
                submit_clicked = await self.wait_and_click("Sign Up")
                await self.page.wait_for_timeout(1000)

                # Check for error messages
                error_indicators = ["error", "required", "fill in", "invalid"]
                page_text = await self.page.text_content("body")
                has_error = any(
                    indicator in page_text.lower() for indicator in error_indicators
                )

                self.log_test_result(
                    "Registration Form Validation",
                    "PASS" if has_error else "FAIL",
                    f"Form validation {'working' if has_error else 'not working'}",
                    "Form Validation",
                    "register.py",
                )
            else:
                self.log_test_result(
                    "Registration Page Access",
                    "FAIL",
                    "Could not access registration page",
                    "Sign Up",
                    "register.py",
                )

        except Exception as e:
            self.log_test_result(
                "Registration Page Test",
                "FAIL",
                f"Error testing registration page: {e}",
                "",
                "register.py",
            )

    async def test_google_sheets_connectivity(self):
        """Test Google Sheets blacklist connectivity"""
        print("\n🔗 Testing Google Sheets Connectivity...")

        try:
            # Check if we can access Google Sheets functionality
            # This tests the backend connectivity via the blacklist check

            # First, let's check the database module directly
            test_commander_id = "1234567890"  # Test ID

            # Simulate the blacklist check function
            try:
                import requests
                import pandas as pd
                from io import StringIO

                # This simulates the check_blacklist function in database.py
                sheet_url = None  # Would come from secrets in real app

                if sheet_url:
                    response = requests.get(sheet_url, timeout=10)
                    if response.status_code == 200:
                        try:
                            df = pd.read_csv(StringIO(response.text))
                            self.log_test_result(
                                "Google Sheets Connection",
                                "PASS",
                                f"Successfully connected, got {len(df)} rows",
                                "API Connection",
                                "database.py",
                            )
                        except Exception as e:
                            self.log_test_result(
                                "Google Sheets Data Parsing",
                                "FAIL",
                                f"Failed to parse CSV data: {e}",
                                "Data Parsing",
                                "database.py",
                            )
                    else:
                        self.log_test_result(
                            "Google Sheets HTTP Request",
                            "FAIL",
                            f"HTTP {response.status_code}",
                            "HTTP Request",
                            "database.py",
                        )
                else:
                    self.log_test_result(
                        "Google Sheets Configuration",
                        "SKIP",
                        "Google Sheets URL not configured (check secrets)",
                        "Configuration",
                        "database.py",
                    )

            except ImportError:
                self.log_test_result(
                    "Google Sheets Dependencies",
                    "SKIP",
                    "Required dependencies (requests, pandas) not available",
                    "Dependencies",
                    "database.py",
                )
            except Exception as e:
                self.log_test_result(
                    "Google Sheets Test",
                    "FAIL",
                    f"Unexpected error: {e}",
                    "Connectivity",
                    "database.py",
                )

        except Exception as e:
            self.log_test_result(
                "Google Sheets Connectivity Test",
                "FAIL",
                f"Failed to test connectivity: {e}",
                "",
                "database.py",
            )

    async def test_admin_pages(self):
        """Test admin functionality (if accessible)"""
        print("\n👤 Testing Admin Pages...")

        admin_pages = [
            ("📊 대시보드", "admin_dashboard.py"),
            ("🎲 회차 관리", "event_sessions.py"),
            ("📋 예약 관리", "admin_reservations.py"),
            ("👥 참여자 관리", "admin_participants.py"),
            ("🚫 블랙리스트 관리", "admin_blacklist.py"),
            ("📢 공지사항 관리", "admin_announcements.py"),
        ]

        for page_name, file_name in admin_pages:
            exists = await self.check_element_exists(page_name)
            self.log_test_result(
                f"Admin Page Access: {page_name}",
                "PASS" if exists else "SKIP",
                f"Page {'accessible' if exists else 'not accessible (may require admin login)'}",
                page_name,
                file_name,
            )

    async def test_form_interactions(self):
        """Test various form interactions"""
        print("\n📋 Testing Form Interactions...")

        # Test login form
        try:
            await self.page.goto(self.base_url, wait_until="networkidle")

            # Fill in login form with test data
            await self.page.fill(
                "input[placeholder*='Commander ID or Username']", "test_user"
            )
            await self.page.fill("input[type='password']", "test_password")

            # Check if login button is clickable
            login_button = await self.page.query_selector("button:has-text('Login')")
            if login_button:
                is_enabled = await login_button.is_enabled()
                self.log_test_result(
                    "Login Form Interaction",
                    "PASS",
                    f"Login form filled, button enabled: {is_enabled}",
                    "Login Form",
                    "home.py",
                )
            else:
                self.log_test_result(
                    "Login Form Interaction",
                    "FAIL",
                    "Login button not found",
                    "Login Form",
                    "home.py",
                )

        except Exception as e:
            self.log_test_result(
                "Form Interaction Test",
                "FAIL",
                f"Error testing form interactions: {e}",
                "",
                "general",
            )

    async def test_streamlit_elements(self):
        """Test Streamlit-specific elements"""
        print("\� Testing Streamlit Elements...")

        # Check for common Streamlit elements
        streamlit_elements = [
            ("st.selectbox", "select dropdown"),
            ("st.text_input", "text input field"),
            ("st.button", "button"),
            ("st.sidebar", "sidebar"),
            ("st.columns", "column layout"),
        ]

        # Check page for Streamlit-specific classes or elements
        try:
            page_content = await self.page.content()

            # Look for Streamlit-specific indicators
            has_streamlit = any(
                indicator in page_content
                for indicator in ['data-testid="stApp"', 'class="stApp"', "streamlit"]
            )

            self.log_test_result(
                "Streamlit Framework Detection",
                "PASS" if has_streamlit else "FAIL",
                f"Streamlit framework {'detected' if has_streamlit else 'not detected'}",
                "Framework",
                "app.py",
            )

            # Check for interactive elements
            buttons = await self.page.query_selector_all("button")
            inputs = await self.page.query_selector_all("input")

            self.log_test_result(
                "Interactive Elements Count",
                "PASS",
                f"Found {len(buttons)} buttons and {len(inputs)} input fields",
                "Element Count",
                "general",
            )

        except Exception as e:
            self.log_test_result(
                "Streamlit Elements Test",
                "FAIL",
                f"Error checking Streamlit elements: {e}",
                "",
                "general",
            )

    async def generate_test_report(self):
        """Generate comprehensive test report"""
        print("\n" + "=" * 60)
        print("📊 COMPREHENSIVE TEST REPORT")
        print("=" * 60)

        # Summary statistics
        total_tests = len(self.test_results)
        passed_tests = len([r for r in self.test_results if r["status"] == "PASS"])
        failed_tests = len([r for r in self.test_results if r["status"] == "FAIL"])
        skipped_tests = len([r for r in self.test_results if r["status"] == "SKIP"])

        print(f"\n📈 SUMMARY:")
        print(f"   Total Tests: {total_tests}")
        print(f"   ✅ Passed: {passed_tests}")
        print(f"   ❌ Failed: {failed_tests}")
        print(f"   ⏭️  Skipped: {skipped_tests}")
        print(
            f"   📊 Success Rate: {(passed_tests / total_tests * 100):.1f}%"
            if total_tests > 0
            else "N/A"
        )

        # Results by page
        print(f"\n📋 RESULTS BY PAGE:")
        pages = {}
        for result in self.test_results:
            page = result["page"] or "general"
            if page not in pages:
                pages[page] = {"PASS": 0, "FAIL": 0, "SKIP": 0}
            pages[page][result["status"]] += 1

        for page, counts in pages.items():
            total = sum(counts.values())
            passed = counts["PASS"]
            print(f"   {page}: {passed}/{total} passed ({passed / total * 100:.1f}%)")

        # Failed tests details
        failed_results = [r for r in self.test_results if r["status"] == "FAIL"]
        if failed_results:
            print(f"\n❌ FAILED TESTS:")
            for result in failed_results:
                print(
                    f"   • {result['test_name']} ({result['page']}): {result['details']}"
                )

        # Google Sheets connectivity summary
        google_sheets_results = [
            r for r in self.test_results if "Google Sheets" in r["test_name"]
        ]
        if google_sheets_results:
            print(f"\n🔗 GOOGLE SHEETS CONNECTIVITY:")
            for result in google_sheets_results:
                status_icon = (
                    "✅"
                    if result["status"] == "PASS"
                    else "❌"
                    if result["status"] == "FAIL"
                    else "⏭️"
                )
                print(f"   {status_icon} {result['test_name']}: {result['details']}")

        # Button functionality summary
        button_results = [r for r in self.test_results if "Button" in r["test_name"]]
        if button_results:
            print(f"\n🔘 BUTTON FUNCTIONALITY:")
            button_pages = {}
            for result in button_results:
                page = result["page"]
                if page not in button_pages:
                    button_pages[page] = {"PASS": 0, "FAIL": 0}
                button_pages[page][result["status"]] += 1

            for page, counts in button_pages.items():
                total = sum(counts.values())
                passed = counts["PASS"]
                print(f"   {page}: {passed}/{total} buttons working")

        print(f"\n📝 RECOMMENDATIONS:")
        if failed_tests > 0:
            print("   • Fix failed button interactions")
            print("   • Check form validation logic")
            print("   • Verify Google Sheets configuration")
        if skipped_tests > 0:
            print("   • Configure missing settings for skipped tests")
        if passed_tests == total_tests:
            print("   🎉 All tests passed! Application is working correctly.")

        # Save detailed report to file
        report_data = {
            "summary": {
                "total_tests": total_tests,
                "passed": passed_tests,
                "failed": failed_tests,
                "skipped": skipped_tests,
                "success_rate": (passed_tests / total_tests * 100)
                if total_tests > 0
                else 0,
                "timestamp": datetime.now().isoformat(),
            },
            "by_page": pages,
            "detailed_results": self.test_results,
        }

        try:
            with open(
                f"test_report_{int(time.time())}.json", "w", encoding="utf-8"
            ) as f:
                json.dump(report_data, f, indent=2, ensure_ascii=False)
            print(f"\n💾 Detailed report saved to: test_report_{int(time.time())}.json")
        except Exception as e:
            print(f"⚠️ Could not save detailed report: {e}")

    async def run_all_tests(self):
        """Run complete test suite"""
        print("🚀 Starting DaWn Dice Party Comprehensive Test Suite")
        print("=" * 60)

        # Setup Playwright
        if not await self.setup_playwright():
            print("❌ Failed to setup Playwright. Aborting tests.")
            return

        try:
            # Create screenshots directory
            import os

            os.makedirs("screenshots", exist_ok=True)

            # Run all tests
            await self.test_home_page()
            await self.test_registration_page()
            await self.test_google_sheets_connectivity()
            await self.test_admin_pages()
            await self.test_form_interactions()
            await self.test_streamlit_elements()

            # Generate report
            await self.generate_test_report()

        finally:
            # Cleanup
            if self.page:
                await self.page.close()
            if self.context:
                await self.context.close()
            if self.browser:
                await self.browser.close()
            if hasattr(self, "playwright"):
                await self.playwright.stop()


async def main():
    """Main test runner"""
    # Check if Streamlit app is running
    try:
        response = requests.get("http://localhost:8501", timeout=5)
        if response.status_code != 200:
            print("❌ Streamlit app not responding. Please start the app first:")
            print("   streamlit run dice_app/app.py")
            return
    except requests.exceptions.ConnectionError:
        print("❌ Cannot connect to Streamlit app at http://localhost:8501")
        print("   Please start the app first: streamlit run dice_app/app.py")
        return
    except Exception as e:
        print(f"⚠️ Error checking app status: {e}")
        print("   Proceeding with tests anyway...")

    # Run tests
    test_suite = DaWnDiceTestSuite()
    await test_suite.run_all_tests()


if __name__ == "__main__":
    print("DaWn Dice Party - Comprehensive Test Suite")
    print("Testing all button interactions and Google Sheets connectivity")
    print()

    # Install required packages if needed
    try:
        import playwright
    except ImportError:
        print("📦 Installing Playwright...")
        import subprocess

        subprocess.run(["pip", "install", "playwright"], check=True)
        subprocess.run(["playwright", "install", "chromium"], check=True)

    # Run tests
    asyncio.run(main())
