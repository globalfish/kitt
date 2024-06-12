# Motorcycle HUD
## Concept and Purpose
I bought a new Royal Enfield brand motorcycle, the Super Meteor 650. Unfortunately this one does not come with a tachometer. 
But it does have an OBD-II port that reports RPM, among other values. I wanted to create a little display that would read the
RPM and possibly a couple of other values and display it in my field of view as I driving. Some of the goals of this exercise:
- No modifications to the existing bike wiring to avoid warranty issues
- Ability to detach/move the setup as needed
- Minimize running wires around the bike

## Approach
I had a few ELM327 Bluetooth adapters at home and so I wanted to use those. An Arduino seemed the right choice to drive the 
displays and if it could connect to the ELM327 adapter that'd be perfect. I bought a short cable to connect the 16-pin adapter
to the 6-pin motorcycle OBD port. That done, the next step was to work on the Bluetooth connectivity.

### Components__
- 6-pin to 16-pin OBD port cable
- generic ELM327 Bluetooth OBDII adapter
- ESP32 microcontroller
- OLED display x 2 (0.94" SSD1306)
- proto boards for use during development/debugging
- USB cable to connect to power/data
- Source of power on the motorcycle (I am using existing USB ports)
- Some ability to fix the setup (I am using magnets)
- A waterproof container (I am temporarily using a medicine bottle :-) )
