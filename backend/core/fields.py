import base64
import uuid

from django.core.files.base import ContentFile
from rest_framework import serializers

# Поддерживаемые форматы изображений
SUPPORTED_IMAGE_FORMATS = {"jpeg", "jpg", "png", "gif", "webp"}
DEFAULT_IMAGE_FORMAT = "jpg"


class Base64ImageField(serializers.ImageField):
    """Кастомное поле для работы с Base64 изображениями."""

    def to_internal_value(self, data):
        """Преобразование Base64 строки в файл или передача файла как есть."""
        # Если это Base64 строка
        if isinstance(data, str) and data.startswith("data:image"):
            try:
                format_part, imgstr = data.split(";base64,")
                ext = format_part.split("/")[-1].lower()

                # Нормализация расширения файла
                if ext not in SUPPORTED_IMAGE_FORMATS:
                    ext = DEFAULT_IMAGE_FORMAT

                decoded_file = base64.b64decode(imgstr)
                data = ContentFile(decoded_file, name=f"{uuid.uuid4()}.{ext}")
            except (ValueError, IndexError) as e:
                raise serializers.ValidationError(
                    f"Неверный формат Base64 изображения: {str(e)}"
                )
            except Exception as e:
                raise serializers.ValidationError(
                    f"Ошибка при декодировании Base64 изображения: {str(e)}"
                )

        # Если это уже файл, передаем в родительский метод
        return super().to_internal_value(data)
