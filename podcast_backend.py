from pathlib import Path
import feedparser
import subprocess
import wikipedia
import requests
import whisper
import openai
import modal
import json
import os
import re


def download_whisper():
    # Load the Whisper model
    print("Download the Whisper model")

    # Perform download only once and save to Container storage
    whisper._download(whisper._MODELS["medium"], '/content/podcast/', False)


stub = modal.Stub("podcast-project")
env_image = modal.Image.debian_slim().pip_install(
    "feedparser",
    "https://github.com/openai/whisper/archive/9f70a352f9f8630ab3aa0d06af5cb9532bd8c21d.tar.gz",
    "requests",
    "ffmpeg",
    "openai",
    "tiktoken",
    "wikipedia",
    "ffmpeg-python").apt_install("ffmpeg").run_function(download_whisper)


@stub.function(image=env_image, gpu="any", timeout=600)
def get_transcribe_podcast(rss_url, local_path):
    print("Starting Podcast Transcription Function")
    print("Feed URL: ", rss_url)
    print("Local Path:", local_path)

    # Read from the RSS Feed URL
    intelligence_feed = feedparser.parse(rss_url)
    podcast_title = intelligence_feed['feed']['title']
    episode_title = intelligence_feed.entries[0]['title']
    episode_image = intelligence_feed['feed']['image'].href
    episode_url = 'Error'
    for item in intelligence_feed.entries[0].links:
        if item['type'] == 'audio/mpeg':
            episode_url = item.href
    episode_name = "full_podcast_episode.mp3"
    print("RSS URL read and episode URL: ", episode_url)

    # Download the podcast episode by parsing the RSS feed
    p = Path(local_path)
    p.mkdir(exist_ok=True)

    print("Downloading the podcast episode")
    with requests.get(episode_url, stream=True) as r:
        r.raise_for_status()
        episode_path = p.joinpath(episode_name)
        with open(episode_path, 'wb') as f:
            for chunk in r.iter_content(chunk_size=8192):
                f.write(chunk)

    print("Podcast Episode downloaded")

    # CUSTOM: Trim the full_podcast_episode down to 28 minutes for podcast_episode
    input_mp3 = local_path + 'full_podcast_episode.mp3'
    output_mp3 = local_path + 'podcast_episode.mp3'
    ffmpeg_command = [
        'ffmpeg',  # The FFmpeg executable
        '-i', input_mp3,  # Input file path
        '-ss', '00:00:00',  # Start trimming from the beginning
        '-t', '00:28:00',  # Trim 28 minutes
        '-y',  # Overwrite output file if it already exists
        '-c:v', 'copy',  # Copy the video codec (if present)
        '-c:a', 'copy',  # Copy the audio codec
        output_mp3  # Output file path
    ]
    subprocess.run(ffmpeg_command)

    # CUSTOM: Check the length of the shortened podcast_episode.mp3
    ffprobe_command = [
        'ffprobe',  # The FFprobe executable
        '-i', output_mp3,  # Input file path
        '-show_entries', 'format=duration',  # Show only the duration information
        '-v', 'error',  # Set error log level to suppress unnecessary output
        '-of', 'default=noprint_wrappers=1:nokey=1'  # Output format settings
    ]
    duration_output = subprocess.check_output(ffprobe_command, stderr=subprocess.STDOUT)
    duration_seconds = float(duration_output)
    print(f"Duration of {output_mp3}: {duration_seconds:.2f} seconds")
    duration_minutes = int(duration_seconds // 60)
    duration_seconds %= 60
    print(f"Duration: {duration_minutes} minutes and {duration_seconds:.2f} seconds")

    # CUSTOM: Rename the output to podcast_episode for next steps
    episode_name = 'podcast_episode.mp3'

    # Load the Whisper model

    # Load model from saved location
    print("Load the Whisper model")
    model = whisper.load_model('medium', device='cuda', download_root='/content/podcast/')

    # Perform the transcription
    print("Starting podcast transcription")
    result = model.transcribe(local_path + episode_name)

    # Return the transcribed text
    print("Podcast transcription completed, returning results...")
    output = {'podcast_title': podcast_title,
              'episode_title': episode_title,
              'episode_image': episode_image,
              'episode_transcript': result['text']}
    return output


@stub.function(image=env_image, secret=modal.Secret.from_name("my-openai-secret"))
def get_podcast_summary(podcast_transcript):
    instruct_prompt = """
    Below is the transcript of a podcast episode. Please provide a concise yet comprehensive summary that captures the 
    main points, key discussions, and any notable insights or takeaways.

    How to perform this task:
    First, break the transcript into logical sections based on topic or theme. Then, generate a concise summary for 
    each section. Finally, combine these section summaries into an overarching summary of the entire podcast episode. 
    The combined summary is what you should return back to me.

    Things to focus on and include in your final summary:
    -Identify the main speakers or participants in the podcast. For each participant, identify what organization they 
    belong to (if any) and what their title is. Then highlight their primary arguments, insights, or contributions. 
    Then, provide a comprehensive summary that captures the essence of their discussions. In your identification of 
    speakers, you should be sure to separate who is being spoken about versus who is actually speaking (as a guest or 
    host) on the podcast. A name being mentioned in the podcast does not automatically 
    mean they are on the podcast itself.
    -Extract the key insights, theories, steps, revelations, opinions, etc discussed in the podcast. Ensure that the 
    summary provides a clear roadmap for listeners who want to implement the advice or insights shared.
    -Identify any controversial or heavily debated points in the podcast. Summarize the various perspectives presented, 
    ensuring a balanced representation of the discussion.
    -Along with a content summary, describe the overall mood or tone of the podcast. Were there moments of tension, 
    humor, or any other notable ambiance details?


    Here is the podcast transcript:
    """
    request = instruct_prompt + podcast_transcript
    chat_output = openai.ChatCompletion.create(model="gpt-3.5-turbo-16k",
                                               messages=[
                                                   {"role": "system", "content": "You are a helpful assistant."},
                                                   {"role": "user", "content": request}
                                                        ]
                                               )
    podcast_summary = chat_output.choices[0].message.content
    print("Podcast summary is:", podcast_summary[:500])
    return podcast_summary


@stub.function(image=env_image, secret=modal.Secret.from_name("my-openai-secret"))
def get_podcast_guest(podcast_transcript):
    request = podcast_transcript[:5000]
    completion = openai.ChatCompletion.create(
        model="gpt-3.5-turbo",
        messages=[{"role": "user", "content": request}],
        functions=[
            {
                "name": "get_podcast_host_information",
                "description": "Get information on the podcast hosts using their full name and the name of the "
                               "organization they are part of to search for them on Wikipedia or Google",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "guest_name": {
                            "type": "string",
                            "description": "The full name of the host who is speaking in the podcast",
                        },
                        "unit": {"type": "string"},
                    },
                    "required": ["guest_name"],
                },
            }
        ],
        function_call={"name": "get_podcast_host_information"}
    )
    podcast_guest = ""
    response_message = completion["choices"][0]["message"]
    if response_message.get("function_call"):
        function_name = response_message["function_call"]["name"]
        function_args = json.loads(response_message["function_call"]["arguments"])
        podcast_guest = function_args.get("guest_name")

    print("Podcast guest is:", podcast_guest)
    return podcast_guest


@stub.function(image=env_image, secret=modal.Secret.from_name("my-openai-secret"))
def get_podcast_highlights(podcast_transcript):
    instruct_prompt = """
    Below is the transcript of a podcast episode. Please provide 3 quotes from the transcription that stand out.

    How to perform this task:
    Identify any controversial or heavily debated points in the podcast. Quote the speaker's name and what they said 
    that may be considered a hot take.

    Things to focus on and include in these quotes:
    -Do not give a reason for choosing each quote, only return the quote and speaker's name.

    Here is the podcast transcript:
    """

    request = instruct_prompt + podcast_transcript
    chat_output = openai.ChatCompletion.create(model="gpt-3.5-turbo-16k",
                                               messages=[
                                                   {"role": "system", "content": "You are a helpful assistant."},
                                                   {"role": "user", "content": request}
                                                        ]
                                               )
    podcast_highlights = chat_output.choices[0].message.content
    print("Podcast highlights are:", podcast_highlights)
    return podcast_highlights


@stub.function(image=env_image, secret=modal.Secret.from_name("my-openai-secret"), timeout=1200)
def process_podcast(url, path):
    output = {}
    podcast_details = get_transcribe_podcast.call(url, path)
    podcast_summary = get_podcast_summary.call(podcast_details['episode_transcript'])
    podcast_guest = get_podcast_guest.call(podcast_details['episode_transcript'])
    podcast_highlights = get_podcast_highlights.call(podcast_details['episode_transcript'])
    output['podcast_details'] = podcast_details
    output['podcast_summary'] = podcast_summary
    output['podcast_guest'] = podcast_guest
    output['podcast_highlights'] = podcast_highlights
    return output


@stub.local_entrypoint()
def test_method(url, path):
    podcast_details = get_transcribe_podcast.call(url, path)
    print("Podcast Summary: ", get_podcast_summary.call(podcast_details['episode_transcript']))
    print("Podcast Guest Information: ", get_podcast_guest.call(podcast_details['episode_transcript']))
    print("Podcast Highlights: ", get_podcast_highlights.call(podcast_details['episode_transcript']))
