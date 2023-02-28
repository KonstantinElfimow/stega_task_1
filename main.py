from PIL import Image, ImageDraw
from collections import deque
import numpy as np


def message_to_bits(string: str) -> list[int]:
    """ Из строки в список битов. Пример: Hi --> [0, 1, 0, 0, 1, 0, 0, 0, 0, 1, 1, 0, 1, 0, 0, 1] """
    b = list(string.encode('utf-8'))
    return list(map(int, ''.join(['{0:08b}'.format(num) for num in b])))


def from_bits(bits: list[int]) -> str:
    """ Из списка битов в строку. Пример: [0, 1, 0, 0, 1, 0, 0, 0, 0, 1, 1, 0, 1, 0, 0, 1] --> Hi """
    return ''.join(chr(int(''.join(map(str, bits[i: i + 8])), 2)) for i in range(0, len(bits), 8))


def lsb_encoding(old_file: str, message: str, new_file: str) -> int:
    global img
    try:
        # Получим 3-мерную матрицу RGB из .png.
        img = Image.open(old_file).convert('RGB')
        pix = img.load()
        # длина и ширина изображения
        width, height = img.size[0], img.size[1]

        # Преобразование сообщения из строки в поток битов.
        bits = message_to_bits(message)
        length: int = len(bits)
        if length > width * height * 3:
            raise ValueError("Размер контейнера не позволяет записать в него сообщение!")
        bits = deque(bits)

        # Так как нужно при скрытии использовать обратный порядок обхода пикселей контейнера при реализации ССИ,
        # то будем использовать стек, а затем формировать новое изображение.
        stack: deque[tuple] = deque()
        # Проходим в обратном порядке
        for y in range(height - 1, -1, -1):
            for x in range(width - 1, -1, -1):
                # Пиксель с тремя координатами
                pixel_rgb: list[int] = list()
                # Для каждого из цветовых каналов пикселя скрываем информацию, если биты сообщения ещё есть в очереди, и
                # запоминаем keys позиции со спрятанной информацией, если нет - пиксель оставляем нетронутым.
                for z in range(3):
                    if bits:
                        # Стираем младший бит цветового канала пикселя, записываем в него новый бит с информацией.
                        pixel_rgb.append(((pix[(x, y)][z] >> 1) << 1) | bits.popleft())
                    else:
                        pixel_rgb.append(pix[(x, y)][z])
                stack.append(((x, y), tuple(pixel_rgb)))
        # Отрисовываем новое изображение со скрытой информацией.
        draw = ImageDraw.Draw(img)
        while stack:
            draw.point(*(stack.pop()))
        img.save(new_file, 'PNG')
        return length
    except Exception as ex:
        print(ex)
    finally:
        img.close()


def lsb_decoding(image_file: str, length: int) -> str:
    # Получим 3-мерную матрицу RGB из .png.
    img = Image.open(image_file).convert('RGB')
    pix = img.load()
    img.close()
    width, height = img.size[0], img.size[1]
    # Получаем биты с пользовательской информацией в изображении по переданным ключам.
    count: int = 0
    bits: list[int] = list()
    for y in range(height - 1, -1, -1):
        for x in range(width - 1, -1, -1):
            for z in range(3):
                bits.append(int(pix[(x, y)][z] & 0x01))
                count += 1
                if count == length:
                    return from_bits(bits)


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
    length = lsb_encoding(empty_file, message, full_file)
    m = lsb_decoding(full_file, length)
    print(m)
    metrics(empty_file, full_file)


if __name__ == '__main__':
    main()
