# wifi_security_book.py
# By Aniket (safe + legal demos only)

import streamlit as st
import subprocess
import platform
import hashlib
import time
import io
from textwrap import dedent
import matplotlib.pyplot as plt
import networkx as nx

st.set_page_config(
    page_title="Wi-Fi Security Knowledge Book",
    layout="wide",
    page_icon="📘"
)

IS_WINDOWS = platform.system() == "Windows"

# ---------- Global Styles ----------
CUSTOM_CSS = """
<style>
/* Subtle card feel */
.block-container { padding-top: 1.2rem; }
div[data-testid="stMarkdownContainer"] h2 { margin-top: .6rem; }
div[data-testid="stStatusWidget"] { border-radius: 14px !important; }
.kb-callout {
  padding: 12px 16px; border-radius: 14px;
  background: #f3f6ff; border: 1px solid #dbe3ff; margin-bottom: 10px;
}
.kb-note {
  padding: 10px 14px; border-radius: 10px;
  background: #f9f9fb; border: 1px dashed #d0d0d5; margin: 8px 0;
}
.kb-badge {
  display:inline-block; padding:2px 8px; border-radius:100px;
  font-size:12px; border:1px solid #ddd; margin-right:6px; background:#fff;
}
hr { border: none; border-top: 1px solid #eee; margin: 10px 0 4px 0;}
.small { font-size: 13px; color:#6b7280; }
pre, code { font-size: 13px !important; }
</style>
"""
st.markdown(CUSTOM_CSS, unsafe_allow_html=True)

# ---------- Helpers ----------
def code_download_button(filename: str, code: str, key: str):
    st.download_button(
        "Download code",
        data=dedent(code).encode("utf-8"),
        file_name=filename,
        mime="text/x-python",
        key=key
    )

def show_code_block(code: str):
    st.code(dedent(code), language="python")

def draw_network_diagram(title="Wi-Fi Topology", risk=False):
    """Simple network diagram with optional risk highlight."""
    G = nx.Graph()
    # Nodes
    G.add_node("Router/AP", kind="ap")
    G.add_node("Laptop", kind="client")
    G.add_node("Phone", kind="client")
    G.add_node("IoT Cam", kind="client")
    # Edges
    G.add_edge("Laptop", "Router/AP")
    G.add_edge("Phone", "Router/AP")
    G.add_edge("IoT Cam", "Router/AP")

    pos = nx.spring_layout(G, seed=7)
    node_colors = []
    for n, data in G.nodes(data=True):
        if data["kind"] == "ap":
            node_colors.append("#10b981" if not risk else "#ef4444")
        else:
            node_colors.append("#3b82f6")
    edge_colors = "#ef4444" if risk else "#94a3b8"

    plt.figure(figsize=(5.4, 4.2))
    nx.draw(
        G, pos, with_labels=True,
        node_color=node_colors,
        edge_color=edge_colors,
        node_size=1800, font_color="white", font_size=10
    )
    plt.title(title)
    st.pyplot(plt.gcf())
    plt.close()

def draw_attack_path_diagram():
    """Shows a conceptual path: Scan -> Collect Info -> Target Weakness -> (Simulated) Crack."""
    G = nx.DiGraph()
    G.add_edge("Scan SSIDs", "Collect Metadata")
    G.add_edge("Collect Metadata", "Pick Target (Weak/WPS)")
    G.add_edge("Pick Target (Weak/WPS)", "Simulated Guessing\n(Demo Hash)")
    pos = nx.spring_layout(G, seed=11)
    colors = ["#60a5fa", "#34d399", "#f59e0b", "#6366f1"]

    plt.figure(figsize=(6.2, 3.6))
    nx.draw(
        G, pos, with_labels=True,
        node_color=["#60a5fa", "#34d399", "#f59e0b", "#a78bfa"][:len(G.nodes())],
        node_size=1800, font_color="white", font_size=10, arrows=True
    )
    plt.title("Conceptual Attack Path (Theory Only)")
    st.pyplot(plt.gcf())
    plt.close()

def draw_crypto_overview():
    """Mini diagram of WPA2/WPA3 at a very high level."""
    G = nx.DiGraph()
    G.add_node("Client")
    G.add_node("AP")
    G.add_edge("Client", "AP", label="Handshake\n(Nonce/Keys)")
    G.add_edge("AP", "Client", label="Encrypted Frames\n(AES-CCMP/GCMP)")

    pos = nx.spring_layout(G, seed=2)
    plt.figure(figsize=(5.2, 3.6))
    nx.draw(
        G, pos, with_labels=True,
        node_color=["#0ea5e9", "#10b981"],
        node_size=1800, font_color="white", font_size=10, arrows=True
    )
    edge_labels = nx.get_edge_attributes(G, 'label')
    nx.draw_networkx_edge_labels(G, pos, edge_labels=edge_labels, font_size=9)
    plt.title("WPA2/WPA3 (Very High Level)")
    st.pyplot(plt.gcf())
    plt.close()

def safe_windows_only():
    if not IS_WINDOWS:
        st.warning("This live demo uses Windows commands (netsh). Try on a Windows laptop with Wi-Fi enabled.")
        return False
    return True

# ---------- Session state for Previous/Next ----------
if "chapter_idx" not in st.session_state:
    st.session_state.chapter_idx = 0

CHAPTERS = [
    "Intro",
    "How Wi-Fi Security Works",
    "Scan Nearby Networks (Live)",
    "Show Saved Wi-Fi Passwords (Live, Your PC)",
    "Forget a Wi-Fi Profile (Live, Your PC)",
    "Dictionary Attack (Safe Simulation)",
    "Glossary",
    "Best Practices"
]

st.sidebar.title("Chapters")
choice = st.sidebar.radio("Navigate", CHAPTERS, index=st.session_state.chapter_idx)

def goto(delta: int):
    idx = CHAPTERS.index(choice) + delta
    idx = max(0, min(len(CHAPTERS) - 1, idx))
    st.session_state.chapter_idx = idx
    st.experimental_rerun()

# ---------- Legal banner ----------
st.markdown(
    """
<div class="kb-callout">
<b>Safety note:</b> This app is for learning and demonstrations only.
It does <b>not</b> hack other networks. Live features show information from your own system.
Avoid real cracking, deauth, or packet injection. Stay ethical.
</div>
""",
    unsafe_allow_html=True
)

# ---------- CHAPTER: Intro ----------
if choice == "Intro":
    st.title("📘 Wi-Fi Security Knowledge Book (Student Edition)")
    col1, col2 = st.columns([1, 1])
    with col1:
        st.markdown("""
**What you'll learn**
- How scanning works (listing nearby SSIDs)
- How saved Wi-Fi passwords can be read on **your own** Windows PC
- How to forget profiles from **your own** PC
- Why weak passwords fail (safe dictionary simulation)
        """)
        st.markdown('<span class="kb-badge">Legal</span><span class="kb-badge">Beginner-friendly</span><span class="kb-badge">Live Demos</span>', unsafe_allow_html=True)
    with col2:
        draw_network_diagram("Your Home/College Network (Example)")

    draw_attack_path_diagram()

# ---------- CHAPTER: How Wi-Fi Security Works ----------
elif choice == "How Wi-Fi Security Works":
    st.header("🔐 How Wi-Fi Security Works (High Level)")
    tabs = st.tabs(["Explanation", "Diagram", "Code (Educational Snippets)"])

    with tabs[0]:
        st.write("""
**Quick overview**
- Modern Wi-Fi uses **WPA2 or WPA3**.
- A 4-way handshake derives session keys, then frames are **encrypted**.
- Attacks often rely on **weak passwords**, **misconfigurations**, or **social engineering**.
- Real cracking requires captured handshakes and heavy compute — not included here.
        """)
        st.info("Focus your talk on password strength, firmware updates, and turning off WPS.")

    with tabs[1]:
        draw_crypto_overview()
        st.caption("We avoid live capture. This is a conceptual diagram for class.")

    with tabs[2]:
        snippet = """
# Pseudocode only — not capturing any traffic
def handshake_overview():
    ssid = "MyNetwork"
    # 1) Client & AP share SSID; AP advertises network
    # 2) 4-way handshake derives keys (PTK) based on passphrase & nonces
    # 3) Encrypted traffic begins
    pass
        """
        show_code_block(snippet)
        code_download_button("handshake_overview.py", snippet, key="dl_hs")

# ---------- CHAPTER: Scan Nearby Networks (Live) ----------
elif choice == "Scan Nearby Networks (Live)":
    st.header("📡 Scan Nearby Networks (Live)")
    tabs = st.tabs(["Explanation", "Live Demo", "Code"])

    with tabs[0]:
        st.write("""
Scanning lists visible SSIDs and sometimes BSSID/RSSI. This is **legal** and does **not** reveal passwords.
On Windows we use `netsh wlan show network mode=bssid`.
        """)

    with tabs[1]:
        if safe_windows_only():
            if st.button("🔍 Scan Now"):
                try:
                    out = subprocess.check_output(
                        ["netsh", "wlan", "show", "network", "mode=Bssid"],
                        stderr=subprocess.STDOUT
                    ).decode("utf-8", errors="backslashreplace")

                    # Parse SSIDs (basic)
                    ssids = []
                    for line in out.splitlines():
                        line = line.strip()
                        if line.startswith("SSID ") and ":" in line:
                            ssid = line.split(":", 1)[1].strip()
                            if ssid and ssid not in ssids:
                                ssids.append(ssid)

                    if ssids:
                        st.success(f"Found {len(ssids)} network(s).")
                        st.table({"SSID": ssids})
                    else:
                        st.warning("No networks found. Ensure Wi-Fi is on.")
                except Exception as e:
                    st.error(f"Scan failed: {e}")
        draw_network_diagram("Scan Perspective (Safe)")

    with tabs[2]:
        code = """
import subprocess

out = subprocess.check_output(
    ["netsh", "wlan", "show", "network", "mode=Bssid"],
    stderr=subprocess.STDOUT
).decode("utf-8", errors="backslashreplace")

ssids = []
for line in out.splitlines():
    line = line.strip()
    if line.startswith("SSID ") and ":" in line:
        ssid = line.split(":", 1)[1].strip()
        if ssid and ssid not in ssids:
            ssids.append(ssid)

print("\\n".join(ssids))
        """
        show_code_block(code)
        code_download_button("scan_networks_windows.py", code, key="dl_scan")

# ---------- CHAPTER: Show Saved Wi-Fi Passwords (Live, Your PC) ----------
elif choice == "Show Saved Wi-Fi Passwords (Live, Your PC)":
    st.header("🔑 Show Saved Wi-Fi Passwords (Your Windows PC)")
    tabs = st.tabs(["Explanation", "Live Demo", "Code"])

    with tabs[0]:
        st.write("""
On Windows, saved Wi-Fi profiles can be listed and shown (with key=clear) **for your own PC only**.
Use this to teach how device compromise can expose stored keys.
        """)
        st.warning("Use this only on **your** computer during the seminar.")

    with tabs[1]:
        if safe_windows_only():
            colA, colB = st.columns([1, 1])
            with colA:
                if st.button("📂 List Profiles"):
                    try:
                        profiles = subprocess.check_output(
                            ["netsh", "wlan", "show", "profiles"]
                        ).decode("utf-8", errors="backslashreplace").splitlines()
                        names = [ln.split(":", 1)[1].strip()
                                 for ln in profiles if "All User Profile" in ln]
                        if names:
                            st.table({"Saved Profiles": names})
                        else:
                            st.info("No profiles found.")
                    except Exception as e:
                        st.error(f"Error: {e}")

            with colB:
                target = st.text_input("Profile name to reveal password")
                if st.button("🔐 Show Password"):
                    if not target:
                        st.warning("Enter a profile name first.")
                    else:
                        try:
                            detail = subprocess.check_output(
                                ["netsh", "wlan", "show", "profile", target, "key=clear"]
                            ).decode("utf-8", errors="backslashreplace")
                            pwd = ""
                            for ln in detail.splitlines():
                                if "Key Content" in ln:
                                    pwd = ln.split(":", 1)[1].strip()
                                    break
                            st.success(f"Password: {pwd or '(blank/not stored)'}")
                        except Exception as e:
                            st.error(f"Error: {e}")
        draw_network_diagram("Saved Password Risk (Concept)", risk=True)

    with tabs[2]:
        code = """
import subprocess

# List profiles
profiles_out = subprocess.check_output(
    ["netsh", "wlan", "show", "profiles"]
).decode("utf-8", errors="backslashreplace").splitlines()

profiles = [ln.split(":",1)[1].strip()
            for ln in profiles_out if "All User Profile" in ln]
print("Profiles:", profiles)

# Show one password
name = input("Profile to reveal: ").strip()
if name:
    detail = subprocess.check_output(
        ["netsh", "wlan", "show", "profile", name, "key=clear"]
    ).decode("utf-8", errors="backslashreplace")

    pwd = ""
    for ln in detail.splitlines():
        if "Key Content" in ln:
            pwd = ln.split(":", 1)[1].strip()
            break
    print("Password:", pwd or "(blank/not stored)")
        """
        show_code_block(code)
        code_download_button("show_saved_wifi_passwords_windows.py", code, key="dl_saved")

# ---------- CHAPTER: Forget a Wi-Fi Profile (Live, Your PC) ----------
elif choice == "Forget a Wi-Fi Profile (Live, Your PC)":
    st.header("🧹 Forget a Wi-Fi Profile (Your Windows PC)")
    tabs = st.tabs(["Explanation", "Live Demo", "Code"])

    with tabs[0]:
        st.write("""
Forgetting a profile removes stored credentials on **your** device. Good to show automation and hygiene.
        """)

    with tabs[1]:
        if safe_windows_only():
            profile_name = st.text_input("Wi-Fi profile name to forget")
            if st.button("🗑️ Forget Profile"):
                if not profile_name:
                    st.warning("Enter a profile name.")
                else:
                    try:
                        subprocess.run(
                            ["netsh", "wlan", "delete", "profile", f"name={profile_name}"],
                            check=True
                        )
                        st.success(f"Profile '{profile_name}' forgotten on this PC.")
                    except Exception as e:
                        st.error(f"Error: {e}")
        draw_network_diagram("Profile Cleanup (Safe)")

    with tabs[2]:
        code = """
import subprocess

name = input("Profile to forget: ").strip()
if name:
    subprocess.run(["netsh", "wlan", "delete", "profile", f"name={name}"], check=True)
    print(f"Forgot profile: {name}")
        """
        show_code_block(code)
        code_download_button("forget_wifi_profile_windows.py", code, key="dl_forget")

# ---------- CHAPTER: Dictionary Attack (Safe Simulation) ----------
elif choice == "Dictionary Attack (Safe Simulation)":
    st.header("📖 Dictionary Attack (Safe Simulation)")
    tabs = st.tabs(["Explanation", "Live Demo", "Code"])

    with tabs[0]:
        st.write("""
Real Wi-Fi cracking needs a captured handshake and specialized tools.  
Here we simulate **hash guessing** to show why weak passwords are risky.
        """)
        st.info("No network traffic, no packet capture, no actual Wi-Fi involvement.")

    with tabs[1]:
        secret = st.text_input("Enter a demo secret (e.g., tiger@123)")
        wl_default = ["123456", "password", "tiger", "tiger123", "tiger@123", "admin", "hello123"]
        custom_list = st.text_area("Wordlist (optional, one per line)", value="\n".join(wl_default), height=140)

        if st.button("▶️ Run Simulation"):
            if not secret:
                st.warning("Enter a secret first.")
            else:
                salt = "seminar-salt"
                stored_hash = hashlib.sha256((salt + secret).encode()).hexdigest()
                st.code(f"Stored Hash: {stored_hash}\nSalt: {salt}")

                words = [w.strip() for w in custom_list.splitlines() if w.strip()]
                start = time.time()
                found = None
                attempts = 0
                prog = st.progress(0)
                for i, word in enumerate(words, 1):
                    attempts = i
                    test_hash = hashlib.sha256((salt + word).encode()).hexdigest()
                    if i % max(1, len(words)//100) == 0:
                        prog.progress(min(100, int((i/len(words))*100)))
                    if test_hash == stored_hash:
                        found = (word, i, time.time() - start)
                        break

                if found:
                    st.success(f"Found: {found[0]}  | Attempts: {found[1]}  | Time: {found[2]:.3f}s")
                else:
                    st.warning(f"Not found in {attempts} guesses. Use stronger passphrases!")

        draw_attack_path_diagram()

    with tabs[2]:
        code = """
import hashlib, time

secret = input("Enter demo secret: ").strip()
salt = "seminar-salt"
stored_hash = hashlib.sha256((salt + secret).encode()).hexdigest()
print("Hash =", stored_hash)

wordlist = ["123456","password","tiger","tiger123","tiger@123","admin","hello123"]

start = time.time()
for i, word in enumerate(wordlist, 1):
    test = hashlib.sha256((salt + word).encode()).hexdigest()
    if test == stored_hash:
        print(f"Found {word} in {i} guesses, time={time.time()-start:.3f}s")
        break
else:
    print("Not found in small list.")
        """
        show_code_block(code)
        code_download_button("dictionary_attack_simulation.py", code, key="dl_dict")

# ---------- CHAPTER: Glossary ----------
elif choice == "Glossary":
    st.header("📚 Glossary (Student Friendly)")
    st.markdown("""
- **SSID**: Wi-Fi network name that devices see when scanning.  
- **BSSID**: MAC address of the access point radio.  
- **RSSI**: Signal strength indicator; higher (closer to 0) is stronger.  
- **WPA2 / WPA3**: Security standards for encrypting Wi-Fi traffic.  
- **Handshake**: Exchange between client and AP to derive session keys.  
- **Dictionary Attack**: Trying many passwords from a list until one works.  
- **WPS**: Wi-Fi Protected Setup; convenient but often risky — disable it.  
- **Deauth**: A frame type that can disconnect clients (don’t do this; illegal without permission).  
    """)
    draw_crypto_overview()

# ---------- CHAPTER: Best Practices ----------
elif choice == "Best Practices":
    st.header("🛡 Best Practices (Protect Your Wi-Fi)")
    st.markdown("""
- Use **WPA3** if available, else **WPA2-AES**.  
- Create a long passphrase (3–4 random words + symbols).  
- **Disable WPS** on the router.  
- Update router firmware regularly.  
- Change default admin username/password of the router.  
- Separate **guest network** for visitors/IoT devices.  
- Turn off unused services (remote mgmt, UPnP if not needed).  
- Educate users about phishing and fake hotspots.
    """)
    draw_network_diagram("Hardened Home Network", risk=False)

# ---------- Prev / Next ----------
st.write("")
col_prev, col_sp, col_next = st.columns([1, 8, 1])
with col_prev:
    if st.button("◀ Previous"):
        goto(-1)
with col_next:
    if st.button("Next ▶"):
        goto(1)

st.markdown('<div class="small">Built for seminars. Safe, legal, and beginner friendly.</div>', unsafe_allow_html=True)
