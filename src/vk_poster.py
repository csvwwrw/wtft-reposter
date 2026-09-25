"""
Browser automation module using Playwright to publish formatted posts
and photos to VK.
"""

import logging
import time
from pathlib import Path
from playwright.sync_api import Page, sync_playwright, expect, Locator
from config import Config
from posts_processor import ProcessedPost

logger = logging.getLogger(__name__)


class VkPoster:
    ATTACHMENT_REMOVE_SELECTOR = (
        '[data-testid="posting_attachment_photo_item_remove"], '
        '[data-testid="photooverlay-remove-button"]'
    )
    TEXT_INPUT = 'posting_start_screen_post_input'
    FILE_INPUT = 'posting_attachments_download_from_device'
    GRID_TOGGLE_BUTTON = 'posting_base_screen_view_button'
    NEXT_BUTTON = 'posting_start_screen_next_button'
    STORY_SWITCH = 'posting_settings_repost_to_story_switch'
    SUBMIT_BUTTON = 'posting_submit_button'

    def __init__(self, settings:Config) -> None:
        """
        Initialize the VK poster with application settings and browser
        profile paths.
        """
        self.settings = settings

    def publish(self, post:ProcessedPost) -> None:
        """
        Orchestrate the end-to-end publishing flow of text and images to
        a VK group using Playwright.
        """
        logger.info(
            'Starting VK publishing for Telegram post %s',
            post.source_post_id,
        )

        storage_state_path = (
                self.settings.PLAYWRIGHT_VK_STATE
        )

        if not storage_state_path.exists():
            raise FileNotFoundError(
                f'VK authentication state was not found: {storage_state_path}'
            )

        with sync_playwright() as p:
            browser = p.chromium.launch(
                headless=True,
            )

            context = browser.new_context(
                storage_state=str(storage_state_path),
            )

            try:
                page = context.new_page()

                self._open_editor(page)
                self._clear_draft_attachments(page)

                if post.caption:
                    self._fill_caption(page, post.caption)

                if post.image_paths:
                    self._upload_images(page, post.image_paths)
                    if len(post.image_paths) > 1:
                        self._switch_to_grid(page)

                self._go_to_settings(page)
                self._disable_story_repost(page)
                self._submit_post(page)

                logger.info('\tPost %s successfully published',
                            post.source_post_id)
            finally:
                context.close()
                browser.close()

    def _get_remove_locator(self, page:Page) -> Locator:
        """
        Return locator targeting image removal buttons in the VK post
        composer.
        """
        return page.locator(self.ATTACHMENT_REMOVE_SELECTOR)

    def _open_editor(self, page:Page) -> None:
        """
        Navigate to the VK mobile post composer page and wait until the interface is ready.
        """
        url = f'https://m.vk.ru/new_post/-{self.settings.VK_GROUP_ID}'
        page.goto(url, wait_until='domcontentloaded')

        upload_button = page.get_by_text('Загрузить с устройства').first
        remove_button = self._get_remove_locator(page).first

        # Ожидаем готовности экрана (чистая форма или форма с черновиком)
        combined = upload_button.or_(remove_button)
        combined.wait_for(state='visible', timeout=60_000)

    def _clear_draft_attachments(self, page:Page) -> None:
        """
        Remove any pre-existing attachment drafts from the composer
        interface.
        """
        remove_locator = self._get_remove_locator(page)
        count = remove_locator.count()

        if count == 0:
            return

        logger.debug('\tRemoving %d stale attachments from draft', count)
        for index in reversed(range(count)):
            button = remove_locator.nth(index)
            expect(button).to_be_visible(timeout=5_000)
            button.click()

        expect(remove_locator).to_have_count(0, timeout=10_000)

    def _fill_caption(self, page:Page, caption:str) -> None:
        """
        Fill the post text input field with the formatted caption.
        """
        page.get_by_test_id(self.TEXT_INPUT).fill(caption)

    def _upload_images(
            self,
            page:Page,
            image_paths: list[Path | str]
    ) -> None:
        """
        Upload local images to the hidden file input and await complete
        upload confirmation.
        """
        page.get_by_test_id(self.FILE_INPUT).set_input_files(image_paths)

        expect(self._get_remove_locator(page)).to_have_count(
            len(image_paths),
            timeout=30_000,
        )

    def _switch_to_grid(self, page:Page) -> None:
        """
        Switch image layout display mode from carousel to grid.
        """
        carousel_switch = page.get_by_test_id(self.GRID_TOGGLE_BUTTON)
        grid_button = page.get_by_test_id(
            'dropdownactionsheet-content').get_by_role(
            'button', name='Сетка'
        )

        start = time.time()
        while time.time() - start < 10:
            try:
                carousel_switch.hover(timeout=1_000)
                expect(grid_button).to_be_visible(timeout=1_000)
                break
            except Exception:
                time.sleep(0.2)

        expect(grid_button).to_be_visible(timeout=5_000)
        grid_button.click()

    def _go_to_settings(self, page:Page) -> None:
        """
        Advance from the composer editor screen to the post settings
        screen.
        """
        next_button = page.get_by_test_id(self.NEXT_BUTTON)
        expect(next_button).to_be_visible(timeout=5_000)
        next_button.click()

    def _disable_story_repost(self, page:Page) -> None:
        """
        Ensure the option to automatically repost to VK story is turned
        off.
        """
        switch_input = page.get_by_test_id(self.STORY_SWITCH)
        expect(switch_input).to_be_visible(timeout=2_000)

        if switch_input.is_checked():
            fake_toggle = switch_input.locator('..').locator(
                'span.vkuiSwitch__inputFake')
            fake_toggle.click()

    def _submit_post(self, page:Page) -> None:
        """
        Click the submit button to finalize publication and wait for network requests to complete.
        """
        submit_button = page.get_by_test_id(self.SUBMIT_BUTTON)
        expect(submit_button).to_be_visible(timeout=2_000)
        submit_button.click()

        page.wait_for_timeout(5_000)