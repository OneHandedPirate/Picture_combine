import asyncio
import pathlib
import time
from io import BytesIO
from typing import List

from PIL import Image
import aiofiles

from config import MARGIN, IMAGE_PER_ROW, RESIZE_RATE


async def async_open_image(image_path: str) -> Image.Image:
    async with aiofiles.open(image_path, 'rb') as f:
        image_data = await f.read()
    return Image.open(BytesIO(image_data))


async def async_process_image(image_path: str, resize_rate: float) -> Image.Image:
    img = await async_open_image(image_path)
    img = img.resize((int(img.width * resize_rate), int(img.height * resize_rate)))
    return img.convert("RGB")


async def combine_images_in_grid(
        image_paths: List[str],
        output_path: str,
        margin: int = MARGIN,
        images_per_row: int = IMAGE_PER_ROW,
        resize_rate: float = RESIZE_RATE
) -> None:
    images = await asyncio.gather(*(async_process_image(image_path, resize_rate) for image_path in image_paths))

    max_width = max(img.width for img in images)
    max_height = max(img.height for img in images)

    grid_width = (max_width + margin) * images_per_row + margin
    num_rows = (len(images) + images_per_row - 1) // images_per_row
    grid_height = (max_height + margin) * num_rows + margin

    combined_image = Image.new("RGB", (grid_width, grid_height), color=(255, 255, 255))

    for index, img in enumerate(images):
        row = index // images_per_row
        col = index % images_per_row
        x_offset = margin + col * (max_width + margin)
        y_offset = margin + row * (max_height + margin)
        combined_image.paste(img, (x_offset, y_offset))

    output_file = "Result.tiff"
    combined_image.save(f'{output_path}/{output_file}', format='TIFF')


async def async_process_folder(path_to_dir: str) -> None:
    images = []
    nested_folders = []

    folder_full_path = pathlib.Path(path_to_dir).resolve()

    for path in folder_full_path.iterdir():
        if path.is_file() and path.suffix.lower() in (".jpg", ".png", "jpeg"):
            images.append(str(path))
        if path.is_dir():
            nested_folders.append(str(path))

    if nested_folders:
        await asyncio.gather(*(async_process_folder(path) for path in nested_folders))

    if images:
        await combine_images_in_grid(images, str(folder_full_path))


async def main():
    while True:
        try:
            path_to_dir = input(
                "Введите путь к папке с изображениями (абсолютный или относительный):\n"
                "Для выхода введите \"exit\" без кавычек\n"
            )

            if path_to_dir.lower() == "exit":
                break

            start_time = time.time()
            await async_process_folder(path_to_dir)

            print(f"Готово. Время выполнения : {time.time() - start_time:.5f}")
            break
        except Exception as e:
            print(f"Что-то пошло не так, попробуйте еще раз: {e}")
            time.sleep(2)


if __name__ == "__main__":
    asyncio.run(main())
