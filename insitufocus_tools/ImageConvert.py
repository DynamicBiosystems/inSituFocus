import logging
import os
import threading
import time
import traceback
import pyvips
import argparse


parser = argparse.ArgumentParser()
parser.add_argument('--path', required=True, help='DAPI.tif absolute path')
args = parser.parse_args()


class ImageConverter:
    def __init__(self, inputImage, outputImage):
        self.inputImage = inputImage
        self.outputImage = outputImage

    def convert(self):
        logging.debug(" ".join(["Converting: ", self.inputImage, self.outputImage]))
        if not os.path.isfile(self.outputImage) or (
            os.path.getmtime(self.inputImage) > os.path.getmtime(self.outputImage)
        ):

            def convertThread():
                try:
                    imgVips = pyvips.Image.new_from_file(self.inputImage)
                    minVal = imgVips.percent(0.5)
                    maxVal = imgVips.percent(99.5)
                    if minVal == maxVal:
                        minVal = 0
                        maxVal = 255
                    if minVal < 0 or maxVal > 255:
                        logging.debug(
                            f"Rescaling image {self.inputImage}: "
                            f"{minVal} - {maxVal} to 0 - 255"
                        )
                        imgVips = (255.0 * (imgVips - minVal)) / (maxVal - minVal)
                        imgVips = (imgVips < 0).ifthenelse(0, imgVips)
                        imgVips = (imgVips > 255).ifthenelse(255, imgVips)
                    imgVips = imgVips.scaleimage()
                    imgVips.tiffsave(
                        self.outputImage,
                        pyramid=True,
                        tile=True,
                        tile_width=256,
                        tile_height=256,
                        compression="jpeg",
                        Q=95,
                        properties=True,
                    )
                except Exception:
                    logging.error("Impossible to convert image using VIPS:")
                    logging.error(traceback.format_exc())
                self.convertDone = True

            self.convertDone = False
            threading.Thread(target=convertThread, daemon=True).start()
            while not self.convertDone:
                time.sleep(0.02)
        return self.outputImage


path = args.path

newpath = (os.path.dirname(path) + "/.insitufocus/" + os.path.splitext(os.path.basename(path))[0] + ".tif")
os.makedirs(os.path.dirname(path) + "/.insitufocus/", exist_ok=True)
ImageConverter(path, newpath).convert()