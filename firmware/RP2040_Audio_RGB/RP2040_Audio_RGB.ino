/*
 * RP2040 Audio RGB firmware
 *
 * Receives RGB frames over USB Serial from the Windows client:
 *   L R1 G1 B1 R2 G2 B2\n
 *
 * Channel 1: discrete RGB LED / MOSFET-driven analog RGB output (PWM)
 * Channel 2: WS2812 / NeoPixel
 *
 * Arduino core: Raspberry Pi Pico/RP2040
 * Library: Adafruit NeoPixel
 */

#include <Adafruit_NeoPixel.h>

// -----------------------------------------------------------------------------
// HARDWARE CONFIGURATION
// -----------------------------------------------------------------------------

// External PWM RGB output.
// Change these four settings to match your wiring.
constexpr uint8_t PIN_RED   = 13;
constexpr uint8_t PIN_GREEN = 14;
constexpr uint8_t PIN_BLUE  = 15;

// Waveshare RP2040-Zero uses GP16 for its onboard WS2812.
constexpr uint8_t PIN_NEOPIXEL = 16;
constexpr uint16_t NEOPIXEL_COUNT = 1;

// false = common cathode / active HIGH
// true  = common anode / active LOW
constexpr bool RGB_COMMON_ANODE = false;

// Set false if the board has no WS2812/NeoPixel.
constexpr bool ENABLE_NEOPIXEL = true;

constexpr uint32_t SERIAL_BAUD = 115200;

// If the PC disappears, LEDs are switched off after this timeout.
constexpr uint32_t FAILSAFE_TIMEOUT_MS = 3000;

// -----------------------------------------------------------------------------

Adafruit_NeoPixel pixel(
    NEOPIXEL_COUNT,
    PIN_NEOPIXEL,
    NEO_GRB + NEO_KHZ800
);

String inputLine;
uint32_t lastValidFrameMs = 0;
bool failsafeActive = false;

static uint8_t clampByte(long value) {
  if (value < 0) return 0;
  if (value > 255) return 255;
  return static_cast<uint8_t>(value);
}

static uint8_t pwmValue(uint8_t value) {
  return RGB_COMMON_ANODE ? static_cast<uint8_t>(255 - value) : value;
}

static void setAnalogRgb(uint8_t r, uint8_t g, uint8_t b) {
  analogWrite(PIN_RED, pwmValue(r));
  analogWrite(PIN_GREEN, pwmValue(g));
  analogWrite(PIN_BLUE, pwmValue(b));
}

static void setNeoPixel(uint8_t r, uint8_t g, uint8_t b) {
  if (!ENABLE_NEOPIXEL) return;

  pixel.setPixelColor(0, pixel.Color(r, g, b));
  pixel.show();
}

static void setAllOff() {
  setAnalogRgb(0, 0, 0);
  setNeoPixel(0, 0, 0);
}

static bool parseLedCommand(const String &line) {
  // Expected format:
  // L R1 G1 B1 R2 G2 B2

  if (line.length() < 2 || line.charAt(0) != 'L') {
    return false;
  }

  long r1, g1, b1, r2, g2, b2;

  int parsed = sscanf(
      line.c_str(),
      "L %ld %ld %ld %ld %ld %ld",
      &r1, &g1, &b1,
      &r2, &g2, &b2
  );

  if (parsed != 6) {
    return false;
  }

  setAnalogRgb(
      clampByte(r1),
      clampByte(g1),
      clampByte(b1)
  );

  setNeoPixel(
      clampByte(r2),
      clampByte(g2),
      clampByte(b2)
  );

  lastValidFrameMs = millis();
  failsafeActive = false;

  return true;
}

static void processSerial() {
  while (Serial.available() > 0) {
    char c = static_cast<char>(Serial.read());

    if (c == '\r') {
      continue;
    }

    if (c == '\n') {
      if (inputLine.length() > 0) {
        parseLedCommand(inputLine);
        inputLine = "";
      }
      continue;
    }

    // Prevent an invalid sender from growing RAM indefinitely.
    if (inputLine.length() < 96) {
      inputLine += c;
    } else {
      inputLine = "";
    }
  }
}

void setup() {
  pinMode(PIN_RED, OUTPUT);
  pinMode(PIN_GREEN, OUTPUT);
  pinMode(PIN_BLUE, OUTPUT);

#if defined(ARDUINO_ARCH_RP2040)
  // 8-bit PWM values: 0..255.
  analogWriteRange(255);
#endif

  if (ENABLE_NEOPIXEL) {
    pixel.begin();
    pixel.setBrightness(255);
    pixel.clear();
    pixel.show();
  }

  setAllOff();

  Serial.begin(SERIAL_BAUD);
  inputLine.reserve(96);

  lastValidFrameMs = millis();
}

void loop() {
  processSerial();

  // Fail safe: don't leave LEDs frozen if the Python app crashes or USB drops.
  if (!failsafeActive &&
      (millis() - lastValidFrameMs > FAILSAFE_TIMEOUT_MS)) {
    setAllOff();
    failsafeActive = true;
  }

  delay(1);
}
