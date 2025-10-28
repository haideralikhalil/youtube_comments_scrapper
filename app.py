import os
import re
import json
import openpyxl
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError
from openpyxl import Workbook
import streamlit as st
from PIL import Image
import requests
from io import BytesIO

# Set up the YouTube Data API client
API_KEY = "AIzaSyCQJ3NGuAae6RpPhJUuq7u5O0IngnETUbI"
youtube = build("youtube", "v3", developerKey=API_KEY)



def get_video_comments(video_id):
    """
    Retrieves comments from a YouTube video using its video_id.
    """
    comments = []
    user_ids = []
    timestamps = []
    try:
        response = youtube.commentThreads().list(
            part="snippet",
            videoId=video_id,
            textFormat="plainText",
            maxResults=100
        ).execute()

        while response:
            for item in response["items"]:
                comment = item["snippet"]["topLevelComment"]["snippet"]["textDisplay"]
                user_id = item["snippet"]["topLevelComment"]["snippet"]["authorChannelId"]["value"]
                timestamp = item["snippet"]["topLevelComment"]["snippet"]["publishedAt"]

                comments.append(comment)
                user_ids.append(user_id)
                timestamps.append(timestamp)

            if "nextPageToken" in response:
                response = youtube.commentThreads().list(
                    part="snippet",
                    videoId=video_id,
                    pageToken=response["nextPageToken"],
                    textFormat="plainText",
                    maxResults=100
                ).execute()
            else:
                break

    except HttpError as e:
        st.error(f"An HTTP error occurred: {e.resp.status} - {e.content}")
    return comments, user_ids, timestamps


def save_comments_to_excel(comments, filename):
    """
    Saves the comments to an Excel file.
    """
    workbook = Workbook()
    sheet = workbook.active
    
    sheet.append(["Comments", "User IDs", "Timestamps"])

    for comment, user_id, timestamp in zip(comments, user_ids, timestamps):
        sheet.append([comment, user_id, timestamp])
    workbook.save(filename)

# ---------- main ----------------

st.title("YouTube Video Comment Scrapper")
st.write("Provide YouTube Video URL and I will give you give all comments in Excel File. Super Easy!")
link = 'Developed by [Haider Ali](https://haiderkhalil.com/)'
st.markdown(link, unsafe_allow_html=True)

video_url = st.text_input("YouTube Video URL") or "https://www.youtube.com/watch?v=OwGsXbsIXEo"
button_disabled = len(video_url.strip()) == 0
button_clicked = st.button("Get Comments", disabled=button_disabled)

 # ############### BUTTON CLICKED #####################

if button_clicked:
    # video_id = YouTube(video_url).video_id
    video_id = re.search(r"v=([^&]+)", video_url).group(1)
    thumbnail_url = f"https://img.youtube.com/vi/{video_id}/maxresdefault.jpg"

    response = requests.get(thumbnail_url)

    img = Image.open(BytesIO(response.content))
    st.image(img)

    with st.spinner('Reading Video Comments! Be patient please...'):
        # comments = get_video_comments(video_id)
        comments, user_ids, timestamps = get_video_comments(video_id)
        if comments:
            filename = "youtube_comments.xlsx"
            save_comments_to_excel(comments, filename)
            # st.success(f"Comments saved to {os.path.abspath(filename)}")
            st.success("Comments Grapped!")
            with open(filename, "rb") as file:
                file_contents = file.read()
            st.download_button(
                    label="Download Excel File",
                    data=file_contents,
                    file_name=filename,
                    mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
                )

        else:
            st.warning("No comments found for the video.")
