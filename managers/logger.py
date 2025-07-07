import logging
import os

LOG_DIRECTORY = 'logs'
LOG_FILE = 'bot.log'

class IgnoreDNSResolutionErrors(logging.Filter):
    def filter(self, record):
        return "Temporary failure in name resolution" not in record.getMessage()

class ColorFormatter(logging.Formatter):
    COLORS = {
        'DEBUG': '\033[94m',
        'INFO': '\033[92m',
        'WARNING': '\033[93m',
        'ERROR': '\033[91m',
        'CRITICAL': '\033[95m'
    }
    RESET = '\033[0m'

    def format(self, record):
        levelname = record.levelname
        if levelname in self.COLORS:
            record.levelname = f"{self.COLORS[levelname]}{levelname}{self.RESET}"
        return super().format(record)

def setup_logger():
    os.makedirs(LOG_DIRECTORY, exist_ok=True)
    logger = logging.getLogger(__name__)
    logger.setLevel(logging.DEBUG)
    logger.handlers.clear()  # Evita handlers duplicados

    # Filtros
    ignore_dns_filter = IgnoreDNSResolutionErrors()
    logger.addFilter(ignore_dns_filter)
    logging.getLogger("aiohttp").addFilter(ignore_dns_filter)

    # Handlers
    file_handler = logging.FileHandler(os.path.join(LOG_DIRECTORY, LOG_FILE))
    file_handler.setLevel(logging.DEBUG)
    file_handler.setFormatter(logging.Formatter(
        '%(asctime)s %(levelname)s     %(message)s', datefmt='%Y-%m-%d %H:%M:%S'
    ))

    console_handler = logging.StreamHandler()
    console_handler.setLevel(logging.INFO)
    console_handler.setFormatter(ColorFormatter(
        '%(asctime)s %(levelname)s     %(message)s', datefmt='%Y-%m-%d %H:%M:%S'
    ))

    logger.addHandler(file_handler)
    logger.addHandler(console_handler)

    # Níveis específicos para outros loggers
    logging.getLogger("discord.gateway").setLevel(logging.INFO)
    logging.getLogger("discord.http").setLevel(logging.INFO)
    logging.getLogger("apscheduler").setLevel(logging.WARNING)

    # Evita propagação para o root logger
    logger.propagate = False

    return logger

logger = setup_logger()
