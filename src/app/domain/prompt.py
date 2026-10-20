from dataclasses import dataclass
from typing import Callable, Iterable

from app.domain.errors import Conflict, InvalidInput


@dataclass(frozen=True)
class Prompt:
    text: str
    hint: str | None = None


@dataclass(frozen=True)
class Category:
    id: str
    name: str
    prompts: tuple[Prompt, ...]


@dataclass(frozen=True)
class Pick:
    text: str
    category: str


def _category(identifier: str, name: str, prompts: Iterable[tuple[str, str | None]]) -> Category:
    return Category(identifier, name, tuple(Prompt(text, hint) for text, hint in prompts))


CATEGORIES = [
    _category("chaos", "Camera roll chaos", [
        ("The 7th photo in your camera roll right now", "Count back from the newest. No cheating."),
        ("Your most recent screenshot", "Albums → Screenshots."),
        ("A photo you took by accident", None),
        ("The most random thing you photographed this month", None),
        ("A photo that makes zero sense without context", None),
        ("Something you photographed so you wouldn't forget it", None),
        ("The last photo you sent to someone", None),
        ("A blurry photo you never deleted", None),
    ]),
    _category("everyday", "Everyday life", [
        ("The view from where you spend most of your day", None),
        ("The last thing you bought that wasn't food", None),
        ("Something that made you laugh this week", None),
        ("An animal. Yours, a friend's, or a stranger's.", 'Search "dog" or "cat" in Photos.'),
        ("A sky you stopped to take a photo of", 'Search "sunset" or "sky".'),
        ("Your favorite corner of your home", None),
        ("Something you see every single day", None),
        ("Your outfit on a day you felt good", None),
    ]),
    _category("food", "Food", [
        ("The last thing you ate that was worth a photo", 'Search "food" in Photos.'),
        ("Something you cooked yourself, proud or not", None),
        ("Your go-to drink", None),
        ("The best thing you ate on a trip", None),
        ("A meal you'd never order again", None),
        ("A late-night snack situation", None),
        ("A café or restaurant you'd go back to tomorrow", None),
        ("Dessert. Any dessert.", None),
    ]),
    _category("throwback", "Throwbacks", [
        ("The oldest photo in your camera roll", "Scroll all the way up in Library."),
        ("The first photo you took this year", None),
        ("A photo from around this time last year", None),
        ("A phase you've grown out of", None),
        ("Your hair a few years ago", None),
        ("A place you used to live or spend a lot of time", None),
        ("A trend you were 100% part of", None),
        ("A photo that brings back one specific memory", None),
    ]),
    _category("travel", "Travel", [
        ("The best view you've ever photographed", None),
        ("A photo from your last trip", None),
        ("An airport, train or road trip moment", None),
        ("Somewhere you'd go back to tomorrow", None),
        ("A trip where something went wrong", None),
        ("The most touristy photo you own", None),
        ("An animal you met while traveling", None),
        ("Your favorite spot in your own city", None),
    ]),
    _category("nights", "Nights out", [
        ("Your last night out in one photo", None),
        ("A concert, festival or event", None),
        ("The best outfit you've worn out", None),
        ("A group photo where someone wasn't ready", None),
        ("The morning after", None),
        ("A photo from a night you barely remember", None),
        ("Something you only find funny at 2am", None),
        ("The food you ate after a night out", None),
    ]),
    _category("embarrassing", "Embarrassing", [
        ("Your worst selfie", None),
        ("A failed attempt at something (cooking, DIY, a haircut…)", None),
        ("A photo someone took of you that you hate", None),
        ("A mirror selfie you'd never post", None),
        ("Proof of a bad decision", None),
        ("Your most dramatic face", None),
        ('A photo you sent to someone asking "is this okay?"', None),
        ("Something you bought and instantly regretted", None),
    ]),
    _category("wholesome", "Wholesome", [
        ("A moment you were genuinely happy this year", None),
        ("Someone who makes your life better", None),
        ("Something you're quietly proud of", None),
        ("A small win nobody knows about", None),
        ("A place where you feel calm", None),
        ("A photo that always makes you smile", None),
        ("A tradition you love", None),
        ("The best day of your summer", None),
    ]),
    _category("birthday", "The birthday star", [
        ("Your first photo with the birthday star", None),
        ("The funniest photo you have of them", None),
        ("Your most recent photo with them", None),
        ("A photo that reminds you of them, even if they're not in it", None),
        ("A place you've been together", None),
        ('Them doing something very "them"', None),
        ("The best memory you have with them", None),
        ("A photo they'd ask you to delete", None),
    ]),
]

SHUFFLE = "shuffle"


def choose_prompt(from_category: str, used: set[str], choose: Callable[[list[Pick]], Pick]) -> Pick:
    categories = CATEGORIES if from_category == SHUFFLE else [
        category for category in CATEGORIES if category.id == from_category
    ]
    options = [
        Pick(prompt.text, category.id)
        for category in categories
        for prompt in category.prompts
        if prompt.text not in used
    ]
    if not options:
        raise Conflict("No prompts remain in this category")
    return choose(options)


def custom_prompt(value: str) -> Pick:
    text = value.strip()
    if not text:
        raise InvalidInput("Prompt must not be empty")
    return Pick(text, "custom")
