import logging

LOG_FORMAT = "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
LOG_LEVEL = logging.INFO
LOG_HANDLERS = [logging.StreamHandler(), logging.FileHandler("app.log", "a", "utf-8")]


def configure_logging():
    logging.basicConfig(
        level=LOG_LEVEL, format=LOG_FORMAT, handlers=LOG_HANDLERS, force=True
    )
