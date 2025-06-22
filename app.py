from flask import Flask, request, jsonify
import subprocess
import tempfile
from pathlib import Path
import re

app = Flask(__name__)

# === TRANSCRIPT EXTRACTOR ===
class YTDLPCommandLineExtractor:
    @staticmethod
    def is_available():
        try:
            result = subprocess.run(['yt-dlp', '--version'], capture_output=True, text=True, timeout=5)
            return result.returncode == 0
        except:
            return False

    @staticmethod
    def get_transcript(video_id):
        if not YTDLPCommandLineExtractor.is_available():
            return None, "yt-dlp not available. Please install yt-dlp."

        try:
            url = f'https://www.youtube.com/watch?v={video_id}'
            temp_dir = tempfile.gettempdir()
            cmd = [
                'yt-dlp',
                '--write-subs',
                '--write-auto-subs',
                '--sub-langs', 'en,en-US,en-GB',
                '--sub-format', 'vtt',
                '--skip-download',
                '--output', f'{temp_dir}/%(id)s.%(ext)s',
                url
            ]
            result = subprocess.run(cmd, capture_output=True, text=True, timeout=30)

            if result.returncode != 0:
                return None, f"yt-dlp failed: {result.stderr}"

            subtitle_files = list(Path(temp_dir).glob(f'{video_id}*.vtt'))
            if subtitle_files:
                with open(subtitle_files[0], 'r', encoding='utf-8') as f:
                    vtt_content = f.read()

                # Clean up
                for file in subtitle_files:
                    try:
                        file.unlink()
                    except:
                        pass

                transcript = YTDLPCommandLineExtractor.parse_vtt(vtt_content)
                return transcript, None if transcript.strip() else "Transcript was empty"
            
            return None, "No subtitle file found"

        except subprocess.TimeoutExpired:
            return None, "yt-dlp timeout"
        except Exception as e:
            return None, str(e)

    @staticmethod
    def parse_vtt(vtt_content):
        # Remove timestamps and metadata
        text = re.sub(r"(\d{2}:\d{2}:\d{2}\.\d{3} --> .*\n)?", "", vtt_content)
        text = re.sub(r"Kind:.*\n|Language:.*\n|Translator:.*\n|Reviewer:.*\n", "", text)
        return text.strip()

# === OLLAMA CALL ===
def summarize_with_mistral(transcript):
    try:
        cmd = ['ollama', 'run', 'mistral']
        process = subprocess.Popen(
            cmd,
            stdin=subprocess.PIPE,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
            encoding="utf-8",
            errors="replace"
        )
        prompt = f"Please provide a concise summary of this YouTube video transcript:\n\n{transcript}\n\nSummary:"
        stdout, stderr = process.communicate(prompt, timeout=120)

        if process.returncode != 0:
            error_msg = f"Ollama error (code {process.returncode}): {stderr.strip()} | {stdout.strip()}"
            return None, error_msg
        return stdout.strip(), None

    except subprocess.TimeoutExpired:
        process.kill()
        stdout, stderr = process.communicate()
        return None, "Ollama summarization timed out"
    except Exception as e:
        return None, str(e)


# === FLASK ROUTE ===
@app.route('/summarize', methods=['POST'])
def summarize():
    data = request.get_json()
    if not data or 'url' not in data:
        return jsonify({"error": "No URL provided"}), 400

    url = data['url']
    video_id_match = re.search(r"v=([a-zA-Z0-9_-]+)", url)
    if not video_id_match:
        return jsonify({"error": "Invalid YouTube URL"}), 400

    video_id = video_id_match.group(1)

    # Get transcript
    transcript, error = YTDLPCommandLineExtractor.get_transcript(video_id)
    if error:
        return jsonify({"error": f"Transcript extraction failed: {error}"}), 500

    # Summarize with Mistral
    summary, error = summarize_with_mistral(transcript)
    if error:
        return jsonify({"error": f"Summarization failed: {error}"}), 500

    return jsonify({
        "summary": summary,
        "transcript": transcript
    })


# === MAIN ===
if __name__ == '__main__':
    app.run(port=5500, debug=True)