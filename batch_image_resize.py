from PIL import Image
import os

# define the directory
dir_path = "static/images"

# set target image width in pixels
target_width = 800

# iterate over all subdirectories
for subdir, dirs, files in os.walk(dir_path):
    for file in files:
        # check if the file is an image
        if file.endswith(('.jpg', '.png', '.jpeg')):
            try:
                # open the image file
                img = Image.open(os.path.join(subdir, file))
                # calculate the target height to keep aspect ratio the same
                width_percent = (target_width / float(img.size[0]))
                height_size = int((float(img.size[1]) * float(width_percent)))
                # resize image and save
                img = img.resize((target_width, height_size), Image.ANTIALIAS)
                img.save(os.path.join(subdir, file))
            except (IOError, PermissionError) as e:
                print(f"Unable to resize image {file} due to {str(e)}")
            except Exception as e:
                print(f"An unexpected error occurred with file {file}: {str(e)}")

print("Image resizing process is completed.")
