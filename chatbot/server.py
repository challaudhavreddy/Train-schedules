import json
import logging
import os
import re
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from urllib.error import HTTPError, URLError
from urllib.parse import urlparse
from urllib.request import Request, urlopen


HOST = os.environ.get("CHATBOT_HOST", "127.0.0.1")
PORT = int(os.environ.get("CHATBOT_PORT", "8000"))
OLLAMA_URL = os.environ.get("OLLAMA_URL", "http://localhost:11434").rstrip("/")
OLLAMA_MODEL = os.environ.get("OLLAMA_MODEL", "qwen2.5:3b")
ROOT = os.path.dirname(os.path.abspath(__file__))

TRAINS = [
    {
        "number": "12002",
        "name": "Shatabdi Express",
        "from": "New Delhi",
        "to": "Bhopal Jn",
        "depart": "06:00",
        "arrive": "14:25",
        "duration": "8h 25m",
        "type": "Superfast",
        "days": "Daily",
        "platform": "3",
        "via": ["Agra Cantt", "Gwalior", "Jhansi Jn"],
        "fare": "₹1,845",
        "status": "On time",
    },
    {
        "number": "12951",
        "name": "Mumbai Rajdhani",
        "from": "Mumbai Central",
        "to": "New Delhi",
        "depart": "17:00",
        "arrive": "08:32",
        "duration": "15h 32m",
        "type": "Rajdhani",
        "days": "Daily",
        "platform": "5",
        "via": ["Vadodara Jn", "Kota Jn", "Sawai Madhopur"],
        "fare": "₹3,280",
        "status": "On time",
    },
    {
        "number": "12627",
        "name": "Karnataka Express",
        "from": "KSR Bengaluru",
        "to": "New Delhi",
        "depart": "19:20",
        "arrive": "10:30",
        "duration": "39h 10m",
        "type": "Superfast",
        "days": "Daily",
        "platform": "6",
        "via": ["Guntakal Jn", "Secunderabad Jn", "Bhopal Jn"],
        "fare": "₹2,145",
        "status": "On time",
    },
    {
        "number": "12952",
        "name": "Mumbai Rajdhani",
        "from": "New Delhi",
        "to": "Mumbai Central",
        "depart": "16:55",
        "arrive": "08:35",
        "duration": "15h 40m",
        "type": "Rajdhani",
        "days": "Daily",
        "platform": "1",
        "via": ["Sawai Madhopur", "Kota Jn", "Vadodara Jn"],
        "fare": "₹3,280",
        "status": "On time",
    },
    {
        "number": "12009",
        "name": "Shatabdi Express",
        "from": "Ahmedabad Jn",
        "to": "Mumbai Central",
        "depart": "06:10",
        "arrive": "12:40",
        "duration": "6h 30m",
        "type": "Shatabdi",
        "days": "Daily",
        "platform": "2",
        "via": ["Vadodara Jn", "Surat"],
        "fare": "₹1,625",
        "status": "On time",
    },
    {
        "number": "12626",
        "name": "Kerala Express",
        "from": "New Delhi",
        "to": "Thiruvananthapuram Central",
        "depart": "11:25",
        "arrive": "15:05",
        "duration": "51h 40m",
        "type": "Superfast",
        "days": "Daily",
        "platform": "7",
        "via": ["Jhansi Jn", "Vijayawada Jn", "Ernakulam Jn"],
        "fare": "₹2,380",
        "status": "On time",
    },
    {
        "number": "12028",
        "name": "Shatabdi Express",
        "from": "Chennai Central",
        "to": "KSR Bengaluru",
        "depart": "06:00",
        "arrive": "10:50",
        "duration": "4h 50m",
        "type": "Shatabdi",
        "days": "Daily",
        "platform": "4",
        "via": ["Katpadi Jn", "Jolarpettai Jn"],
        "fare": "₹1,395",
        "status": "On time",
    },
    {
        "number": "12802",
        "name": "Purushottam Express",
        "from": "New Delhi",
        "to": "Puri",
        "depart": "22:25",
        "arrive": "05:40",
        "duration": "31h 15m",
        "type": "Superfast",
        "days": "Daily",
        "platform": "8",
        "via": ["Kanpur Central", "Prayagraj Jn", "Bhubaneswar"],
        "fare": "₹1,950",
        "status": "On time",
    },
    {
        "number": "12903",
        "name": "Golden Temple Mail",
        "from": "Mumbai Central",
        "to": "Amritsar Jn",
        "depart": "18:45",
        "arrive": "02:20",
        "duration": "31h 35m",
        "type": "Mail/Express",
        "days": "Daily",
        "platform": "9",
        "via": ["Surat", "Kota Jn", "New Delhi"],
        "fare": "₹1,780",
        "status": "On time",
    },
    {
        "number": "22691",
        "name": "Rajdhani Express",
        "from": "KSR Bengaluru",
        "to": "Hazrat Nizamuddin",
        "depart": "20:00",
        "arrive": "05:20",
        "duration": "33h 20m",
        "type": "Rajdhani",
        "days": "Mon, Wed, Fri",
        "platform": "1",
        "via": ["Dharwad", "Vasai Road", "Kota Jn"],
        "fare": "₹3,140",
        "status": "On time",
    },
    {
        "number": "12617",
        "name": "Mangala Lakshadweep Express",
        "from": "Ernakulam Jn",
        "to": "Hazrat Nizamuddin",
        "depart": "13:25",
        "arrive": "13:50",
        "duration": "48h 25m",
        "type": "Superfast",
        "days": "Daily",
        "platform": "2",
        "via": ["Mangaluru Jn", "Panvel", "Kota Jn"],
        "fare": "₹2,240",
        "status": "On time",
    },
    {
        "number": "12019",
        "name": "Shatabdi Express",
        "from": "Howrah Jn",
        "to": "Ranchi",
        "depart": "06:05",
        "arrive": "13:15",
        "duration": "7h 10m",
        "type": "Shatabdi",
        "days": "Daily except Sunday",
        "platform": "12",
        "via": ["Kharagpur Jn", "Tatanagar Jn", "Muri Jn"],
        "fare": "₹1,520",
        "status": "On time",
    },
]

SYSTEM_PROMPT = """You are Railwise, a friendly train timetable assistant.
Answer using only the sample train schedule provided in the conversation.
Be concise and helpful. Give train numbers, stations, times, duration, running
days, platforms, and fares exactly as supplied when relevant. Make it clear
that these are example schedules, not live railway data: do not claim to check
real-time running status, seat availability, bookings, or current official
fares. If no matching train is listed or the schedule does not contain the
answer, say so plainly and suggest searching the timetable on the page. Never
invent trains or schedule details. Match a requested route using the train's
"from" and "to" fields only: a train with the requested station as its "from"
station is departing that station, not arriving at it. Never infer a route from
a train's name, reverse its direction, or assume a train serves a station
unless that station appears in its supplied "from", "to", or "via" fields."""


def schedule_for_question(message):
    stations = {
        station.casefold(): station
        for train in TRAINS
        for station in (train["from"], train["to"])
    }
    stations.update(
        {
            "delhi": "New Delhi",
            "mumbai": "Mumbai Central",
            "bengaluru": "KSR Bengaluru",
            "bangalore": "KSR Bengaluru",
            "bangaluru": "KSR Bengaluru",
            "bhopal": "Bhopal Jn",
        }
    )
    ordered_stations = sorted(stations, key=len, reverse=True)
    normalized_message = message.casefold()

    def mentioned_station(prefixes):
        for alias in ordered_stations:
            pattern = rf"(?:{prefixes})\s+(?:the\s+)?{re.escape(alias)}(?!\w)"
            if re.search(pattern, normalized_message):
                return stations[alias]
        return None

    origin = mentioned_station(r"\bfrom\b|\bdepart\w*\s+from\b|\bleav\w*\s+from\b")
    destination = mentioned_station(
        r"\bto\b|\btoward(?:s)?\b|\barriv\w*\s+(?:at|in)\b|\breach\w*"
    )

    if origin is None or destination is None:
        mentions = []
        for alias in ordered_stations:
            for match in re.finditer(
                rf"(?<!\w){re.escape(alias)}(?!\w)", normalized_message
            ):
                mentions.append((match.start(), match.end(), stations[alias]))
        mentions.sort(key=lambda item: (item[0], -(item[1] - item[0])))
        route_stations = []
        last_end = -1
        for start, end, station in mentions:
            if start < last_end:
                continue
            if not route_stations or route_stations[-1] != station:
                route_stations.append(station)
            last_end = end
        if len(route_stations) >= 2:
            if origin is None:
                origin = route_stations[0]
            if destination is None:
                destination = next(
                    (station for station in route_stations if station != origin),
                    None,
                )

    if origin is None and destination is None:
        return TRAINS, None, None

    matching_trains = [
        train
        for train in TRAINS
        if (origin is None or train["from"] == origin)
        and (destination is None or train["to"] == destination)
    ]
    return matching_trains, origin, destination


def json_response(handler, status, payload):
    body = json.dumps(payload, ensure_ascii=False).encode("utf-8")
    handler.send_response(status)
    handler.send_header("Content-Type", "application/json; charset=utf-8")
    handler.send_header("Content-Length", str(len(body)))
    handler.send_header("Cache-Control", "no-store")
    handler.end_headers()
    handler.wfile.write(body)


def ollama_tags():
    request = Request(f"{OLLAMA_URL}/api/tags")
    with urlopen(request, timeout=4) as response:
        return json.loads(response.read().decode("utf-8"))


class ChatbotHandler(BaseHTTPRequestHandler):
    def do_GET(self):
        path = urlparse(self.path).path
        if path == "/api/trains":
            json_response(self, 200, {"trains": TRAINS})
            return
        if path == "/api/status":
            try:
                models = ollama_tags().get("models", [])
            except (HTTPError, URLError, TimeoutError, OSError, json.JSONDecodeError) as exc:
                logging.warning("Ollama health check failed: %s", exc)
                json_response(
                    self,
                    200,
                    {"connected": False, "model": OLLAMA_MODEL},
                )
                return
            connected = any(
                model.get("name") == OLLAMA_MODEL for model in models
            )
            json_response(
                self,
                200,
                {"connected": connected, "model": OLLAMA_MODEL},
            )
            return
        if path in ("/", "/index.html"):
            self.serve_file("index.html", "text/html; charset=utf-8")
            return
        if path == "/styles.css":
            self.serve_file("styles.css", "text/css; charset=utf-8")
            return
        if path == "/app.js":
            self.serve_file("app.js", "text/javascript; charset=utf-8")
            return
        json_response(self, 404, {"error": "Not found."})

    def do_POST(self):
        if urlparse(self.path).path != "/api/chat":
            json_response(self, 404, {"error": "Not found."})
            return
        try:
            content_length = int(self.headers.get("Content-Length", "0"))
        except ValueError:
            json_response(self, 400, {"error": "Invalid request length."})
            return
        if content_length <= 0 or content_length > 16_384:
            json_response(self, 400, {"error": "Message must be under 16 KB."})
            return
        try:
            payload = json.loads(self.rfile.read(content_length))
        except (json.JSONDecodeError, UnicodeDecodeError):
            json_response(self, 400, {"error": "Request body must be valid JSON."})
            return
        if not isinstance(payload, dict) or not isinstance(payload.get("message"), str):
            json_response(self, 400, {"error": "A message is required."})
            return
        message = payload["message"].strip()
        if not message:
            json_response(self, 400, {"error": "Please enter a message."})
            return
        if len(message) > 4_000:
            json_response(self, 400, {"error": "Message must be under 4,000 characters."})
            return

        relevant_trains, origin, destination = schedule_for_question(message)
        has_route_filter = origin is not None or destination is not None
        asks_fastest = re.search(
            r"\b(?:fastest|quickest|shortest)\b", message, re.IGNORECASE
        )
        asks_stops = re.search(
            r"\b(?:stops?|stations?|via|en.route)\b", message, re.IGNORECASE
        )
        if has_route_filter or asks_fastest:
            matching_trains = relevant_trains if has_route_filter else TRAINS
            if not matching_trains:
                reply = "There are no matching trains in the sample timetable."
            elif asks_fastest:
                def travel_minutes(train):
                    hours, minutes = re.fullmatch(
                        r"(\d+)h\s+(\d+)m", train["duration"]
                    ).groups()
                    return int(hours) * 60 + int(minutes)

                train = min(matching_trains, key=travel_minutes)
                reply = (
                    f"The fastest matching sample train is {train['number']} — "
                    f"{train['name']}, from {train['from']} at {train['depart']} "
                    f"to {train['to']} at {train['arrive']} "
                    f"({train['duration']}; {train['days']}). "
                    "These are illustrative schedules, not live railway information."
                )
            else:
                if origin is not None and destination is not None:
                    heading = f"Sample trains from {origin} to {destination}:"
                elif origin is not None:
                    heading = f"Sample trains departing from {origin}:"
                else:
                    heading = f"Sample trains arriving at {destination}:"
                details = [
                    (
                        f"- {train['number']} — {train['name']}: "
                        f"{train['from']} {train['depart']} to {train['to']} "
                        f"{train['arrive']} ({train['duration']}; {train['days']})."
                        + (
                            f" Stops: {', '.join(train['via'])}."
                            if asks_stops
                            else ""
                        )
                    )
                    for train in relevant_trains
                ]
                reply = (
                    heading
                    + "\n\n"
                    + "\n".join(details)
                    + "\n\nThese are illustrative schedules, not live railway information."
                )
            json_response(self, 200, {"reply": reply})
            return

        conversation = payload.get("history", [])
        messages = [{"role": "system", "content": SYSTEM_PROMPT}]
        if isinstance(conversation, list):
            for item in conversation[-8:]:
                if (
                    isinstance(item, dict)
                    and item.get("role") in ("user", "assistant")
                    and isinstance(item.get("content"), str)
                ):
                    messages.append(
                        {
                            "role": item["role"],
                            "content": item["content"][:4_000],
                        }
                    )

        schedule = json.dumps(relevant_trains, ensure_ascii=False)
        messages.append(
            {
                "role": "user",
                "content": (
                    f"Sample train timetable (JSON):\n{schedule}\n\n"
                    f"Question: {message}"
                ),
            }
        )
        request_body = json.dumps(
            {
                "model": OLLAMA_MODEL,
                "messages": messages,
                "stream": False,
                "options": {"temperature": 0.3},
            }
        ).encode("utf-8")
        request = Request(
            f"{OLLAMA_URL}/api/chat",
            data=request_body,
            headers={"Content-Type": "application/json"},
            method="POST",
        )
        try:
            with urlopen(request, timeout=180) as response:
                result = json.loads(response.read().decode("utf-8"))
        except HTTPError as exc:
            detail = exc.read().decode("utf-8", errors="replace")[:500]
            logging.error("Ollama returned HTTP %s: %s", exc.code, detail)
            json_response(
                self,
                502,
                {"error": f"Ollama could not answer (HTTP {exc.code}). Check that the model is available."},
            )
            return
        except (URLError, TimeoutError, OSError) as exc:
            logging.error("Could not reach Ollama at %s: %s", OLLAMA_URL, exc)
            json_response(
                self,
                502,
                {"error": "Could not connect to Ollama. Make sure Ollama is running at localhost:11434."},
            )
            return
        except (json.JSONDecodeError, UnicodeDecodeError) as exc:
            logging.error("Ollama returned invalid JSON: %s", exc)
            json_response(self, 502, {"error": "Ollama returned an invalid response."})
            return

        answer = result.get("message", {}).get("content", "").strip()
        if not answer:
            json_response(self, 502, {"error": "Ollama returned an empty answer. Please try again."})
            return
        json_response(self, 200, {"reply": answer})

    def serve_file(self, filename, content_type):
        try:
            with open(os.path.join(ROOT, filename), "rb") as source:
                body = source.read()
        except OSError as exc:
            logging.error("Could not read %s: %s", filename, exc)
            json_response(self, 500, {"error": "The web application file could not be read."})
            return
        self.send_response(200)
        self.send_header("Content-Type", content_type)
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def log_message(self, format, *args):
        logging.info("%s - %s", self.address_string(), format % args)


if __name__ == "__main__":
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s %(levelname)s %(message)s",
    )
    server = ThreadingHTTPServer((HOST, PORT), ChatbotHandler)
    logging.info("Railwise running at http://%s:%s", HOST, PORT)
    logging.info("Ollama: %s | model: %s", OLLAMA_URL, OLLAMA_MODEL)
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        logging.info("Shutting down Railwise.")
    finally:
        server.server_close()
