"""
google_form_selenium_bulk_v2.py
- Uses Selenium + webdriver-manager
- Handles "Other" options by filling 'nan'
- Works with required fields
"""

from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.service import Service
from webdriver_manager.chrome import ChromeDriverManager
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
import time, random
from faker import Faker

fake = Faker()

# CONFIG
FORM_URL = "https://docs.google.com/forms/d/e/1FAIpQLSfUZ-extvDgIEJFP2tYAIM9Qc4BX14CH3nCnS3TSTdSjbBteA/viewform"
NUM_RESPONSES = 20
DELAY = 0.5
HEADLESS = False   # Run without browser window if True

# Setup Chrome
opts = Options()
if HEADLESS:
    opts.add_argument("--headless=new")
opts.add_argument("--no-sandbox")
opts.add_argument("--disable-dev-shm-usage")

driver = webdriver.Chrome(service=Service(ChromeDriverManager().install()), options=opts)
driver.maximize_window()


# ---------- HELPERS ----------

def click_option(option_text, question_xpath=""):
    """
    Click an option. If 'Other', also fill sibling textbox.
    Optionally scoped by a question container (question_xpath).
    """
    try:
        # scope by question if provided
        base = driver if not question_xpath else driver.find_element(By.XPATH, question_xpath)

        # Try exact aria-label
        try:
            el = base.find_element(By.XPATH, f".//*[@aria-label='{option_text}']")
        except:
            # fallback by visible text
            el = base.find_element(By.XPATH, f".//span[normalize-space(text())='{option_text}']")

        driver.execute_script("arguments[0].scrollIntoView(true);", el)
        time.sleep(0.2)
        el.click()

        # Handle Other
        if option_text.lower() == "other":
            try:
                parent_div = el.find_element(By.XPATH, "./ancestor::div[@role='radiogroup'] | ./ancestor::div[@role='listitem']")
                other_input = parent_div.find_element(By.XPATH, ".//input[@type='text']")
                other_input.clear()
                other_input.send_keys("nan")
                time.sleep(0.2)
            except Exception:
                print("⚠️ Could not find textbox for 'Other' in this question.")

        return True
    except Exception as e:
        # print(f"❌ Could not find option: {option_text} -> {e}")
        return False


def fill_textbox_by_partial_label(partial_label, value):
    """Fill textbox/textarea by partial aria-label text"""
    xps = [
        f"//input[contains(@aria-label, '{partial_label}')]",
        f"//textarea[contains(@aria-label, '{partial_label}')]"
    ]
    for xp in xps:
        try:
            el = driver.find_element(By.XPATH, xp)
            el.clear()
            el.send_keys(value)
            return True
        except:
            continue
    return False


def submit_form():
    """Click Submit button if available"""
    try:
        btn = WebDriverWait(driver, 5).until(
            EC.element_to_be_clickable((By.XPATH, "//div[@role='button']//span[text()='Submit']"))
        )
        parent_btn = btn.find_element(By.XPATH, "./ancestor::div[@role='button']")
        parent_btn.click()
        return True
    except Exception as e:
        print("❌ Submit button not found:", e)
        return False


# ---------- OPTION POOLS ----------
age_opts = ["18-20", "21-23", "23-25", "Other"]
gender_opts = ["Male", "Female", "Other"]
class_opts = ["FY", "SY", "TY", "EY", "Other"]
ai_yesno = ["YES", "NO"]
which_ai_opts = ["ChatGPT", "Gemini", "Copilot", "Other"]
purpose_opts = ["Assignments", "Projects", "Study", "Fun", "Other"]
freq_opts = ["Daily", "Weekly", "Occasionally", "Other"]
improved_opts = ["Yes", "No", "Maybe"]
tech_excites = ["AI", "Blockchain", "AR/VR", "Robotics", "Cybersecurity", "Other"]
prefer_learning = ["AI-assisted", "Traditional", "Both"]
career_opts = ["Higher studies", "Job", "Startup", "Research", "Other"]


# ---------- MAIN LOOP ----------
for i in range(NUM_RESPONSES):
    driver.get(FORM_URL)
    time.sleep(1.0)

    try:
        # Name field
        fill_textbox_by_partial_label("Name", fake.name())

        # MCQs
        click_option(random.choice(age_opts))
        click_option(random.choice(gender_opts))
        click_option(random.choice(class_opts))
        click_option(random.choice(ai_yesno))
        click_option(random.choice(which_ai_opts))
        click_option(random.choice(purpose_opts))
        click_option(random.choice(freq_opts))
        click_option(random.choice(improved_opts))
        click_option(random.choice(tech_excites))
        click_option(random.choice(prefer_learning))
        click_option(random.choice(career_opts))

        # optional "Other:" text field (if present outside MCQs)
        fill_textbox_by_partial_label("Other:", "nan")

    except Exception as e:
        print("⚠️ Non-fatal fill error:", e)

    time.sleep(0.4)
    if submit_form():
        print(f"✅ Submitted {i+1}/{NUM_RESPONSES}")
    else:
        print(f"❌ Failed to submit form at iteration {i+1}")

    time.sleep(DELAY)

driver.quit()
print("🎉 Done submitting all responses.")
