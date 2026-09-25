from playwright.sync_api import sync_playwright
from src.config import settings

profile_dir = settings.APP_ROOT / 'vk_profile'
state_file = settings.PLAYWRIGHT_VK_STATE

with sync_playwright() as p:
    context = p.chromium.launch_persistent_context(
        user_data_dir=str(profile_dir),
        headless=False,
    )

    try:
        page = context.pages[0] if context.pages else context.new_page()
        page.goto('https://m.vk.ru', wait_until='domcontentloaded')

        input('Log in to VK, then press Enter to save the session...')

        context.storage_state(
            path=str(state_file),
            indexed_db=True,
        )
    finally:
        context.close()