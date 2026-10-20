import pytest

from app.domain.errors import Conflict, InvalidInput
from app.domain.prompt import CATEGORIES, SHUFFLE, choose_prompt, custom_prompt


def test_prompt_catalog_contains_all_reference_categories_and_prompts():
    assert [category.id for category in CATEGORIES] == [
        "chaos",
        "everyday",
        "food",
        "throwback",
        "travel",
        "nights",
        "embarrassing",
        "wholesome",
        "birthday",
    ]
    assert [len(category.prompts) for category in CATEGORIES] == [8] * 9

    chaos = next(category for category in CATEGORIES if category.id == "chaos")
    assert chaos.name == "Camera roll chaos"
    assert chaos.prompts[0].text == "The 7th photo in your camera roll right now"
    assert chaos.prompts[0].hint == "Count back from the newest. No cheating."
    assert chaos.prompts[2].hint is None

    everyday = next(category for category in CATEGORIES if category.id == "everyday")
    animal = next(prompt for prompt in everyday.prompts if prompt.text.startswith("An animal."))
    assert animal.hint == 'Search "dog" or "cat" in Photos.'


def test_category_selection_excludes_prompts_already_used():
    category = next(category for category in CATEGORIES if category.id == "food")
    used = {category.prompts[0].text}
    choices = []

    def choose(options):
        choices.append(options)
        return options[0]

    prompt = choose_prompt(category.id, used, choose)

    assert prompt.text == category.prompts[1].text
    assert prompt.category == category.id
    assert [candidate.text for candidate in choices[0]] == [
        prompt.text for prompt in category.prompts[1:]
    ]


def test_shuffle_selection_excludes_prompts_used_across_categories():
    used = {CATEGORIES[0].prompts[0].text, CATEGORIES[-1].prompts[-1].text}
    choices = []

    def choose(options):
        choices.append(options)
        return options[0]

    prompt = choose_prompt(SHUFFLE, used, choose)

    assert prompt.text == CATEGORIES[0].prompts[1].text
    assert prompt.category == CATEGORIES[0].id
    assert all(
        candidate.text not in used
        for candidate in choices[0]
    )


def test_exhausted_category_raises_conflict():
    category = next(category for category in CATEGORIES if category.id == "nights")
    used = {prompt.text for prompt in category.prompts}

    with pytest.raises(Conflict):
        choose_prompt(category.id, used, lambda options: options[0])


@pytest.mark.parametrize("value", ["", "   ", "\t\n"])
def test_custom_prompt_must_not_be_empty(value):
    with pytest.raises(InvalidInput):
        custom_prompt(value)


def test_custom_prompt_is_trimmed():
    prompt = custom_prompt("  Bring the weirdest mug  ")

    assert prompt.text == "Bring the weirdest mug"
    assert prompt.category == "custom"
