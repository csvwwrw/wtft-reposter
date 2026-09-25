'''
Configuration settings and paths for Telegram bot, VK poster, logging,
and external services.

# Copy these settings into a local .env file at the project root.
# Replace the example values with your own.
TG_API_TOKEN=your_telegram_bot_token
TINYURL_TOKEN=your_tinyurl_token

VK_GROUP_URL=https://vk.com/your_group
VK_GROUP_ID=11111111

TG_ALERT_SUPERGROUP_ID=-10011111111
TG_ALERT_TOPIC_ID=2

ADS_MESSAGES_ACTIVE="First ad message.
It can have several lines.

And even a second paragraph.
---
Second ad message.
Also as long as you like.
---
Third ad message."
ADS_MESSAGE_ACTIVE_2=Second active ads message
ADS_MESSAGE_INACTIVE=Message if ads are inactive
ADS_PRICELIST_TEXT=Caption for pricelist.
'''

import os
from dotenv import load_dotenv
from pathlib import Path

APP_ROOT = Path(__file__).resolve().parent.parent
load_dotenv(dotenv_path=APP_ROOT / '.env', override=False)

def required(name:str) -> str:
    value = os.getenv(name)
    if value is None or not value.strip():
        raise RuntimeError(f'Missing setting: {name}')
    return value

class Config:
    TG_API_TOKEN = required('TG_API_TOKEN')
    TINYURL_TOKEN = required('TINYURL_TOKEN')

    VK_GROUP_URL = required('VK_GROUP_URL')
    VK_GROUP_ID = int(required('VK_GROUP_ID'))

    TG_ALERT_SUPERGROUP_ID = int(required('TG_ALERT_SUPERGROUP_ID'))
    TG_ALERT_TOPIC_ID = int(required('TG_ALERT_TOPIC_ID'))

    ADS_ACTIVE = True # switch to false if your ad campaign is stopped

    ADS_MESSAGES = {
        True: [
            message.strip()
            for message in required('ADS_MESSAGES_ACTIVE').split('\n---\n')
        ],
        False: required('ADS_MESSAGE_INACTIVE'),
    }

    ADS_PRICELIST = {
        'text': required('ADS_PRICELIST_TEXT'),
        'image': APP_ROOT / 'price.png',
    }

    MEDIA_GROUP_TIMEOUT = 5 # Speed of media group flushing
    # (if posts arrive with more seconds in between, they aren't considered single media group)

    APP_ROOT = Path(__file__).parent.parent
    LOGS_DIR = APP_ROOT / 'logs'
    TEMP_IMG_DIR = APP_ROOT / 'temp_img'
    PLAYWRIGHT_VK_STATE = APP_ROOT / 'vk_state.json'

    LOGS_DIR.mkdir(parents=True, exist_ok=True)
    TEMP_IMG_DIR.mkdir(parents=True, exist_ok=True)

    LOG_LEVEL = 'INFO'
    LOG_FILE = LOGS_DIR / 'log.log'
    LOG_FORMAT = '%(asctime)s | %(name)s | %(levelname)s : %(message)s'
    LOG_DATE_FORMAT = '%Y-%m-%d %H:%M:%S'

settings = Config()