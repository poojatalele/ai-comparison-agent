"""Directory of known Indian retailers.

It does two jobs:

* **Normalize** messy store names from search results to one canonical name —
  so "Purplle.com – Beauty Online", "Purplle.com – Purplle Shopping" and
  "Purplle.com – Purplle Stores" all collapse into a single "Purplle".
* **Trust-tier** retailers — tell well-known stores apart from obscure ones,
  so the UI can show "Recommended" vs "Other" lists.
"""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class Retailer:
    """A known retailer: its canonical name, domain, and matching aliases."""

    canonical: str
    domain: str
    aliases: tuple[str, ...]   # lowercase substrings that identify this retailer


# Order matters: more specific aliases must precede broader ones
# (e.g. "nykaa man" before "nykaa", or "Nykaa Man" would match "Nykaa").
_KNOWN_RETAILERS: tuple[Retailer, ...] = (
    Retailer("Amazon", "amazon.in", ("amazon",)),
    Retailer("Flipkart", "flipkart.com", ("flipkart",)),
    Retailer("Myntra", "myntra.com", ("myntra",)),
    Retailer("Ajio", "ajio.com", ("ajio",)),
    Retailer("Nykaa Man", "nykaaman.com", ("nykaa man",)),
    Retailer("Nykaa Fashion", "nykaafashion.com", ("nykaa fashion",)),
    Retailer("Nykaa", "nykaa.com", ("nykaa",)),
    Retailer("Purplle", "purplle.com", ("purplle",)),
    Retailer("Tira", "tirabeauty.com", ("tira beauty", "tirabeauty")),
    Retailer("Croma", "croma.com", ("croma",)),
    Retailer("Reliance Digital", "reliancedigital.in", ("reliance digital",)),
    Retailer("Tata CLiQ", "tatacliq.com", ("tata cliq", "tatacliq")),
    Retailer("Vijay Sales", "vijaysales.com", ("vijay sales",)),
    Retailer("JioMart", "jiomart.com", ("jiomart",)),
    Retailer("Shoppers Stop", "shoppersstop.com", ("shoppers stop",)),
    Retailer("BigBasket", "bigbasket.com", ("bigbasket",)),
    Retailer("Blinkit", "blinkit.com", ("blinkit",)),
    Retailer("Zepto", "zeptonow.com", ("zepto",)),
    Retailer("Swiggy Instamart", "swiggy.com", ("swiggy", "instamart")),
    Retailer("FirstCry", "firstcry.com", ("firstcry",)),
    Retailer("Meesho", "meesho.com", ("meesho",)),
    Retailer("Snapdeal", "snapdeal.com", ("snapdeal",)),
    Retailer("PharmEasy", "pharmeasy.in", ("pharmeasy",)),
    Retailer("Apollo Pharmacy", "apollopharmacy.in", ("apollo pharmacy", "apollo247", "apollo 247")),
    Retailer("Tata 1mg", "1mg.com", ("1mg", "tata 1mg")),
    Retailer("Netmeds", "netmeds.com", ("netmeds",)),
    Retailer("Truemeds", "truemeds.in", ("truemeds",)),
    Retailer("H&M", "hm.com", ("h&m", "h & m")),
    Retailer("Adidas", "adidas.co.in", ("adidas",)),
    Retailer("Decathlon", "decathlon.in", ("decathlon",)),
    Retailer("Uniqlo", "uniqlo.com", ("uniqlo",)),
    Retailer("Sugar Cosmetics", "sugarcosmetics.com", ("sugar cosmetics",)),
    Retailer("Forest Essentials", "forestessentialsindia.com", ("forest essentials",)),
    Retailer("Mokobara", "mokobara.com", ("mokobara",)),
)


class RetailerDirectory:
    """Looks up a raw store name (or domain) against the known-retailer list."""

    def __init__(self, retailers: tuple[Retailer, ...] = _KNOWN_RETAILERS) -> None:
        self._retailers = retailers

    def match(self, raw_name: str) -> Retailer | None:
        """Return the known `Retailer` for a raw store name/domain, or `None`."""
        haystack = (raw_name or "").lower()
        for retailer in self._retailers:
            if any(alias in haystack for alias in retailer.aliases):
                return retailer
        return None
