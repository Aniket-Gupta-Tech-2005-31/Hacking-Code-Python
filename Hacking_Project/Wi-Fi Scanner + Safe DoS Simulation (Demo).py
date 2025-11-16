"""
Streamlit Wi-Fi Scanner + Safe DoS Simulation (Demo)
- DOES NOT perform any real attack.
- Scans visible Wi-Fi networks (if pywifi works on the platform).
- Lets user select a network and run a simulated DoS for demo/visualization.
- Generates downloadable JSON log of the simulation.
"""

import streamlit as st
import time
import json
import random
from datetime import datetime
import pandas as pd

# Try to import pywifi; if not available or fails, we'll use a mock scan
try:
    import pywifi
    from pywifi import const
    PYWIFI_AVAILABLE = True
except Exception:
    PYWIFI_AVAILABLE = False

# ---- Utilities ----
LOGFILE_NAME = "simulation_log.jsonl"  # each line is a JSON log entry

def scan_networks_pywifi(timeout=3):
    """Scan using pywifi. Returns list of dicts {ssid,bssid,signal,freq}"""
    wifi = pywifi.PyWiFi()
    ifaces = wifi.interfaces()
    if not ifaces:
        return []
    iface = ifaces[0]
    iface.scan()
    time.sleep(timeout)
    results = iface.scan_results()
    networks = {}
    for r in results:
        key = (r.ssid, r.bssid)
        if key not in networks or r.signal > networks[key]['signal']:
            networks[key] = {
                'ssid': r.ssid,
                'bssid': r.bssid,
                'signal': r.signal,
                'freq': getattr(r, 'freq', None)
            }
    return list(networks.values())

def mock_scan_networks():
    """Return a mocked list of networks for demo purposes."""
    sample_ssids = [
        "Cafe_Free_WiFi", "Home-Net_2.4G", "OfficeNet", "HiddenSSID", "Campus-Guest", "IoT-AP-123"
    ]
    nets = []
    for i, s in enumerate(sample_ssids):
        nets.append({
            'ssid': s,
            'bssid': f"02:00:00:00:0{i:02x}",
            'signal': random.randint(-90, -30),
            'freq': random.choice([2412, 2437, 2462, 5180])
        })
    return nets

def append_log(entry: dict):
    """Append JSON-line to local log file."""
    with open(LOGFILE_NAME, "a") as f:
        f.write(json.dumps(entry) + "\n")

def load_all_logs():
    try:
        with open(LOGFILE_NAME, "r") as f:
            lines = f.readlines()
        entries = [json.loads(l) for l in lines]
        return entries
    except FileNotFoundError:
        return []

# ---- Streamlit UI ----
st.set_page_config(page_title="Safe Wi-Fi Scanner & DoS Simulation", layout="wide")
st.title("📶 Safe Wi-Fi Scanner + DoS Simulation (Educational Demo)")

st.markdown(
    """
    **Note:** This app only *simulates* a DoS for demonstration. It **does not** send any real attack traffic.
    Use this to demonstrate attack behaviour visually and to generate logs for your project.
    """
)

# Sidebar: scan controls
st.sidebar.header("Scan Controls")
scan_btn = st.sidebar.button("Scan Nearby Wi-Fi")

scan_timeout = st.sidebar.slider("Scan wait time (seconds)", min_value=1, max_value=8, value=3)
use_mock = st.sidebar.checkbox("Force mock scan (if pywifi failing)", value=not PYWIFI_AVAILABLE)

# Show environment status
st.sidebar.markdown(f"**pywifi available:** {PYWIFI_AVAILABLE}")

# Containers
scan_col, sim_col = st.columns([1, 1])

with scan_col:
    st.subheader("Nearby Networks")
    scan_placeholder = st.empty()
    # Perform scan if button pressed or cached list empty
    if scan_btn:
        scan_placeholder.info("Scanning ... (this may take a few seconds)")
        try:
            if not PYWIFI_AVAILABLE or use_mock:
                networks = mock_scan_networks()
            else:
                networks = scan_networks_pywifi(timeout=scan_timeout)
                if not networks:
                    # fallback to mock if none found
                    networks = mock_scan_networks()
            # present as dataframe
            df = pd.DataFrame(networks)
            # prettify signal column
            if not df.empty:
                df['signal_dbm'] = df['signal']
                df['signal'] = df['signal'].apply(lambda s: f"{s} dBm")
            st.session_state['last_scan'] = networks
            scan_placeholder.success(f"Scan complete — found {len(networks)} networks")
            st.dataframe(df[['ssid','bssid','signal_dbm','freq']] if not df.empty else df)
        except Exception as e:
            scan_placeholder.error(f"Scan failed: {e}")
            st.session_state['last_scan'] = []
    else:
        # show last scan if available
        last = st.session_state.get('last_scan', None)
        if last is None:
            st.info("Click 'Scan Nearby Wi-Fi' in the sidebar to start.")
        else:
            df = pd.DataFrame(last)
            if not df.empty:
                df['signal_dbm'] = df['signal']; df['signal'] = df['signal'].apply(lambda s: f"{s} dBm")
                st.dataframe(df[['ssid','bssid','signal_dbm','freq']])
            else:
                st.info("No networks found in last scan.")

with sim_col:
    st.subheader("Simulation Controls")
    last_scan = st.session_state.get('last_scan', [])
    if not last_scan:
        st.info("No networks to select. Run a scan first (sidebar).")
    else:
        # display selectbox with SSID (include BSSID for uniqueness)
        options = [f"{n['ssid'] or '<hidden>'} — {n['bssid']}" for n in last_scan]
        sel = st.selectbox("Select a network to simulate against", options)
        selected_idx = options.index(sel)
        selected_network = last_scan[selected_idx]

        st.markdown("**Simulation parameters**")
        duration = st.slider("Duration (seconds)", min_value=5, max_value=120, value=20, step=5)
        intensity = st.slider("Intensity (simulated packets per second)", min_value=10, max_value=5000, value=500, step=10)
        jitter = st.slider("Jitter (±% variability)", min_value=0, max_value=80, value=20, step=5)

        simulate_btn = st.button("Run Safe Simulation")

        st.markdown("---")
        st.write("Selected network metadata:")
        st.json({
            "ssid": selected_network.get('ssid'),
            "bssid": selected_network.get('bssid'),
            "signal_dbm": selected_network.get('signal'),
            "freq": selected_network.get('freq')
        })

# Simulation run (when button pressed)
if 'simulate_trigger' not in st.session_state:
    st.session_state['simulate_trigger'] = False

if 'last_sim_result' not in st.session_state:
    st.session_state['last_sim_result'] = None

if 'simulate_counter' not in st.session_state:
    st.session_state['simulate_counter'] = 0

if 'simulate_running' not in st.session_state:
    st.session_state['simulate_running'] = False

if 'simulate_btn' not in locals():
    simulate_btn = False

if simulate_btn and last_scan:
    # start simulation
    st.session_state['simulate_running'] = True
    st.session_state['simulate_counter'] += 1

    st.info("Simulation started — this is a SAFE visual simulation only.")
    progress = st.progress(0)
    status_text = st.empty()
    chart_area = st.empty()
    metrics_area = st.empty()

    # Prepare time series for chart
    timestamps = []
    packets_sent_series = []
    errors_series = []

    start_time = time.time()
    total_ticks = max(1, int(duration))  # update each second
    packets_total = 0
    errors_total = 0

    for elapsed in range(0, duration):
        # Simulate packets for this second with jitter
        base_pps = intensity
        jitter_fraction = jitter / 100.0
        pps = int(base_pps * (1 + random.uniform(-jitter_fraction, jitter_fraction)))
        # Simulate occasional errors proportional to intensity
        error_chance = min(0.05, 0.0005 * base_pps)  # keep errors small
        errors_this_tick = sum(1 for _ in range(max(0, pps//100)) if random.random() < error_chance)
        packets_total += pps
        errors_total += errors_this_tick

        # append data
        timestamps.append(elapsed)
        packets_sent_series.append(packets_total)
        errors_series.append(errors_total)

        # Update chart and metrics
        df_chart = pd.DataFrame({
            "elapsed_s": timestamps,
            "packets_total": packets_sent_series,
            "errors_total": errors_series
        }).set_index("elapsed_s")

        chart_area.line_chart(df_chart)
        metrics_area.markdown(
            f"**Elapsed:** {elapsed+1}s  &nbsp;&nbsp; **Packets (total):** {packets_total}  &nbsp;&nbsp; **Errors (total):** {errors_total}"
        )

        # update progress
        progress.progress(min(1.0, (elapsed+1)/duration))
        status_text.text(f"Simulating... ({elapsed+1}/{duration} s)")

        # sleep to simulate real-time (this keeps UI responsive)
        time.sleep(1)

    # Simulation finished
    st.session_state['simulate_running'] = False
    status_text.success("Simulation complete (SIMULATION — no real traffic sent).")
    final_entry = {
        "timestamp_utc": datetime.utcnow().isoformat() + "Z",
        "network": {
            "ssid": selected_network.get('ssid'),
            "bssid": selected_network.get('bssid'),
            "signal_dbm": selected_network.get('signal'),
            "freq": selected_network.get('freq')
        },
        "simulation_params": {
            "duration_s": duration,
            "intensity_pps": intensity,
            "jitter_percent": jitter
        },
        "results": {
            "packets_sent_simulated": packets_total,
            "errors_simulated": errors_total,
            "note": "SIMULATION - no real packets were sent"
        }
    }

    # Append to local log file and session
    append_log(final_entry)
    st.session_state['last_sim_result'] = final_entry

    st.success(f"Simulation finished — simulated packets: {packets_total}, simulated errors: {errors_total}")

    # Provide download of last log as JSON
    json_str = json.dumps(final_entry, indent=2)
    st.download_button("Download simulation log (JSON)", json_str, file_name=f"sim_log_{int(time.time())}.json", mime="application/json")

# Show last logs and export options
st.markdown("---")
st.subheader("Saved Simulation Logs")
logs = load_all_logs()
if logs:
    # show table with key columns
    df_logs = pd.DataFrame([{
        "time_utc": e.get("timestamp_utc") or e.get("timestamp"),
        "ssid": e['network'].get('ssid'),
        "bssid": e['network'].get('bssid'),
        "duration_s": e['simulation_params'].get('duration_s'),
        "packets_sim": e['results'].get('packets_sent_simulated')
    } for e in logs])
    st.dataframe(df_logs)

    # allow download of all logs
    all_json = "\n".join(json.dumps(e) for e in logs)
    st.download_button("Download all logs (.jsonl)", all_json, file_name="all_sim_logs.jsonl", mime="application/json")
else:
    st.info("No simulation logs yet. Run a simulation to create logs.")
