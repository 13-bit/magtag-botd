from io import BytesIO
import ssl
import wifi
import socketpool
import adafruit_requests as requests

import time
import terminalio
import displayio
import adafruit_imageload
from adafruit_bitmap_font import bitmap_font
from adafruit_display_text import label
from adafruit_magtag.magtag import MagTag

try:
    from secrets import secrets
except ImportError:
    print("WiFi secrets are kept in secrets.py, please add them there!")
    raise


def connect_wifi():
    wifi.radio.connect(secrets["ssid"], secrets["password"])

    print("My IP address is", wifi.radio.ipv4_address)

    socket = socketpool.SocketPool(wifi.radio)
    https = requests.Session(socket, ssl.create_default_context())

    return https


def download_botd_image():
    url = secrets["birdboard_server"] + "/static/botd.bmp"

    print("Fetching BOTD image from %s" % url)
    response = HTTPS_SESSION.get(url)
    print("GET complete")

    bytes_img = BytesIO(response.content)

    response.close()

    return bytes_img


def download_qr_image():
    url = secrets["birdboard_server"] + "/static/qr.bmp"

    print("Fetching QR code from %s" % url)
    response = HTTPS_SESSION.get(url)
    print("GET complete")

    bytes_img = BytesIO(response.content)

    response.close()

    return bytes_img


def get_botd_data():
    url = secrets["birdboard_server"] + "/botd"

    print("Fetching BOTD data from %s" % url)
    response = HTTPS_SESSION.get(url)
    print("GET complete")

    data = response.json()

    response.close()

    print("BOTD data:", data)

    return data


# ----------------------------
# Connect to the wifi and get the HTTPS session
# ----------------------------
HTTPS_SESSION = connect_wifi()

# ----------------------------
# Layout the UI
# ----------------------------
magtag = MagTag()

magtag.graphics.set_background("bmps/botd-bg.bmp")

# ----------------------------
# Display the scientific and common names
# ----------------------------
botd = get_botd_data()

font_monogram_14 = bitmap_font.load_font("fonts/monogram-14.pcf")
font_monogram_12 = bitmap_font.load_font("fonts/monogram-12.pcf")

common_name = label.Label(
    font_monogram_14, text=botd["bird"]["comName"], color=0x000000)
common_name.anchor_point = (0, 0.5)
common_name.anchored_position = (90, 92)

scientific_name = label.Label(
    font_monogram_12, text=botd["bird"]["sciName"], color=0x000000)
scientific_name.anchor_point = (0, 0.5)
scientific_name.anchored_position = (90, 106)

name_banner = displayio.Group()
name_banner.append(common_name)
name_banner.append(scientific_name)

magtag.splash.append(name_banner)

# ----------------------------
# Download and display the BOTD image
# ----------------------------
botd_bytes = download_botd_image()

botd_image, palette = adafruit_imageload.load(botd_bytes)
botd_tile_grid = displayio.TileGrid(botd_image, pixel_shader=palette, width=1,
                                    height=1, tile_width=100, tile_height=75, default_tile=0, x=194, y=2)

magtag.splash.append(botd_tile_grid)

# ----------------------------
# Download and display the QR Code image
# ----------------------------
qr_bytes = download_qr_image()

qr_image, palette = adafruit_imageload.load(qr_bytes)
qr_tile_grid = displayio.TileGrid(qr_image, pixel_shader=palette, width=1,
                                  height=1, tile_width=80, tile_height=80, default_tile=0, x=0, y=40)

magtag.splash.append(qr_tile_grid)

# refresh display
time.sleep(magtag.display.time_to_refresh + 1)
magtag.display.refresh()
time.sleep(magtag.display.time_to_refresh + 1)

print("Sleeping for %d seconds" % botd["untilTomorrow"])

magtag.exit_and_deep_sleep(botd["untilTomorrow"])
