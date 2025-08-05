
CAN Logger, Decoder, and Visualizer

This Streamlit-based application allows you to **log**, **decode**, and **visualize** CAN messages from industrial machines such as **CARDING**, **DF**, and **FLYER**. It supports both **real-time logging via serial port** and **offline decoding via uploaded logs**.


Features

* Connect to a CAN interface via a serial port.
* Start/Stop real-time CAN logging with automatic timestamping.
* Decode messages using a user-provided `.ods` DBC file.
* Supports machine-specific decoding logic (CARDING, DF, FLYER).
* Upload previously recorded CAN logs for decoding.
* Export decoded data to **CSV** or **Excel** format.
* Visualize numeric signals in time-series plots.
* Split FLYER lift data into **Left** and **Right** sheets.
* Optional support for uploading FLYER plan `.xlsx` files.

---
How to Use
 1. Prerequisites

* Python 3.8+
* Required packages (install using pip):

```bash
pip install streamlit pandas matplotlib pyserial openpyxl odfpy xlsxwriter
```

---

2. Running the App

```bash
streamlit run can_teraterm.py
```

---

 3. App Workflow

🔌 Connect to CAN

1. Open the sidebar.
2. Select the serial port from the list.
3. Set baud rate (default: `5600000`).
4. Select your **machine type** (CARDING, DF, or FLYER).
5. Click **"🔌 Connect to CAN"** to initialize the serial connection.

 Start Logging

* Click **"▶️ Start Logging"** to begin capturing CAN data.
* Data is logged with timestamps in a `.txt` file.
* Click **"⏹️ Stop Logging"** to end logging.
* Download the logged file if needed.

 📁 Upload Log & DBC Files

* Upload:

  * CAN Log file (`.txt` or `.log`)
  * DBC `.ods` file (must contain correct sheet names)
  * (Optional) FLYER plan file (`.xlsx`)
* Sheets expected in DBC `.ods`:

  * `FunctionID`
  * `Carding_IDs`
  * `DF_IDs`
  * `FF_IDs`
  * `Operation`
  * `Error`

✅ Decoding and Output

* Messages are decoded into a table with interpreted values.
* Download decoded data:

  * As **CSV**
  * As Excel with **Left** and **Right** Lift data (for FLYER only)

 📊 Visualization

* Select numeric columns to plot.
* Optionally filter by **Lift Side**.
* View time-series plots of selected signals.

---

🧾 File Structure

```
app.py                     # Main Streamlit app
can_log_<timestamp>.txt    # Auto-saved CAN log
decoded_log.csv            # Downloaded decoded CSV
lift_sheets.xlsx           # (Optional) Split Excel for Flyer lift data
```

---

 📌 Notes

* If no serial port is detected, try reconnecting your device.
* The `dbc_file` must follow the expected format; otherwise, decoding will fail.
* Flyer decoding assumes specific byte mapping – ensure compatibility.

---

🛠️ Troubleshooting

* **"No serial ports detected"**: Ensure your CAN USB device is connected.
* **"Flyer decoding error" or "Line parsing error"**: Check if log format and hex data are valid.
* **"Log file not found"**: Make sure you stop logging before trying to download the file.

---

