from PIL import Image
import numpy as np

import warnings
warnings.filterwarnings(action='once')

encoding: str = 'utf-8'


class LSB:
    def __init__(self, old_image_path: str, new_image_path: str):
        self.__empty_image_path: str = old_image_path
        self.__full_image_path: str = new_image_path
        self.__occupancy: int = 0

    @staticmethod
    def str_to_bits(message: str) -> list:
        result = []
        for num in list(message.encode(encoding=encoding)):
            result.extend([(num >> x) & 1 for x in range(7, -1, -1)])
        return result

    @staticmethod
    def bits_to_str(bits: list) -> str:
        chars = []
        for b in range(len(bits) // 8):
            byte = bits[b * 8:(b + 1) * 8]
            chars.append(chr(int(''.join([str(bit) for bit in byte]), 2)))
        return ''.join(chars)

    def embed(self, message: str):
        img = Image.open(self.__empty_image_path).convert('RGB')
        picture = np.asarray(img, dtype='uint8')
        img.close()

        picture_shape = picture.shape
        height, width, depth = picture.shape[0], picture.shape[1], picture.shape[2]

        message_bits = LSB.str_to_bits(message)
        if len(message_bits) > height * width * depth:
            raise ValueError('Размер сообщения превышает размер контейнера!')
        message_bits = np.asarray(message_bits)
        bits_length = message_bits.shape[0]

        picture = picture.reshape(-1)
        picture[:bits_length] = ((picture[:bits_length] >> 1) << 1) | message_bits

        picture = picture.reshape(picture_shape)

        self.__occupancy = bits_length
        Image.fromarray(picture).save(self.__full_image_path, 'PNG')

    def recover(self) -> str:
        img = Image.open(self.__full_image_path).convert('RGB')
        picture = np.asarray(img, dtype='uint8')
        img.close()

        recovered_message = picture.reshape(-1)[:self.__occupancy] & 0x01
        return LSB.bits_to_str(list(recovered_message))

    @property
    def occupancy(self) -> int:
        return self.__occupancy


def metrics(empty_image: str, full_image: str) -> None:
    img = Image.open(empty_image).convert('RGB')
    empty = np.asarray(img, dtype='uint8')
    img.close()

    img = Image.open(full_image).convert('RGB')
    full = np.asarray(img, dtype='uint8')
    img.close()

    max_d = np.max(np.abs(empty.astype(int) - full.astype(int)))
    print('Максимальное абсолютное отклонение:\n{}'.format(max_d))

    SNR = np.sum(empty * empty) / np.sum((empty - full) ** 2)
    print('Отношение сигнал-шум:\n{}'.format(SNR))

    H, W = empty.shape[0], empty.shape[1]
    MSE = np.sum((empty - full) ** 2) / (W * H)
    print('Среднее квадратичное отклонение:\n{}'.format(MSE))

    # Универсальный индекс качества (УИК)
    # С помощью данной метрики оцениваются
    # коррелированность, изменение динамического диапазона, а также изменение
    # среднего значения одного изображения относительно другого.
    # -1 <= UQI <= 1
    # минимальному искажению изображения соответствуют
    # значения UQI ~ 1
    sigma = np.sum((empty - np.mean(empty)) * (full - np.mean(full))) / (H * W)
    UQI = (4 * sigma * np.mean(empty) * np.mean(full)) / \
          ((np.var(empty) ** 2 + np.var(full) ** 2) * (np.mean(empty) ** 2 + np.mean(full) ** 2))
    print(f'Универсальный индекс качества (УИК):\n{UQI}\n')


def main():
    old_image = 'input/old_image.png'
    new_image = 'output/new_image.png'

    with open('message.txt', mode='r', encoding=encoding) as file:
        message = file.read()

    lsb = LSB(old_image, new_image)
    lsb.embed(message)
    recovered_message = lsb.recover()
    print('Ваше сообщение:\n{}'.format(recovered_message))

    metrics(old_image, new_image)


if __name__ == '__main__':
    main()
