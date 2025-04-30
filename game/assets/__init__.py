from game.types import AnimalType, ItemType

from .loader import load_image


def load_images():
    return {
        AnimalType.RABBIT: load_image("rabbit.png"),
        AnimalType.SEAL: load_image("seal.png"),
        AnimalType.FISH: load_image("fish.png"),
        AnimalType.DOG: load_image("dog.png"),
        AnimalType.HEDGEHOG: load_image("hedgehog.png"),
        AnimalType.SNAIL: load_image("snail.png"),
        ItemType.CARROT: load_image("carrot.png"),
        ItemType.BONE: load_image("bone.png"),
        ItemType.STAR: load_image("star.png"),
        ItemType.SHELL: load_image("shell.png"),
        ItemType.WORM: load_image("worm.png"),
        ItemType.STRAWBERRY: load_image("strawberry.png"),
    }
