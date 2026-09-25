"""
Thread-safe buffer module for grouping Telegram media album messages
using debounce timers.
"""

import logging
from threading import Lock, Timer
from collections.abc import Callable
import telebot

logger = logging.getLogger(__name__)

class MediaGroupBuffer:
    def __init__(
            self,
            timeout_seconds: int,
            on_album_ready: Callable[[list], None],
    ):
        """
        Initialize the media buffer with a collection timeout and
        callback for completed albums.
        """
        self.timeout_seconds = timeout_seconds
        self.on_album_ready = on_album_ready

        self._lock = Lock()
        self._albums: dict[str, list] = {}
        self._timers: dict[str, Timer] = {}
        self._generations: dict[str, int] = {}

    def add(self, message:telebot.types.Message) -> None:
        """
        Add a media group message to the buffer and restart the debounce
        timer for its album.
        """
        media_group_id = message.media_group_id

        if media_group_id is None:
            raise ValueError('\t\tMediaGroupBuffer received a '
                             'non-album message.')

        with self._lock:

            if media_group_id not in self._albums:
                self._albums[media_group_id] = []
                self._generations[media_group_id] = 0

            self._albums[media_group_id].append(message)

            old_timer = self._timers.get(media_group_id)
            if old_timer is not None:
                old_timer.cancel()

            self._generations[media_group_id] += 1
            generation = self._generations[media_group_id]

            timer = Timer(
                self.timeout_seconds,
                self._flush,
                args=(media_group_id, generation),
            )
            timer.daemon = True
            self._timers[media_group_id] = timer
            timer.start()

            logger.info(
                '\t\tBuffered message %s in media group %s',
                message.message_id,
                media_group_id,
            )

    def _flush(self, media_group_id:str, expected_generation:int) -> None:
        """
        Flush buffered messages for an album if the timer generation
        matches and trigger the processing callback.
        """
        with self._lock:
            current_generation = self._generations.get(media_group_id)
            if current_generation != expected_generation:
                return

            messages = self._albums.pop(media_group_id, [])
            self._timers.pop(media_group_id, None)
            self._generations.pop(media_group_id, None)

        if not messages:
            return

        messages.sort(key=lambda message: message.message_id)

        logger.info(
            '\t\tMedia group %s is complete: %s image(s)',
            media_group_id,
            len(messages),
        )

        try:
            self.on_album_ready(messages)
        except Exception:
            logger.exception(
                '\t\tFailed to process media group %s',
                media_group_id
            )