#!/usr/bin/env python3
import argparse
from PIL import Image
from colorama import init

# Initialize colorama
init(autoreset=True)

# Characters ordered from dark to light
ASCII_CHARS = r"$@B%8&WM#*oahkbdpqwmZO0QLCJUYXzcvunxrjft/\|()1{}[]?-_+~<>i!lI;:,\"^`'."[::-1]


def resize_image(image, new_width=100):
    width, height = image.size
    aspect_ratio = height / width
    # Adjust for terminal character aspect
    new_height = int(new_width * aspect_ratio * 0.55)
    return image.resize((new_width, new_height))


def pixels_to_colored_ascii(image, use_color=True):
    image = image.convert("RGB")
    pixels = list(image.getdata())
    ascii_image = ""

    for i in range(len(pixels)):
        r, g, b = pixels[i]
        brightness = int((r + g + b) / 3)
        char = ASCII_CHARS[brightness * len(ASCII_CHARS) // 256]
        if use_color:
            ascii_image += f"\033[38;2;{r};{g};{b}m{char}"
        else:
            ascii_image += char
        if (i + 1) % image.width == 0:
            ascii_image += "\n"

    return ascii_image


def convert_image_to_ascii(path, width, use_color=True):
    try:
        image = Image.open(path)
    except Exception as e:
        return f"Error opening image: {e}"

    image = resize_image(image, width)
    return pixels_to_colored_ascii(image, use_color)


def main():
    parser = argparse.ArgumentParser(
        description="Convert image to colored ASCII art.")
    parser.add_argument("image_path", help="Path to the image file")
    parser.add_argument("-w", "--width", type=int,
                        default=100, help="Width of output ASCII")
    parser.add_argument("-nc", "--no-color", action="store_true",
                        help="Disable colored output")

    args = parser.parse_args()
    ascii_art = convert_image_to_ascii(
        args.image_path, args.width, not args.no_color)
    print(ascii_art)


if __name__ == "__main__":
    main()
