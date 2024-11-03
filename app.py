import re
from flask import Flask, request, jsonify
from flask_cors import CORS
from youtube_transcript_api import YouTubeTranscriptApi
from transformers import pipeline

app = Flask(__name__)
CORS(app, resources={r"/*": {"origins": "*"}}, supports_credentials=True, allow_headers=["Content-Type", "Authorization"], methods=["GET", "POST"])

# Initialize summarization pipeline
summarizer = pipeline("summarization")

def summary_api():
    try:
        url = request.args.get('url', '')
        if not url:
            return jsonify({"error": "URL parameter is missing."}), 400

        if not validate_youtube_url(url):
            return jsonify({"error": "Invalid YouTube video URL."}), 400

        video_id = extract_video_id(url)
        if not video_id:
            return jsonify({"error": "Failed to extract video ID from URL."}), 400

        transcript = get_transcript(video_id)
        if not transcript:
            return jsonify({"error": "Failed to retrieve transcript."}), 500

        summary = get_summary(transcript)
        if not summary:
            return jsonify({"error": "Failed to generate summary."}), 500

        return jsonify({"summary": summary})
    
    except Exception as e:
        # Log the error
        app.logger.error('Error occurred: %s', str(e))
        return jsonify({"error": str(e)}), 500

def validate_youtube_url(url):
    """
    Validates if the provided URL is a valid YouTube video URL.
    Returns True if valid, False otherwise.
    """
    youtube_url_pattern = (
        r'(https?://)?(www\.)?'
        '(youtube|youtu|youtube-nocookie)\.(com|be)/'
        '(watch\?v=|embed/|v/|.+\?v=)?([^&=%\?]{11})'
    )
    match = re.match(youtube_url_pattern, url)
    return bool(match)

def extract_video_id(url):
    try:
        match = re.search(r'(?<=v=)[^&]+', url)
        video_id = match.group(0) if match else None
        return video_id
    except Exception as e:
        # Log the error
        app.logger.error('Error occurred while extracting video ID: %s', str(e))
        return None

def get_transcript(video_id):
    try:
        transcript_list = YouTubeTranscriptApi.get_transcript(video_id)
        return ' '.join([d['text'] for d in transcript_list])
    except Exception as e:
        # Log the error
        app.logger.error('Error occurred while retrieving transcript: %s', str(e))
        return None

def get_summary(transcript):
    try:
        if len(transcript) < 100:
            return "Transcript is too short to summarize."
        summary = ''
        for i in range(0, len(transcript) // 1000 + 1):
            chunk = summarizer(transcript[i*1000:(i+1)*1000], max_length=100, min_length=50, do_sample=False)[0]['summary_text']
            summary += chunk + ' '
        return summary
    except Exception as e:
        # Log the error
        app.logger.error('Error occurred while generating summary: %s', str(e))
        return None

if __name__ == '__main__':
    # Set up logging
    import logging
    logging.basicConfig(filename='app.log', level=logging.DEBUG)

    # Run the Flask app on port 5500
    app.run(debug=True, port=5500)
