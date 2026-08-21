import logging

from locations.search import SearchPattern
from src.core.config import Config
from src.enums.ExtractionMode import ExtractionMode
from src.utils.data.io import update_count
from src.utils.device.interfaces import DeviceController
from src.utils.ocr.extract import extract_from_region

logger = logging.getLogger("BA-Scanner")


def get_currencies(device: DeviceController) -> bool:
    image = device.capture_screenshot()

    if image is None:
        return False

    currencies = [SearchPattern.AP, SearchPattern.CREDIT, SearchPattern.PYROXENE]
    owned_currencies_file = Config.scanned_currencies

    for currency in currencies:
        how_many = extract_from_region(
            image, currency.value, mode=ExtractionMode.NUMBER
        )  # reuse
        logger.info(
            f"[bold yellow]Detected[/bold yellow] [bold]Currency[/bold] {currency.name}: [cyan]{how_many}[/cyan]"
        )

        if currency.name == "AP":
            AP = how_many.split("/", 1)
            AP = {"Remaining": AP[0], "Max": AP[-1]}
            update_count(owned_currencies_file, currency.name.title(), AP)
        else:
            update_count(owned_currencies_file, currency.name.title(), how_many)
