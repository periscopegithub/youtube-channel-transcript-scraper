import os
import re
import logging
import yaml
import pandas as pd
from pathlib import Path
from youtube_transcript_api import YouTubeTranscriptApi, TooManyRequests
from youtube_transcript_api.formatters import TextFormatter
import scrapetube
from typing import Dict, List, Optional, Tuple

# --- Configuration and Logging ---
CONFIG_FILE = "config.yaml"
LOG_FILE = "logs/app.log"


def setup_logging() -> None:
    """Initialize logging configuration."""
    os.makedirs("logs", exist_ok=True)
    logging.basicConfig(
        filename=LOG_FILE,
        level=logging.INFO,
        format="%(asctime)s - %(levelname)s - %(message)s",
    )


def load_config() -> Dict:
    """Load and validate configuration from YAML file."""
    if not os.path.exists(CONFIG_FILE):
        raise FileNotFoundError(f"Configuration file {CONFIG_FILE} is missing.")

    with open(CONFIG_FILE, "r", encoding="utf-8") as f:
        config = yaml.safe_load(f)

    return {
        "preferred_languages": config.get("preferred_languages"),
        "html_formatting": config.get("html_formatting", True),
        "file_name_max_length": config.get("file_name_max_length", 30),
        "file_name_timestamp": config.get("file_name_timestamp", True),
        "channels": config.get("channels", []),
    }


# --- Helper Functions ---
def sanitize_name(name: str) -> str:
    """Sanitize folder or file names by removing special characters and spaces."""
    return re.sub(r"[^\w\s-]", "", name.strip().replace(" ", "_"))


def update_csv(file_path: Path, data: Dict) -> None:
    """Update CSV file with new data efficiently."""
    df = pd.DataFrame([data])
    if not os.path.exists(file_path):
        df.to_csv(file_path, index=False)
        return

    # Read only necessary columns for checking duplicates
    existing = pd.read_csv(file_path, usecols=["Video ID", "Status"])
    if data["Video ID"] not in existing["Video ID"].values:
        df.to_csv(file_path, mode="a", header=False, index=False)


def save_transcript(
    folder: Path, channel_username: str, video_name: str, transcript: str, config: Dict
) -> None:
    """Save transcript to individual file and master file."""
    file_name = sanitize_name(video_name)[: config["file_name_max_length"]]
    if config["file_name_timestamp"]:
        file_name += f"_{pd.Timestamp.now().strftime('%Y%m%d%H%M%S')}"

    # Save individual transcript
    file_path = folder / f"{file_name}.txt"
    with open(file_path, "w", encoding="utf-8") as f:
        f.write(transcript)

    # Append to master file
    master_file = folder / f"0_{channel_username}_master_transcripts.txt"
    with open(master_file, "a", encoding="utf-8") as f:
        f.write(f"\n<{file_name}>\n{transcript}\n</{file_name}>\n")


def process_video(video: Dict, channel_folder: Path, config: Dict) -> Tuple[Dict, bool]:
    """Process a single video and return its data and success status."""
    video_id = video["videoId"]
    video_url = f"https://www.youtube.com/watch?v={video_id}"
    video_title = (
        video.get("title", {}).get("runs", [{}])[0].get("text", "No Title Available")
    )

    video_data = {
        "Video URL": video_url,
        "Video ID": video_id,
        "Scrape Date": pd.Timestamp.now().strftime("%Y-%m-%d %H:%M:%S"),
        "Status": "PENDING",
    }

    try:
        transcript_text = YouTubeTranscriptApi.get_transcript(
            video_id,
            languages=(
                config["preferred_languages"] if config["preferred_languages"] else None
            ),
            preserve_formatting=config["html_formatting"],
        )

        formatter = TextFormatter()
        txt_formatted = formatter.format_transcript(transcript_text)
        save_transcript(channel_folder, video_title, video_title, txt_formatted, config)

        video_data["Status"] = "SUCCESS"
        return video_data, True

    except TooManyRequests:
        video_data["Status"] = "FAILED - Rate Limited"
        logging.warning(f"Rate limit reached for video {video_id}")
        return video_data, False

    except Exception as e:
        status = (
            "FAILED - Subtitles disabled"
            if "Subtitles are disabled" in str(e)
            else "FAILED"
        )
        video_data["Status"] = status
        logging.warning(f"Error processing video {video_id}: {str(e)}")
        return video_data, False


def process_channel(channel_username: str, output_folder: Path, config: Dict) -> None:
    """Process videos from a single YouTube channel."""
    try:
        videos = scrapetube.get_channel(channel_username=channel_username)
        if not videos:
            logging.warning(f"No videos found for channel {channel_username}")
            return

        channel_folder = output_folder / sanitize_name(channel_username)
        channel_folder.mkdir(parents=True, exist_ok=True)
        csv_path = channel_folder / "channel_data.csv"

        consecutive_failures = 0
        for video in videos:
            if consecutive_failures >= 5:
                logging.warning(
                    f"Stopping after 5 consecutive failures for {channel_username}"
                )
                break

            # Skip if video was previously processed successfully
            if os.path.exists(csv_path):
                existing = pd.read_csv(csv_path, usecols=["Video ID", "Status"])
                if video["videoId"] in existing["Video ID"].values:
                    if (
                        "SUCCESS"
                        in existing[existing["Video ID"] == video["videoId"]][
                            "Status"
                        ].values
                    ):
                        continue

            video_data, success = process_video(video, channel_folder, config)
            update_csv(csv_path, video_data)

            consecutive_failures = 0 if success else consecutive_failures + 1

    except Exception as e:
        logging.error(f"Error processing channel {channel_username}: {str(e)}")


def main() -> None:
    """Main execution function."""
    try:
        setup_logging()
        config = load_config()

        if not config["channels"]:
            logging.error("No channels found in configuration")
            return

        output_folder = Path("channels")
        output_folder.mkdir(exist_ok=True)

        for username in config["channels"]:
            process_channel(username, output_folder, config)

    except Exception as e:
        logging.error(f"Application error: {str(e)}")


if __name__ == "__main__":
    main()
