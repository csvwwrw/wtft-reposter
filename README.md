# Telegram-to-VK Reposting Bot

A Python bot that watches a Telegram channel and republishes photo posts to a VK community. It formats captions for VK, shortens source links with TinyURL, and uses Playwright to publish through VK's mobile web interface. The bot also answers private advertising enquiries and sends an alert to a Telegram supergroup topic if reposting fails.

Context: project created and maintained to synchronise posts for _wtf_tumblr_ [TG channel](https://t.me/wtf_tumblr) and [VK group](https://vk.ru/wtf_tumblr).

## What it does

- Reposts single-photo posts and photo albums from a Telegram channel to a VK group. It ignores any other post types (e.g. text, video).
- Buffers album items briefly so they can be published as one post.
- Converts the first line of a caption into VK community hashtags and includes a shortened source link.
- Sends `/start`, `/help`, and `/ads` replies in private chat, including a price-list image when ads are active.
- Writes logs to `logs/log.log` and uses `temp_img/` for downloaded photos.

**Supported input:** 
- Photo posts must have a caption with a `text_link` entity for the source URL.
- The caption formatter expects hashtags on the first line and an `источник: ...` line. Example:
```text
#tag_1 #tag_2

источник: source_username
```
The formatter appends `@<VK_GROUP_URL>` to each first-line tag and adds the shortened URL to the source line. It does not extract an ordinary pasted URL in place of a `text_link` entity. Example:
```text
#tag_1@VK_GROUP_URL #tag_2@VK_GROUP_URL

источник: source_username (tinyurl.com/example)
```


## Project layout

```text
.
├── .dockerignore
├── docker-compose.yml
├── Dockerfile               # Docker files prewritten for quick docker deployment
├── requirements.txt
├── vk_login.py              # One-time interactive VK login
├── price.png                # Add your own price-list image
├── vk_state.json            # Generated locally; keep private
├── .env                     # Create manually; keep private
└── src/
    ├── config.py           # Tokens, VK/Telegram IDs, paths, ad messages
    ├── logging_config.py   # Console and rotating file logging
    ├── main.py             # Application entry point
    ├── media_buffer.py     # Telegram album buffering
    ├── posts_processor.py  # Caption formatting and TinyURL request
    ├── telegram_bot.py     # Telegram handlers and alerts
    ├── vk_poster.py        # Playwright-based VK publishing
    └── __init__.py
```

## Prerequisites

- Python and the packages listed in `requirements.txt`.
- Playwright Chromium installed locally.
- A Telegram bot added to the source channel with permission to receive channel posts and to alert group with permission to send messages.
- A VK account with permission to publish to the target community.
- A TinyURL API token.
- A Telegram supergroup/topic for failure alerts.

## Setup

1. Clone the repository and install its dependencies from the repository root:

   ```bash
   python -m pip install -r requirements.txt
   python -m playwright install chromium
   ```


2. Configure `src/config.py`.


4. Create `.env` (you can refer to the beginning of `src/config.py` for tips). Set `TG_API_TOKEN`, `TINYURL_TOKEN`, `VK_GROUP_URL`, `VK_GROUP_ID`, `TG_ALERT_SUPERGROUP_ID`, and `TG_ALERT_TOPIC_ID`. Customize `ADS_MESSAGES_ACTIVE`, `ADS_MESSAGE_INACTIVE`, and `ADS_PRICELIST_TEXT` as needed. `VK_GROUP_URL` is the community short name used in the caption; `VK_GROUP_ID` is its positive numeric ID.


3. Add your own `price.png` to the repository root (the location expected by `ADS_PRICELIST['image']`). This is needed when `ADS_ACTIVE` is `True` and someone requests advertising information.


4. Generate the VK login state **before** starting the bot. `src/config.py` expects the saved state at `./vk_state.json`:

   ```bash
   python vk_login.py
   ```

   Sign in to VK in the opened browser, then return to the terminal and press Enter. Check that `vk_state.json` now exists in the repository root. Re-run the login script if the session expires.


5. Start the application from the repository root:

   ```bash
   python src/main.py
   ```

   The bot removes any existing Telegram webhook and starts polling for messages and channel posts.

## Docker

A `Dockerfile` and `docker-compose.yml` are included, but check their actual build and volume settings before running them. The runtime container must be able to read `vk_state.json` and `price.png` at the paths expected by `src/config.py`, and it must have Playwright Chromium available. Run the interactive `vk_login.py` step on a machine with a display first, then provide the generated state file to the container securely. The supplied file list does not establish whether the current Docker configuration already handles these requirements.
