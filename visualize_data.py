import argparse
import os
import ntpath
from tkinter import *
from PIL import Image, ImageTk, ImageDraw
import xml.etree.ElementTree as ET


argparser = argparse.ArgumentParser(
    description='Visualize training data for YOLO algorithm')

argparser.add_argument(
    '-f',
    '--file',
    help='path to annotation file')

curFilePath = ""
root = Tk()
canvas = Canvas(root, width = 800, height = 600)      
img = None
img_on_canvas = None

def nextFile(filename):
    global fileList
    global directory
    nextIndex = fileList.index(ntpath.basename(filename)) + 1
    if nextIndex == 0 or nextIndex == len(fileList):
        return None
    return os.path.join(directory, fileList[nextIndex])

def prevFile(filename):
    global fileList
    global directory

    nextIndex = fileList.index(ntpath.basename(filename)) - 1
    if nextIndex == 0 or nextIndex == len(fileList):
        return None
    return os.path.join(directory, fileList[nextIndex])

def leftKey(event):
    global canvas
    global img_on_canvas
    global img
    global curFilePath

    curFilePath = prevFile(curFilePath)
    image = drawBoundingBoxesOnImage(curFilePath)
    
    img = ImageTk.PhotoImage(image)
    imgWidth, imgHeight = image.size
    canvas.itemconfig(img_on_canvas, image = img)
    canvas.pack()


def rightKey(event):
    global canvas
    global img_on_canvas
    global img
    global curFilePath

    curFilePath = nextFile(curFilePath)
    image = drawBoundingBoxesOnImage(curFilePath)

    img = ImageTk.PhotoImage(image)
    imgWidth, imgHeight = image.size
    canvas.itemconfig(img_on_canvas, image = img)
    canvas.pack()

def drawBoundingBoxesOnImage(annotationPath):
    global canvas
    global img
    global root
    global img_on_canvas
    global directory
    
    tree = ET.parse(annotationPath)
    rootXml = tree.getroot()

    imagePath = rootXml.findall("./path")[0].text
    
    imagePath = os.path.join(directory, "..", imagePath)

    image = Image.open(imagePath)
    draw = ImageDraw.Draw(image)

    annotatedObjects = rootXml.findall("./object")
    for annotatedObject in annotatedObjects:
        objType = annotatedObject.find("name").text
        xmin = float(annotatedObject.find("bndbox/xmin").text)
        ymin = float(annotatedObject.find("bndbox/ymin").text)
        xmax = float(annotatedObject.find("bndbox/xmax").text)
        ymax = float(annotatedObject.find("bndbox/ymax").text)
        color = "Blue"
        if objType == "newsfeed":
            color = "Yellow"
        elif objType == "newsfeed_ad":
            color = "Red"
        elif objType == "side_ad":
            color = "orange"
        draw.rectangle(((xmin, ymin), (xmax, ymax)), outline = color)
    
    return image


def _main_(args):

    global canvas
    global img
    global root
    global img_on_canvas
    global directory
    global fileList
    global curFilePath

    curFilePath = args.file
    
    directory = os.path.dirname(curFilePath)
    fileList = os.listdir(directory)
    
    image = drawBoundingBoxesOnImage(args.file)

    img = ImageTk.PhotoImage(image)
    imgWidth, imgHeight = image.size
    canvas = Canvas(root, width = imgWidth, height = imgHeight)
    img_on_canvas = canvas.create_image(20,20, anchor=NW, image=img)
    canvas.pack()

    root.bind('<Left>', leftKey)
    root.bind('<Right>', rightKey)
    mainloop()


if __name__ == '__main__':
    args = argparser.parse_args()
    _main_(args)
