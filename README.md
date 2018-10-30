# AMG88-Thermal-Camera GUI Overview
The purpose of this project was to develop a Thermal Camera GUI on the Raspberry Pi capable of capturing infrared motion and still images. The hardware for the GUI is the [Panasonic AMG88 8X8 pixel thermal imager](https://na.industrial.panasonic.com/products/sensors/sensors-automotive-industrial-applications/grid-eye-infrared-array-sensor). The sensor features an 8x8 array of IR thermal sensors which will measure temperatures ranging from 0°C to 80°C (32°F to 176°F) with an accuracy of +- 2.5°C (4.5°F).  Some potential applications include security, lighting control, medical imaging, automatic doors, thermal mapping, people counting, and robotics. It can detect a human from a distance of up to 7 meters (23) feet. The sensor communicates over I2C with a maximum frame rate of 10Hz. The Thermal Imager GUI was developed around the [Adafruit AMG88 breakout board](https://learn.adafruit.com/adafruit-amg8833-8x8-thermal-camera-sensor/overview) and the provided Python library. The Python example code also demonstrates the use of image processing from the SciPy python library which is used to interpolate the 8x8 grid and get smoothed images. Aside from the Adafruit documentation, the following references were used;[AMG88 GRID-EYE SPECIFICATION](REF/AMG88 GRID-EYE SPECIFICATION.pdf)[GRID-EYE FAQ](REF/GRID_EYE FAQ.pdf)[GRID_EYE CHARACTERISTICS](REF/GRID_EYE CHARACTERISTICS.pdf)# AMG88-Thermal-Camera GUI Description





![Demo](IMG/ThermalCamDemo.gif)
