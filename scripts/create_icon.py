from pathlib import Path

from PIL import Image


ROOT = Path(__file__).resolve().parents[1]
SOURCE = ROOT / "assets" / "playlist-porter-logo.png"
DESTINATION = ROOT / "build" / "playlist-porter.ico"


def main() -> None:
    DESTINATION.parent.mkdir(parents=True, exist_ok=True)
    with Image.open(SOURCE) as image:
        image.convert("RGBA").save(
            DESTINATION,
            format="ICO",
            sizes=[(16, 16), (24, 24), (32, 32), (48, 48), (64, 64), (128, 128), (256, 256)],
        )
    print(f"Created {DESTINATION}")


if __name__ == "__main__":
    main()

