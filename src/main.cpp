#include <Arduino.h>
#include <Wire.h>

// AS5600 I2C address
#define AS5600_ADDRESS 0x36

// AS5600 register addresses
#define RAW_ANGLE_HIGH 0x0C
#define RAW_ANGLE_LOW 0x0D

// Function to read raw angle from AS5600
int readRawAngle() {
    Wire.beginTransmission(AS5600_ADDRESS);
    Wire.write(RAW_ANGLE_HIGH);
    Wire.endTransmission();
    
    Wire.requestFrom(AS5600_ADDRESS, 2);
    
    if(Wire.available() <= 2) {
        int high = Wire.read();
        int low = Wire.read();
        // Combine high and low bytes
        int rawAngle = (high << 8) | low;
        return rawAngle;
    }
    return -1;
}

void setup() {
    // Initialize Serial for debugging
    Serial.begin(115200);
    
    // Initialize I2C
    Wire.begin();
    
    delay(1000); // Give some time for initialization
}

void loop() {
    // Read the raw angle
    int rawAngle = readRawAngle();
    
    if(rawAngle != -1) {
        // Convert raw angle to degrees (12-bit resolution)
        float degrees = (rawAngle * 360.0) / 4096.0;
        
        // Print the results
        Serial.print("Raw angle: ");
        Serial.print(rawAngle);
        Serial.print(" Degrees: ");
        Serial.println(degrees);
    } else {
        Serial.println("Error reading sensor");
    }
    
    delay(100); // Read every 100ms
}