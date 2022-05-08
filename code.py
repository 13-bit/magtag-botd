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

    print("Connecting to %s from %s" % (secrets["ssid"], wifi.radio.ipv4_address), end ="... ")

    socket = socketpool.SocketPool(wifi.radio)
    https = requests.Session(socket, ssl.create_default_context())

    print("Done.")

    return https

def time_to_sleep():
    TIME_URL = "https://io.adafruit.com/api/v2/%s/integrations/time/struct?x-aio-key=%s&tz=%s" % (aio_username, aio_key, aio_timezone)

    response = HTTPS_SESSION.get(TIME_URL)
    time_json = response.json()

    now = time.struct_time(
        (time_json["year"], time_json["mon"], time_json["mday"], time_json["hour"], time_json["min"], time_json["sec"], time_json["wday"], time_json["yday"], time_json["isdst"])
    )

    wake = time.struct_time(
        (now[0], now[1], now[2], 5, 0, 0, -1, -1, now[8])
    )

    to_sleep = time.mktime(wake) - time.mktime(now)

    if to_sleep < 0:
        to_sleep += 24 * 60 * 60

    return to_sleep, str(wake)

def download_botd_image():
    url = secrets["birdboard_server"] + "/static/botd.bmp"

    print("Fetching BOTD image from %s" % url, end ="... ")
    response = HTTPS_SESSION.get(url)
    print("Done.")

    bytes_img = BytesIO(response.content)

    response.close()

    return bytes_img


def download_qr_image():
    url = secrets["birdboard_server"] + "/static/qr.bmp"

    print("Fetching QR code from %s" % url, end ="... ")
    response = HTTPS_SESSION.get(url)
    print("Done.")

    bytes_img = BytesIO(response.content)

    response.close()

    return bytes_img

def download_life_history_image():
    url = secrets["birdboard_server"] + "/static/life-history.bmp"

    print("Fetching life history image from %s" % url, end ="... ")
    response = HTTPS_SESSION.get(url)
    print("Done.")

    bytes_img = BytesIO(response.content)

    response.close()

    return bytes_img

def get_botd_data():
    url = secrets["birdboard_server"] + "/botd"

    print("Fetching BOTD data from %s" % url, end ="... ")
    response = HTTPS_SESSION.get(url)
    print("Done.")

    data = response.json()

    response.close()

    print("BOTD data:", data)

    return data

# Instantiate the MagTag
magtag = MagTag()

# Connect to wifi and get the HTTPS session
HTTPS_SESSION = connect_wifi()

# Secrets
aio_username = secrets["aio_username"]
aio_key = secrets["aio_key"]
aio_timezone = secrets["timezone"]

# Layout the UI
neopixel_colors = ((235, 61, 0), (235, 61, 0), (235, 61, 0), (235, 61, 0))
magtag.peripherals.neopixel_disable = False

magtag.peripherals.neopixels[0] = neopixel_colors[0]
magtag.peripherals.neopixels[1] = neopixel_colors[1]
magtag.peripherals.neopixels[2] = neopixel_colors[2]
magtag.peripherals.neopixels[3] = neopixel_colors[3]
magtag.peripherals.neopixels.show()

magtag.graphics.set_background("bmps/botd-bg.bmp")

# Display the scientific and common names
botd = get_botd_data()

font_common_name = bitmap_font.load_font("fonts/envypn7x15.bdf")
font_scientific_name = bitmap_font.load_font("fonts/envypn7x13.bdf")

common_name = label.Label(
    font_common_name, text=botd["bird"]["comName"], color=0x000000)
common_name.anchor_point = (0, 0.5)
common_name.anchored_position = (90, 92)

scientific_name = label.Label(
    font_scientific_name, text=botd["bird"]["sciName"], color=0x000000)
scientific_name.anchor_point = (0, 0.5)
scientific_name.anchored_position = (90, 106)

name_banner = displayio.Group()
name_banner.append(common_name)
name_banner.append(scientific_name)

magtag.splash.append(name_banner)

# Download and display the BOTD image
botd_bytes = download_botd_image()

botd_image, palette = adafruit_imageload.load(botd_bytes)
botd_tile_grid = displayio.TileGrid(botd_image, pixel_shader=palette, width=1,
                                    height=1, tile_width=100, tile_height=75, default_tile=0, x=194, y=2)

magtag.splash.append(botd_tile_grid)

# Download and display the life history image
lh_bytes = download_life_history_image()

lh_image, palette = adafruit_imageload.load(lh_bytes)
lh_tile_grid = displayio.TileGrid(lh_image, pixel_shader=palette, width=1,
                                    height=1, tile_width=76, tile_height=76, default_tile=0, x=100, y=2)

magtag.splash.append(lh_tile_grid)

# Download and display the QR Code image
qr_bytes = download_qr_image()

qr_image, palette = adafruit_imageload.load(qr_bytes)
qr_tile_grid = displayio.TileGrid(qr_image, pixel_shader=palette, width=1,
                                  height=1, tile_width=80, tile_height=80, default_tile=0, x=0, y=40)

magtag.splash.append(qr_tile_grid)

# refresh display
time.sleep(magtag.display.time_to_refresh + 1)
magtag.display.refresh()
time.sleep(magtag.display.time_to_refresh + 1)

until_tomorrow, wake = time_to_sleep()

print("Sleeping for %d seconds until %s" % (until_tomorrow, wake))

magtag.peripherals.neopixel_disable = True

magtag.exit_and_deep_sleep(until_tomorrow)
