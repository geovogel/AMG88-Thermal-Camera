# amg88xx thermal camera GUI using OcempGUI
# Uses partial screen assignment technique to combine pyGame and OcempGUI widget screens.

import sys
import pygame.locals
from ocempgui.widgets import *
from ocempgui.widgets.Constants import *
from ocempgui.draw import Image as guiImage   # Rename to avoid conflict wil PIL Image
from AMG88_CTRL import *
import math
import time
import numpy as np
from scipy.interpolate import griddata
from colour import Color
from PIL import Image, ImageDraw

#frame rates
AMG88_FPS_10 = 0x00
AMG88_FPS_1 = 0x01

#Twice moving average output mode
AMG88_AVE_ON = 0x01
AMG88_AVE_OFF = 0x00

# RGB Color Definition
black = (0, 0, 0)
white = (255, 255, 255)
red = (150, 0, 0)
bright_red = (255, 0, 0)
green = (0, 150, 0)
bright_green = (0, 255, 0)
blue = (0, 0, 255)

# ===== INITIALIZE THERMAL CAMERA ======================================================================================
sensor = AMG88_CTRL()          # Initialize the sensor
time.sleep(.1)   # Pause to let the sensor initialize
# ===== FUNCTIONS ======================================================================================================


def runControl():
    state = button.active                      # Read the toggle button state
    if state:
        button.set_text("STOP")                # if state is active change the next button action to stop
        # ===== ACQUIRE CAMERA DATA =====
        # color map
        MovColorDepth = 1024
        MovColors = colorMap(MovColorDepth)  # Range of color values for movie imaging
        pixels = sensor.readPixels()           # read the pixels
        tempRange = updateTemp()               # Gets list of min & max temp values
        pixels = [pixelMap(p, tempRange[0], tempRange[1], 0, MovColorDepth - 1) for p in pixels]
        # perform interpolation
        bicubic = griddata(points, pixels, (grid_x, grid_y), method='cubic')
        # draw the screen
        for ix, row in enumerate(bicubic):
            for jx, pixel in enumerate(row):
                pygame.draw.rect(screen, MovColors[constrain(int(pixel), 0, MovColorDepth - 1)],
                                 ((displayPixelHeight * ix) + thermImg_X, (displayPixelWidth * jx) + thermImg_Y,
                                  displayPixelHeight, displayPixelWidth))
        # Force the status bar to update the clock by marking the widget as
        # dirty, so that it will be updated and redrawn.
        status.set_dirty(True, True)
    elif not state:
        button.set_text("RUN")
        # Draw a blank screen camera display rectangle.
        pygame.draw.rect(screen, black, (thermImg_X, thermImg_Y, 384, 384))
        status.set_dirty(True, True)


def stillShot():
    # parse command line arguments
    stillImgScale = 48                # specify image scale
    # sensor setup
    NX = 8
    NY = 8
    pixels = sensor.readPixels()     # get sensor readings
    # output image buffer
    image = Image.new("RGB", (NX, NY), "white")
    draw = ImageDraw.Draw(image)
    # color map
    StillColorDepth = 256
    StillColors = colorMap(256)            # Range of color values for movie imaging
    # map sensor readings to color map
    tempRange = updateTemp()  # Gets list of min & max temp values
    pixels = [pixelMap(p, tempRange[0], tempRange[1], 0, StillColorDepth - 1) for p in pixels]
    # create the image
    for ix in range(NX):
        for iy in range(NY):
            draw.point([(ix, iy % NX)], fill=StillColors[constrain(int(pixels[ix + NX * iy]), 0, StillColorDepth - 1)])
    # scale and save
    fileOutEntry.set_dirty(True, True)
    fileOutEntry.activate()
    stillFileName = fileOutEntry.text
    image.resize((NX * stillImgScale, NY * stillImgScale), Image.BICUBIC).save(stillFileName)
    # File saved dialog window.
    # Create and display a simple window.
    saveWindow = Window("File Saved")
    saveWindow.child = Button("   OK   ")
    saveWindow.child.connect_signal(SIG_CLICKED, saveWindow.destroy)
    saveWindow.minsize = (200, 80)
    saveWindow.topleft = 10, 280
    saveWindow.depth = 1
    renderer_1.add_widget(saveWindow)


def constrain(val, min_val, max_val):
    return min(max_val, max(min_val, val))


def pixelMap(x, in_min, in_max, out_min, out_max):
    return (x - in_min) * (out_max - out_min) / (in_max - in_min) + out_min


def updateTemp():
    tMin = ((float(minTempEntry.text))-32)/1.8
    tMax = ((float(maxTempEntry.text))-32)/1.8
    return tMin, tMax


def thermistorPlot():
    global rate, xData, yData, xDataVal, minDigTmp, maxDigTmp
    ET = round((time.time() - startTim), 2)        # Elapsed time to 2 decimals
    ET_mod_lo = ET % rate
    ET_mod_hi = rate - (ET % rate)
    # print("ET:", "{:2.2f}".format(ET), "ET_mod_lo:", "{:2.2f}".format(ET_mod_lo), "ET_mod_hi:", "{:2.2f}".format(ET_mod_hi))
    # Scale the data for better appearance on the graph
    yScale = 20
    yOffset = -1550
    # Update the graph at specified intervals
    if ET < 0.1:                         # On first pass initialize plot and wait for the first data point
        yDataVal = (sensor.readThermistor() * 1.8) + 32  # Get thermistor reading. convert to deg F
        yDataValPlot = (yDataVal * yScale) + yOffset
        yData[0] = yDataValPlot
        xDataVal = 0
        xData[0] = xDataVal
        time.sleep(1)
        minDigTmp = yDataVal
        maxDigTmp = yDataVal
        # Update the temperature digital displays
        curDigTmpEntry.set_text(str(round(yDataVal, 1)))
        minDigTmpEntry.set_text(str(round(minDigTmp, 1)))
        maxDigTmpEntry.set_text(str(round(maxDigTmp, 1)))
        return
    if ET_mod_lo <= 0.1 or ET_mod_hi <= 0.1:
        yDataVal = (sensor.readThermistor() * 1.8) + 32  # Get thermistor reading. convert to deg F
        yDataValPlot = (yDataVal * yScale) + yOffset
        if xDataVal < 582:                               # Fill the plot buffer to the end of the plot screen
            xDataVal += 1                                # Increment along x axis
            print(xDataVal)
            xData = np.append(xData, xDataVal)
            yData = np.append(yData, yDataValPlot)
            # Update the temperature digital displays
            if yDataVal < minDigTmp:
                minDigTmp = yDataVal
            if yDataVal > minDigTmp:
                maxDigTmp = yDataVal
            curDigTmpEntry.set_text(str(round(yDataVal, 1)))
            minDigTmpEntry.set_text(str(round(minDigTmp, 1)))
            maxDigTmpEntry.set_text(str(round(maxDigTmp, 1)))
            time.sleep(.2)  # Pause to make sure we don't trip the plot routine a second time
        else:
            yDataVal = (sensor.readThermistor() * 1.8) + 32  # Get thermistor reading. convert to deg F
            yDataValPlot = (yDataVal * yScale) + yOffset
            xData = np.arange(583)                           # After screen is full roll data right to left
            yData = np.roll(yData, -1)
            yData[581] = yDataValPlot
            # Update the temperature digital displays
            if yDataVal < minDigTmp:
                minDigTmp = yDataVal
            if yDataVal > minDigTmp:
                maxDigTmp = yDataVal
            curDigTmpEntry.set_text(str(round(yDataVal, 1)))
            minDigTmpEntry.set_text(str(round(minDigTmp, 1)))
            maxDigTmpEntry.set_text(str(round(maxDigTmp, 1)))
            time.sleep(.2)  # Pause to make sure we don't trip the plot routine a second time

    # Plot Data
    thermistorGraph.set_data(xData.tolist())
    thermistorGraph.set_values(yData.tolist())
    time.sleep(.05)                # Loop pause


def colorMap(ColDepth):
    # Create a color map distributed over the color depth
    # Cold color is named color indigo from Color module
    # Hot color is named color red from Color module
    colors = list(Color("indigo").range_to(Color("red"), ColDepth))
    colors = [(int(c.red * 255), int(c.green * 255), int(c.blue * 255)) for c in colors]
    return colors


def updateRate():
    global radioState
    global updateDict
    global rate
    for j in range(0, 6):
        radioState[j] = radiogroup._list[j]._active
        if radioState[j] is True:
            rate = updateDict[j]


def colRangeSel(self):
    minTempEntry.set_text(str(vScrollMin.value))
    maxTempEntry.set_text(str(vScrollMax.value))


def movAvg():
    state = avg_button.active  # Read the toggle button state
    if state:
        avg_button.set_text("OFF")  # if state is active change the next button action to stop
        AMG88_CTRL.setMovingAverageMode(sensor, AMG88_AVE_ON)
    elif not state:
        button.set_text("RUN")
        AMG88_CTRL.setMovingAverageMode(sensor, AMG88_AVE_OFF)


def frameRate():
    if FPS_Btn1.active is True:
        AMG88_CTRL.setFPS(sensor, AMG88_FPS_1)
    elif FPS_Btn2.active is True:
        AMG88_CTRL.setFPS(sensor, AMG88_FPS_10)


def smoothCtrl():
    global grid_x, grid_y, displayPixelWidth, displayPixelHeight
    if smoothBtn1.active is True:
        grid_x, grid_y = np.mgrid[0:7:32j, 0:7:32j]
        displayPixelWidth = 12
        displayPixelHeight = 12
    elif smoothBtn2.active is True:
        grid_x, grid_y = np.mgrid[0:7:64j, 0:7:64j]
        displayPixelWidth = 6
        displayPixelHeight = 6
    elif smoothBtn3.active is True:
        grid_x, grid_y = np.mgrid[0:7:128j, 0:7:128j]
        displayPixelWidth = 3
        displayPixelHeight = 3


def _set_files(result, dialog, entry):
    if result == DLGRESULT_OK:
        fileString = dialog.get_filenames()[0]
        stillImage = pygame.image.load(fileString)
        stillImage = pygame.transform.rotate(stillImage, 270)
        stillImage = pygame.transform.flip(stillImage, True, False)
        # Create close image dialog window.
        global closeWindow
        closeWindow = Window("Still Image")
        closeWindow.child = Button("#Close")
        closeWindow.child.connect_signal(SIG_CLICKED, closeImage)
        closeWindow.minsize = (200, 80)
        closeWindow.topleft = 10, 280
        closeWindow.depth = 1
        renderer_1.add_widget(closeWindow)
        screen.blit(stillImage, (thermImg_X, thermImg_Y))
    else:
        fileString = "Nothing selected"
    dialog.destroy()
    entry.text = fileString


def _open_filedialog(renderer_1, entry):
    buttons = [Button("#OK"), Button("#Cancel")]
    buttons[0].minsize = 80, buttons[0].minsize[1]
    buttons[1].minsize = 80, buttons[1].minsize[1]
    results = [DLGRESULT_OK, DLGRESULT_CANCEL]
    dialog = FileDialog("Select your file(s)", buttons, results)
    dialog.depth = 1  # Make it the top window
    dialog.topleft = 0, 0
    dialog.minsize = 222, 370
    dialog.filelist.selectionmode = SELECTION_MULTIPLE
    dialog.connect_signal(SIG_DIALOGRESPONSE, _set_files, dialog, entry)
    renderer_1.add_widget(dialog)


def closeImage():
    global closeWindow
    closeWindow.destroy()
    pygame.draw.rect(screen, black, (thermImg_X, thermImg_Y, 384, 384))


# ===== PYGAME WINDOW SETUP for CAMERA==================================================================================
points = [(math.floor(i_x / 8), (i_x % 8)) for i_x in range(0, 64)]
grid_x, grid_y = np.mgrid[0:7:32j, 0:7:32j]
displayPixelWidth = 12
displayPixelHeight = 12

thermImg_X = 235  # X offset location of thermal image screen
thermImg_Y = 40   # Y offset location of thermal image screen
# Font Definitions
numberFont = pygame.font.SysFont(None, 25)
titleFont = pygame.font.Font('freesansbold.ttf', 25)
labelFont = pygame.font.Font("freesansbold.ttf", 12)
# Initialize the pygame drawing window for the application.
pygame.init()
screen = pygame.display.set_mode((630, 740))
screen.fill((234, 228, 223))
pygame.draw.rect(screen, black, (thermImg_X, thermImg_Y, 384, 384))
pygame.display.set_caption('Grid-EYE Infrared Camera GUI')
# Draw the application title on the pygame screen
appTitle = "Grid-EYE Infrared Imaging Control"
appTitleWid = 610                  # Width of title text box
appTitleHt = 30                    # Height of title box
appTitleXoff = 10                  # Top left x location of title box
appTitleYoff = 5                   # Top left x location of title box
pygame.draw.rect(screen, blue, [appTitleXoff, appTitleYoff, appTitleWid, appTitleHt])
appTitleSurf = titleFont.render(appTitle, True, white)    # Create a text surface
appTitleRect = appTitleSurf.get_rect()                    # Get the size of the text box
appTitleRect.center = (appTitleXoff + appTitleWid/2, appTitleYoff + appTitleHt/2)  # Center the text box
screen.blit(appTitleSurf, appTitleRect)

# ===== OcempGUI SETUP =================================================================================================
# Partial screen assignment for the controls Renderer.
renderer_1 = Renderer()
surface_1 = pygame.Surface((220, 383))
renderer_1.screen = surface_1
renderer_1.color = 100, 100, 100
renderer_1.topleft = 10, 40
# Use a second renderer instance for the status bar.
renderer_2 = Renderer()
surface_2 = pygame.Surface((610, 35))
renderer_2.screen = surface_2
renderer_2.color = 100, 100, 100
renderer_2.topleft = 10, 695
# Use a Third partial screen renderer instance for the Thermistor Graph.
renderer_3 = Renderer()
surface_3 = pygame.Surface((610, 261))
renderer_3.screen = surface_3
renderer_3.color = 100, 100, 100
renderer_3.topleft = 10, 430

# ===== OcempGUI WIDGETS================================================================================================
# Table of radio buttons to set graph update rate
frame_2 = VFrame(Label("Thermistor Graph Controls"))
frame_2.minsize = (214, 60)
frame_2.topleft = 3, 190

radioTable = Table(2, 6)
radioTable.spacing = 10
radioTable.set_row_align(0, ALIGN_BOTTOM)
radioTable.set_row_align(1, ALIGN_TOP)
radioTable.set_padding(0)
for i in range(5):
    radioTable.set_column_align(i, ALIGN_NONE)

strings = ("2s", "10s", "1m", "2m", "5m", "15m")
# Create a dictionary of update values in the order that they are assigned to buttons.
# To start in the 10s update mode the radio button is assign last
updateDict = {0: 900, 1: 300, 2: 120, 3: 60, 4: 10, 5: 2}
radiogroup = None                                  # Create group object
for i in reversed(range(0, 6)):
    TblLabel = Label(strings[i])                            # Crete radio button labels
    radioTable.add_child(0, i, TblLabel)           # Add them to the table, row 1
    graphRateBtn = RadioButton(None, radiogroup)   # Create the radio buttons
    graphRateBtn.connect_signal(SIG_TOGGLED, updateRate)
    if i == 5:
        radiogroup = graphRateBtn                  # Assign the radio button(s) to the group
    radioTable.add_child(1, i, graphRateBtn)       # Add them to the table, row 2
frame_2.add_child(radioTable)                       # Add the radio button table to the frame
# ======================================================================================================================
# Setup Still Image Controls
frame_3 = HFrame(Label("Still Imaging"))     # Create a frame for the still image controls
frame_3.minsize = (214, 117)
frame_3.topleft = 3, 263
stillBox = Box(190, 90)

image_1 = guiImage.load_image("camera2.png")
stillSnapBtn = ImageButton(image_1)
stillSnapBtn.connect_signal(SIG_CLICKED, stillShot)

# Entry box for output file name
lbl_5 = Label("Save Filename:")
fileOutEntry = Entry('ThermImg_1.png')
fileOutEntry.minsize = (100, 5)
stillSnapBtn.topleft = 0, 0
lbl_5.topleft = 60, 0
fileOutEntry.topleft = 60, 15
lbl_14 = Label("Open Image Filename:")
lbl_14.topleft = 3, 42
fileEntry = Entry()
fileEntry.minsize = 120, 5
fileEntry.topleft = 3, 60
fileButton = Button("#Browse")
fileButton.topleft = 130, 58
fileButton.connect_signal(SIG_CLICKED, _open_filedialog, renderer_1, fileEntry)
stillBox.add_child(stillSnapBtn, lbl_5, fileOutEntry, lbl_14, fileEntry, fileButton)

frame_3.add_child(stillBox)
# ======================================================================================================================
# Setup Thermistor Graph
graphFrame = VFrame(Label("Thermistor Graph"))     # Create a frame for the graph widget
thermistorGraph = Graph2D(588, 230)                # Create the graph
graphFrame.add_child(thermistorGraph)              # Add the 2dGraph widget to the frame
graphFrame.topleft = 5, 5

# Set Thermistor Graph options
thermistorGraph.axes = "time", "Temperature"       # Set thermistor temperature related to time.
thermistorGraph.set_axis_color((255, 255, 0))
thermistorGraph.scale_units = ("sec", "C")         # Scale units for the x and y axis.
thermistorGraph.units = 1, 1                       # Set  px for the horizontal and vertical units
thermistorGraph.origin = 4, 15                     # Point of origin.
thermistorGraph.negative = False                   # Don't need to see negative values.
thermistorGraph.show_names = True                  # Show the names
thermistorGraph.set_graph_color((255, 255, 0))     # Set the color of the graph line
thermistorGraph.set_zoom_factor(1.0, 1.0)          # Zoom both axis in.

# Entry box for digital output of current temp degrees F
lbl_3 = Label("Now")
lbl_3.topleft = 535, 28
lbl_3.minsize = (30, 10)
curDigTmpEntry = Entry()
curDigTmpEntry.minsize = (30, 2)
curDigTmpEntry.topleft = 566, 25

# Entry box for digital output of minimum temp degrees F
lbl_4 = Label("Min")
lbl_4.topleft = 535, 51
lbl_4.minsize = (30, 10)
minDigTmpEntry = Entry()
minDigTmpEntry.minsize = (30, 5)
minDigTmpEntry.topleft = 566, 48

# Entry box for digital output of maximum temp degrees F
lbl_6 = Label("Max")
lbl_6.topleft = 535, 74
lbl_6.minsize = (30, 10)
maxDigTmpEntry = Entry()
maxDigTmpEntry.minsize = (30, 5)
maxDigTmpEntry.topleft = 566, 71
renderer_3.add_widget(graphFrame, lbl_3, curDigTmpEntry, lbl_4, minDigTmpEntry, lbl_6, maxDigTmpEntry)
# =====================================================================================================================
# Frame within main Renderer
frame_1 = VFrame(Label("Thermal Image Controls"))
frame_1.minsize = (202, 163)
frame_1.topleft = 3, 3

frame_1_box = Box(202, 159)

minTemp = 80.0  # Initial Low range of the sensor (this will be blue on the screen)
maxTemp = 90.0  # Initial High range of the sensor (this will be red on the screen)

# Entry box for min temp in degrees C
lbl_1 = Label("Min Temp (F)")
lbl_1.topleft = 1, 8
minTempEntry = Entry(str(minTemp))
minTempEntry.minsize = (30, 10)
minTempEntry.topleft = 83, 8

# Entry box for max temp in degrees C
lbl_2 = Label("Max Temp (F)")
lbl_2.topleft = 1, 49
maxTempEntry = Entry(str(maxTemp))
maxTempEntry.minsize = (30, 5)
maxTempEntry.topleft = 83, 48
# Entry widgets are tied to the ENTER key and emit a signal directing to the update function
minTempEntry.connect_signal("input", updateTemp)
maxTempEntry.connect_signal("input", updateTemp)

# Small ScrollBars.
vScrollMin = VScrollBar(10, 200)
vScrollMin.step = -0.1
vScrollMin.topleft = 120, 0
vScrollMin.set_value(minTemp)
vScrollMax = VScrollBar(10, 200)
vScrollMax.step = -0.1
vScrollMax.topleft = 120, 37
vScrollMax.set_value(maxTemp)
vScrollMin.connect_signal(SIG_MOUSEDOWN, colRangeSel)
vScrollMax.connect_signal(SIG_MOUSEDOWN, colRangeSel)

# Load the movie camera icon.
frame_4 = VFrame()
frame_4.minsize = (40, 40)
imagemap = ImageMap("camera3.png")
frame_4.add_child(imagemap)
frame_4.topleft = 146, 28

# Table for frame rate radio buttons
FPS_Table = Table(2, 2)
FPS_Table.spacing = 2
FPS_Table.set_column_align(0, ALIGN_LEFT)
FPS_Table.set_column_align(1, ALIGN_LEFT)
FPS_Table.topleft = 1, 80
lbl_7 = Label("1 fps")
lbl_8 = Label("10 fps")
FPS_Table.add_child(0, 0, lbl_7)
FPS_Table.add_child(1, 0,  lbl_8)
# Create radio buttons and assign to group
fpsGroup = None
FPS_Btn1 = RadioButton(None, fpsGroup)   # Create the radio buttons
FPS_Btn1.minsize = (10,10)
FPS_Table.add_child(0, 1, FPS_Btn1)
FPS_Btn1.connect_signal(SIG_TOGGLED, frameRate)
FPS_Btn2 = RadioButton(None, FPS_Btn1)
FPS_Btn2.connect_signal(SIG_TOGGLED, frameRate)
FPS_Btn2.minsize = (10, 10)
FPS_Table.add_child(1, 1, FPS_Btn2)
FPS_Btn1.activate()

# Table for smoothing control
lbl_12 = Label("Image")
lbl_13 = Label("Smoothing")
lbl_12.topleft = 3, 125
lbl_13.topleft = 3, 140
smoothTable = Table(2, 3)
smoothTable.spacing = 4
smoothTable.set_column_align(0, ALIGN_LEFT)
smoothTable.set_column_align(1, ALIGN_LEFT)
smoothTable.topleft = 82, 118
lbl_9 = Label("Low")
lbl_10 = Label("Med")
lbl_11 = Label("High")
smoothTable.add_child(0, 0, lbl_9)
smoothTable.add_child(0, 1,  lbl_10)
smoothTable.add_child(0, 2,  lbl_11)
# Create radio buttons and assign to group
smoothGroup = None
smoothBtn1 = RadioButton(None, fpsGroup)   # Create the radio buttons
smoothBtn1.minsize = (10, 10)
smoothTable.add_child(1, 0, smoothBtn1)
smoothBtn1.connect_signal(SIG_TOGGLED, smoothCtrl)
smoothBtn2 = RadioButton(None, smoothBtn1)
smoothBtn2.connect_signal(SIG_TOGGLED, smoothCtrl)
smoothBtn2.minsize = (10, 10)
smoothTable.add_child(1, 1, smoothBtn2)
smoothBtn3 = RadioButton(None, smoothBtn1)
smoothBtn3.connect_signal(SIG_TOGGLED, smoothCtrl)
smoothBtn3.minsize = (10, 10)
smoothTable.add_child(1, 2, smoothBtn3)
smoothBtn1.activate()

# Custom color modifications to the widgets
# Add it here to avoid changing label color for frame and entry widgets
base.GlobalStyle.load("ThermalCam.rc")

# Run button
button = ToggleButton("RUN")
button.minsize = 48, 28
button.topleft = 148, 0
button.connect_signal(SIG_TOGGLED, runControl)

avg_button = ToggleButton("Avg ON")
avg_button.minsize = 65, 28
avg_button.topleft = 70, 86
avg_button.connect_signal(SIG_TOGGLED, movAvg)

frame_1_box.add_child(lbl_1, minTempEntry, lbl_2, maxTempEntry, vScrollMin, vScrollMax, button, frame_4,
                     FPS_Table, avg_button, lbl_12, lbl_13, smoothTable)
frame_1.add_child(frame_1_box)
# =====================================================================================================================
# Add all widgets to the renderer and Blit the Renderer's contents at the desired position.
renderer_1.add_widget(frame_1, frame_2, frame_3)
screen.blit(renderer_1.screen, renderer_1.topleft)

# Add Status bar to second renderer instance.
status = StatusBar()
status.push_tip("VOGELECTRIC")
status.minsize = (600, status.minsize[1])
status.tip_width = 100
status.date_width = 120
status.topleft = 5, 5
renderer_2.add_widget(status)

# Set up the tick event for timer based widgets.
# pygame.time.set_timer(Constants.SIG_TICK, 10)

# ===== Main EVENT LOOP ===================================
# Setup 1 axis data arrays for plotting, arrange x axis in sequential order
xData = np.arange(1)               # Set up 1 axis array for X (time interval values)
yData = np.empty(1)                # Set up 1 axis array for Y (thermistor readings)
minDigTmp = None  # Initialize minimum temp tracking variable
maxDigTmp = None  # Initialize maximum temp tracking variable
startTim = time.time()             # Initialize plot timer
# Initialize update rate radio buttons
radioState = [False, False, False, False, False, False]
rate = updateDict[5]
graphRateBtn.activate()            # Activates the first radio button assigned

while True:
    if button.active:
        runControl()
    thermistorPlot()               # run the thermistor plotting function
    # Get events
    events = pygame.event.get()
    for event in events:
        if event.type == pygame.locals.QUIT:
            sys.exit()
    # Pass all events to the Renderer(s).
    renderer_1.distribute_events(*events)
    renderer_2.distribute_events(*events)
    renderer_3.distribute_events(*events)
    # Blit the renderer(s)
    screen.blit(renderer_1.screen, renderer_1.topleft)
    renderer_1.update()
    screen.blit(renderer_2.screen, renderer_2.topleft)
    renderer_2.update()
    screen.blit(renderer_3.screen, renderer_3.topleft)
    renderer_3.update()
    # Update pygame
    pygame.display.flip()     # Update the entire screen
    # pygame.time.delay(5)    # Pause the program in milliseconds
