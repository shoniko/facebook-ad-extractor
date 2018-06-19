import time
import os
import argparse
import msvcrt
from PIL import Image

from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.common.exceptions import NoSuchElementException, StaleElementReferenceException

import xml.etree.ElementTree as ET

annotation_xml_template = '''<annotation verified="yes">
	<folder>images</folder>
	<filename>{filename}</filename>
	<path>{path_to_file}</path>
	<source>
		<database>Unknown</database>
	</source>
	<size>
		<width>{width}</width>
		<height>{height}</height>
		<depth>3</depth>
	</size>
	<segmented>0</segmented>
</annotation>
'''

object_template = '''<object>
		<name>{objtype}</name>
		<pose>Unspecified</pose>
		<truncated>{truncated}</truncated>
		<difficult>0</difficult>
		<bndbox>
			<xmin>{xmin}</xmin>
			<ymin>{ymin}</ymin>
			<xmax>{xmax}</xmax>
			<ymax>{ymax}</ymax>
		</bndbox>
	</object>'''

argparser = argparse.ArgumentParser(
    description='Scroll the Facebook feed and store screenshots for further training')

argparser.add_argument(
    '-d',
    '--dir',
    help='path to root directory int which to store files',
    required=True)
argparser.add_argument(
    '-p',
    '--profiledir',
    help='path to the Chrome profile directory (...Google/Chrome/User Data/Default)',
    required=True)



def _main_(args):

    options = webdriver.ChromeOptions()
    # To make sure we are logged in on Facebook, use a real profile. On Windows:
    # C:\\Users\\[USERNAME]\\AppData\\Local\\Google\\Chrome\\User Data\\Default
    options.add_argument(
        "user-data-dir=" + args.profiledir)
    # Optional argument, if not specified will search path.
    driver = webdriver.Chrome(chrome_options=options)

    driver.get('https://facebook.com')

    time.sleep(5)  # Let the user actually see something!

    dpi = driver.execute_script("return window.devicePixelRatio;")
    root = args.rootDir


    body = driver.find_element_by_tag_name("body")
    cur_example = 49
    cur_element_in_fb_stream = 0
    total_elements_in_feed = 0
    while True:
        try:
            news_feed = driver.find_elements_by_css_selector(
                "div[id^=\"hyperfeed_story_id_\"]")
            total_elements_in_feed = len(news_feed)
            if (total_elements_in_feed > 20):
                raise NoSuchElementException()
            if (len(news_feed)) == 0:
                raise NoSuchElementException()
        except NoSuchElementException as exception:
            body.send_keys(webdriver.common.keys.Keys.HOME)
            cur_element_in_fb_stream = 0
            driver.refresh()
            body = driver.find_element_by_tag_name("body")
            time.sleep(2)  # Let the user actually see something!
            continue

        pos_in_list = 0
        listOfObjects = {}
        failure = False

        window_size = driver.get_window_size()

        # Create a dictionary of news feed items
        for i in range(0, len(news_feed)):
            cur_element_in_fb_stream += 1
            try:
                location = news_feed[i].location
                size = news_feed[i].size
                isSponsored = False
                offset = vertOffset = driver.execute_script(
                    "return window.pageYOffset;")
                if ((location["y"] - offset) >= window_size["height"]):
                    break
                # Below are all the checks to detect if the item is actually an ad
                if ("\nSponsored " in news_feed[i].text):
                    isSponsored = True

                if (len(news_feed[i].find_elements_by_partial_link_text("is_sponsored")) != 0):
                    isSponsored = True

                if (len(news_feed[i].find_elements_by_css_selector(
                        "div[id^=\"feed_subtitle_\"] > span > a[class*=\"_\"][href=\"#\"] > div")) != 0):
                    isSponsored = True
                if (len(news_feed[i].find_elements_by_css_selector("input[data-next-question-id]")) != 0):
                    isSponsored = True

                listOfObjects[pos_in_list] = [location, size, isSponsored, offset]
                pos_in_list += 1
            except StaleElementReferenceException as identifier:
                failure = True
                break
        if failure:
            # force exception
            cur_element_in_fb_stream = 1000
            continue
        # Make a screenshot and resize it
        filename = "example_" + str(cur_example) + ".png"
        driver.save_screenshot(root + "images_full//" + filename)

        basewidth = window_size["width"]
        img = Image.open(root + "images_full//" + filename)
        hsize = int((float(img.size[1]) / float(dpi)))
        img = img.resize((basewidth, hsize), Image.ANTIALIAS)
        img.save(root + "images//" + filename)
        img.close()
        os.remove(root + "images_full//" + filename)

        f = open(root + "annotations//fbad-" + str(cur_example) + ".xml", "w")

        print(cur_example)

        xmlTree = ET.fromstring(annotation_xml_template.format(
            filename=filename,
            path_to_file="images/" + filename,
            width=basewidth,
            height=hsize))

        objectsAdded = False

        for (index, (location, size, isSponsored, offset)) in listOfObjects.items():
            xmin = location["x"]
            ymin = (location["y"] - offset)
            xmax = (location["x"] + size["width"])
            ymax = (location["y"] + size["height"] - offset)
            truncated = False
            fbHeaderHeight = 42 # Yes, 42!
            if (size["width"]) == 0 or (size["height"]) == 0 or (ymax <= 0):
                continue
            if ymin > hsize:
                #object is not yet in viewport. ignore
                continue
            if ymin < fbHeaderHeight:
                # truncated object?
                if ymax < hsize and ymax > fbHeaderHeight:
                    truncated = True
                    cur_element_in_fb_stream -= 1
                    ymin = fbHeaderHeight
                else:
                    # object is out of viewport. ignore
                    continue
            if ymax > hsize:
                truncated = True
                cur_element_in_fb_stream -= 1
                ymax = hsize

            xmlTree.append(ET.fromstring(object_template.format(
                xmin=xmin,
                ymin=ymin,
                xmax=xmax + 7,
                ymax=ymax,
                objtype='newsfeed_ad' if isSponsored else 'newsfeed',
                truncated='1' if truncated else '0'
            )))
            objectsAdded = True

        sideAd = body.find_elements_by_class_name('ego_unit_container')
        sideAdLen = len(sideAd)
        while (sideAdLen > 0):
            location = sideAd[sideAdLen - 1].location
            size = sideAd[sideAdLen - 1].size
            offset = driver.execute_script("return window.pageYOffset;")

            sideAd = sideAd[:sideAdLen - 1]
            sideAdLen = len(sideAd)

            xmin = location["x"]
            ymin = (location["y"] - offset)
            xmax = (location["x"] + size["width"])
            ymax = (location["y"] + size["height"] - offset)
            truncated = False
            if (size["width"]) == 0 or (size["height"]) == 0 or (ymax <= 0):
                continue
            if ymin > hsize:
                continue
            # truncate the object
            if ymin < 0:
                truncated = True
                ymin = 0
            if ymax > hsize:
                truncated = True
                ymax = hsize

            xmlTree.append(ET.fromstring(object_template.format(
                xmin=xmin - 3,
                ymin=ymin,
                xmax=xmax + 23,
                ymax=ymax,
                objtype='side_ad',
                truncated='1' if truncated else '0'
            )))

        if objectsAdded:
            outputXml = ET.tostring(xmlTree, encoding="unicode")
            f.write(outputXml)
            f.close()
            cur_example += 1
        else:
            # Force exception
            cur_element_in_fb_stream = 1000
        body.send_keys(webdriver.common.keys.Keys.PAGE_DOWN)
        time.sleep(2)  # Let the user actually see something!

    driver.quit()


if __name__ == '__main__':
    args = argparser.parse_args()
    _main_(args)

