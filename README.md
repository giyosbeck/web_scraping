# UniPage.net University Data Scraper

A Python-based web scraper that extracts university information from UniPage.net and converts it to JSON format compatible with Bilkent University's schema.

## Prerequisites

- **Operating System**: Windows 10 or later
- **Python**: Version 3.8 or higher
- **Web Browser**: Google Chrome (latest version recommended)
- **Git**: For cloning the repository

## Local Setup

### 1. Clone the Repository

```bash
git clone <repository-url>
cd py_test
```

### 2. Create Virtual Environment

```bash
python -m venv venv
venv\Scripts\activate
```

### 3. Install Dependencies

```bash
pip install -r requirements.txt
```

## ChromeDriver Configuration

The scraper uses WebDriverManager to automatically download and manage ChromeDriver. No manual ChromeDriver installation is required - the tool will:

- Automatically detect your Chrome browser version
- Download the compatible ChromeDriver version
- Cache the driver for future use

## Running the Scraper

**Note**: The `scraper/__init__.py` file has been added to treat the `scraper` directory as a Python package, ensuring that internal imports resolve properly.

### Basic Usage

```bash
python -m scraper.main --countries "Turkey,Germany"
```

### Command Line Arguments

- `--countries`: Comma-separated list of countries to scrape (required)
- `--output-dir`: Custom output directory (optional, defaults to `unipage_data/`)
- `--log-level`: Logging level (DEBUG, INFO, WARNING, ERROR, default: INFO)

### Examples

```bash
# Scrape universities from multiple countries
python -m scraper.main --countries "Turkey,Germany,France"

# Scrape with custom output directory
python -m scraper.main --countries "Turkey" --output-dir "custom_output/"

# Enable debug logging
python -m scraper.main --countries "Turkey" --log-level DEBUG
```

## Output

The scraper generates the following outputs:

### Data Files

- **Location**: `unipage_data/` directory (or custom directory specified)
- **Format**: JSON files named by country (e.g., `turkey_universities.json`)
- **Schema**: Compatible with Bilkent University's data format

### Log Files

- **Location**: `logs/app.log`
- **Content**: Detailed execution logs including:
  - Scraping progress
  - Error messages
  - Performance metrics
  - Debug information (if enabled)

### Sample Output Structure

```json
{
  "universities": [
    {
      "name": "University Name",
      "location": "City, Country",
      "website": "https://university-website.com",
      "description": "University description...",
      "programs": ["Program 1", "Program 2"],
      "scraped_at": "2024-01-01T12:00:00Z"
    }
  ],
  "metadata": {
    "total_universities": 150,
    "country": "Turkey",
    "scraped_at": "2024-01-01T12:00:00Z"
  }
}
```

## TraycerAI Deployment

### 1. Connect Repository

1. Log in to your TraycerAI dashboard
2. Click "New Project" or "Connect Repository"
3. Provide your repository URL
4. Authenticate with your Git provider

### 2. Configuration

The project includes a `traycerai.yaml` configuration file that defines:

- Runtime environment (Python 3.8+)
- Dependencies installation
- Entry point and execution commands
- Resource requirements

### 3. Deploy and Run

1. Once connected, TraycerAI will automatically detect the `traycerai.yaml` file
2. Click "Deploy" to set up the environment
3. Click "Run" to execute the scraper
4. Monitor execution through the TraycerAI dashboard
5. Download results from the TraycerAI interface

### 4. Scheduling (Optional)

Set up automated runs through TraycerAI's scheduling feature:

- Daily, weekly, or monthly scraping
- Custom cron expressions
- Email notifications on completion/failure

## Troubleshooting

### Common Issues

#### Chrome/ChromeDriver Issues

**Problem**: "ChromeDriver not found" or version mismatch errors

**Solutions**:

- Ensure Google Chrome is installed and up-to-date
- Clear WebDriverManager cache: Delete `~/.wdm` directory
- Run with admin privileges if permission errors occur

#### Network/Connection Issues

**Problem**: Timeout errors or connection failures

**Solutions**:

- Check internet connection
- Verify UniPage.net is accessible
- Increase timeout values in configuration
- Use VPN if site is geo-blocked

#### Memory Issues

**Problem**: Out of memory errors during large scraping operations

**Solutions**:

- Reduce batch size by scraping fewer countries at once
- Increase system RAM or virtual memory
- Close other applications during scraping

#### Permission Errors

**Problem**: Cannot write to output directory or log files

**Solutions**:

- Run command prompt as Administrator
- Check directory permissions
- Ensure output directory is not read-only

### Debug Mode

Enable detailed logging for troubleshooting:

```bash
python -m scraper.main --countries "Turkey" --log-level DEBUG
```

This will provide:

- Detailed HTTP request/response information
- Element selection details
- Step-by-step execution flow
- Performance timing information

### Log Analysis

Check `logs/app.log` for:

- Error messages with stack traces
- Warning messages about data quality
- Info messages about scraping progress
- Debug messages (if enabled)

### Getting Help

1. **Check Logs**: Always review `logs/app.log` first
2. **Verify Prerequisites**: Ensure all requirements are met
3. **Test with Single Country**: Start with one country to isolate issues
4. **Update Dependencies**: Run `pip install -r requirements.txt --upgrade`

### Performance Tips

- **Batch Processing**: Scrape countries in smaller batches for better stability
- **Resource Monitoring**: Monitor CPU and memory usage during execution
- **Network Optimization**: Use stable internet connection for consistent results
- **Regular Updates**: Keep Chrome and Python dependencies updated

## Project Structure

```
py_test/
├── scraper/
│   ├── main.py           # Main orchestration script
│   ├── navigator.py      # Web navigation logic
│   ├── extractor.py      # Data extraction logic
│   ├── writer.py         # JSON output handling
│   └── logger_config.py  # Logging configuration
├── requirements.txt      # Python dependencies
├── traycerai.yaml       # TraycerAI deployment config
├── unipage_data/        # Output directory (created automatically)
├── logs/                # Log files (created automatically)
└── README.md            # This file
```

## Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Test thoroughly
5. Submit a pull request

## License

[Add your license information here]
