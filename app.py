import re
from flask import Flask, request, jsonify
from flask_cors import CORS, cross_origin
from youtube_transcript_api import YouTubeTranscriptApi
from transformers import pipeline

app = Flask(__name__)
CORS(app, resources={r"/*": {"origins": "*"}}, supports_credentials=True, allow_headers=["Content-Type", "Authorization"], methods=["GET", "POST"])

# Initialize summarization pipeline
summarizer = pipeline("summarization")

def validate_youtube_url(url):
    # Validates if the provided URL is a valid YouTube video URL.
    youtube_url_pattern = (
        r'(https?://)?(www\.)?'
        '(youtube|youtu|youtube-nocookie)\.(com|be)/'
        '(watch\?v=|embed/|v/|.+\?v=)?([^&=%\?]{11})'
    )
    return bool(re.match(youtube_url_pattern, url))

def extract_video_id(url):
    # Extracts video ID from a YouTube URL.
    try:
        match = re.search(r'(?<=v=)[^&]+', url)
        return match.group(0) if match else None
    except Exception as e:
        app.logger.error('Error occurred while extracting video ID: %s', str(e))
        return None

def get_transcript(video_id):
    # Retrieves the transcript of a YouTube video by video ID.
    try:
        transcript_list = YouTubeTranscriptApi.get_transcript(video_id)
        return ' '.join([d['text'] for d in transcript_list])
    except Exception as e:
        app.logger.error('Error occurred while retrieving transcript: %s', str(e))
        return None


def get_summary(transcript):
    try:
        if len(transcript) < 100:
            return "Transcript is too short to summarize."

        summary = ''
        chunk_size = 1000  # Define a chunk size for splitting long transcripts

        for i in range(0, len(transcript) // chunk_size + 1):
            chunk = transcript[i*chunk_size:(i+1)*chunk_size]
            max_len = min(100, len(chunk) // 2)  # Set max_length to half the chunk length or 100, whichever is smaller
            chunk_summary = summarizer(chunk, max_length=max_len, min_length=50, do_sample=False)[0]['summary_text']
            summary += chunk_summary + ' '

        return summary.strip()
    except Exception as e:
        app.logger.error('Error occurred while generating summary: %s', str(e))
        return None


@app.route('/summary', methods=['GET'])
@cross_origin(origin='*')
def summary_api():
    url = request.args.get('url', '')
    if not url:
        return jsonify({"error": "URL parameter is missing."}), 400

    # Validate the URL (use your validate_youtube_url function)
    if not validate_youtube_url(url):
        return jsonify({"error": "Invalid YouTube video URL."}), 400

    # Extract video ID and retrieve transcript (use your existing functions)
    video_id = extract_video_id(url)
    transcript = get_transcript(video_id)
    if not transcript:
        return jsonify({"error": "Failed to retrieve transcript."}), 500

    # Generate summary
    summary = get_summary(transcript)
    if not summary:
        return jsonify({"error": "Failed to generate summary."}), 500

    return jsonify({"summary": summary})


if __name__ == '__main__':
    app.run(debug=True, port=5500)
