# Alexa Plus – Network Analyzer

A mobile-friendly Flask web application that scans local networks (Bluetooth & Wi-Fi) and uses the Gemini AI model to produce an analysis and security recommendations.

## Features

- Scans for Bluetooth Classic and BLE devices
- Detects nearby Wi-Fi cameras by SSID pattern
- Identifies connected network devices
- Sends collected data to Gemini AI for intelligent analysis
- Provides AI-generated security recommendations
- Responsive, mobile-friendly web UI

## Quick Start

### 1. Install dependencies

```bash
pip install -r requirements.txt
```

### 2. Set environment variables

```bash
export GOOGLE_CLOUD_PROJECT="your-gcp-project-id"
export GOOGLE_CLOUD_LOCATION="us-central1"
```

### 3. Run the app

```bash
python app.py
```

The server starts on `http://0.0.0.0:5000`. Open this URL from any device on the same network (including a phone) and tap **Run Network Scan**.

## Testing on a Phone

1. Start the app on your computer (or a Raspberry Pi on the same LAN).
2. Find the computer's local IP address (e.g. `192.168.1.10`).
3. Open `http://192.168.1.10:5000` in the browser on your phone.
4. Tap **Run Network Scan** to trigger analysis.

## Running Tests

```bash
python -m pytest tests/ -v
```

## API Reference

| Endpoint | Method | Description |
|---|---|---|
| `/` | GET | Mobile-friendly web UI |
| `/api/analyze/network` | GET | Trigger network scan and AI analysis |

### Response format – `/api/analyze/network`

```json
{
  "success": true,
  "analysis": "...",
  "security_recommendations": "..."
}
```
