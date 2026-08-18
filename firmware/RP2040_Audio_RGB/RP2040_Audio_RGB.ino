/* RP2040 Audio RGB firmware v2.0
 * Commands:
 *   L R1 G1 B1 R2 G2 B2
 *   PING
 *   INFO
 *   BRI 0..100
 *   COUNT 1..300
 *   OFF
 */
#include <Adafruit_NeoPixel.h>

constexpr uint8_t PIN_RED=13, PIN_GREEN=14, PIN_BLUE=15;
constexpr uint8_t PIN_NEOPIXEL=16;
constexpr bool RGB_COMMON_ANODE=false;
constexpr uint32_t SERIAL_BAUD=115200;
constexpr uint32_t FAILSAFE_TIMEOUT_MS=3000;

Adafruit_NeoPixel pixels(1, PIN_NEOPIXEL, NEO_GRB + NEO_KHZ800);
String inputLine;
uint32_t lastValidFrameMs=0;
uint8_t globalBrightness=100;
uint16_t pixelCount=1;
bool failsafeActive=false;

uint8_t clampByte(long v){ return v<0?0:(v>255?255:(uint8_t)v); }
uint8_t applyBrightness(uint8_t v){ return (uint16_t)v*globalBrightness/100; }
uint8_t pwmValue(uint8_t v){ v=applyBrightness(v); return RGB_COMMON_ANODE?255-v:v; }

void setAnalog(uint8_t r,uint8_t g,uint8_t b){
  analogWrite(PIN_RED,pwmValue(r)); analogWrite(PIN_GREEN,pwmValue(g)); analogWrite(PIN_BLUE,pwmValue(b));
}
void setPixels(uint8_t r,uint8_t g,uint8_t b){
  r=applyBrightness(r); g=applyBrightness(g); b=applyBrightness(b);
  for(uint16_t i=0;i<pixelCount;i++) pixels.setPixelColor(i,pixels.Color(r,g,b));
  pixels.show();
}
void off(){ setAnalog(0,0,0); setPixels(0,0,0); }

bool processLine(const String &line){
  if(line=="PING"){ Serial.println("PONG"); return true; }
  if(line=="INFO"){ Serial.print("INFO RP2040-Audio-RGB 2.0.0 PIXELS="); Serial.print(pixelCount); Serial.print(" BRI="); Serial.println(globalBrightness); return true; }
  if(line=="OFF"){ off(); lastValidFrameMs=millis(); return true; }
  long value;
  if(sscanf(line.c_str(),"BRI %ld",&value)==1 && line.startsWith("BRI ")){
    globalBrightness=(uint8_t)constrain(value,0,100); Serial.println("OK BRI"); return true;
  }
  if(sscanf(line.c_str(),"COUNT %ld",&value)==1 && line.startsWith("COUNT ")){
    pixelCount=(uint16_t)constrain(value,1,300); pixels.updateLength(pixelCount); pixels.clear(); pixels.show(); Serial.println("OK COUNT"); return true;
  }
  long r1,g1,b1,r2,g2,b2;
  if(sscanf(line.c_str(),"L %ld %ld %ld %ld %ld %ld",&r1,&g1,&b1,&r2,&g2,&b2)==6){
    setAnalog(clampByte(r1),clampByte(g1),clampByte(b1));
    setPixels(clampByte(r2),clampByte(g2),clampByte(b2));
    lastValidFrameMs=millis(); failsafeActive=false; return true;
  }
  Serial.println("ERR"); return false;
}

void setup(){
  pinMode(PIN_RED,OUTPUT); pinMode(PIN_GREEN,OUTPUT); pinMode(PIN_BLUE,OUTPUT);
#if defined(ARDUINO_ARCH_RP2040)
  analogWriteRange(255);
#endif
  pixels.begin(); pixels.clear(); pixels.show(); off();
  Serial.begin(SERIAL_BAUD); inputLine.reserve(96); lastValidFrameMs=millis();
}

void loop(){
  while(Serial.available()){
    char c=(char)Serial.read();
    if(c=='\r') continue;
    if(c=='\n'){
      if(inputLine.length()){ processLine(inputLine); inputLine=""; }
    } else if(inputLine.length()<96) inputLine+=c; else inputLine="";
  }
  if(!failsafeActive && millis()-lastValidFrameMs>FAILSAFE_TIMEOUT_MS){ off(); failsafeActive=true; }
  delay(1);
}
