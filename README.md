# GoFile Downloader

Minimal GoFile downloader with concurrent downloads and progress tracking.

![Demo](https://github.com/Lysagxra/GoFileDownloader/blob/90b902ff734115dd1d955f80ac855700bcde7cc2/assets/demo.gif)

## Features

- 🚀 Concurrent downloads
- 📦 Batch downloading
- 🔒 Password support
- 📁 Custom paths
- 📊 Progress bars

## Install

```bash
pip install -r requirements.txt
```

## Usage

```bash
# Single download
python3 downloader.py <url>

# With password
python3 downloader.py <url> <password>

# Custom path
python3 downloader.py <url> --custom-path /path/to/dir

# Batch (create URLs.txt first)
python3 main.py
```

## License

GPL-3.0
