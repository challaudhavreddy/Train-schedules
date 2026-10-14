# Railwise

A local train timetable web app with a chat assistant powered by Ollama and
`qwen2.5:3b`. The included Indian train schedules are illustrative examples,
not live railway data.

## Start the app

1. Make sure Ollama is running and the model is installed:

   ```powershell
   ollama list
   ```

2. Double-click `start.bat`, or run the server from this directory:

   ```powershell
   & "C:\Program Files\Python314\python.exe" server.py
   ```

3. Open [http://localhost:8000](http://localhost:8000).

The Python server uses only the standard library. Ollama should be available at
`http://localhost:11434`. Configure `OLLAMA_URL`, `OLLAMA_MODEL`,
`CHATBOT_HOST`, or `CHATBOT_PORT` with environment variables if needed.

The timetable search, route filters, stop details, fare examples, and suggested
chat questions are available as soon as the app is open. Chat answers use the
local Ollama model and the sample timetable.

## Troubleshooting

- If the assistant shows as unavailable, start Ollama and check that
  `qwen2.5:3b` appears in `ollama list`.
- The web app reports Ollama connection errors in the chat window; no external
  AI service is used.
- The timetable is sample content. It does not reflect live train running
  status, seat availability, bookings, or official fares.
