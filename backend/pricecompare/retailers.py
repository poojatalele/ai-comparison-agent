"""Directory of known Indian retailers.

It does three jobs:

* **Normalize** messy store names from search results to one canonical name —
  so "Purplle.com – Beauty Online", "Purplle.com – Purplle Shopping" and
  "Purplle.com – Purplle Stores" all collapse into a single "Purplle".
* **Trust-tier** retailers — tell well-known stores apart from obscure ones,
  so the UI can show "Recommended" vs "Other" lists.
* **Identify the brand** behind a pasted URL — a single-brand store's domain
  *is* the brand, which anchors exact-product matching.
"""

from __future__ import annotations

from dataclasses import dataclass

from .web import domain_from_url


@dataclass(frozen=True)
class Retailer:
    """A known retailer: its canonical name, domain, and matching aliases."""

    canonical: str
    domain: str
    aliases: tuple[str, ...]   # lowercase substrings that identify this retailer
    is_marketplace: bool = False  # True = multi-brand store; False = single brand


# Order matters: more specific aliases must precede broader ones
# (e.g. "nykaa man" before "nykaa", or "Nykaa Man" would match "Nykaa").
_KNOWN_RETAILERS: tuple[Retailer, ...] = (
    Retailer("Amazon", "amazon.in", ("amazon",), is_marketplace=True),
    Retailer("Flipkart", "flipkart.com", ("flipkart",), is_marketplace=True),
    Retailer("Myntra", "myntra.com", ("myntra",), is_marketplace=True),
    Retailer("Ajio", "ajio.com", ("ajio",), is_marketplace=True),
    Retailer("Nykaa Man", "nykaaman.com", ("nykaa man",), is_marketplace=True),
    Retailer("Nykaa Fashion", "nykaafashion.com", ("nykaa fashion",), is_marketplace=True),
    Retailer("Nykaa", "nykaa.com", ("nykaa",), is_marketplace=True),
    Retailer("Purplle", "purplle.com", ("purplle",), is_marketplace=True),
    Retailer("Tira", "tirabeauty.com", ("tira beauty", "tirabeauty"), is_marketplace=True),
    Retailer("Croma", "croma.com", ("croma",), is_marketplace=True),
    Retailer("Reliance Digital", "reliancedigital.in", ("reliance digital",), is_marketplace=True),
    Retailer("Tata CLiQ", "tatacliq.com", ("tata cliq", "tatacliq"), is_marketplace=True),
    Retailer("Vijay Sales", "vijaysales.com", ("vijay sales",), is_marketplace=True),
    Retailer("JioMart", "jiomart.com", ("jiomart",), is_marketplace=True),
    Retailer("Shoppers Stop", "shoppersstop.com", ("shoppers stop",), is_marketplace=True),
    Retailer("BigBasket", "bigbasket.com", ("bigbasket",), is_marketplace=True),
    Retailer("Blinkit", "blinkit.com", ("blinkit",), is_marketplace=True),
    Retailer("Zepto", "zeptonow.com", ("zepto",), is_marketplace=True),
    Retailer("Swiggy Instamart", "swiggy.com", ("swiggy", "instamart"), is_marketplace=True),
    Retailer("FirstCry", "firstcry.com", ("firstcry",), is_marketplace=True),
    Retailer("Meesho", "meesho.com", ("meesho",), is_marketplace=True),
    Retailer("Snapdeal", "snapdeal.com", ("snapdeal",), is_marketplace=True),
    Retailer("PharmEasy", "pharmeasy.in", ("pharmeasy",), is_marketplace=True),
    Retailer("Apollo Pharmacy", "apollopharmacy.in", ("apollo pharmacy", "apollo247", "apollo 247"), is_marketplace=True),
    Retailer("Tata 1mg", "1mg.com", ("1mg", "tata 1mg"), is_marketplace=True),
    Retailer("Netmeds", "netmeds.com", ("netmeds",), is_marketplace=True),
    Retailer("Truemeds", "truemeds.in", ("truemeds",), is_marketplace=True),
    Retailer("Decathlon", "decathlon.in", ("decathlon",), is_marketplace=True),
    # --- single-brand stores: the domain *is* the brand (is_marketplace=False) ---
    Retailer("H&M", "hm.com", ("h&m", "h & m"), is_marketplace=False),
    Retailer("Adidas", "adidas.co.in", ("adidas",), is_marketplace=False),
    Retailer("Uniqlo", "uniqlo.com", ("uniqlo",), is_marketplace=False),
    Retailer("Sugar Cosmetics", "sugarcosmetics.com", ("sugar cosmetics",), is_marketplace=False),
    Retailer("Forest Essentials", "forestessentialsindia.com", ("forest essentials",), is_marketplace=False),
    Retailer("Mokobara", "mokobara.com", ("mokobara",), is_marketplace=False),
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

    def match_domain(self, domain: str) -> Retailer | None:
        """Return the `Retailer` that owns `domain`, by exact host match.

        Unlike `match`, this does not rely on alias substrings — so a multi-word
        brand like "Forest Essentials" is found from `forestessentialsindia.com`,
        whose spaceless domain its spaced alias could never match.
        """
        host = (domain or "").lower().strip()
        if host.startswith("www."):
            host = host[4:]
        if not host:
            return None
        for retailer in self._retailers:
            if host == retailer.domain or host.endswith("." + retailer.domain):
                return retailer
        return None

    def brand_for_url(self, url: str) -> str | None:
        """The brand behind a pasted URL — only when its domain is a brand store.

        Marketplaces (Amazon, Myntra, ...) sell many brands, so their domain is
        not a brand: those return `None`, as do unrecognized domains. A non-None
        result is a trustworthy brand to anchor exact-product matching on.
        """
        retailer = self.match_domain(domain_from_url(url))
        if retailer is None or retailer.is_marketplace:
            return None
        return retailer.canonical
