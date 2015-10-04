from PIL import Image
import argparse
import binascii
import os


# Opens an image at the given path
def open_image(path):
    image = None
    try:
        image = Image.open(path)
    except Exception as e:
        print("Image not found")
        print(e)
        return
    return image


def file_to_binary(file):
    with file as f:
        byte = f.read()
        return list(bin(int('1'+binascii.hexlify(byte), 16))[3:].zfill(8))


def str_to_binary(string):
    return ''.join(format(ord(c), 'b').zfill(8) for c in string)


def change_lsb(color, binary, index):
    if(get_lsb(color) != binary[index]):
        modified = list(bin(color)[2:].zfill(8))
        modified[-1] = binary[index]
        modified = int(''.join(modified), 2)
        return modified
    else:
        return color


def get_lsb(color):
    if(color % 2 == 0):
        return '0'
    else:
        return '1'


def process_pixel(pixel, file_binary, index, bits_left):
    color = 0
    rgb = [pixel[0], pixel[1], pixel[2]]
    for color in range(3):
        rgb[color] = change_lsb(pixel[color], file_binary, index + color)
        bits_left -= 1
        if(bits_left == 0):
            break
    return (rgb[0], rgb[1], rgb[2])


def process_image(image, binary):
    pixels = list(image.getdata())
    file_index = 0
    pixel_index = 0
    bits_left = len(binary)
    for pixel in pixels:
        pixels[pixel_index] = process_pixel(pixel, binary, file_index, bits_left)
        file_index += 3
        bits_left -= 3
        pixel_index += 1
        if(bits_left <= 0):
            break
    return pixels


def stego_image():
    img = open_image(args.image)
    width, height = img.size
    max_size = width * height * 3 / 8

    file = open(args.file, 'rb')
    filename = os.path.basename(args.file)
    filesize = os.path.getsize(args.file)

    file_header = filename + "\0" + str(filesize) + "\0"
    file_header_size = len(str_to_binary(file_header))

    if(filesize + file_header_size > max_size):
        exit("File too large for image: {} in {}".format(filesize, max_size))
    binary = str_to_binary(file_header) + ''.join(file_to_binary(file))
    image_data = process_image(img, binary)
    img.putdata(image_data)
    img.save("stego.BMP")


def get_header(string):
    results = string.split('\0', 2)
    if(len(results) != 3):
        return 0
    return results


def decode_image():
    img = open_image("stego.BMP")
    pixels = img.getdata()
    result = []
    for pixel in pixels:
        for color in pixel:
            result.append(get_lsb(color))
    n = int(''.join(result), 2)
    filename, filesize, data = get_header(binascii.unhexlify('%x' % n))
    with open("decoded_" + filename, 'wb') as f:
        f.write(data[:int(filesize)])

# def decode_image():
#     img = open_image("stego.BMP")
#     pixels = img.getdata()
#     result = []
#     decode_count = 0
#     filesize = 0
#     quit_loop = 0
#     header_length = 0
#     for pixel in pixels:
#         if(quit_loop == 1):
#             break
#         rgb = [pixel[0], pixel[1], pixel[2]]
#         for color in rgb:
#             result.append(get_lsb(color))
#             decode_count += 1
#             if(filesize == 0 and decode_count % 8 == 0):
#                 n = int(''.join(result), 2)
#                 decoded = get_header(binascii.unhexlify('%x' % n))
#                 if(decoded != 0):
#                     filename, filesize, tempData = decoded
#                     filesize = int(filesize)*8
#                     header_length = decode_count
#         if(decode_count == filesize + header_length):
#             break
#     m = int(''.join(result), 2)
#     data = (binascii.unhexlify('%x' % m))[2]
#     with open("decoded_" + filename, 'wb') as f:
#         f.write(data)


def main():
    stego_image()
    print("Stego image created")
    decode_image()
    print("Image decoded")


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument("file", help="File to hide")
    parser.add_argument("image", help="Image to hide in")
    args = parser.parse_args()
    try:
        main()
    except KeyboardInterrupt:
        print("Exiting...")
