from flask import Flask, request, jsonify, Response, send_from_directory
from flask_cors import CORS

from chat import (
    getOutputPacked,
    setKey,
    has_api_key,
    resetMemory,
    setLLMModel,
    getLLMModel,
    get_raw_memory,
    SpecialInteraction,
    setPersonality,
    getPersonality,
    uses_local_replies,
)

from tts import streamVoiceChunks, tts_available

import threading
import uuid
import time
from itertools import chain
from pathlib import Path

application = Flask(__name__)
CORS(application)

_speech_requests: dict[str, tuple[float, str]] = {}
_speech_requests_lock = threading.Lock()
_reaction_audio_dir = Path(__file__).resolve().parent / "assets" / "reaction_audio"

# pre:
# - JSON body contains an "key" field
#
# post:
# - updates the active API key if provided
# - returns status indicating success or error
@application.route("/set_key", methods=["POST"])
def set_api_key():
    print("[Flask] /set_key route triggered")  # ← add this
    data = request.get_json(silent=True)
    key = data.get("key") if isinstance(data, dict) else None
    if isinstance(key, str) and key.strip():
        try:
            setKey(key.strip())
        except OSError:
            return jsonify({"message": "Could not save API key"}), 500
        return jsonify({"status": "ok", "message": "API key received"})
    else:
        return jsonify({"status": "error", "message": "No key received"}), 400


@application.route("/api_key_status", methods=["GET"])
def api_key_status():
    response = jsonify({
        "configured": has_api_key(),
        "no_ai": uses_local_replies(),
    })
    response.headers["Cache-Control"] = "no-store"
    return response

# pre:
# - JSON body contains "user_input" as a string
#
# post:
# - generates an assistant response and voice output
# - returns English UI text to the client
@application.route("/", methods=["POST"])
def request_message():
    print("[Flask] / route triggered")
    content = request.get_json() or {}
    user_input = content.get("user_input", "")

    pack = getOutputPacked(user_input)
    print("\n[Flask]: ENG:", pack.assistant_reply_ENG)
    print("[Flask]: JPS:", pack.assistant_reply_JPS)

    payload = {"response": pack.assistant_reply_ENG}

    # Local scripted turns have no GPT-SoVITS stream. Skip the speech ticket
    # so the WebUI does not wait on a missing voice server.
    if uses_local_replies() or not tts_available():
        return jsonify(payload)

    # Give the browser a single-use speech id. The browser then opens the
    # streaming WAV endpoint, so the same sound that reaches the speakers also
    # drives the Live2D analyser/lip sync.
    speech_id = uuid.uuid4().hex
    with _speech_requests_lock:
        now = time.monotonic()
        for expired in [key for key, (created, _) in _speech_requests.items() if now - created > 300]:
            _speech_requests.pop(expired, None)
        _speech_requests[speech_id] = (now, pack.assistant_reply_JPS)
        while len(_speech_requests) > 20:
            _speech_requests.pop(next(iter(_speech_requests)))

    payload["speech_id"] = speech_id
    return jsonify(payload)

@application.route("/speech/<speech_id>", methods=["GET"])
def speech(speech_id):
    if request.method == "HEAD":
        return "", 405
    with _speech_requests_lock:
        item = _speech_requests.pop(speech_id, None)

    if item is None or time.monotonic() - item[0] > 300:
        return jsonify({"message": "Speech request not found"}), 404

    chunks = streamVoiceChunks(item[1])
    try:
        first = next(chunks)
    except Exception:
        chunks.close()
        return jsonify({"message": "Speech generation failed"}), 502

    def generate():
        try:
            yield from chain((first,), chunks)
        finally:
            chunks.close()

    response = Response(generate(), mimetype="audio/wav")
    response.headers["Cache-Control"] = "no-store"
    response.call_on_close(chunks.close)
    return response


@application.route("/reaction_audio/<path:filename>", methods=["GET"])
def reaction_audio(filename):
    # Serve prerecorded interaction lines from backend/assets/reaction_audio.
    response = send_from_directory(_reaction_audio_dir, filename, conditional=True)
    response.headers["Cache-Control"] = "no-store"
    return response


# pre
# post:
# - clears all stored conversation memory
# - returns confirmation status
@application.route("/memory_reset", methods=["POST"])
def memory_reset():
    print("[Flask] /memory_reset triggered")  
    resetMemory()
    return jsonify({"status": "ok", "message": "Memory reset"})


# pre:
# - JSON body contains "model" option as string
#
# post:
# - updates the active LLM model if provided
# - returns success or error status
@application.route("/setLLMModel", methods=["POST"])
def settingLLMModel():
    print("[Flask] /setLLMModel triggered")  
    data = request.get_json() or {}
    new_model = data.get("model", "").strip()
    if new_model:
        setLLMModel(new_model)
        return jsonify({"status": "ok", "message": "new model recieved!"})
    else:
        return jsonify({"status": "error", "message": "No model recieved"}), 400

# pre
# post:
# - returns the currently active LLM model name as a string
@application.route("/getCurrLLMModel", methods=["GET"])
def getCurrLLMModel():
    print("[Flask] /getCurrLLMModel triggered")  
    LLM_Model = getLLMModel()
    if LLM_Model:
        return jsonify({"status": "ok", "message": LLM_Model})
    else:
        return jsonify({"status": "error", "message": "No Model Selected"}), 400

# pre
# post:
# - returns all stored conversation messages in list of Jsons
@application.route("/getMemory", methods=["POST"])
def getMemory():
    print("[Flask] /getMemory triggered")  
    msgs = get_raw_memory()
    return jsonify({"status":"ok","messages": msgs})


@application.route("/getPersonality", methods=["GET"])
def get_personality():
    try:
        personality = getPersonality()
    except OSError:
        return jsonify({"message": "Could not load personality"}), 500
    response = jsonify({"status": "ok", "personality": personality})
    response.headers["Cache-Control"] = "no-store"
    return response


# pre: 
# - JSON body containing new context for personality as string.
#
# post:
# - overwrite the current personality.txt
# - return sucess or error status
@application.route("/setPersonality", methods=["POST"])
def settingPersonality():
    print("[Flask] /setPersonality triggered")  
    data = request.get_json(silent=True)
    new_personality = data.get("personality") if isinstance(data, dict) else None
    if not isinstance(new_personality, str) or not new_personality.strip():
        return jsonify({"status": "error", "message": "Enter a personality before saving."}), 400
    new_personality = new_personality.strip()
    try:
        setPersonality(new_personality)
    except OSError:
        return jsonify({"message": "Could not save personality. Please try again."}), 500
    return jsonify({"status": "ok", "message": "Personality updated", "personality": new_personality})


# pre: Interaction number is given. e.g., 1,2,3
# post: use SpecialInteraction() from chat to update accordingly
@application.route("/doSpecialInteraction", methods=["POST"])
def doSpecialInteraction():
    data = request.get_json(silent=True)
    interaction_value = data.get("interaction_value") if isinstance(data, dict) else None
    if type(interaction_value) is not int:
        return jsonify({"message": "Interaction must be an integer"}), 400
    try:
        reply = SpecialInteraction(interaction_value)
    except ValueError:
        return jsonify({"message": "Unknown interaction"}), 400

    # chat.py stores reaction recordings relative to backend/. Convert those
    # internal paths into a browser-facing Flask endpoint.
    audio_url = reply.get("audio_url")
    prefix = "assets/reaction_audio/"
    if isinstance(audio_url, str) and audio_url.startswith(prefix):
        reply = {
            **reply,
            "audio_url": "/reaction_audio/" + audio_url[len(prefix):],
        }

    return jsonify({"status": "ok", **reply})
