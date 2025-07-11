import logging
import io
from typing import Optional
import numpy as np
import PIL
from PIL import Image
import pillow_avif
from abc import abstractmethod
from .utils import get_jpg_quality
from PIL.JpegImagePlugin import get_sampling


class BaseTransformer:
    @abstractmethod
    def __call__(self, img):
        # [H, W, C]
        raise NotImplementedError


class ThresholdCrop(BaseTransformer):
    def __init__(self, lower_threshold: int, upper_threshold: int) -> None:
        self.lower = lower_threshold
        self.upper = upper_threshold

    def __call__(self, img: Image.Image):
        if img.mode == 'L':
            gray_img = img
        else:
            gray_img = img.convert('L')
        mat = np.array(gray_img)
        in_threshold = (mat >= self.lower) & (mat <= self.upper)  # type: ignore
        if not np.any(in_threshold): return img
        for h0 in range(in_threshold.shape[0]):
            if np.any(in_threshold[h0, :]): break
        for w0 in range(in_threshold.shape[1]):
            if np.any(in_threshold[:, w0]): break
        for h1 in range(in_threshold.shape[0] - 1, -1, -1):
            if np.any(in_threshold[h1, :]): break
        for w1 in range(in_threshold.shape[1] - 1, -1, -1):
            if np.any(in_threshold[:, w1]): break
        if w0 == w1 or h0 == h1: return img  # type: ignore
        return img.crop((w0, h0, w1, h1))  # type: ignore


class DownSample(BaseTransformer):
    def __init__(self, screen_height: int, screen_width: int, interpolation: str = 'cubic') -> None:
        self.height = screen_height
        self.width = screen_width
        if interpolation == 'cubic': self.interpolation = Image.Resampling.BICUBIC
        elif interpolation == 'lanczos': self.interpolation = Image.Resampling.LANCZOS
        elif interpolation == 'box': self.interpolation = Image.Resampling.BOX
        elif interpolation == 'linear': self.interpolation = Image.Resampling.BILINEAR
        elif interpolation == 'nearest': self.interpolation = Image.Resampling.NEAREST

        else: raise ValueError(f'Invalid interpolation {interpolation}')

    def __call__(self, img: Image.Image):
        if img.height > self.height or img.width > self.width:
            scaled_height = int(img.height * self.width / img.width)
            scaled_width = int(img.width * self.height / img.height)
            if scaled_height > self.height: shape = (scaled_width, self.height)
            else: shape = (self.width, scaled_height)
            img = img.resize(shape, resample=self.interpolation)
        return img


class ImagePipeline:
    def __init__(
        self,
        fixed_ext: str = '',
        jpeg_quality: int = -1,
        avif_quality: int = 85,
        avif_speed: int = 6,
        webp_quality: int = 95,
        webp_method: int = 4,
        webp_lossless: bool = False,
        png_compression: int = 1,
    ) -> None:
        self.transforms = []
        self.fixed_ext = None if fixed_ext == '' else fixed_ext
        self.jpeg_quality = jpeg_quality
        self.avif_quality = avif_quality
        self.avif_speed = avif_speed
        self.webp_quality = webp_quality
        self.webp_method = webp_method
        self.webp_lossless = webp_lossless
        self.png_compression = png_compression

    def append(self, transform: BaseTransformer):
        self.transforms.append(transform)

    def transform(self, img: Image.Image):
        for transform in self.transforms:
            try:
                img = transform(img)
            except UserWarning as e:
                raise UserWarning(e)
        return img

    def convert(self, img: Image.Image):
        if img.mode in ['RGBA', 'RGBa', 'P', 'CMYK']:
            img = img.convert('RGB')
        elif img.mode in ['LA', 'La']:
            img = img.convert('L')
        elif img.mode not in ['RGB', 'L']:
            raise UserWarning(f'Unrecognizable color space {img.mode}')
        return img

    def save_png(self, img: Image.Image):
        new_data = io.BytesIO()
        if self.png_compression == -1:
            img.save(new_data, 'PNG', optimize=True)
        else:
            img.save(new_data, 'PNG', compress_level=self.png_compression)
        return new_data.getvalue(), '.png'

    def save_jpeg(self, img: Image.Image, quality: Optional[int] = None, qtables=None,
                  subsampling=None):
        new_data = io.BytesIO()
        if self.jpeg_quality != -1 and (quality is None or quality > self.jpeg_quality):
            img.save(new_data, 'JPEG', quality=self.jpeg_quality, optimize=True)
        elif self.jpeg_quality == -1 and quality is None:
            img.save(new_data, 'JPEG', quality=100, optimize=True)
        else:
            img.save(new_data, 'JPEG', qtables=qtables, optimize=True, subsampling=subsampling)
        return new_data.getvalue(), '.jpg'

    def save_jpeg_fixed(self, img: Image.Image):
        new_data = io.BytesIO()
        quality = self.jpeg_quality if self.jpeg_quality != -1 else 100
        img.save(new_data, 'JPEG', quality=quality, optimize=True, subsampling=0)
        return new_data.getvalue(), '.jpg'

    def save_avif(self, img: Image.Image):
        new_data = io.BytesIO()
        img.save(new_data, 'AVIF', quality=self.avif_quality, speed=self.avif_speed)
        return new_data.getvalue(), '.avif'

    def save_webp(self, img: Image.Image):
        new_data = io.BytesIO()
        img.save(new_data, 'WEBP', quality=self.webp_quality, method=self.webp_method,
                 lossless=self.webp_lossless)
        return new_data.getvalue(), '.webp'

    def __call__(self, data: bytes, ext: str):
        try:
            img = Image.open(io.BytesIO(data))
            _ = img.getdata()
        except PIL.UnidentifiedImageError:
            raise UserWarning('Invalid image')
        except OSError:
            raise UserWarning('Truncated image')
        ext = ext.lower()
        try:
            if ext in ['.jpg', '.jpeg'] and self.fixed_ext in [None, '.jpg', '.jpeg']:
                try:
                    qtables = img.quantization  # type: ignore
                    quality = get_jpg_quality(qtables)
                    subsampling = get_sampling(img)
                except AttributeError:
                    qtables, quality, subsampling = None, None, None
                img = self.transform(img)
                img = self.convert(img)
                return self.save_jpeg(img, quality, qtables, subsampling)
            else:
                if self.fixed_ext is not None:
                    ext = self.fixed_ext
                img = self.transform(img)
                if ext in ['.jpg', '.jpeg']:
                    img = self.convert(img)
                    return self.save_jpeg_fixed(img)
                elif ext == '.png':
                    return self.save_png(img)
                elif ext == '.avif':
                    return self.save_avif(img)
                elif ext == '.webp':
                    return self.save_webp(img)
                else:
                    raise NotImplementedError(f'Unsupported format {ext}')
        except UserWarning as e:
            raise UserWarning(e)
