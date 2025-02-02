import os
import re
import logging
import yaml
import pandas as pd
from pathlib import Path
from youtube_transcript_api import YouTubeTranscriptApi, TooManyRequests
from youtube_transcript_api.formatters import TextFormatter
import scrapetube

# --- Configuration and Logging ---
CONFIG_FILE = "config.yaml"
LOG_FILE = "logs/app.log"

# Set up logging
os.makedirs("logs", exist_ok=True)
logging.basicConfig(
    filename=LOG_FILE,
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s",
)

# Load configuration
if not os.path.exists(CONFIG_FILE):
    logging.error(f"Configuration file {CONFIG_FILE} is missing.")
    exit(1)

with open(CONFIG_FILE, "r", encoding="utf-8") as f:
    config = yaml.safe_load(f)

PREFERRED_LANGUAGES = config.get("preferred_languages", None)
HTML_FORMATTING = config.get("html_formatting", True)
FILE_NAME_MAX_LENGTH = config.get("file_name_max_length", 30)
FILE_NAME_TIMESTAMP = config.get("file_name_timestamp", True)


# --- Helper Functions ---
def sanitize_name(name):
    """Sanitize folder or file names by removing special characters and spaces."""
    return re.sub(r"[^\w\s\u4e00-\u9fff]", "", name.strip().replace(" ", "_"))


def append_to_csv(file_path, data):
    """Append data to a CSV file, creating it if it doesn't exist."""
    columns = ["Video URL", "Video ID", "Scrape Date", "Status"]
    df = pd.DataFrame(data, columns=columns)
    if not os.path.exists(file_path):
        df.to_csv(file_path, index=False)
    else:
        existing = pd.read_csv(file_path)
        combined = pd.concat([existing, df]).drop_duplicates(subset=["Video ID"])
        combined.to_csv(file_path, index=False)


def save_transcript_txt(folder, video_name, transcript):
    """Save the transcript as a .txt file and append to master file."""
    # Save individual transcript file
    file_name = sanitize_name(video_name)[:FILE_NAME_MAX_LENGTH]
    if FILE_NAME_TIMESTAMP:
        file_name += f"_{pd.Timestamp.now().strftime('%Y%m%d%H%M%S')}"
    file_path = folder / f"{file_name}.txt"

    # Save to individual file
    with open(file_path, "w", encoding="utf-8") as f:
        f.write(transcript)

    # Append to master file
    master_file = folder / "master_transcripts.txt"
    with open(master_file, "a", encoding="utf-8") as f:
        f.write(f"\n<{file_name}>\n")
        f.write(transcript)
        f.write(f"\n</{file_name}>\n")


# --- Main Workflow ---
def process_channel(channel_username, output_folder):
    formatter = TextFormatter()
    """Process a single YouTube channel."""
    try:
        # Scrape video data
        videos = scrapetube.get_channel(channel_username=channel_username)
        if not videos:
            logging.warning(
                f"No videos found for channel {channel_username}. Skipping."
            )
            return

        channel_name = sanitize_name(channel_username)
        channel_folder = output_folder / channel_name
        channel_folder.mkdir(parents=True, exist_ok=True)
        csv_path = channel_folder / "channel_data.csv"

        video_details = []
        video_ids = []

        for video in videos:
            # print(video)
            video_id = video["videoId"]
            video_url = f"https://www.youtube.com/watch?v={video_id}"
            video_title = (
                video.get("title", {})
                .get("runs", [{}])[0]
                .get("text", "No Title Available")
            )
            # upload_date = video.get("publishedTimeText", {}).get(
            #     "simpleText", "Unknown Date"
            # )

            video_data = {
                "Video URL": video_url,
                "Video ID": video_id,
                # "Upload Date": upload_date,
                "Scrape Date": pd.Timestamp.now().strftime("%Y-%m-%d %H:%M:%S"),
                "Status": "PENDING",
            }

            # Check for previously processed or failed videos
            if os.path.exists(csv_path):
                existing_data = pd.read_csv(csv_path)
                if video_id in existing_data["Video ID"].values:
                    existing_row = existing_data[
                        existing_data["Video ID"] == video_id
                    ].iloc[0]
                    if existing_row["Status"] == "FAILED":
                        logging.info(f"Skipping known failed video: {video_id}")
                    elif existing_row["Status"] == "SUCCESS":
                        logging.info(f"Skipping previously processed video: {video_id}")
                    continue

            try:
                if PREFERRED_LANGUAGES:  # Check if preferred languages are defined
                    transcript_text = YouTubeTranscriptApi.get_transcript(
                        video_id,
                        languages=PREFERRED_LANGUAGES,
                        preserve_formatting=HTML_FORMATTING,
                    )
                else:  # Use default transcript fetching method if no preferred languages
                    transcript_text = YouTubeTranscriptApi.get_transcript(
                        video_id, preserve_formatting=HTML_FORMATTING
                    )

                # Format the transcript
                txt_formatted = formatter.format_transcript(transcript_text)
                video_data["Status"] = "SUCCESS"

                # Save transcript to file if successful
                save_transcript_txt(channel_folder, video_title, txt_formatted)
                logging.info(f"Processed video: {video_id}")

            except TooManyRequests:
                logging.warning(
                    f"Too many requests made for video {video_id}. Rate limit reached."
                )
                video_data["Status"] = "FAILED"
                break  # Exit loop to avoid too many retries
            except Exception as e:
                error_msg = str(e)
                if "Subtitles are disabled for this video" in error_msg:
                    logging.warning(f"Subtitles are disabled for video {video_id}")
                    video_data["Status"] = "FAILED - Subtitles disabled"
                else:
                    logging.warning(
                        f"Error in transcript fetching for video {video_id}: {error_msg}"
                    )
                    video_data["Status"] = "FAILED"  # Mark as failed attempt

            # Record both successful and failed attempts in CSV
            append_to_csv(csv_path, [video_data])

            video_ids.append(video_id)
            video_details.append(
                (
                    video_data,
                    channel_folder,
                    video.get("title", {}).get("simpleText", "unknown_video"),
                )
            )

    except Exception as e:
        logging.error(f"Error processing channel {channel_username}: {e}")


# --- Entry Point ---
def main():
    output_folder = Path("channels")
    output_folder.mkdir(exist_ok=True)

    # Read channel usernames from the config file
    channels = config.get("channels", [])
    if not channels:
        logging.error("No channels found in the configuration file.")
        exit(1)

    for username in channels:
        process_channel(username, output_folder)


if __name__ == "__main__":
    main()
