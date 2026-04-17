# GoFile Downloader

Modern async downloader for GoFile with concurrent downloads and real-time progress tracking.

![Demo](https://github.com/Lysagxra/GoFileDownloader/blob/90b902ff734115dd1d955f80ac855700bcde7cc2/assets/demo.gif)

## Features

- ⚡ Async concurrent downloads
- 📦 Batch downloading via URL list
- 🔒 Password-protected album support
- 📁 Custom download location
- 📊 Real-time progress tracking

## Requirements

- Python 3.11+
- httpx
- rich

## Installation

```bash
git clone https://github.com/dacrab/GoFileDownloader.git
cd GoFileDownloader
pip install -r requirements.txt
```

## Usage

### Single Album

```bash
python3 downloader.py <gofile_url>
```

### Password-Protected Album

```bash
python3 downloader.py <gofile_url> <password>
```

### Batch Download

1. Create `URLs.txt` with one URL per line:
```
https://gofile.io/d/clgeTz
https://gofile.io/d/FrYeIy
```

2. Run:
```bash
python3 main.py
```

### Custom Download Location

```bash
python3 main.py --custom-path /path/to/directory
```

Files are saved to `<custom_path>/Downloads` or `./Downloads` by default.

## Development

### Setup

```bash
pip install -r requirements.txt
pip install pre-commit ruff mypy
pre-commit install
```

### Code Quality

```bash
ruff check .          # Lint
ruff format .         # Format
mypy src/             # Type check
```

## Project Structure

```
GoFileDownloader/
├── src/
│   ├── config.py
│   ├── download_utils.py
│   ├── gofile_utils.py
│   └── ui.py
├── downloader.py
├── main.py
├── pyproject.toml
└── requirements.txt
```

## License

GPL-3.0
