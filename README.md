# UniPage.net University Scraper

A focused Python scraper that extracts comprehensive university information from [UniPage.net](https://www.unipage.net/en/study_countries) and returns data in a structured JSON format.

## Features

- **AI-Powered Extraction**: Uses DeepSeek AI to intelligently extract comprehensive university data
- **Structured Output**: Returns data in a detailed JSON format with all university information
- **Focused Approach**: Scrapes from the study countries page for accurate country-specific results
- **Comprehensive Data**: Extracts university name, type, location, rankings, tuition fees, and study programs

## Prerequisites

- **Python**: Version 3.8 or higher
- **Google Chrome**: Latest version
- **DeepSeek API Key**: For AI-powered data extraction

## Setup

### 1. Clone and Navigate
```bash
git clone <repository-url>
cd py_test
```

### 2. Create Virtual Environment
```bash
python -m venv venv
venv\Scripts\activate  # On Windows
# or
source venv/bin/activate  # On macOS/Linux
```

### 3. Install Dependencies
```bash
pip install -r requirements.txt
```

## Usage

### Basic Usage
```bash
python -m scraper.main --country "Turkey" --limit 1
```

### Command Line Options
- `--country`: Country to scrape universities from (default: Turkey)
- `--limit`: Number of universities to scrape for testing (default: 1)
- `--output`: Output JSON file (default: universities_data.json)

### Examples
```bash
# Scrape 1 university from Turkey (for testing)
python -m scraper.main --country "Turkey" --limit 1

# Scrape 3 universities from Germany
python -m scraper.main --country "Germany" --limit 3

# Custom output file
python -m scraper.main --country "USA" --limit 2 --output "usa_universities.json"
```

## Output Format

The scraper extracts comprehensive university data in this JSON structure:

```json
{
  "scraping_info": {
    "country": "Turkey",
    "total_universities_found": 50,
    "universities_scraped": 1,
    "timestamp": "2024-01-01T12:00:00"
  },
  "universities": [
    {
      "university": {
        "name": "Bilkent University",
        "type": "private non-profit",
        "location": {
          "country": "Turkey",
          "city": "Ankara"
        },
        "website": "http://www.bilkent.edu.tr/",
        "about": {
          "description": "University description...",
          "establishment_year": 1984,
          "students": {
            "total": 9961,
            "international": 521,
            "female_percentage": 46
          },
          "rankings": {
            "QS_World_University_Rankings_2025": 477,
            "THE_Ranking": 701,
            "by_subject": {
              "Engineering_And_Technology": {
                "QS_2024": 285
              }
            }
          },
          "degrees_offered": ["Bachelor", "Master", "Doctorate"]
        },
        "tuition_fees": {
          "academic_calendar": "Semesters",
          "calculation_period": "Per year",
          "bachelor": {
            "local": {
              "cost": 4165,
              "currency": "USD",
              "period": "year"
            },
            "foreign": {
              "cost": 14468,
              "currency": "USD",
              "period": "year"
            }
          },
          "financial_aid": "Yes",
          "additional_costs": ["accommodation", "transportation"],
          "website_for_details": "http://www.bilkent.edu.tr/"
        },
        "study_programs": [
          {
            "level": "Bachelor",
            "programs": [
              {
                "name": "Law",
                "details": {
                  "study_mode": "On campus",
                  "study_form": "Full-time",
                  "duration_months": 48,
                  "exams": ["IELTS", "TOEFL"],
                  "study_field": "Law",
                  "exam_scores": {
                    "IELTS": 6.5,
                    "TOEFL_iBT": 87
                  },
                  "program_page": "https://catalog.bilkent.edu.tr/dep/d45.html",
                  "price": {
                    "cost": 16945,
                    "currency": "USD",
                    "period": "year"
                  }
                }
              }
            ]
          }
        ]
      },
      "extraction_metadata": {
        "source_url": "https://www.unipage.net/en/123/bilkent-university",
        "extracted_at": "2024-01-01T12:00:00",
        "extractor_version": "1.0"
      }
    }
  ]
}
```

## Project Structure

```
py_test/
├── scraper/
│   ├── main.py           # Main entry point
│   ├── navigator.py      # Web navigation logic
│   ├── extractor.py      # AI-powered data extraction
│   ├── writer.py         # JSON output handling
│   ├── logger_config.py  # Logging configuration
│   └── __init__.py       # Package initialization
├── requirements.txt      # Python dependencies
├── README.md            # This file
└── output/              # Generated output directory
```

## How It Works

1. **Navigation**: Opens https://www.unipage.net/en/study_countries
2. **Country Selection**: Finds and navigates to the specified country's university page
3. **University Discovery**: Extracts all university links from the country page
4. **Data Extraction**: Uses AI to extract comprehensive data from each university page
5. **Output**: Saves structured data in the specified JSON format

## API Configuration

The scraper uses DeepSeek AI for intelligent data extraction. The API key is currently configured in the code:

```python
api_key = "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"
```

## Logging

Logs are automatically created in the `logs/` directory with detailed information about:
- Navigation progress
- Data extraction results
- Any errors or warnings

## Troubleshooting

### Common Issues

1. **Chrome not found**: Install Google Chrome browser
2. **API errors**: Check DeepSeek API key and internet connection
3. **No universities found**: Verify country name spelling
4. **Timeout errors**: Increase timeout or check internet connection

### Debug Mode

For detailed debugging, check the log files in the `logs/` directory.

## Testing

Start with a single university to verify the extraction:

```bash
python -m scraper.main --country "Turkey" --limit 1
```

Check the output file and logs to ensure data quality before scaling up.

## License

[Add your license information here]
