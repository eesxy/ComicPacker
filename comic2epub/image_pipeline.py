import logging
import io
import numpy as np
import PIL
from PIL import Image
from PIL.JpegImagePlugin import get_sampling
from abc import abstractmethod
from .utils import get_jpg_quality


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
        logger: logging.Logger,
        fixed_ext: str = '',
        jpeg_quality: int = -1,
        png_compression: int = 1,
    ) -> None:
        self.transforms = []
        self.fixed_ext = None if fixed_ext == '' else fixed_ext
        self.jpeg_quality = jpeg_quality
        self.png_compression = png_compression
        self.logger = logger.getChild('ImagePipeline')

    def append(self, transform: BaseTransformer):
        self.transforms.append(transform)

    def __call__(self, data: bytes, ext: str):
        try:
            img = Image.open(io.BytesIO(data))
        except PIL.UnidentifiedImageError:
            self.logger.warning('Invalid image, skip')
            return data, ext
        ext = ext.lower()
        if ext in ['.jpg', '.jpeg']:
            quality = get_jpg_quality(img)
            qtables = img.quantization  # type: ignore
            subsampling = get_sampling(img)  # type: ignore
            for transform in self.transforms:
                img = transform(img)
            new_data = io.BytesIO()
            if self.jpeg_quality != -1 and quality > self.jpeg_quality:
                img.save(new_data, 'JPEG', quality=self.jpeg_quality, optimize=True,
                         subsampling=subsampling)
            else:
                img.save(new_data, 'JPEG', qtables=qtables, optimize=True, subsampling=subsampling)
            return new_data.getvalue(), ext
        elif ext in ['.png']:
            for transform in self.transforms:
                img = transform(img)
            new_data = io.BytesIO()
            if self.png_compression == -1:
                img.save(new_data, 'PNG', optimize=True)
            else:
                img.save(new_data, 'PNG', compress_level=self.png_compression)
            return new_data.getvalue(), ext
        else:
            raise NotImplementedError(f'Unsupported format {ext}')
