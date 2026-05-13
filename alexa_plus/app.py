import asyncio
import logging
import os

from flask import Flask, jsonify, render_template

# Configure logging
logging.basicConfig(level=logging.INFO)

# --- Class Definitions ---


class BluetoothScanner:
    """Scans for both Bluetooth Classic and Bluetooth Low Energy devices."""

    def __init__(self):
        self.logger = logging.getLogger(__name__)

    def scan_bluetooth_classic(self):
        try:
            import bluetooth

            devices = bluetooth.discover_devices(
                duration=8, lookup_names=True, lookup_class=True
            )
            return [
                {"address": addr, "name": name, "class": dev_class}
                for addr, name, dev_class in devices
            ]
        except Exception as e:
            self.logger.error(f"Bluetooth classic scan error: {str(e)}")
            return []

    def scan_bluetooth_le(self):
        try:
            from bluetooth.ble import DiscoveryService

            service = DiscoveryService()
            devices = service.discover(2)
            return [{"address": addr, "name": name} for addr, name in devices.items()]
        except Exception as e:
            self.logger.error(f"Bluetooth LE scan error: {str(e)}")
            return []


class WifiScanner:
    """Scans for Wi-Fi cameras based on SSID patterns."""

    def __init__(self):
        self.logger = logging.getLogger(__name__)

    def scan_wifi_cameras(self, interface="wlan0"):
        try:
            from scapy.all import Dot11, Dot11Beacon, sniff

            cameras = []

            def packet_handler(pkt):
                if pkt.haslayer(Dot11):
                    if pkt.type == 0 and pkt.subtype == 8:  # Beacon frame
                        if pkt.info:  # SSID
                            ssid = pkt.info.decode("utf-8", errors="ignore")
                            if any(
                                cam_pattern in ssid.lower()
                                for cam_pattern in ["cam", "ipcam", "camera", "webcam"]
                            ):
                                signal_raw = (
                                    pkt[Dot11Beacon].network_stats().get("signal", 0)
                                )
                                cameras.append(
                                    {
                                        "ssid": ssid,
                                        "bssid": pkt.addr2,
                                        "signal_strength": int(signal_raw),
                                    }
                                )

            sniff(iface=interface, prn=packet_handler, timeout=10)
            return cameras
        except Exception as e:
            self.logger.error(f"WiFi camera scan error: {str(e)}")
            return []


class GeminiAIAnalyzer:
    """Uses Gemini AI to analyze network data and provide recommendations."""

    def __init__(self, project_id, location):
        import vertexai
        from vertexai.language_models import TextGenerationModel

        vertexai.init(project=project_id, location=location)
        self.model = TextGenerationModel.from_pretrained("gemini-pro")

    async def analyze_network_data(self, network_data):
        prompt = f"""
        Analyze the following network data and provide insights:
        Network Devices: {network_data['devices']}
        Signal Strengths: {network_data['signals']}
        Traffic Patterns: {network_data['traffic']}
        """
        response = self.model.predict(prompt)
        return response.text

    async def generate_security_recommendations(self, scan_results):
        prompt = f"""
        Based on the network scan results, provide security recommendations:
        {scan_results}
        """
        response = self.model.predict(prompt)
        return response.text


class NetworkScanner:
    """Scans the network for connected devices."""

    def __init__(self):
        self._known_devices = set()

    def scan_network(self, ip_range):
        # Placeholder for actual network scanning logic (e.g., using nmap or arp-scan)
        devices = [{"ip": "192.168.1.5", "mac": "00:11:22:33:44:55", "hostname": "my-device"}]
        for device in devices:
            mac = device.get("mac")
            if mac not in self._known_devices:
                device["color"] = "blue"
                self._known_devices.add(mac)
        return devices


# --- Flask Application ---

app = Flask(__name__)

_project_id = os.environ.get("GOOGLE_CLOUD_PROJECT", "your-project-id")
_location = os.environ.get("GOOGLE_CLOUD_LOCATION", "us-central1")

network_scanner = NetworkScanner()


@app.route("/")
def index():
    return render_template("index.html")


@app.route("/api/analyze/network")
def analyze_network():
    """API endpoint to trigger network analysis."""

    async def _run():
        bluetooth_scanner = BluetoothScanner()
        wifi_scanner = WifiScanner()
        ai_analyzer = GeminiAIAnalyzer(project_id=_project_id, location=_location)

        # Collect data
        network_data = network_scanner.scan_network("192.168.1.0/24")
        bluetooth_data = bluetooth_scanner.scan_bluetooth_classic()
        wifi_data = wifi_scanner.scan_wifi_cameras()

        combined_data = {
            "devices": network_data,
            "signals": {"bluetooth": bluetooth_data, "wifi_cameras": wifi_data},
            "traffic": {},
        }

        analysis = await ai_analyzer.analyze_network_data(combined_data)
        security_recommendations = await ai_analyzer.generate_security_recommendations(analysis)
        return analysis, security_recommendations

    try:
        analysis, security_recommendations = asyncio.run(_run())
        return jsonify(
            {
                "success": True,
                "analysis": analysis,
                "security_recommendations": security_recommendations,
            }
        )
    except Exception as e:
        logging.error("API endpoint error", exc_info=True)
        return jsonify({"success": False, "error": "Network analysis failed. Please try again."}), 500


# --- Main Entry Point ---

if __name__ == "__main__":
    debug_mode = os.environ.get("FLASK_DEBUG", "0") == "1"
    app.run(debug=debug_mode, host="0.0.0.0", port=5000)
