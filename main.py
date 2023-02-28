from PIL import Image, ImageDraw
from collections import deque
import numpy as np


def to_bits(string: str) -> list[int]:
    """ Из строки в список битов. Пример: Hi --> [0, 1, 0, 0, 1, 0, 0, 0, 0, 1, 1, 0, 1, 0, 0, 1] """
    return list(map(int, ''.join([bin(ord(i)).lstrip('0b').rjust(8, '0') for i in string])))


def from_bits(bits: list[int]) -> str:
    """ Из списка битов в строку. Пример: [0, 1, 0, 0, 1, 0, 0, 0, 0, 1, 1, 0, 1, 0, 0, 1] --> Hi """
    return ''.join(chr(int(''.join(map(str, bits[i: i + 8])), 2)) for i in range(0, len(bits), 8))


def lsb_encoding(old_file: str, message: str, new_file: str, key_file: str) -> None:
    global img
    try:
        # Получим 3-мерную матрицу RGB из .png.
        img = Image.open(old_file).convert('RGB')
        pix = img.load()
        # длина и ширина изображения
        width, height = img.size[0], img.size[1]

        if len(message) * 8 > width * height * 3:
            raise ValueError("Размер контейнера не позволяет записать в него сообщение!")

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
        for y in range(height - 1, -1, -1):
            for x in range(width - 1, -1, -1):
                # Пиксель с тремя координатами
                pixel_rgb: list[int] = list()
                # Для каждого из цветовых каналов пикселя скрываем информацию, если биты сообщения ещё есть в очереди, и
                # запоминаем keys позиции со спрятанной информацией, если нет - пиксель оставляем нетронутым.
                for z in range(3):
                    if bits:
                        keys.append('{} {} {}'.format(x, y, z))
                        # Стираем младший бит цветового канала пикселя, записываем в него новый бит с информацией.
                        pixel_rgb.append(((pix[(x, y)][z] >> 1) << 1) | bits.popleft())
                    else:
                        pixel_rgb.append(pix[(x, y)][z])
                stack.append(((x, y), tuple(pixel_rgb)))
        # Записываем ключи в файл в том же порядке, что и при обратном обходе пикселей контейнера при реализации
        # нашего ССИ.
        with open(key_file, encoding='utf-8', mode='w') as file:
            while keys:
                file.write(keys.popleft() + '\n')
        # Отрисовываем новое изображение со скрытой информацией.
        draw = ImageDraw.Draw(img)
        while stack:
            draw.point(*(stack.pop()))
        img.save(new_file, 'PNG')
    except Exception as ex:
        print(ex)
    finally:
        img.close()


def lsb_decoding(image_file: str, key_filepath: str) -> str:
    # Получим 3-мерную матрицу RGB из .png.
    img = Image.open(image_file).convert('RGB')
    pix = img.load()
    img.close()
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
        x, y, z = key
        bits.append(int(pix[(x, y)][z] & 1))
    result: str = from_bits(bits)
    return result


def metrics(empty_file: str, full_file: str) -> None:
    img = Image.open(empty_file).convert('RGB')
    empty = np.asarray(img, dtype=np.uint8)
    img.close()

    img = Image.open(full_file).convert('RGB')
    full = np.asarray(img, dtype=np.uint8)
    img.close()

    NMSE_res = np.sum((empty - full) * (empty - full)) / np.sum((empty * empty))
    print('Нормированное среднее квадратичное отклонение:\n{}'.format(NMSE_res))

    SNR_res = 1 / NMSE_res
    print('Отношение сигнал-шум:\n{}'.format(SNR_res))

    H, W = empty.shape[0], empty.shape[1]
    PSNR_res = W * H * ((np.max(empty) ** 2) / np.sum((empty - full) * (empty - full)))
    print('Пиковое отношение сигнал-шум:\n{}'.format(PSNR_res))


def main():
    empty_file: str = 'in/image.png'
    message: str = 'This is the secret!'
    full_file: str = 'out/new_image.png'
    key_filepath: str = 'keys.txt'
    lsb_encoding(empty_file, message, full_file, key_filepath)
    m = lsb_decoding(full_file, key_filepath)
    print(m)
    metrics(empty_file, full_file)


if __name__ == '__main__':
    main()
