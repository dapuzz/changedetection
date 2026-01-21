"""Constants for ChangeDetection.io integration."""

DOMAIN = "changedetection"

# Configuration
CONF_BASE_URL = "base_url"
CONF_API_KEY = "api_key"

# Defaults
DEFAULT_SCAN_INTERVAL = 60
DEFAULT_NAME = "ChangeDetection.io"

# Platforms
PLATFORMS = ["sensor", "button"]

# Services
SERVICE_CREATE_WATCH = "create_watch"
SERVICE_DELETE_WATCH = "delete_watch"
SERVICE_UPDATE_WATCH = "update_watch"
SERVICE_RECHECK_WATCH = "recheck_watch"
SERVICE_PAUSE_WATCH = "pause_watch"
SERVICE_UNPAUSE_WATCH = "unpause_watch"
SERVICE_MUTE_WATCH = "mute_watch"
SERVICE_UNMUTE_WATCH = "unmute_watch"
SERVICE_GET_SNAPSHOT = "get_snapshot"
SERVICE_GET_DIFF = "get_diff"
SERVICE_CREATE_TAG = "create_tag"
SERVICE_DELETE_TAG = "delete_tag"
SERVICE_UPDATE_TAG = "update_tag"
SERVICE_RECHECK_TAG = "recheck_tag"
SERVICE_MUTE_TAG = "mute_tag"
SERVICE_UNMUTE_TAG = "unmute_tag"
SERVICE_SEARCH = "search"
SERVICE_BULK_IMPORT = "bulk_import"
SERVICE_ADD_NOTIFICATIONS = "add_notifications"
SERVICE_REPLACE_NOTIFICATIONS = "replace_notifications"
SERVICE_DELETE_NOTIFICATIONS = "delete_notifications"

# Attributes
ATTR_UUID = "uuid"
ATTR_URL = "url"
ATTR_TITLE = "title"
ATTR_TAG = "tag"
ATTR_TAGS = "tags"
ATTR_PAUSED = "paused"
ATTR_MUTED = "muted"
ATTR_NOTIFICATION_MUTED = "notification_muted"
ATTR_METHOD = "method"
ATTR_FETCH_BACKEND = "fetch_backend"
ATTR_HEADERS = "headers"
ATTR_BODY = "body"
ATTR_PROXY = "proxy"
ATTR_TIME_BETWEEN_CHECK = "time_between_check"
ATTR_NOTIFICATION_URLS = "notification_urls"
ATTR_NOTIFICATION_TITLE = "notification_title"
ATTR_NOTIFICATION_BODY = "notification_body"
ATTR_NOTIFICATION_FORMAT = "notification_format"
ATTR_PROCESSOR = "processor"
ATTR_TIMESTAMP = "timestamp"
ATTR_FROM_TIMESTAMP = "from_timestamp"
ATTR_TO_TIMESTAMP = "to_timestamp"
ATTR_FORMAT = "format"
ATTR_WORD_DIFF = "word_diff"
ATTR_QUERY = "query"
ATTR_URLS_TEXT = "urls_text"
ATTR_TAG_UUIDS = "tag_uuids"
ATTR_DEDUPE = "dedupe"
