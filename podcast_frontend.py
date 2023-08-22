import streamlit as st
import requests
import modal
import json
import os
import re


def main():
    st.title("Podcast Dashboard")

    available_podcast_info = create_dict_from_json_files('.')

    # Logo
    st.sidebar.image("music-pod-summaries.jpg", use_column_width=True)

    # Left section - Input fields
    st.sidebar.header("Podcast RSS Feeds")

    # Dropdown box
    st.sidebar.subheader("Available Podcasts Feeds")
    selected_podcast = st.sidebar.selectbox("Select Podcast", options=available_podcast_info.keys(), index=1)

    if selected_podcast:

        podcast_info = available_podcast_info[selected_podcast]

        # Right section - Newsletter content
        st.header("Newsletter Content")

        # Display the podcast title
        st.subheader("Episode Title")
        st.write(podcast_info['podcast_details']['episode_title'])

        # Display the podcast summary and the cover image in a side-by-side layout
        col1, col2 = st.columns([7, 3])

        with col1:
            # Display the podcast episode summary
            st.subheader("Podcast Episode Summary")
            st.write(podcast_info['podcast_summary'])

        with col2:
            st.image(podcast_info['podcast_details']['episode_image'], caption="Podcast Cover", width=300,
                     use_column_width=True)

        # # Display the podcast guest and their details in a side-by-side layout
        # col3, col4 = st.columns([3, 7])

        # with col3:
        #     st.subheader("Podcast Guest")
        #     st.write(podcast_info['podcast_guest']['name'])

        # with col4:
        #     st.subheader("Podcast Guest Details")
        #     st.write(podcast_info["podcast_guest"]['summary'])

        # Display the five key moments
        st.subheader("Key Moments")
        key_moments = podcast_info['podcast_highlights']
        for moment in key_moments.split('\n'):
            st.markdown(
                f"<p style='margin-bottom: 5px;'>{moment}</p>", unsafe_allow_html=True)

    # User Input box
    st.sidebar.subheader("Add Your Own Podcast")
    url = st.sidebar.text_input("Link to Apple Podcast")

    process_button = st.sidebar.button("Process Podcast Feed")
    st.sidebar.markdown("**Note**: Podcast processing can take up to 5 minutes, please be patient.")

    if process_button:

        apple_podcast_link = url

        def extract_podcast_id(apple_podcast_link):

            # Extract the podcast ID from the Apple Podcast link using regular expression
            match = re.search(r'id(\d+)', apple_podcast_link)
            if match:
                return match.group(1)
            return None

        def get_rss_feed_url(apple_podcast_link):
            podcast_id = extract_podcast_id(apple_podcast_link)

            if podcast_id:
                lookup_url = f"https://itunes.apple.com/lookup?id={podcast_id}"
                response = requests.get(lookup_url)
                data = response.json()
    
                if "results" in data and len(data["results"]) > 0:
                    podcast_info = data["results"][0]
                    rss_feed_url = podcast_info.get("feedUrl")
                    return rss_feed_url
    
            return None

        rss_feed_url = get_rss_feed_url(apple_podcast_link)
        if rss_feed_url:
            print("RSS Feed URL:", rss_feed_url)
        else:
            print("RSS feed URL not found")

        url = rss_feed_url

    # Call the function to process the URLs and retrieve podcast guest information
    podcast_info = process_podcast_info(url)

    # Right section - Newsletter content
    st.header("Newsletter Content")

    # Display the podcast title
    st.subheader("Episode Title")
    st.write(podcast_info['podcast_details']['episode_title'])

    # Display the podcast summary and the cover image in a side-by-side layout
    col1, col2 = st.columns([7, 3])

    with col1:
        # Display the podcast episode summary
        st.subheader("Podcast Episode Summary")
        st.write(podcast_info['podcast_summary'])

    with col2:
        st.image(podcast_info['podcast_details']['episode_image'], caption="Podcast Cover", width=300,
                 use_column_width=True)

    # # Display the podcast guest and their details in a side-by-side layout
    # col3, col4 = st.columns([3, 7])

    # with col3:
    #     st.subheader("Podcast Guest")
    #     st.write(podcast_info['podcast_guest']['name'])

    # with col4:
    #     st.subheader("Podcast Guest Details")
    #     st.write(podcast_info["podcast_guest"]['summary'])

    # Display the five key moments
    st.subheader("Key Moments")
    key_moments = podcast_info['podcast_highlights']
    for moment in key_moments.split('\n'):
        st.markdown(
            f"<p style='margin-bottom: 5px;'>{moment}</p>", unsafe_allow_html=True)


def create_dict_from_json_files(folder_path):
    json_files = [f for f in os.listdir(folder_path) if f.endswith('.json')]
    data_dict = {}

    for file_name in json_files:
        file_path = os.path.join(folder_path, file_name)
        with open(file_path, 'r') as file:
            podcast_info = json.load(file)
            podcast_name = podcast_info['podcast_details']['podcast_title']
            # Process the file data as needed
            data_dict[podcast_name] = podcast_info

    return data_dict


def process_podcast_info(url):
    f = modal.Function.lookup("corise-podcast-project", "process_podcast")
    output = f.call(url, '/content/podcast/')
    return output


if __name__ == '__main__':
    main()
