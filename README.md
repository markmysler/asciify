# Asciify

Convert images to colored ASCII art in your terminal. This tool transforms any image into ASCII characters while preserving the original colors.

![Example Output](docs/example.png)

## Features

-   Convert images to ASCII art
-   Preserve original colors in terminal output
-   Adjustable output width
-   Option for monochrome output
-   Supports most common image formats (PNG, JPEG, GIF, etc.)

## Installation

```bash
pip install asciifyy
```

## Usage

Basic usage:

```bash
asciify path/to/image.jpg
```

### Options

-   `-w, --width` : Set output width in characters (default: 100)

    ```bash
    asciify path/to/image.jpg -w 150
    ```

-   `-nc, --no-color` : Disable colored output
    ```bash
    asciify path/to/image.jpg --no-color
    ```

## Requirements

-   Python 3.7 or higher
-   Pillow (PIL)
-   Colorama

## Development

To set up the development environment:

```bash
git clone https://github.com/markmysler/asciify.git
cd asciify
pip install -e .
```

## License

MIT License - See [LICENSE](LICENSE) for details.

## Author

Mark Mysler (myslermark@gmail.com)

## Contributing

Contributions are welcome! Please feel free to submit a Pull Request.
