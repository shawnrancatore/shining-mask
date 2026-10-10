# Shining Mask

**Drive an LED face mask from a Wii Nunchuk, with a CircuitPython board in between.**

<!-- bricoleur:intro -->
<!-- /bricoleur:intro -->

![A Meeseeks face on the LED mask, changing as the joystick moves](./examples/MeeseeksMask/MeeseeksMaskInAction.gif?raw=true "Look at me!")

## What it does

- Reads a Wii Nunchuk's joystick and its C and Z buttons over I2C.
- Turns them into a choice of one of 20 images stored on the mask, and sends that choice over Bluetooth LE.
- Adds a random blink now and then, so the face is never quite still.

The code is one file, `main.py`. It does not upload images; load them onto the mask first.

## Setup

This section holds only what `main.py` proves. The board, the CircuitPython version, the wiring and the steps for loading images are not written down in this repo yet; they will be added after a session with the hardware.

What the code needs:

- A CircuitPython board with Bluetooth LE. `main.py` does not name one.
- A Wii Nunchuk on the board's I2C bus. The code opens it with `board.I2C()`, so the board must define the default I2C pins.
- These modules importable on the board: `adafruit_ble`, `adafruit_nunchuk`, `asynccp`, `aesio`, plus the built-in `board`, `supervisor`, `microcontroller` and `watchdog`.
- A mask loaded with your own images, in slots 1 to 20.

Copy `main.py` to the board as `code.py` or `main.py`. At start it retries until the Nunchuk answers, then scans until it finds a mask.

### Choosing one mask

By default the controller connects to the first device that advertises the mask's Bluetooth service, `0000fff0-0000-1000-8000-00805f9b34fb`. To connect to one mask only, set `MASK_ADDRESS` at the top of `main.py`:

```python
MASK_ADDRESS = "AA:BB:CC:DD:EE:01"
```

With an address set, the scan skips every other advertiser. With `None`, the default, any mask in range can be taken.

## Gestures

The code reads the joystick's `x` axis (0 to 255) and the two buttons. The `y` axis and the accelerometer are not used. Image numbers below are positions in the code's list of 20; image `n` is mask slot `n + 1`.

| Hold | Joystick `x` | Image |
|---|---|---|
| nothing | above 200 | 10 |
| nothing | 121 to 200 | 8 |
| nothing | 100 to 120 | unchanged |
| nothing | 50 to 99 | 8 |
| nothing | below 50 | 9 |
| **Z** | above 200 | 5 |
| **Z** | 121 to 200 | 2 |
| **Z** | 100 to 120 | unchanged |
| **Z** | 50 to 99 | 3 |
| **Z** | below 50 | 4 |
| **C** | any | a random pick from 0, 1, 8, 13, 14, 15, 16, 17, 18, 19 |

**C** wins over **Z**. Without **C**, each check has about a 4 in 100 chance of starting a blink, and at most one blink starts per second. A blink plays four images at 12 per second: 12, 11, 11, 12 with nothing held, 6, 7, 7, 6 with **Z** held. Blinks are random, not a reaction to movement.

## How it works

`main.py` writes to one characteristic, `d44bc439-abfd-45a2-b575-925416129600`, on the mask's service. Each write is 16 bytes, `\x06PLAY\x01`, the slot number and nine fixed bytes, encrypted with AES-128 in ECB mode. The key is in `main.py`.

`asynccp` runs three tasks:

- every 1000/24 ms (about 42 ms), send the current image to the mask, and feed the watchdog;
- every 100 ms, read the Nunchuk and choose the image;
- every second, allow one more blink.

The watchdog is armed just before the loop starts, in `RESET` mode with a 2.5 second timeout, so waiting for the Nunchuk or the mask at startup is never cut short. The frame task feeds it. If the loop stalls, including during a long reconnect, the board resets and waits again at startup. If a write fails, the code drops the connection and calls `supervisor.reload()`, which restarts the program.

## What it deliberately does not do

- It does not pair or bond with the mask. Without `MASK_ADDRESS`, it connects to any device advertising the mask's service.
- It does not upload images. The mask must already hold them.
- It does not read the accelerometer, and blinks do not respond to movement.
- The watchdog change and `MASK_ADDRESS` have not been run on hardware yet. The address comparison was checked by hand in plain Python and will be confirmed on hardware.

## The pixel images

The pixel images in `examples/MeeseeksMask/` are the author's own fan art of a character owned by its rights holders. They are not covered by the MIT licence.

## The full guide

Setup, running it and drawing your own expressions: **[bricoleur.ai/projects/shining-mask](https://bricoleur.ai/projects/shining-mask)**.

<!-- bricoleur:footer -->
<!-- /bricoleur:footer -->
