# AMG88-Thermal-Camera
The purpose of this project was to develop a Raspberry PI Python GUI for the Panasonic AMG88 8X8 pixel thermal imager. the sensor is an 8x8 array of IR thermal sensors which will measure temperatures ranging from 0°C to 80°C (32°F to 176°F) with an accuracy of +- 2.5°C (4.5°F).  Applications include security, lighting control, kiosk / ATM, medical imaging, automatic doors, thermal mapping, people counting, robotics, and others. It can detect a human from a distance of up to 7 meters (23) feet. The sensor communicates over I2C with a maximum frame rate of 10Hz. The Thermal Imager GUI was developed around the[Adafruit AMG88 breakout board](https://learn.adafruit.com/adafruit-amg8833-8x8-thermal-camera-sensor/overview) and Pthon library. The Python example code also demonstrates the use of image processing from the SciPy python library which is used to interpolate the 8x8 grid and get smoothed images.





![Demo](IMG/ThermalCamDemo.gif)
