from PIL import Image
import sys, os


def webp_to_jpg_path(path):
    if not path.endswith(".webp"):
        return
    return path[:-5] + ".jpg"


def convert_image(image_path, delete_old=False):
    if not image_path.endswith(".webp"):
        return
    Image.open(image_path).convert("RGB").save(
        webp_to_jpg_path(image_path), "jpeg")
    # Todo: Remove old file when delete_old is True


def convert_path(path):
    if not os.path.exists(path):
        print("Not found")
        return
    if os.path.isdir(path):
        for webp_file in os.listdir(path):
            if os.path.isfile(os.path.join(path, webp_file)) and webp_file.endswith(".webp"):
                convert_image(os.path.join(path, webp_file))
    else:
        convert_image(path)


def prompt_for_path():
    convert_path(input("Enter file path: "))


if __name__ == "__main__":
    if len(sys.argv) != 2:
        prompt_for_path()
    elif os.path.exists(sys.argv[1]):
        convert_path(sys.argv[1])

