# GoFile Downloader

Minimal GoFile downloader with concurrent downloads and progress tracking.

![Demo](https://github.com/Lysagxra/GoFileDownloader/blob/90b902ff734115dd1d955f80ac855700bcde7cc2/assets/demo.gif)

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

# Batch download from file
python3 downloader.py --batch URLs.txt
```

## License

GPL-3.0
