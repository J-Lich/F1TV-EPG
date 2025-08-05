# F1TV to XMLTV EPG Generator

![Python](https://img.shields.io/badge/python-3.8+-blue.svg)

A Python script to fetch the complete F1TV event schedule and generate a standards-compliant XMLTV file (`.xml`) for use as an Electronic Program Guide (EPG) in IPTV systems.

This project is a modification of an original script written by [Plebster on Gitlab](https://gitlab.com/Plebster/f1tv/) designed to create `.ics` calendar files. It has been repurposed to serve the IPTV community by generating a guide that can be imported into EPG-aware clients like PVRs and media centers.

## Key Features

-   **Fetches Full Season Data:** Pulls the schedule for all sessions (Practice, Qualifying, Sprint, Race) for Formula 1, F2, F3, and Porsche Supercup.
-   **Generates XMLTV Format:** Creates a `guide.xml` file with program details, including titles, descriptions, and start/end times.
-   **Customizable Channel Info:** Allows you to set the channel ID, display name, and output file path via command-line arguments.
-   **No Dependencies (beyond standard libraries):** The core logic for XML generation uses Python's built-in `xml.etree.ElementTree`. It only requires the `requests` library for API calls.

## Background & Key Changes

This script was originally created to pull the F1TV schedule and add the events to a personal calendar using the `.ics` format. While useful, the data is also perfectly suited for an EPG.

The key changes from the original concept are:

-   **Output Format:** The core logic was switched from the `icalendar` library to Python's native `xml.etree.ElementTree` to build an XMLTV-compliant document.
-   **Data Structure:** Instead of creating `VEVENT` entries for a calendar, the script now generates `<programme>` and `<channel>` tags.
-   **User Input:** Command-line argument parsing (`argparse`) was added to allow users to easily customize the channel ID, name, and output file without editing the code.
-   **Focus:** The goal shifted from personal calendar management to providing a functional EPG source for media systems.

# EPG Source Link: [https://raw.githubusercontent.com/J-Lich/F1TV-EPG/refs/heads/main/guide.xml](https://raw.githubusercontent.com/J-Lich/F1TV-EPG/refs/heads/main/guide.xml)

## Usage

You can run the script with or without command-line arguments. If no arguments are provided, it will use default values.

### Basic Execution (with defaults)

```bash
python f1tv_epg.py
```

This will generate a file named guide.xml in the same directory with the following channel details:
- Channel ID: <mark>**f1tv**</mark>
- Channel Name: <mark>**F1TV**</mark>

### Custom Execution (with arguments)
You can specify a custom channel ID, channel name, and output file/path.

```bash
python f1tv_epg.py --id "MyF1" --name "My Formula 1 Channel" --output "/path/to/my/epg.xml"
```

#### Arguments:
* --id: The channel ID to be used in the XMLTV file (e.g., MyF1.tv).
* --name: The display name for the channel (e.g., My Formula 1 Channel).
* --output: The full path and filename for the output file (e.g., /home/user/guides/f1_guide.xml).

## Example Output (guide.xml)
The generated XML file will have the following structure:

```xml
<?xml version="1.0" encoding="utf-8"?>
<tv generator-info-name="F1TV EPG Generator">
  <channel id="f1tv">
    <display-name>F1TV</display-name>
  </channel>
  <programme start="20240830133000 +0000" stop="20240830143000 +0000" channel="f1tv">
    <title lang="en">Formula 1: Practice 1</title>
    <desc lang="en">FORMULA 1 HEINEKEN DUTCH GRAND PRIX 2024 - Practice 1</desc>
    <category lang="en">Formula 1</category>
  </programme>
  <programme start="20240830170000 +0000" stop="20240830180000 +0000" channel="f1tv">
    <title lang="en">Formula 1: Qualifying</title>
    <desc lang="en">FORMULA 1 HEINEKEN DUTCH GRAND PRIX 2024 - Qualifying</desc>
    <category lang="en">Formula 1</category>
  </programme>
  <!-- ... more events ... -->
</tv>
```

## Dependencies
- requests
- pydantic

You can install them using pip:

```bash
pip install requests pydantic
```
