# Cryptocurrency Transaction Scraper

Because I'm an idiot and couldn't work out how to scrape the BitInfoCharts website, I've created this Python script that scrapes historical transaction data using OCR. I'm sure that there is a better way to do this, but I couldn't work it out.

## Features

- Scrapes daily transaction counts for multiple cryptocurrencies
- Saves data to individual CSV files
- Handles OCR-based data extraction from charts
- Includes error handling and retry mechanisms

## Prerequisites

- Python 3.x
- pip install selenium webdriver-manager pandas pytesseract pillow opencv-python numpy

You'll also need to install Tesseract OCR:
- Windows: Download and install from [GitHub](https://github.com/UB-Mannheim/tesseract/wiki)
- Linux: `sudo apt-get install tesseract-ocr`
- Mac: `brew install tesseract`

## Usage

1. Clone the repository
2. Install the required dependencies
3. Run the script:

python bitinfocharts_scraper.py

## Adding New Cryptocurrencies

To add additional cryptocurrencies, modify the `cryptos` list in the `main()` function:

{
'name': 'Your Crypto Name',
'url': 'https://bitinfocharts.com/comparison/your-crypto-transactions.html#3m',
'output': 'your_crypto_transactions.csv'
},

URL format:
- Bitcoin: `bitcoin-transactions.html`
- Other coins: `transactions-SYMBOL.html` or `COINNAME-transactions.html`

## Output

The script generates CSV files with two columns:
- `date`: The date of the transactions
- `transactions`: Number of transactions on that date

## Limitations

- The script relies on OCR to extract data from charts
- Rate limiting may be necessary for frequent usage
- Some cryptocurrency charts may have different layouts

## Error Handling

The script includes error handling for:
- Network issues
- OCR recognition failures
- Invalid data formats
- Browser automation errors



