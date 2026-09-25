"""
Telebot-interacting module.
Initiates bot, parses channel posts, downloads images, passes processed
posts to post them in VK, sends feedback to alert chat in case of error
during post duplication, and replies to private advertisement requests.
"""

import logging
import telebot
from posts_processor import ProcessedPost, build_caption
from media_buffer import MediaGroupBuffer
from pathlib import Path
import shutil
from vk_poster import VkPoster
from config import Config
import time

logger = logging.getLogger(__name__)

def create_bot(settings:Config) -> telebot.TeleBot:
    """
    Initialize and configure Telebot instance.
    Registers handlers:
        message handler for ads info
        channel post handler for parsing
    """
    bot = telebot.TeleBot(
        settings.TG_API_TOKEN,
        parse_mode='HTML',
    )

    @bot.channel_post_handler(content_types=['photo'])
    def handle_channel_post(message:telebot.types.Message) -> None:
        """
        Handle incoming channel posts. Direct album items to media
        buffer, but process single image posts immediately.
        """
        if message.media_group_id:
            media_buffer.add(message)
            return

        logger.info(f'Detected telegram post!')

        prepare_post([message])

    def _error_message(message_id:int) -> None:
        """
        Send an error alert to the specified Telegram supergroup topic
        when post replication fails.
        """
        bot.send_message(
            chat_id=settings.TG_ALERT_SUPERGROUP_ID,
            text=f'Произошла ошибка при копировании поста '
                 f'https://t.me/catdead_tester_channel/{message_id} '
                 f'в ВК. <b>Повторите вручную.</b>',
            message_thread_id=settings.TG_ALERT_TOPIC_ID,
        )


    def _download_image(
            image:telebot.types.PhotoSize,
            temp_img_dir:Path,
            n:int=None
    ) -> Path:
        """
        Download a Telegram photo attachment and save it to the
        temporary image directory.
        """
        file_info = bot.get_file(image.file_id)
        downloaded_file = bot.download_file(file_info.file_path)

        filename = 'image' if n is None else f'image_{n}'
        image_path = temp_img_dir / f'{filename}.jpg'

        with image_path.open('wb') as f:
            f.write(downloaded_file)

        logger.info(f'\tDownloaded Telegram image to {image_path}')

        return image_path

    def _clear_temp_img_dir() -> None:
        """
        Clear and recreate temporary image directory to purge stale
        files.
        """
        temp_img_dir = Path(settings.TEMP_IMG_DIR)

        if temp_img_dir.exists():
            shutil.rmtree(temp_img_dir)

        temp_img_dir.mkdir(parents=True, exist_ok=True)

    def _find_caption_message(
            messages:list[telebot.types.Message]
    ) -> telebot.types.Message:
        """
        Find and return the message containing the caption from a list
        of album messages.
        """
        for message in messages:
            if message.caption:
                return message

        raise ValueError('\tThe Telegram post/album has no caption.')

    def prepare_post(messages:list[telebot.types.Message]) -> None:
        """
        Download album photos, format the post caption, and trigger VK
        publication.
        """
        try:
            _clear_temp_img_dir()
            messages.sort(key=lambda message: message.message_id) # redundancy for self-testing
            caption_message = _find_caption_message(messages)

            image_paths = []
            logger.info('\tPreparing images...')
            for number, message in enumerate(messages, start=1):
                image_path = _download_image(
                    image=message.photo[-1],
                    temp_img_dir=settings.TEMP_IMG_DIR,
                    n=number
                )
                image_paths.append(image_path)

            logger.info('\tPreparing caption...')
            caption = build_caption(
                caption=caption_message.caption,
                caption_entities= caption_message.caption_entities,
                settings=settings
            )

            processed_post = ProcessedPost(
                caption=caption,
                image_paths=image_paths,
                source_post_id=caption_message.message_id
            )

            logger.info(
                '\tPrepared Telegram post with %s image(s)',
                len(processed_post.image_paths),
            )

            logger.info("\t========== POST READY ==========")
            logger.info("\tCaption:\n%s", processed_post.caption)
            logger.info("\tImage paths: %s", processed_post.image_paths)
            logger.info("\t================================")

            vk_poster = VkPoster(settings)
            vk_poster.publish(processed_post)

            logger.info('\tPosted!')

        except Exception as e:
            logging.error(e)
            _error_message(messages[0].message_id)

    @bot.message_handler(chat_types=['private'], commands=['start', 'help', 'ads'])
    def send_ads_info(message:telebot.types.Message) -> None:
        """
        Send advertising availability info to users interacting via
        private chat.
        """
        for ad_message in settings.ADS_MESSAGES[settings.ADS_ACTIVE]:
            bot.send_message(
                chat_id=message.from_user.id,
                text=ad_message,
            )
            time.sleep(2)
        if settings.ADS_ACTIVE:
            bot.send_photo(
                chat_id=message.from_user.id,
                caption=settings.ADS_PRICELIST['text'],
                photo=open(settings.ADS_PRICELIST['image'], 'rb')
            )

    media_buffer = MediaGroupBuffer(
        timeout_seconds=settings.MEDIA_GROUP_TIMEOUT,
        on_album_ready=prepare_post,
    )

    return bot