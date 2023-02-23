from PIL import Image, ImageDraw
from collections import deque


def to_bits(string: str) -> list[int]:
    """ Из строки в список битов. Пример: Hi --> [0, 1, 0, 0, 1, 0, 0, 0, 0, 1, 1, 0, 1, 0, 0, 1] """
    return list(map(int, ''.join([bin(ord(i)).lstrip('0b').rjust(8, '0') for i in string])))


def from_bits(bits: list[int]) -> str:
    """ Из списка битов в строку. Пример: [0, 1, 0, 0, 1, 0, 0, 0, 0, 1, 1, 0, 1, 0, 0, 1] --> Hi """
    return ''.join(chr(int(''.join(map(str, bits[i: i + 8])), 2)) for i in range(0, len(bits), 8))


def lsb_encoding(old_filepath: str, message: str, new_filepath: str, key_filepath: str) -> bool:
    # Получим 3-мерную матрицу RGB из .png.
    img = Image.open(old_filepath)
    draw = ImageDraw.Draw(img)
    pix = img.load()
    # длина и ширина изображения
    length, width = img.size[0], img.size[1]

    # Преобразование сообщения из строки в очередь битов строки.
    bits: deque[int] = deque(to_bits(message))
    # Так как нужно при скрытии использовать обратный порядок обхода пикселей контейнера при реализации ССИ,
    # то будем использовать стек, а затем формировать новое изображение.
    stack: deque[tuple] = deque()
    # Флаг записи сообщения в контейнер (если False, то размера контейнера не хватило для записи M в контейнер).
    is_hidden: bool = False
    # Координаты точек, где будет сокрыто сообщение.
    keys: deque[str] = deque()
    # Проходим в обратном порядке
    for i in range(width - 1, -1, -1):
        for j in range(length - 1, -1, -1):
            # Пиксель с тремя координатами
            pixel_rgb: list[int] = list()
            # Для каждого из цветовых каналов пикселя скрываем информацию, если биты сообщения ещё есть в очереди, и
            # запоминаем keys позиции со спрятанной информацией, если нет - пиксель оставляем нетронутым.
            for k in range(3):
                if bits:
                    keys.append(str(j) + ' ' + str(i) + ' ' + str(k))
                    # Стираем младший бит цветового канала пикселя, записываем в него новый бит с информацией.
                    pixel_rgb.append(((pix[(j, i)][k] >> 1) << 1) | bits.popleft())
                    if not bits:
                        # Сообщение успешно было спрятано.
                        is_hidden = True
                else:
                    pixel_rgb.append(pix[(j, i)][k])
            stack.append(((j, i), tuple(pixel_rgb)))

    if not is_hidden:
        raise ValueError("Контейнер был переполнен раньше, чем записалось сообщение!")
    # Записываем ключи в файл в том же порядке, что и при обратном обходе пикселей контейнера при реализации нашего ССИ.
    with open(key_filepath, encoding='utf-8', mode='w') as key_file:
        while keys:
            key_file.write(keys.popleft() + '\n')
    # Отрисовываем новое изображение со скрытой информацией.
    while stack:
        draw.point(*(stack.pop()))
    img.save(new_filepath, 'PNG')
    # Сокрытие информации в изображение прошло успешно.
    return True


def lsb_decoding(image_file: str, key_filepath: str) -> str:
    # Получим 3-мерную матрицу RGB из .png.
    img = Image.open(image_file)
    pix = img.load()
    # Получаем ключи из файла.
    keys = list()
    with open(key_filepath, encoding='utf-8', mode='r') as key_file:
        for line in key_file.readlines():
            key = list()
            for word in line.split():
                key.append(int(word))
            keys.append(tuple(key))
    keys = tuple(keys)
    # Получаем биты с пользовательской информацией в изображении по переданным ключам.
    bits: list[int] = list()
    for key in keys:
        j, i, k = key
        bits.append(int(pix[(j, i)][k] & 1))
    result: str = from_bits(bits)
    return result


def main():
    old_file: str = 'in/image.png'
    message: str = 'This is the secret!'
    new_file: str = 'out/new_image.png'
    key_filepath: str = 'keys.txt'
    lsb_encoding(old_file, message, new_file, key_filepath)
    m = lsb_decoding(new_file, key_filepath)
    print(m)


if __name__ == '__main__':
    main()
