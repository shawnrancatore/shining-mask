import supervisor
import random
import board
import adafruit_ble
import asynccp
from adafruit_ble.advertising.standard import ProvideServicesAdvertisement
from adafruit_ble.characteristics import Characteristic
from adafruit_ble.services.nordic import Service
import adafruit_nunchuk
from asynccp.time import Duration

from microcontroller import watchdog as w
from watchdog import WatchDogMode
w.timeout=2.5 # Set a timeout of 2.5 seconds
w.mode = WatchDogMode.RAISE
w.feed()
nc = None
while nc is None:
    try:
        nc = adafruit_nunchuk.Nunchuk(board.I2C())
    except:
        pass

key = b'\x32\x67\x2f\x79\x74\xad\x43\x45\x1d\x9c\x6c\x89\x4a\x0e\x87\x64'

try:
    from aesio import AES,MODE_ECB
    cipher = AES(key, MODE_ECB)
    def mask_encrypt(value):
        e_msg = bytearray(16)
        cipher.encrypt_into(value, e_msg)
        return e_msg
except ImportError:
    from Crypto.Cipher import AES
    from Crypto.Cipher.AES import MODE_ECB
    cipher = AES.new(key, MODE_ECB)
    def mask_encrypt(value):
        return cipher.encrypt(value)

from adafruit_ble.uuid import VendorUUID, StandardUUID

msgs = [mask_encrypt(b'\x06PLAY\x01\x03;\x97\xf2\xf3U\xa9r\x13\x8b'),
        mask_encrypt(b'\x06PLAY\x01\x04;\x97\xf2\xf3U\xa9r\x13\x8b'),
        mask_encrypt(b'\x06PLAY\x01\x03;\x97\xf2\xf3U\xa9r\x13\x8b')]


class MaskService(Service):
    # pylint: disable=no-member
    uuid = VendorUUID("0000fff0-0000-1000-8000-00805f9b34fb")
    play = Characteristic(uuid=VendorUUID("d44bc439-abfd-45a2-b575-925416129600"), properties=Characteristic.WRITE, max_length=128)
    def __init__(self, service=None):
        super().__init__(service=service)
        self.connectable = True

# PyLint can't find BLERadio for some reason so special case it here.
ble = adafruit_ble.BLERadio()  # pylint: disable=no-member


service = None

class FaceMask:
    def __init__(self):
        try:
            self.images = [ mask_encrypt(b'\x06PLAY\x01' + int(i+1).to_bytes(1,'big') + b';\x97\xf2\xf3U\xa9r\x13\x8b') for i in range(20)]
        except Exception as e:
            print('error setting up encrypted messages', e)
        self._init_mask_service()
        self.current_image = 1
        self.last_image = 2
        self.can_blink = True
    def send_image(self):
        if self.service:
            try:
                self.service.play = self.images[self.current_image]
                self.last_image = self.current_image
            except Exception as e:
                print('Error setting image ', e)
                if self.mask_connection and self.mask_connection.connected:
                    self.mask_connection.disconnect()
                self.mask_connection = None
                supervisor.reload()
                self._init_mask_service()
        else:
            if self.mask_connection and self.mask_connection.connected:
                try:
                    self.mask_connection.disconnect()
                except:
                    pass
            self.mask_connection = None
            self._init_mask_service()
    def set_image(self, id):
        self.current_image = id

    def _init_mask_service(self):
            while True:
                self.mask_connection = None
                try:
                    for adv in ble.start_scan(ProvideServicesAdvertisement, timeout=5):
                        if MaskService in adv.services:
                            self.mask_connection = ble.connect(adv)

                            if self.mask_connection and self.mask_connection.connected:
                                ble.stop_scan()
                                try:
                                    self.service =  self.mask_connection[MaskService]
                                    return
                                except Exception as e:
                                    print('ERR ', e)
                                    if self.mask_connection.connected:
                                        try:
                                            self.mask_connection.disconnect()
                                        except:
                                            pass
                                    self.mask_connection = None
                                    ble.stop_scan()
                                    break
                            else:
                                ble.stop_scan()
                                break
                except:
                    pass

resting_grin_frames = [2,4,6,8]
resting_smile_frames = [2,3]
mask = FaceMask()

async def update_mask():
    for i in range(10):
        if nc.buttons.C:
            mask.set_image(random.choice([0,1,8, 13,14,15,16,17,18,19]))
        else:
            x, y = nc.joystick
            if nc.buttons.Z:
                if mask.can_blink and random.randint(0,100) < 4:
                    for j in [6, 7,  7, 6]:
                        mask.set_image(j)
                        mask.send_image()
                        await asynccp.delay(1 / 12)
                    mask.can_blink = False
                if x > 200:
                    mask.set_image(5)
                elif x > 120:
                    mask.set_image(2)
                elif x < 50:
                    mask.set_image(4)
                elif x < 100:
                    mask.set_image(3)
            else:
                if mask.can_blink and random.randint(0,100) < 4:
                    for j in [12, 11, 11, 12]:
                        mask.set_image(j)
                        mask.send_image()
                        await asynccp.delay(1 / 12)
                    mask.can_blink = False
                if x > 200:
                    mask.set_image(10)
                elif x > 120:
                    mask.set_image(8)
                elif x < 50:
                    mask.set_image(9)
                elif x < 100:
                    mask.set_image(8)
        await asynccp.delay(1/10)
async def update_frame():
    mask.send_image()
async def allow_blink():
    mask.can_blink = True

asynccp.schedule(Duration.of_milliseconds(1000), coroutine_function=allow_blink)
asynccp.schedule(Duration.of_milliseconds(100), coroutine_function=update_mask)
asynccp.schedule(Duration.of_milliseconds(1000/24), coroutine_function=update_frame)

asynccp.run()