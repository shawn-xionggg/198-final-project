// UNO R4 Minima + SSD1306 128x64. Touch D2, buzzer D3, single LED D4.
#include <Wire.h>
#include <Adafruit_GFX.h>
#include <Adafruit_SSD1306.h>
#include <stdio.h>
#include <string.h>

const int TOUCH_PIN=2, BUZZER_PIN=3, LED_PIN=4;
Adafruit_SSD1306 display(128,64,&Wire,-1,100000UL,100000UL);
bool displayReady=false, connected=false, flashing=false, buzzing=false;
bool rawTouch=false, stableTouch=false, touchArmed=false;
unsigned long touchChanged=0, lastMessage=0, lastMode=0, flashAt=0, buzzAt=0;
unsigned long lastEvent=0;
unsigned long modeRevision=0;
char mode[6]="SQUAT", state[12]="READY", result[16]="NONE";
long attempts=0, passed=0, durationMs=-1;
int angle=-1;
char input[128];
size_t used=0;
bool overflow=false;

void silence() { noTone(BUZZER_PIN); digitalWrite(BUZZER_PIN,LOW); buzzing=false; }
void render() {
  if (!displayReady) return;
  display.clearDisplay(); display.setTextColor(SSD1306_WHITE); display.setTextWrap(false);
  display.setTextSize(1); display.setCursor(0,0);
  display.print(!strcmp(mode,"SQUAT") ? "SQUATS" : "CURLS");
  display.print("  Touch: switch");
  display.setCursor(0,12); display.print("Attempts "); display.print(attempts);
  display.setCursor(0,23); display.print("Met targets "); display.print(passed);
  display.setCursor(0,34);
  if (!connected) display.print("Waiting for PC");
  else if (!strcmp(state,"LOST")) display.print("Tracking lost");
  else if (!strcmp(state,"READY")) display.print(!strcmp(mode,"SQUAT") ? "Stand to begin" : "Extend arm to begin");
  else if (!strcmp(state,"MOVING")) display.print("Moving");
  else display.print("Ready for next rep");
  display.setCursor(0,45);
  if (!strcmp(result,"OK")) display.print("Targets met");
  else if (!strcmp(result,"RANGE")) display.print("Missed range");
  else if (!strcmp(result,"FAST")) display.print("Too fast");
  else if (!strcmp(result,"SLOW")) display.print("Too slow");
  else if (!strcmp(result,"RANGE_FAST")) display.print("Range + too fast");
  else if (!strcmp(result,"RANGE_SLOW")) display.print("Range + too slow");
  display.setCursor(0,56);
  if (angle>=0) { display.print(angle); display.print(" deg "); }
  if (durationMs>=0) { display.print(durationMs/1000.0,1); display.print("s last"); }
  display.display();
}
void sendMode() {
  if (Serial && Serial.availableForWrite()>=24) {
    Serial.print("MODE,"); Serial.print(mode); Serial.print(','); Serial.println(modeRevision); lastMode=millis();
  }
}
void touch(unsigned long now) {
  bool reading=digitalRead(TOUCH_PIN)==HIGH;
  if (reading!=rawTouch) { rawTouch=reading; touchChanged=now; }
  if (now-touchChanged<60) return;
  if (!reading) touchArmed=true;
  if (reading==stableTouch) return;
  stableTouch=reading;
  if (stableTouch && touchArmed) {
    touchArmed=false;
    strcpy(mode,!strcmp(mode,"SQUAT") ? "CURL" : "SQUAT");
    modeRevision++;
    connected=false; attempts=0; passed=0; angle=-1; durationMs=-1;
    strcpy(state,"READY"); strcpy(result,"NONE");
    silence(); digitalWrite(LED_PIN,LOW); flashing=false;
    sendMode(); render();
  }
}
bool validResult(const char *r) {
  return !strcmp(r,"NONE") || !strcmp(r,"OK") || !strcmp(r,"RANGE") || !strcmp(r,"FAST") ||
         !strcmp(r,"SLOW") || !strcmp(r,"RANGE_FAST") || !strcmp(r,"RANGE_SLOW");
}
void receive(char *line) {
  char m[6], s[12], r[16], extra;
  long a,p,d;
  int value;
  unsigned long event;
  if (sscanf(line,"EX,%5[^,],%ld,%ld,%11[^,],%d,%lu,%15[^,],%ld%c",m,&a,&p,s,&value,&event,r,&d,&extra)!=8) return;
  if (strcmp(m,mode) || a<0 || p<0 || p>a || value < -1 || value>180 || d < -1 || !validResult(r)) return;
  if (strcmp(s,"READY") && strcmp(s,"START") && strcmp(s,"MOVING") && strcmp(s,"LOST")) return;
  unsigned long now=millis();
  // A new connection establishes a baseline. Never replay old rep feedback.
  if (connected && event>lastEvent && strcmp(s,"LOST")) {
    if (!strcmp(r,"OK")) { digitalWrite(LED_PIN,HIGH); flashing=true; flashAt=now; }
    else if (strcmp(r,"NONE")) { tone(BUZZER_PIN,2300); buzzing=true; buzzAt=now; }
  }
  lastEvent=event; connected=true; lastMessage=now;
  attempts=a; passed=p; angle=value; durationMs=d;
  strcpy(state,s); strcpy(result,r);
  if (!strcmp(state,"LOST")) silence();
  render();
}
void setup() {
  pinMode(TOUCH_PIN,INPUT); pinMode(BUZZER_PIN,OUTPUT); pinMode(LED_PIN,OUTPUT);
  pinMode(LED_BUILTIN,OUTPUT); digitalWrite(LED_PIN,LOW); digitalWrite(BUZZER_PIN,LOW);
  Serial.begin(115200); Wire.begin(); Wire.setClock(100000); delay(200);
  uint8_t address=0;
  for(uint8_t a=0x3C;a<=0x3D;++a) { Wire.beginTransmission(a); if(Wire.endTransmission()==0){address=a;break;} }
  if(address) displayReady=display.begin(SSD1306_SWITCHCAPVCC,address,false,false);
  rawTouch=digitalRead(TOUCH_PIN)==HIGH; stableTouch=rawTouch; touchChanged=millis();
  render();
}
void loop() {
  unsigned long now=millis(); touch(now);
  // Bound work per pass so USB traffic cannot starve touch and sound timers.
  int budget=128;
  while(Serial.available() && budget-->0) {
    char c=Serial.read();
    if(c=='\n') { input[used]='\0'; if(!overflow)receive(input); used=0;overflow=false; }
    else if(c!='\r') { if(used<sizeof(input)-1)input[used++]=c;else overflow=true; }
  }
  now=millis();
  if(now-lastMode>=500)sendMode();
  if(buzzing && now-buzzAt>=180)silence();
  if(flashing && now-flashAt>=500){digitalWrite(LED_PIN,LOW);flashing=false;}
  if(connected && now-lastMessage>3000){connected=false;silence();digitalWrite(LED_PIN,LOW);flashing=false;render();}
  if(!displayReady)digitalWrite(LED_BUILTIN,(now/500)%2);
}
