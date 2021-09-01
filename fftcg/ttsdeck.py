from __future__ import annotations

import json
import os

import requests

from .carddb import CardDB
from .cards import Cards
from .code import Code
from .language import Language
from .utils import CARD_BACK_URL, DECKS_DIR_NAME


class TTSDeck(Cards):
    def __init__(self, codes: list[Code], name: str, description: str):
        super().__init__(name)
        self.__description = description

        # get cards from carddb
        carddb = CardDB()
        self.extend([
            carddb[code]
            for code in codes
        ])

    __FFDECKS_API_URL = "https://ffdecks.com/api/deck"

    @classmethod
    def from_ffdecks_deck(cls, deck_id: str) -> TTSDeck:
        req = requests.get(TTSDeck.__FFDECKS_API_URL, params={"deck_id": deck_id})
        codes = [
            Code(card["card"]["serial_number"])
            for card in req.json()["cards"]
        ]
        name = f"{req.json()['name']} ({deck_id})"
        description = req.json()["description"]

        return cls(codes, name, description)

    def tts_object(self, language: Language) -> dict[str, any]:
        # unique face urls used
        unique_faces = set([
            card[language].face
            for card in self
        ])

        # lookup for indices of urls
        url_indices = {
            url: i + 1
            for i, url in enumerate(unique_faces)
        }

        # build the "CustomDeck" dictionary
        custom_deck = {
            str(i): {
                "NumWidth": "10",
                "NumHeight": "7",
                "FaceURL": url,
                "BackURL": CARD_BACK_URL,
            } for url, i in url_indices.items()
        }

        # values both in main deck and each contained card
        common_dict = {
            "Transform": {
                "scaleX": 2.17822933,
                "scaleY": 1.0,
                "scaleZ": 2.17822933,
                "rotY": 180.0,
            },
            "Locked": False,
            "Grid": True,
            "Snap": True,
            "Autoraise": True,
            "Sticky": True,
            "Tooltip": True,
            "GridProjection": False,
        }

        # cards contained in deck
        contained_objects = [
            {
                "Nickname": card[language].name,
                "Description": card[language].text,
                "CardID": 100 * url_indices[card[language].face] + card.index,

                "Name": "Card",
                "Hands": True,
                "SidewaysCard": False,
            } | common_dict for card in self
        ]

        # extract the card ids
        deck_ids = [
            contained_object["CardID"]
            for contained_object in contained_objects
        ]

        # create the deck dictionary
        return {"ObjectStates": [
            {
                "Nickname": self.name,
                "Description": self.__description,
                "DeckIDs": deck_ids,
                "CustomDeck": custom_deck,
                "ContainedObjects": contained_objects,

                "Name": "Deck",
                "Hands": False,
                "SidewaysCard": False,
            } | common_dict
        ]}

    def save(self, language: Language) -> None:
        # only save if the deck contains cards
        if self:
            if not os.path.exists(DECKS_DIR_NAME):
                os.mkdir(DECKS_DIR_NAME)

            with open(os.path.join(DECKS_DIR_NAME, f"{self.file_name}.json"), "w") as file:
                json.dump(self.tts_object(language), file, indent=2)
