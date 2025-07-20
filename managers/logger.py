import logging
import os

LOG_DIRECTORY = 'logs'
LOG_FILE = 'rebellion.log'


class IgnoreDNSResolutionErrors(logging.Filter):
    """
    Filtra mensagens de erro temporário de resolução de DNS.
    """
    def filter(self, record: logging.LogRecord) -> bool:
        return "Temporary failure in name resolution" not in record.getMessage()


class IgnoreDiscordResume(logging.Filter):
    """
    Filtra mensagens de RESUMED session do Discord Gateway.
    """
    def filter(self, record: logging.LogRecord) -> bool:
        return "RESUMED session" not in record.getMessage()


class ColorFormatter(logging.Formatter):
    """
    Formata o console com cores ANSI conforme o nível de log.
    """
    COLORS = {
        'DEBUG': '\033[94m',     # Azul claro
        'INFO': '\033[1;34m',    # Azul forte
        'WARNING': '\033[93m',   # Amarelo
        'ERROR': '\033[91m',     # Vermelho
        'CRITICAL': '\033[95m'   # Magenta
    }
    RESET = '\033[0m'

    def format(self, record: logging.LogRecord) -> str:
        levelname = record.levelname
        if levelname in self.COLORS:
            record.levelname = f"{self.COLORS[levelname]}{levelname}{self.RESET}"
        return super().format(record)


def setup_logger() -> logging.Logger:
    """
    Configura e retorna o logger principal com handlers de arquivo e console colorido.
    """
    os.makedirs(LOG_DIRECTORY, exist_ok=True)

    logger = logging.getLogger("rebellion")
    logger.setLevel(logging.INFO)
    logger.handlers.clear()  # Evita múltiplos handlers ao recarregar

    # Filtros globais
    ignore_dns_filter = IgnoreDNSResolutionErrors()
    ignore_resume_filter = IgnoreDiscordResume()

    logger.addFilter(ignore_dns_filter)
    logging.getLogger("aiohttp").addFilter(ignore_dns_filter)

    # Handler de arquivo
    file_handler = logging.FileHandler(
        os.path.join(LOG_DIRECTORY, LOG_FILE),
        encoding="utf-8"
    )
    file_handler.setLevel(logging.INFO)
    file_handler.setFormatter(logging.Formatter(
        '%(asctime)s %(levelname)s     %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S'
    ))

    # Handler de console colorido
    console_handler = logging.StreamHandler()
    console_handler.setLevel(logging.INFO)
    console_handler.setFormatter(ColorFormatter(
        '%(asctime)s %(levelname)s     %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S'
    ))
    # Exemplo de aplicação do filtro IgnoreDiscordResume apenas no console
    console_handler.addFilter(ignore_resume_filter)

    # Anexa handlers
    logger.addHandler(file_handler)
    logger.addHandler(console_handler)

    # Ajustes em outros loggers utilizados no projeto
    logging.getLogger("discord.gateway").setLevel(logging.WARNING)
    logging.getLogger("discord.http").setLevel(logging.WARNING)
    logging.getLogger("apscheduler").setLevel(logging.WARNING)
    
    

    logger.propagate = False

    return logger


logger = setup_logger()
