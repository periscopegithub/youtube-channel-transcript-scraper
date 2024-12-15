# YouTube Channel Transcript Scraper

This Python project allows you to scrape transcripts of videos from specified YouTube channels. The app utilizes the **[youtube-transcript-api](https://github.com/jdepoix/youtube-transcript-api)** and **[scrapetube](https://github.com/axelperret/scrapetube)** libraries to efficiently gather video metadata and transcripts.

Both libraries are open-source and distributed under the **MIT License**, so please make sure to acknowledge them accordingly.

---

## Purpose

The purpose of this project is to allow users to scrape **YouTube video transcripts** for videos in **preferred languages** from channels they specify. The transcripts are then saved as `.txt` files in the project directory, along with relevant metadata about each video. This helps with archiving and processing video content without needing manual transcription.

---

## Features

- Scrapes video metadata (such as title, upload date, and URL) from specified YouTube channels.
- Fetches transcripts in **preferred languages** (e.g., Traditional Chinese, Simplified Chinese, English).
- Saves video transcripts in **.txt** files while retaining HTML formatting (optional).
- Records metadata (video URLs, upload dates, scrape dates) in **CSV** files for each channel.
- Logs any errors or issues that occur during the scraping process.

---

## Usage of Libraries

- **[scrapetube](https://github.com/axelperret/scrapetube)**: A Python library that allows easy access to public YouTube channel videos without the need for authentication. This library is used to retrieve video metadata (URLs, titles, upload dates) for the specified channels.  

- **[youtube-transcript-api](https://github.com/jdepoix/youtube-transcript-api)**: This library is used to retrieve transcripts of YouTube videos. It supports multiple languages, including Traditional and Simplified Chinese, English, and more. The transcript is fetched for each video in the preferred language (if available).

---

## Python Version

This project is developed using **Python 3.9**.

---

## Installation

To set up the project, you'll need to install the necessary dependencies. The easiest way to install the required packages is by using **Conda** and **Pip**.

### 1. Set Up Conda Environment
First, create and activate a conda environment:
```bash
conda create -n <env_name> python=3.9 -y
conda activate <env_name>
```

### 2. Install Required Libraries
Install the necessary Python libraries using conda and pip:
```bash
conda install pandas pyyaml rich -y
pip install youtube-transcript-api scrapetube
```

### 3. Create Configuration File
You will need to create a `config.yaml` file in the project root directory. This file contains the settings for the scraper, including preferred languages, file naming options, and the list of channels to scrape.

#### config.yaml Template
Below is a template for the `config.yaml` file, which must be present in your project folder. You can customize it according to your needs.
```yaml
preferred_languages:
    - zh-HK    # Chinese (Hong Kong)
    - zh-CN    # Chinese (China)
    - zh-Hant  # Traditional Chinese
    - zh-Hans  # Simplified Chinese
    - en       # English

file_name_max_length: 30
file_name_timestamp: true
html_formatting: true

channels:
    - channel_1  # Example Channel 1
    - channel_2  # Example Channel 2
```

#### Explanation of Each Line in config.yaml
- `preferred_languages`: This list defines the languages in which the transcript will be scraped for each video. The list is ordered from most preferred to least preferred. If the transcript is available in one of these languages, it will be used. If the video does not have a transcript in one of the preferred languages, the script will try to fetch the transcript in English by default (if available).

    **Important**: According to the YouTube Transcript API documentation, the API tries to fetch the transcript based on the order of languages provided. If the preferred language is unavailable, it will fall back to other languages in the list.

- `file_name_max_length`: Defines the maximum length of the transcript file name. The file name will be truncated if it exceeds this length.

- `file_name_timestamp`: If set to true, a timestamp will be appended to the file name to ensure it is unique.

- `html_formatting`: If set to true, the script will preserve HTML formatting in the transcript (if available). Otherwise, plain text will be used.

- `channels`: This list contains the YouTube channel usernames you want to scrape. You can find the channel username from their YouTube URL (e.g., https://www.youtube.com/c/channel_1) or their channel pages. Use the username without the `@` symbol, as shown in the example.

---

## Directory Structure
Once the application has run, the following directory structure will be created:
```
project_folder/
│
├── channels/                      # Folder for storing channel data
│   ├── channel_1/                 # Folder for Channel 1
│   │   ├── channel_data.csv       # CSV file containing video metadata
│   │   ├── video_1.txt            # Transcript for Video 1
│   │   ├── video_2.txt            # Transcript for Video 2
│   │   └── ...                    # Additional video files
│   └── channel_2/                 # Folder for Channel 2
│       ├── channel_data.csv       # CSV file containing video metadata
│       ├── video_1.txt            # Transcript for Video 1
│       └── ...                    # Additional video files
├── config.yaml                    # Configuration file
├── logs/                          # Folder for log files
│   └── app.log                    # Log file capturing errors and warnings
└── README.md                      # Project's README file
```

- `channels/`: Contains a folder for each channel you scrape. Each folder will hold a CSV file with metadata about the videos and `.txt` files containing the transcripts.
- `logs/`: Contains a log file where errors and warnings are logged for later review.

#### CSV File in Each Channel Folder
In each channel folder, there will be a CSV file (`channel_data.csv`) containing the metadata for the scraped videos. The columns in the CSV file are as follows:

| Column Name | Description |
|-------------|-------------|
| Video URL   | The URL of the YouTube video |
| Video ID    | The unique ID of the YouTube video |
| Upload Date | The upload date of the video |
| Scrape Date | The date when the video was processed and scraped |
| Transcript  | The transcript of the video (if available) |

This file helps track which videos have been processed and whether the transcript was successfully scraped.

---

## Warning
Please note that this application relies on parts of the YouTube API that are not officially documented, meaning it may stop working if YouTube decides to change its web client or API. While every effort will be made to address any issues if they arise, you may encounter occasional disruptions. If that happens, please report the issue, and it will be resolved as quickly as possible.

---

## Known Issues
- **Missing Transcripts**: If a video does not have a transcript available in any of the preferred languages (or English), it will fail to scrape, and no transcript will be saved. The failure will be logged in the `app.log` file.

---

## License
This project is licensed under the MIT License. Please see the LICENSE file for more information.