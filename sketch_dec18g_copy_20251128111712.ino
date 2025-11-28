// Pin Definitions
const int motor1pin1 = 2;
const int motor1pin2 = 3;
const int motor2pin1 = 4;
const int motor2pin2 = 5;

// PWM Speed Control Pins (Enable Pins)
const int enA = 9;   
const int enB = 10;

// Sensor Pins
const int trigPin = 7;
const int echoPin = 8;

const int trigPin_left = 13;
const int echoPin_left = 12;

const int trigPin_right = 11;
const int echoPin_right = 6;

// Global Variables
float distance, distance_left, distance_right;
int obstacleThreshold = 20; // Distance in cm to trigger a stop

void setup() {
  // Motor pins
  pinMode(motor1pin1, OUTPUT);
  pinMode(motor1pin2, OUTPUT);
  pinMode(motor2pin1, OUTPUT);
  pinMode(motor2pin2, OUTPUT);
   
  // Speed control pins
  pinMode(enA, OUTPUT); 
  pinMode(enB, OUTPUT);
   
  // Sensor pins
  pinMode(trigPin, OUTPUT);
  pinMode(echoPin, INPUT);

  pinMode(trigPin_right, OUTPUT);
  pinMode(echoPin_right, INPUT);

  pinMode(trigPin_left, OUTPUT);
  pinMode(echoPin_left, INPUT);
   
  Serial.begin(9600);
}

void loop() {
  // 1. Read all sensors
  distance_left = get_distance(trigPin_left, echoPin_left);
  delay(5); // Small delay between sensor reads to prevent interference
  distance_right = get_distance(trigPin_right, echoPin_right);
  delay(5);
  distance = get_distance(trigPin, echoPin);


  // 2. Navigation Logic
  
  // PRIORITY 1: Front Obstacle Detected
  if (distance < obstacleThreshold) {
    stopMotors();
    delay(300); // Brief pause to stabilize

    // Compare Left and Right to decide which way to turn
    if (distance_left > distance_right) {
      // More space on the left
      turnLeft();
      delay(500); // Turn for 0.5 second
    } else {
      // More space on the right (or equal)
      turnRight();
      delay(500); 
    }
  }
  // PRIORITY 2: Left Side Obstacle (Avoidance)
  else if (distance_left < 15) {
    // Wall on left? Nudge right slightly while moving forward
    turnRight(); 
    delay(100); // Short turn just to steer away
  }
  // PRIORITY 3: Right Side Obstacle (Avoidance)
  else if (distance_right < 15) {
    // Wall on right? Nudge left slightly while moving forward
    turnLeft();
    delay(100); // Short turn just to steer away
  }
  // PRIORITY 4: Path Clear
  else {
    moveForward();
  }
  
  delay(50); // Small loop delay
}

// --- HELPER FUNCTIONS ---

void moveForward() {
  analogWrite(enA, 100); 
  analogWrite(enB, 100); 
  digitalWrite(motor1pin1, HIGH);
  digitalWrite(motor1pin2, LOW);
  digitalWrite(motor2pin1, HIGH);
  digitalWrite(motor2pin2, LOW);
}

void stopMotors() {
  analogWrite(enA, 0);
  analogWrite(enB, 0);
  digitalWrite(motor1pin1, LOW);
  digitalWrite(motor1pin2, LOW);
  digitalWrite(motor2pin1, LOW);
  digitalWrite(motor2pin2, LOW);
}

void turnRight() {
  analogWrite(enA, 150); 
  analogWrite(enB, 150);
  // Motor 1 Forward (Left Motor)
  digitalWrite(motor1pin1, HIGH);
  digitalWrite(motor1pin2, LOW);
  // Motor 2 Backward (Right Motor)
  digitalWrite(motor2pin1, LOW); 
  digitalWrite(motor2pin2, HIGH);
}

void turnLeft() {
  analogWrite(enA, 150); 
  analogWrite(enB, 150);
  // Motor 1 Backward (Left Motor)
  digitalWrite(motor1pin1, LOW);
  digitalWrite(motor1pin2, HIGH);
  // Motor 2 Forward (Right Motor)
  digitalWrite(motor2pin1, HIGH); 
  digitalWrite(motor2pin2, LOW);
}

// Corrected function: Added variable types (int) to arguments
float get_distance(int trig, int echo) {
  digitalWrite(trig, LOW);
  delayMicroseconds(2);
  digitalWrite(trig, HIGH);
  delayMicroseconds(10);
  digitalWrite(trig, LOW);

  // Use a local variable for duration
  float duration = pulseIn(echo, HIGH);
   
  // Calculate distance in cm
  float dist = (duration * 0.0343) / 2;
  
  // Filter out 0 readings (sensor timeout usually returns 0)
  if (dist == 0) { return 999.0; } 
  
  return dist;
}