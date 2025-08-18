import requests
import os
from dotenv import load_dotenv
from serpapi import GoogleSearch
import dateparser
import streamlit as st

# Load environment variables
load_dotenv()

# Retrieve secrets
NOTION_TOKEN = os.getenv("NOTION_TOKEN")
DATABASE_ID = os.getenv("DATABASE_ID")
PREDICTHQ_API_KEY = os.getenv("PREDICTHQ_API_KEY")
SERPAPI_API_KEY = os.getenv("SERPAPI_API_KEY")
MAKE_WEBHOOK_URL = os.getenv("MAKE_WEBHOOK_URL")

# Notion API headers
notion_headers = {
    "Authorization": f"Bearer {NOTION_TOKEN}",
    "Notion-Version": "2022-06-28",
    "Content-Type": "application/json",
}

def post_to_notion(payload):
     response = requests.post("https://api.notion.com/v1/pages", headers=notion_headers, json=payload)
     if response.status_code == 200:
          st.success(f"✅ Added: {payload['properties']['Name']['title'][0]['text']['content']}")
     else:
          st.error(f"❌ Failed: {response.text}")


# UI
st.title("Senda Notion Event Uploader 🎟️ ")
st.markdown("_This app uses the PredictHQ API & Serp API to find events in Spain and upload them to our Senda Notion database._")
st.write("Enter your keywords and dates below. Click the button to fetch and upload events to Notion.")
 
# Keywords Input
keywords_input = st.text_input("🔤 Keywords (comma-separated):", "networking, meetup, AI, venture, investment")
list_of_keywords = [kw.strip() for kw in keywords_input.split(",") if kw.strip()]

# Dates input
st.write("🗓️ Specify the date range for events:")
start_date = st.date_input("Start Date", value=None)
end_date = st.date_input("End Date", value=None)

# PredictHQ Search
all_phq_events = []

# Main code
if st.button("🚀 Populate Notion Database"):
     if not list_of_keywords:
          st.warning("⚠️ Please enter at least one keyword.")
     
     """ This section of the code does a Google search of events to complete the data collected from PredictHQ. 
     It only looks at events that have a start date in the future, 
     so it will not collect past events, and it wil only collect events of the current month """

     # Google Search Events using SerpAPI
     all_serpapi_events = []

     for keyword in list_of_keywords:
          st.write(f"🔍 Searching SerpAPI for: {keyword}")
          params = {
               "engine": "google_events",
               "q": f"{keyword} + Spain",
               "gl": "ES",
               "api_key": f"{SERPAPI_API_KEY}",
               "date": "month",
          }

          search = GoogleSearch(params)
          results = search.get_dict()
          serpapi_events = results.get("events_results", [])
          st.write(f"✅ Found {len(serpapi_events)} events for '{keyword}'")
          
          all_serpapi_events.extend(serpapi_events)

     print(f"\n📦 Total SerpAPI events collected: {len(all_serpapi_events)}")


     # Process and post SerpAPI events to Notion
     for event in all_serpapi_events:
          title = event.get("title", "Untitled Event")

          start_date_raw = event.get("date", {}).get("start_date") or event.get("date", {}).get("when", "")
          start_date_parsed = dateparser.parse(start_date_raw)
          if start_date_parsed:
               start_date = start_date_parsed.date().isoformat()  # '2025-08-06'
          else:
               st.error(f"⚠️ Could not parse date: {start_date_raw}")
               start_date = None

          address_list = event.get("address", [])
          address = ", ".join(address_list) if address_list else "Unknown"
          description = event.get("description", "No description provided") or ""
          google_link = event.get("link") or event.get("search_metadata", {}).get("google_url", "")


          make_payload = {
               "name": title,                         # string
               "location": address,                   # string
               "description": description[:2000],     # string
               "start_date": start_date or "",        # ISO string (or "")
               "review": "Review",                    # matches Notion Select option
               "event_link": google_link              # url string
               }

          headers = {"Content-Type": "application/json"}
          response = requests.post(MAKE_WEBHOOK_URL, json=make_payload, headers=headers)
          st.success(f"✅ Added: {title}")
          print("Status:", response.status_code)
          print("Response:", response.text)
          

           
