#!/usr/bin/python3
import requests
import json
import time
import sys
import re
import xml.etree.ElementTree as ET
from xml.dom import minidom

from datetime import datetime, timedelta, timezone
from pydantic import BaseModel, Field, parse_obj_as
from typing import Any, List, Optional

# --- Pydantic Models (No changes needed here) ---
class Action(BaseModel):
    uri: str

class Container(BaseModel):
     actions: List[Action]

class ResultObj(BaseModel):
    containers: Optional[List[Container]] = None

class RetrieveItems(BaseModel):
     resultObj: ResultObj

class RaceEmfAttributes(BaseModel):
    Meeting_Name: str
    Series: str
    sessionEndDate: int
    sessionStartDate: int

class RaceMetadata(BaseModel):
    emfAttributes: RaceEmfAttributes
    longDescription: str
    title: str

class RaceEvent(BaseModel):
    metadata: RaceMetadata

class RaceContainer(BaseModel):
    eventName: Optional[str] = None
    events: Optional[List[RaceEvent]] = None 

class RaceResultObj(BaseModel):
    containers: List[RaceContainer]

class RaceRetrieveItems(BaseModel):
    resultObj: RaceResultObj

class RaceContainer(BaseModel):
    layout: str
    retrieveItems: RaceRetrieveItems

class RaceResultObj(BaseModel):
    containers: List[RaceContainer]

class RaceModel(BaseModel):
    resultObj: Optional[RaceResultObj] = None

class ContainerRaceURI(BaseModel):
     retrieveItems: RetrieveItems

class ResultObjRaceURI(BaseModel):
    containers: List[ContainerRaceURI]

class RaceURI(BaseModel):
     resultObj: Optional[ResultObjRaceURI] = None

class ActionSeasonUri(BaseModel):
    href: str

class ContainerSeasonUri(BaseModel):
    actions: List[ActionSeasonUri]

class ResultObjSeasonUri(BaseModel):
    containers: Optional[List[ContainerSeasonUri]] = None

class WebsiteLinks(BaseModel):
    resultObj: Optional[ResultObjSeasonUri]

# --- NEW: XMLTV Generation Functions ---

def create_xmltv_structure():
    """Creates the root <tv> element and adds the channel definition."""
    root = ET.Element("tv")
    root.set("generator-info-name", "F1TV EPG Generator")

    channel = ET.SubElement(root, "channel")
    channel.set("id", "f1tv")
    
    display_name = ET.SubElement(channel, "display-name")
    display_name.text = "F1TV"
    
    return root

def add_programme_to_xmltv(root, start_time, end_time, title, description, category):
    """Adds a <programme> element to the XMLTV root."""
    # Ensure times are in UTC for correct formatting
    start_utc = start_time.astimezone(timezone.utc)
    end_utc = end_time.astimezone(timezone.utc)
    
    # Format times to XMLTV standard (e.g., 20240518140000 +0000)
    start_str = start_utc.strftime('%Y%m%d%H%M%S %z')
    end_str = end_utc.strftime('%Y%m%d%H%M%S %z')

    programme = ET.SubElement(root, "programme")
    programme.set("start", start_str)
    programme.set("stop", end_str)
    programme.set("channel", "f1tv")

    # Add title
    title_elem = ET.SubElement(programme, "title")
    title_elem.set("lang", "en")
    title_elem.text = title

    # Add description
    desc_elem = ET.SubElement(programme, "desc")
    desc_elem.set("lang", "en")
    desc_elem.text = description

    # Add category
    cat_elem = ET.SubElement(programme, "category")
    cat_elem.set("lang", "en")
    cat_elem.text = category

def write_xmltv_file(root, filename):
    """Writes the ElementTree to a file in a readable format."""
    rough_string = ET.tostring(root, 'utf-8')
    reparsed = minidom.parseString(rough_string)
    pretty_xml = reparsed.toprettyxml(indent="  ", encoding="utf-8")

    with open(filename, 'wb') as f:
        f.write(pretty_xml)
    print(f"Successfully generated EPG file: {filename}")

# --- Data Fetching and Parsing Functions (Largely Unchanged) ---

def extract_season_id():
    base_uri = "https://f1tv.formula1.com/2.0/A/ENG/WEB_DASH/ALL/MENU/Anonymous/12"
    try:
        website_links = requests.get(base_uri).json()
    except requests.exceptions.RequestException as e:
        print(f"Error fetching season ID: {e}")
        sys.exit(1)
    
    website_links_obj = WebsiteLinks(**website_links)

    if website_links_obj.resultObj and website_links_obj.resultObj.containers:
        for container in website_links_obj.resultObj.containers:
            for action in container.actions:
                href = action.href
                match = re.search(r'/page/(\d+)/', href)
                if match:
                    season_id = match.group(1)
                    return f"https://f1tv.formula1.com/2.0/A/ENG/WEB_DASH/ALL/PAGE/{season_id}/Anonymous/12"
    
    print("Could not find the season ID. Exiting.")
    sys.exit(1)

def epoch_to_date(epoch):
    """Converts epoch milliseconds to a datetime object."""
    return datetime.fromtimestamp(epoch / 1000, tz=timezone.utc)

def get_grand_prix_uris(season_uri):
    try:
        response = requests.get(season_uri)
        response.raise_for_status()
        upcoming_races = response.json()
    except requests.exceptions.RequestException as e:
        print(f"Error fetching grand prix URIs from {season_uri}: {e}")
        return []

    outside_containers = RaceURI(**upcoming_races)
    race_uris = []

    if outside_containers.resultObj:
        for outside_container in outside_containers.resultObj.containers:
            if outside_container.retrieveItems.resultObj.containers is not None:
                for inside_container in outside_container.retrieveItems.resultObj.containers:
                    for action in inside_container.actions:
                        race_uri = 'https://f1tv.formula1.com' + action.uri
                        race_uris.append(race_uri)
    return race_uris

def get_grand_prix_events(race_uris, xml_root):
    """Retrieves event details and adds them to the XMLTV structure."""
    for race_uri in race_uris:
        try:
            response = requests.get(race_uri)
            response.raise_for_status()
            event_details = response.json()
        except requests.exceptions.RequestException as e:
            print(f"Warning: Could not fetch details for {race_uri}. Skipping. Error: {e}")
            continue

        outside_containers = RaceModel(**event_details)
        if not outside_containers.resultObj:
            continue

        for containers in outside_containers.resultObj.containers:
            if containers.layout == 'interactive_schedule':
                for events_containers in containers.retrieveItems.resultObj.containers:
                    if events_containers.eventName == 'ALL' and events_containers.events:
                        for event in events_containers.events:
                            meta = event.metadata
                            attrs = meta.emfAttributes
                            
                            event_name = attrs.Meeting_Name
                            series = attrs.Series.title()
                            long_desc = meta.longDescription

                            # Determine the session title
                            if '#' in long_desc and 'Show' not in meta.title:
                                session = meta.title
                            elif '#' in long_desc and 'Show' in meta.title:
                                session = meta.title
                                series = 'Formula 1' # Override series for special shows
                            else:
                                session = long_desc # Fallback to long description for title
                            
                            session_start = epoch_to_date(attrs.sessionStartDate)
                            session_end = epoch_to_date(attrs.sessionEndDate)
                            
                            # Construct full title for the EPG
                            full_title = f"{series}: {session}"
                            description = f"{event_name} - {session}"
                            
                            # Add the event to our XML file
                            add_programme_to_xmltv(
                                root=xml_root,
                                start_time=session_start,
                                end_time=session_end,
                                title=full_title,
                                description=description,
                                category=series
                            )

if __name__ == "__main__":
    # 1. Create the basic XMLTV structure with channel info
    xmltv_root = create_xmltv_structure()

    # 2. Extract the main URI for the current season
    print("Fetching season data...")
    season_uri = extract_season_id()
    
    # 3. Get URIs for each Grand Prix in the season
    print(f"Found season URI. Fetching all event URIs...")
    race_uris = get_grand_prix_uris(season_uri)
    print(f"Found {len(race_uris)} event groups.")

    # 4. Get details for each session and add to the XMLTV structure
    print("Processing events and building EPG...")
    get_grand_prix_events(race_uris, xmltv_root)
    
    # 5. Write the final XML to the guide.xml file
    write_xmltv_file(xmltv_root, "guide.xml")
