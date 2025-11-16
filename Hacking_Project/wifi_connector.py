# app.py
import time
import streamlit as st
from pywifi import PyWiFi, const, Profile

st.set_page_config(page_title="Wi-Fi Connector (pywifi + Streamlit)", layout="centered")

# --- Helpers ---
def get_interface():
    wifi = PyWiFi()
    ifaces = wifi.interfaces()
    if not ifaces:
        return None
    return ifaces[0]   # default: first wireless interface

def scan_networks(iface, scan_wait=2):
    """Trigger scan and return list of networks (unique SSIDs)."""
    try:
        iface.scan()
    except Exception as e:
        st.error(f"Scan failed: {e}")
        return []
    time.sleep(scan_wait)  # allow some time for scan to complete
    try:
        results = iface.scan_results()
    except Exception as e:
        st.error(f"Failed to get scan results: {e}")
        return []

    # gather unique SSIDs (keep strongest signal if duplicates)
    seen = {}
    for r in results:
        ssid = r.ssid or "<hidden>"
        # signal attribute may be named 'signal' or 'rssi' depending on platform/pywifi; handle gracefully
        sig = getattr(r, "signal", None)
        if sig is None:
            sig = getattr(r, "rssi", None)
        # keep strongest
        if ssid not in seen or (sig is not None and (seen[ssid]["signal"] is None or sig > seen[ssid]["signal"])):
            seen[ssid] = {"ssid": ssid, "bssid": getattr(r, "bssid", None), "signal": sig, "akm": getattr(r, "akm", None)}
    # return sorted by signal desc if available
    networks = list(seen.values())
    networks.sort(key=lambda x: (x["signal"] is None, -(x["signal"] or 0)))
    return networks

def build_profile(ssid, password, hidden=False):
    p = Profile()
    p.ssid = ssid
    p.hidden = hidden
    p.auth = const.AUTH_ALG_OPEN
    # try common AKM types
    try:
        p.akm.append(const.AKM_TYPE_WPA2PSK)
        p.akm.append(const.AKM_TYPE_WPAPSK)
    except Exception:
        pass
    p.cipher = const.CIPHER_TYPE_CCMP
    p.key = password
    return p

def connect_to_network(iface, ssid, password, timeout=20, hidden=False):
    # Remove existing profiles optionally (safer to not remove all in some environments)
    try:
        iface.remove_all_network_profiles()
    except Exception:
        pass

    profile = build_profile(ssid, password, hidden)
    tmp = iface.add_network_profile(profile)

    try:
        iface.connect(tmp)
    except Exception as e:
        return False, f"Connect failed: {e}"

    start = time.time()
    while time.time() - start < timeout:
        st.session_state["last_status_poll"] = time.time()
        state = iface.status()
        # const.IFACE_CONNECTED typically equals 4
        if state == const.IFACE_CONNECTED:
            return True, "Connected"
        time.sleep(1)
    # timeout
    try:
        iface.disconnect()
    except Exception:
        pass
    return False, "Connection timed out or wrong password"

# --- Streamlit UI ---
st.title("📶 Wi-Fi Connector (pywifi + Streamlit)")

if "networks" not in st.session_state:
    st.session_state["networks"] = []
if "selected_ssid" not in st.session_state:
    st.session_state["selected_ssid"] = None
if "connect_result" not in st.session_state:
    st.session_state["connect_result"] = None

iface = get_interface()
if iface is None:
    st.error("No wireless interface found. Ensure your Wi-Fi adapter is enabled and drivers are installed.")
    st.stop()
else:
    st.info(f"Using interface: {iface.name()}")

col1, col2 = st.columns([2,1])
with col1:
    if st.button("🔄 Scan for networks"):
        st.session_state["connect_result"] = None
        st.session_state["networks"] = scan_networks(iface)
    if not st.session_state["networks"]:
        st.write("Scan results empty — क्लिक करें 'Scan for networks' या ensure Wi-Fi is on.")
    else:
        st.write("Available networks:")
        for net in st.session_state["networks"]:
            ss = net["ssid"]
            sig = net["signal"]
            sig_str = f"{sig} dBm" if sig is not None else "N/A"
            btn_key = f"btn_{ss}"
            cols = st.columns([6,1,2])
            cols[0].markdown(f"**{ss}**")
            cols[1].markdown(f"`{sig_str}`")
            if cols[2].button("Select", key=btn_key):
                st.session_state["selected_ssid"] = ss
                st.session_state["connect_result"] = None

with col2:
    st.write("Controls")
    st.write("Selected SSID:")
    st.write(st.session_state["selected_ssid"] or "—")
    if st.session_state["selected_ssid"]:
        with st.form("connect_form"):
            pwd = st.text_input("Enter password", type="password")
            hidden_chk = st.checkbox("Hidden SSID", value=False)
            timeout = st.number_input("Timeout seconds", min_value=5, max_value=120, value=25)
            submitted = st.form_submit_button("Connect")
            if submitted:
                ssid = st.session_state["selected_ssid"]
                st.session_state["connect_result"] = None
                with st.spinner(f"Trying to connect to {ssid} ..."):
                    ok, msg = connect_to_network(iface, ssid, pwd, timeout=timeout, hidden=hidden_chk)
                    st.session_state["connect_result"] = (ok, msg)
    if st.session_state["connect_result"]:
        ok, msg = st.session_state["connect_result"]
        if ok:
            st.success(f"{msg}")
        else:
            st.error(f"{msg}")

st.markdown("---")
st.caption("Note: Run Streamlit with admin/root if connection/scan fails. macOS support for pywifi may be limited.")
