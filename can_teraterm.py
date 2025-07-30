import streamlit as st
import serial
import time
import pandas as pd
import struct
import io
import matplotlib.pyplot as plt
from tempfile import NamedTemporaryFile
import serial.tools.list_ports
from datetime import datetime
import threading

# Helper to decode signed 16-bit integers (big endian)
def decode_signed_16bit(b1, b2):
    return struct.unpack(">h", bytes([b1, b2]))[0]

CARDING, DF, FLYER = 1, 2, 3

st.set_page_config(layout="wide")
st.title("📡 CAN Logger, Decoder, and Visualizer")

# Sidebar: CAN Setup
st.sidebar.header("CAN Setup")

# Detect available serial ports
def get_available_ports():
    return [port.device for port in serial.tools.list_ports.comports()]

available_ports = get_available_ports()
serial_port = st.sidebar.selectbox("Select Serial Port", available_ports) if available_ports else None
if not serial_port:
    st.sidebar.warning("⚠️ No serial ports detected.")

baudrate = st.sidebar.number_input("Baud Rate", value=5600000)
machine_type = st.sidebar.selectbox("Machine Type", ("CARDING", "DF", "FLYER"))
machine = {"CARDING": CARDING, "DF": DF, "FLYER": FLYER}[machine_type]

# Setup CAN
def setup_can(serial_port, baudrate):
    try:
        ser = serial.Serial(serial_port, baudrate, timeout=1)
        time.sleep(2)
        cmds = [
            'can off\n',
            'conf set can.termination 0\n',
            'conf set can.bitrate 500000\n',
            'conf set can.fd_bitrate 1000000\n',
            'can on\n'
        ]
        for cmd in cmds:
            ser.write(cmd.encode())
            time.sleep(0.3)
        return ser
    except Exception as e:
        return str(e)

# Background logging function
def background_logger(ser, log_file_path, stop_event):
    while not stop_event.is_set():
        try:
            line = ser.readline().decode("utf-8", errors="ignore").strip()
            if line:
                timestamp = datetime.now().strftime("[%Y-%m-%d %H:%M:%S.%f]")[:-3]
                full_line = f"{timestamp} {line}"
                with open(log_file_path, "a") as f:
                    f.write(full_line + "\n")
        except Exception:
            pass

# Initialize state
if "is_logging" not in st.session_state:
    st.session_state.is_logging = False
if "ser" not in st.session_state:
    st.session_state.ser = None
if "log_file_path" not in st.session_state:
    st.session_state.log_file_path = None
if "log_thread" not in st.session_state:
    st.session_state.log_thread = None
if "stop_event" not in st.session_state:
    st.session_state.stop_event = None

# Connect button
if serial_port and not st.session_state.ser:
    if st.sidebar.button("🔌 Connect to CAN"):
        result = setup_can(serial_port, baudrate)
        if isinstance(result, serial.Serial):
            st.session_state.ser = result
            st.success("✅ Connected to CAN.")
        else:
            st.error(f"❌ Error: {result}")

# Start Logging
if st.session_state.ser and not st.session_state.is_logging:
    if st.sidebar.button("▶️ Start Logging"):
        st.session_state.is_logging = True
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        log_filename = f"can_log_{timestamp}.txt"
        st.session_state.log_file_path = log_filename

        st.session_state.stop_event = threading.Event()
        thread = threading.Thread(target=background_logger, args=(st.session_state.ser, log_filename, st.session_state.stop_event))
        thread.start()
        st.session_state.log_thread = thread
        st.success("✅ Logging started.")

# Stop Logging
if st.session_state.is_logging:
    if st.sidebar.button("⏹️ Stop Logging"):
        st.session_state.stop_event.set()
        st.session_state.log_thread.join()
        st.session_state.is_logging = False
        if st.session_state.ser:
            st.session_state.ser.close()
            st.session_state.ser = None
        st.success("✅ Logging stopped.")

# Download latest log
if st.session_state.log_file_path and not st.session_state.is_logging:
    try:
        with open(st.session_state.log_file_path, "rb") as f:
            st.download_button("📥 Download Latest Log", data=f, file_name=st.session_state.log_file_path, mime="text/plain")
    except FileNotFoundError:
        st.error("⚠️ Log file not found.")

# Upload section
st.header("📁 Upload CAN Log and DBC File")
log_file = st.file_uploader("Upload CAN log file", type=["txt", "log"])
dbc_file = st.file_uploader("Upload DBC .ods file", type=["ods"])
flyer_plan_file = st.file_uploader("(Optional) Upload Flyer Plan (.xlsx)", type=["xlsx"])

# Determine input log
log_input = None
if st.session_state.log_file_path and not st.session_state.is_logging:
    try:
        with open(st.session_state.log_file_path, "rb") as f:
            log_input = io.BytesIO(f.read())
    except:
        pass
if log_file:
    log_input = log_file

# Decoding logic (unchanged)
# [Your decoding logic starts here, kept as-is from original script]"


if log_input and dbc_file:
    functionIDs = pd.read_excel(dbc_file, engine="odf", index_col=0, sheet_name="FunctionID")
    CardingAddressIDs = pd.read_excel(dbc_file, engine="odf", index_col=0, sheet_name="Carding_IDs")
    DFAddressIDs = pd.read_excel(dbc_file, engine="odf", index_col=0, sheet_name="DF_IDs")
    FlyerAddressIDs = pd.read_excel(dbc_file, engine="odf", index_col=0, sheet_name="FF_IDs")
    Operations = pd.read_excel(dbc_file, engine="odf", index_col=0, sheet_name="Operation")
    Errors = pd.read_excel(dbc_file, engine="odf", index_col=2, sheet_name="Error")

    lines = log_input.read().decode("utf-8").splitlines()
    allDicts = []

    for line in lines:
        splits = line.split(" ")
        if 'rcv' in splits:
            try:
                linedict = {}
                date = splits[0][1:]
                time_str = splits[1][:-1]
                extID = splits[3]
                hexData = splits[4]
                source = extID[-2:]
                dst = extID[-4:-2]
                fID = extID[-6:-4]

                linedict.update({
                    "date": date,
                    "time": time_str,
                    "extID": extID,
                    "hexData": hexData,
                    "msgType": functionIDs.loc[str(fID), "msgType"]
                })

                machineIDs = {
                    CARDING: CardingAddressIDs,
                    DF: DFAddressIDs,
                    FLYER: FlyerAddressIDs
                }[machine]

                linedict["source"] = machineIDs.loc[str(source), "name"]
                linedict["dst"] = machineIDs.loc[str(dst), "name"]

                if linedict["msgType"] == "Operation":
                    linedict["OperationCommand"] = Operations.loc[str(hexData), "msgType"]
                elif linedict["msgType"] == "Error":
                    linedict["ErrorCommand"] = Errors.loc[int(str(hexData)), "msgType"]

                if machine == FLYER and len(hexData) >= 40:
                    try:
                        data_bytes = bytes.fromhex(hexData)
                        linedict.update({
                            "targetPosition": decode_signed_16bit(data_bytes[0], data_bytes[1]) / 100.0,
                            "presentPosition": decode_signed_16bit(data_bytes[2], data_bytes[3]) / 100.0,
                            "presentRPM": (data_bytes[4] << 8) | data_bytes[5],
                            "appliedDuty": (data_bytes[6] << 8) | data_bytes[7],
                            "FETtemp": data_bytes[8],
                            "MOTtemp": data_bytes[9],
                            "busCurrentADC": (data_bytes[10] << 8) | data_bytes[11],
                            "busVoltageADC": (data_bytes[12] << 8) | data_bytes[13],
                            "liftDirection": data_bytes[14],
                            "GBPresentPosition": decode_signed_16bit(data_bytes[15], data_bytes[16]) / 100.0,
                            "encPresentPosition": decode_signed_16bit(data_bytes[17], data_bytes[18]) / 100.0,
                            "usingPosition": data_bytes[19],
                        })

                        src = linedict.get("source", "").lower()
                        dst = linedict.get("dst", "").lower()
                        if "right" in src or "right" in dst:
                            linedict["LiftSide"] = "Right Lift"
                        elif "left" in src or "left" in dst:
                            linedict["LiftSide"] = "Left Lift"
                        else:
                            linedict["LiftSide"] = "Unknown Lift"

                    except Exception as decode_err:
                        st.warning(f"Flyer decoding error: {decode_err}")

                allDicts.append(linedict)

            except Exception as e:
                st.warning(f"Line parsing error: {e}")

    df = pd.DataFrame(allDicts)
    st.success("✅ Log processed.")
    st.dataframe(df.head(50), height=400)

    csv = df.to_csv(index=False).encode('utf-8')
    st.download_button("📅 Download Decoded CSV", csv, "decoded_log.csv", "text/csv")

    if "LiftSide" in df.columns:
        right_df = df[df["LiftSide"] == "Right Lift"]
        left_df = df[df["LiftSide"] == "Left Lift"]

        with NamedTemporaryFile(delete=False, suffix=".xlsx") as tmp:
            with pd.ExcelWriter(tmp.name, engine="xlsxwriter") as writer:
                right_df.to_excel(writer, sheet_name="Right Lift", index=False)
                left_df.to_excel(writer, sheet_name="Left Lift", index=False)

            with open(tmp.name, "rb") as f:
                st.download_button(
                    "📅 Download Left/Right Lift Sheets",
                    data=f,
                    file_name="lift_sheets.xlsx",
                    mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
                )

    st.subheader("📊 Plot Numeric Data")
    if "LiftSide" in df.columns:
        lift_filter = st.selectbox("Filter by Lift Side", ["All", "Right Lift", "Left Lift"])
        filtered_df = df[df["LiftSide"] == lift_filter] if lift_filter != "All" else df
    else:
        filtered_df = df

    numeric_columns = filtered_df.select_dtypes(include="number").columns.tolist()
    selected_cols = st.multiselect("Select numeric columns to plot", numeric_columns)

    if selected_cols:
        fig, ax = plt.subplots()
        for col in selected_cols:
            filtered_df[col].plot(ax=ax, label=col)
        ax.set_title(f"Plot ({lift_filter})")
        ax.legend()
        st.pyplot(fig)

    if machine == FLYER and flyer_plan_file:
        flyer_df = pd.read_excel(flyer_plan_file)
        st.subheader("📋 Flyer Communication Plan")
        st.dataframe(flyer_df.head())
