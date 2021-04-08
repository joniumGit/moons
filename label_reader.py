from vicarutil.image import read_image

if __name__ == '__main__':
    while True:
        file = input("Give file path: ")
        if file:
            file = file.strip()
        else:
            break
        image = read_image(file)
        print(file)
        print(image.labels)
        if image.eol_labels:
            print(image.eol_labels)
