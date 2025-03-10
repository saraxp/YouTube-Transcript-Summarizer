import re
import textwrap
from flask import Flask, request, jsonify
from flask_cors import CORS, cross_origin
from youtube_transcript_api import YouTubeTranscriptApi
from transformers import pipeline

app = Flask(__name__)
CORS(app, resources={r"/*": {"origins": "*"}}, 
        supports_credentials=True, 
        allow_headers=["Content-Type", "Authorization"], 
        methods=["GET", "POST", "OPTIONS"])

# Initialize summarization pipeline
summarizer = pipeline("summarization", model="t5-large")
print("Model loaded!")

def validate_youtube_url(url):
    # Validates if the provided URL is a valid YouTube video URL.
    youtube_url_pattern = r"(https?://)?(www\.)?(youtube|youtu|youtube-nocookie)\.(com|be)/"
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
        transcript = ' '.join([d['text'] for d in transcript_list])
        print(f"Transcript Retrieved: {transcript[:100]}...") 
        return transcript
    except Exception as e:
        app.logger.error('Error occurred while retrieving transcript: %s', str(e))
        return None


def clean_transcript(transcript):
    """ Removes redundant sentences and cleans transcript """
    sentences = transcript.split(". ")
    unique_sentences = []
    seen = set()

    for sentence in sentences:
        cleaned = sentence.strip()
        if cleaned and cleaned not in seen:
            unique_sentences.append(cleaned)
            seen.add(cleaned)

    return ". ".join(unique_sentences)

def chunk_transcript(transcript, max_chars=1024):
    """ Breaks transcript into chunks at sentence boundaries """
    sentences = transcript.split(". ")
    chunks = []
    current_chunk = ""

    for sentence in sentences:
        if len(current_chunk) + len(sentence) < max_chars:
            current_chunk += sentence + ". "
        else:
            chunks.append(current_chunk.strip())
            current_chunk = sentence + ". "

    if current_chunk:
        chunks.append(current_chunk.strip())

    return chunks


def get_summary(transcript):
    try:
        if len(transcript) < 100:
            return "Transcript is too short to summarize."

        # Clean & break transcript at proper sentence boundaries
        transcript = clean_transcript(transcript)
        chunks = chunk_transcript(transcript)

        summaries = []
        for chunk in chunks:
            max_len = min(300, len(chunk) // 2)  # Ensure max length is dynamic
            chunk_summary = summarizer(chunk, max_length=max_len, min_length=100, do_sample=False)[0]['summary_text']
            summaries.append(chunk_summary)

        # **Final Pass: Summarize the Summaries to Improve Context**
        final_summary_text = " ".join(summaries)
        if len(final_summary_text) > 1024:  # Ensure it's not too long
            final_summary = summarizer(final_summary_text, max_length=250, min_length=100, do_sample=False)[0]['summary_text']
        else:
            final_summary = final_summary_text

        return final_summary.strip()

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
    app.run(debug=True, port=5000)
