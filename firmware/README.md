# QL-01 RP2040 acquisition firmware

Pico SDK 2.1.1, C11. Target: Raspberry Pi Pico (RP2040). Firmware is compiled in CI; this is NOT evidence of flashing real hardware or simulating analogue circuitry.

| Signal | Pico GPIO | Physical pin |
|---|---:|---:|
| Odometer A/B | 0/1 | 1/2 |
| Encoder SCK/MOSI/MISO | 2/3/4 | 4/5/6 |
| Bank CS0/CS1/CS2/CS3 | 5/6/7/8 | 7/9/10/11 |
| ADXL355 SCK/MOSI/MISO/CS | 10/11/12/13 | 14/15/16/17 |
| ADXL355 optional DRDY, unused in Q1 | 14 | 19 |
| USB CDC | native USB | USB connector |

31 AS5048A: banks of 8+8+8+7; inside a bank MISO goes to the next sensor MOSI. The last sensor MISO returns to the carrier. Shared SCK and bank CS. Response chain order is reversed to restore physical sensor order. Verify this mapping by rotating ONE shaft at a time before mounting all 31.

All sensor power comes from a separate current-limited 3.3 V supply, NOT the Pico 3V3 output. Pico remains USB-powered. Common ground is required. Do not apply 5 V encoder outputs to RP2040 inputs. Use a 3.3 V-compatible quadrature encoder or a proper level translator; the carrier does not accept industrial 12/24 V encoder signals.

AS5048A SPI mode 1, 1 MHz, even parity, error flag, OCF/COF and magnet diagnostics. A read is pipelined; the second transaction retrieves the answer. AGC/magnitude and temperature are not yet retained in the Q1 frame; their inclusion is a next protocol revision before metrological qualification.

ADXL355 uses a dedicated SPI mode 0 bus, 250 Hz ODR, ±2g, HPF off. The firmware polls data-ready and reads all 9 XYZ bytes. Missing/invalid sensor gives zero acceleration; the agent invalidates attitude. ADXL filter group delay is NOT compensated in Q1, and row channels are polled sequentially (not simultaneous ADC captures). The timing uncertainty must be bounded experimentally and low-speed/stop-and-measure accepted before any accuracy claim.

Wire format, ASCII before a newline:
```
Q1,sequence,time_us,odometer_ticks,ax20,ay20,az20,valid_mask_hex,a0,...,a30*crc32hex
```
CRC is IEEE CRC-32 over bytes before `*`. Units: µs, encoder counts; angles are raw unsigned 14-bit counts. The validity mask means sensor/angle diagnostics, NOT wheel contact. Agent always sets CONTACT_UNKNOWN for Q1. Frame datum remains FREE_ROLL. No false positive acceptance is permitted.

Build: set `PICO_SDK_PATH`, `cmake -S firmware -B firmware/build -DPICO_BOARD=pico`, then `cmake --build firmware/build`. Hold BOOTSEL, connect Pico USB and copy the built UF2 to RPI-RP2. Disconnect all external sensor power during initial USB-only firmware loading. Verify supplies/current limits and connector pinout before powering the full array.

Primary sources:
* https://www.infineon.com/assets/row/public/documents/24/49/infineon-as5048a-as5048b-datasheet-en.pdf
* https://www.analog.com/media/en/technical-documentation/data-sheets/adxl354_adxl355.pdf
* https://www.raspberrypi.com/documentation/pico-sdk/hardware.html
