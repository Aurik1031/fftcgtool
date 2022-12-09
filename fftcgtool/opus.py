import dataclasses
import logging
from typing import Callable, Iterable

import requests
import roman

from .card import Card
from .carddb import CardDB
from .cards import Cards
from .language import API_LANGS, Language
from .ttsdeck import TTSDeck


class Opus(Cards):
    __SQUARE_API_URL = "https://fftcg.square-enix-games.com/en/get-cards"

    def __init__(self, opus_id: str, language: Language):
        logger = logging.getLogger(__name__)
        self.__language = language

        params: dict[str, any]
        if opus_id.isnumeric():
            name = f"Opus {opus_id} ({self.__language.short})"
            self.__number = opus_id

            if (opus_id := int(opus_id)) <= 14:
                params = {"set": [f"Opus {roman.toRoman(opus_id).upper()}"]}

            else:
                opus_map = {
                    15: "Crystal Dominion",
                    16: "Emissaries of Light",
                    17: "Rebellion's Call",
                    18: "Resurgence of Power",
                }
                params = {"set": [opus_map[opus_id]]}

        elif opus_id == "chaos":
            name = f"Boss Deck Chaos ({self.__language.short})"
            self.__number = "B"
            params = {"set": ["Boss Deck Chaos"]}

        elif opus_id == "promo":
            name = f"Promo ({self.__language.short})"
            self.__number = "PR"
            params = {"rarity": ["pr"]}

        else:
            name = "?"
            self.__number = "?"
            self.__filename = "?"
            params = {"set": "?"}

        logger.info(f"Importing {name}")

        # required params:
        #  text
        # supported params:
        #  [str] text, language, code, multicard="○"|"", ex_burst="○"|"", special="《S》"|""
        #  [array] type, element, cost, rarity, power, category_1, set
        #  [int] exactmatch=0|1

        if "text" not in params:
            params["text"] = ""

        # get cards from square api
        logger.debug(f"POST params: {params}")
        req = requests.post(Opus.__SQUARE_API_URL, json=params)
        carddb = CardDB()
        cards = (
            Card.from_square_api_data(card_data)
            for card_data in req.json()["cards"]
        )

        cards = [
            card
            for card in cards
            if card.code.opus == self.__number or not card.code.opus.isnumeric()
        ]

        # remove reprints
        super().__init__(name, cards)

        # sort cards by opus, then serial
        self.sort(key=lambda x: x.code.serial)
        self.sort(key=lambda x: x.code.opus)

        for card in self:
            try:
                for lang in API_LANGS:
                    card[lang] = dataclasses.replace(card[lang], face=carddb[card.code][lang].face)

            except KeyError:
                pass

            logger.debug(f"imported card {card}")

    @property
    def number(self) -> str:
        return self.__number

    @property
    def elemental_decks(self) -> Iterable[TTSDeck]:
        if self.number in ["PR", "B"]:
            return [TTSDeck(
                codes=[
                    card.code
                    for card in self
                ],
                name=f"{self.name}",
                description=f"All {self.name} Cards",
                face_down=False,
            )]

        else:
            def element_filter(element: str) -> Callable[[Card], list[str]]:
                return lambda card: card.elements == [element]

            # simple cases: create lambdas for base elemental decks
            base_elements = ["Fire", "Ice", "Wind", "Earth", "Lightning", "Water"]
            filters = {
                elem: element_filter(elem)
                for elem in base_elements
            }

            filters |= {
                # light/darkness elemental deck
                "Light-Darkness": lambda card: card.elements in (["Light"], ["Darkness"]),
                # multi element deck
                "Multi": lambda card: "Crystal" in card.elements or len(card.elements) > 1,
            }

            # sort cards by element, then alphabetically
            cards = list(self)
            cards.sort(key=lambda x: x[self.__language].name)
            cards.sort(key=lambda x: "Multi" if len(x.elements) > 1 else x.elements[0])

            # generate decks
            decks = (
                TTSDeck(
                    codes=[
                        card.code
                        for card in cards
                        if f(card)
                    ],
                    name=f"{self.name} {elem}",
                    description=f"All {self.name} Cards with {elem} element in alphabetical order",
                    face_down=False,
                ) for elem, f in filters.items()
            )

            # Ignore empty decks
            return (
                deck
                for deck in decks
                if deck
            )
