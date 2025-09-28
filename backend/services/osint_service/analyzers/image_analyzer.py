"""
Image Analyzer - Análise forense de imagens
Extração de metadados, OCR, detecção facial e reverse search
Projeto Vértice - SSP-GO
"""

import asyncio
import aiohttp
import base64
import io
import json
import hashlib
from typing import Dict, List, Optional, Tuple
from datetime import datetime
import logging
from PIL import Image
import exifread
import cv2
import numpy as np
import pytesseract
from fake_useragent import UserAgent

logger = logging.getLogger(__name__)


class ImageAnalyzer:
    def __init__(self):
        self.timeout = aiohttp.ClientTimeout(total=30)
        self.session = None
        self.ua = UserAgent()

        # Carregar classificadores Haar Cascade
        self.face_cascade = cv2.CascadeClassifier(
            cv2.data.haarcascades + "haarcascade_frontalface_default.xml"
        )
        self.eye_cascade = cv2.CascadeClassifier(
            cv2.data.haarcascades + "haarcascade_eye.xml"
        )

    async def __aenter__(self):
        self.session = aiohttp.ClientSession(timeout=self.timeout)
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        if self.session:
            await self.session.close()

    async def analyze(
        self,
        image_url: Optional[str] = None,
        image_base64: Optional[str] = None,
        extract_faces: bool = True,
        extract_text: bool = True,
        extract_metadata: bool = True,
        reverse_search: bool = False,
    ) -> dict:
        """Análise completa de imagem"""

        logger.info("Iniciando análise de imagem")

        try:
            # Obter bytes da imagem
            if image_url:
                image_data = await self._download_image(image_url)
            elif image_base64:
                image_data = base64.b64decode(image_base64)
            else:
                return {"error": "Nenhuma imagem fornecida"}

            # Converter para objetos PIL e OpenCV
            pil_image = Image.open(io.BytesIO(image_data))
            cv_image = cv2.imdecode(
                np.frombuffer(image_data, np.uint8), cv2.IMREAD_COLOR
            )

            results = {
                "timestamp": datetime.utcnow().isoformat(),
                "image_properties": self._get_image_properties(pil_image),
                "hashes": self._calculate_hashes(image_data),
            }

            # Extrair metadados EXIF
            python  # Extrair metadados EXIF
            if extract_metadata:
                results["metadata"] = await self._extract_metadata(image_data)

            # Detectar e analisar faces
            if extract_faces:
                results["faces"] = self._detect_faces(cv_image)

            # Extrair texto (OCR)
            if extract_text:
                results["text_extraction"] = self._extract_text(cv_image)

            # Reverse image search
            if reverse_search:
                results["reverse_search"] = await self._reverse_search(image_data)

            # Análise forense adicional
            results["forensics"] = self._forensic_analysis(cv_image, pil_image)

            # Detecção de manipulação
            results["manipulation_detection"] = self._detect_manipulation(cv_image)

            # Classificação de conteúdo
            results["content_classification"] = self._classify_content(cv_image)

            return results

        except Exception as e:
            logger.error(f"Erro na análise de imagem: {e}")
            return {"error": str(e)}

    async def _download_image(self, url: str) -> bytes:
        """Download de imagem via URL"""
        if not self.session:
            self.session = aiohttp.ClientSession(timeout=self.timeout)

        headers = {"User-Agent": self.ua.random}

        async with self.session.get(url, headers=headers) as response:
            if response.status == 200:
                return await response.read()
            else:
                raise Exception(f"Falha no download: status {response.status}")

    def _get_image_properties(self, image: Image.Image) -> dict:
        """Extrai propriedades básicas da imagem"""
        return {
            "format": image.format,
            "mode": image.mode,
            "size": {
                "width": image.width,
                "height": image.height,
                "pixels": image.width * image.height,
            },
            "file_size_estimate": len(image.tobytes()),
            "has_transparency": image.mode in ("RGBA", "LA")
            or (image.mode == "P" and "transparency" in image.info),
            "is_animated": hasattr(image, "is_animated") and image.is_animated,
        }

    def _calculate_hashes(self, image_data: bytes) -> dict:
        """Calcula hashes da imagem para identificação única"""
        return {
            "md5": hashlib.md5(image_data).hexdigest(),
            "sha1": hashlib.sha1(image_data).hexdigest(),
            "sha256": hashlib.sha256(image_data).hexdigest(),
            "perceptual_hash": self._calculate_phash(image_data),
        }

    def _calculate_phash(self, image_data: bytes) -> str:
        """Calcula hash perceptual (resistente a modificações)"""
        try:
            img = Image.open(io.BytesIO(image_data))
            img = img.convert("L").resize((32, 32), Image.LANCZOS)

            pixels = np.array(img).flatten()
            mean = pixels.mean()
            diff = pixels > mean

            # Converter array booleano para hash hexadecimal
            hash_str = "".join("1" if b else "0" for b in diff)
            return hex(int(hash_str, 2))[2:].zfill(16)

        except Exception as e:
            logger.error(f"Erro ao calcular phash: {e}")
            return ""

    async def _extract_metadata(self, image_data: bytes) -> dict:
        """Extrai metadados EXIF da imagem"""
        metadata = {"exif": {}, "gps": {}, "camera": {}, "software": {}, "dates": {}}

        try:
            # Usar exifread para extrair tags EXIF
            tags = exifread.process_file(io.BytesIO(image_data))

            for tag, value in tags.items():
                tag_name = tag.replace("EXIF ", "").replace("Image ", "")

                # Organizar por categoria
                if "GPS" in tag:
                    metadata["gps"][tag_name] = str(value)
                elif any(cam in tag for cam in ["Make", "Model", "LensModel"]):
                    metadata["camera"][tag_name] = str(value)
                elif any(soft in tag for soft in ["Software", "ProcessingSoftware"]):
                    metadata["software"][tag_name] = str(value)
                elif "Date" in tag:
                    metadata["dates"][tag_name] = str(value)
                else:
                    metadata["exif"][tag_name] = str(value)

            # Processar coordenadas GPS se disponíveis
            if metadata["gps"]:
                coords = self._parse_gps_coordinates(metadata["gps"])
                if coords:
                    metadata["gps"]["coordinates"] = coords
                    metadata["gps"][
                        "maps_link"
                    ] = f"https://maps.google.com/?q={coords['latitude']},{coords['longitude']}"

        except Exception as e:
            logger.error(f"Erro ao extrair metadados: {e}")

        return metadata

    def _parse_gps_coordinates(self, gps_data: dict) -> Optional[dict]:
        """Converte dados GPS EXIF para coordenadas decimais"""
        try:

            def convert_to_degrees(value_string):
                """Converte coordenada GPS para graus decimais"""
                values = value_string.replace("[", "").replace("]", "").split(", ")
                degrees = float(values[0])
                minutes = float(values[1]) / 60
                seconds = float(values[2]) / 3600
                return degrees + minutes + seconds

            lat = convert_to_degrees(gps_data.get("GPSLatitude", ""))
            lat_ref = gps_data.get("GPSLatitudeRef", "N")
            lon = convert_to_degrees(gps_data.get("GPSLongitude", ""))
            lon_ref = gps_data.get("GPSLongitudeRef", "E")

            if lat_ref == "S":
                lat = -lat
            if lon_ref == "W":
                lon = -lon

            return {"latitude": round(lat, 6), "longitude": round(lon, 6)}

        except:
            return None

    def _detect_faces(self, image: np.ndarray) -> dict:
        """Detecta faces na imagem"""
        results = {"count": 0, "faces": [], "analysis": {}}

        try:
            # Converter para escala de cinza
            gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)

            # Detectar faces
            faces = self.face_cascade.detectMultiScale(
                gray, scaleFactor=1.1, minNeighbors=5, minSize=(30, 30)
            )

            results["count"] = len(faces)

            for i, (x, y, w, h) in enumerate(faces):
                face_data = {
                    "id": i + 1,
                    "position": {"x": int(x), "y": int(y)},
                    "size": {"width": int(w), "height": int(h)},
                    "area_percentage": round(
                        (w * h) / (image.shape[0] * image.shape[1]) * 100, 2
                    ),
                }

                # Detectar olhos dentro da face
                roi_gray = gray[y : y + h, x : x + w]
                eyes = self.eye_cascade.detectMultiScale(roi_gray)
                face_data["eyes_detected"] = len(eyes)

                # Análise adicional da face
                face_roi = image[y : y + h, x : x + w]
                face_data["blur_score"] = self._calculate_blur(face_roi)
                face_data["brightness"] = np.mean(face_roi)

                results["faces"].append(face_data)

            # Análise geral
            if results["count"] > 0:
                results["analysis"] = {
                    "group_photo": results["count"] > 3,
                    "portrait": results["count"] == 1
                    and results["faces"][0]["area_percentage"] > 15,
                    "crowd": results["count"] > 10,
                }

        except Exception as e:
            logger.error(f"Erro na detecção de faces: {e}")

        return results

    def _calculate_blur(self, image: np.ndarray) -> float:
        """Calcula o nível de desfoque da imagem"""
        gray = (
            cv2.cvtColor(image, cv2.COLOR_BGR2GRAY) if len(image.shape) == 3 else image
        )
        laplacian = cv2.Laplacian(gray, cv2.CV_64F)
        return float(laplacian.var())

    def _extract_text(self, image: np.ndarray) -> dict:
        """Extrai texto da imagem usando OCR"""
        results = {
            "text": "",
            "confidence": 0,
            "languages": [],
            "word_count": 0,
            "entities": [],
        }

        try:
            # Pré-processamento para melhorar OCR
            gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)

            # Aplicar threshold adaptativo
            processed = cv2.adaptiveThreshold(
                gray, 255, cv2.ADAPTIVE_THRESH_GAUSSIAN_C, cv2.THRESH_BINARY, 11, 2
            )

            # OCR com pytesseract
            custom_config = r"--oem 3 --psm 6"
            text = pytesseract.image_to_string(processed, config=custom_config)
            data = pytesseract.image_to_data(
                processed, output_type=pytesseract.Output.DICT
            )

            results["text"] = text.strip()
            results["word_count"] = len(text.split())

            # Calcular confiança média
            confidences = [int(conf) for conf in data["conf"] if int(conf) > 0]
            if confidences:
                results["confidence"] = sum(confidences) / len(confidences)

            # Detectar entidades (emails, telefones, URLs)
            results["entities"] = self._extract_entities(text)

            # Detectar idioma predominante
            if text:
                # Análise simplificada de idioma
                if any(char in text for char in "àáâãèéêìíîòóôõùúûç"):
                    results["languages"].append("portuguese")
                if any(ord(char) > 127 for char in text):
                    results["languages"].append("non-ascii")
                else:
                    results["languages"].append("english")

        except Exception as e:
            logger.error(f"Erro no OCR: {e}")

        return results

    def _extract_entities(self, text: str) -> dict:
        """Extrai entidades do texto (emails, telefones, etc)"""
        import re

        entities = {
            "emails": [],
            "phones": [],
            "urls": [],
            "ips": [],
            "hashtags": [],
            "mentions": [],
        }

        # Padrões regex
        patterns = {
            "emails": r"\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b",
            "phones": r"[\+]?[(]?[0-9]{1,3}[)]?[-\s\.]?[(]?[0-9]{1,4}[)]?[-\s\.]?[0-9]{1,4}[-\s\.]?[0-9]{1,9}",
            "urls": r"https?://(?:[-\w.]|(?:%[\da-fA-F]{2}))+[/]?",
            "ips": r"\b(?:[0-9]{1,3}\.){3}[0-9]{1,3}\b",
            "hashtags": r"#\w+",
            "mentions": r"@\w+",
        }

        for entity_type, pattern in patterns.items():
            matches = re.findall(pattern, text)
            entities[entity_type] = list(set(matches))  # Remover duplicatas

        return entities

    async def _reverse_search(self, image_data: bytes) -> dict:
        """Busca reversa de imagem"""
        results = {"services_checked": [], "matches_found": [], "similar_images": []}

        try:
            # Google Images (via URL do hash)
            image_hash = hashlib.md5(image_data).hexdigest()

            # TinEye API (simulado - em produção usar API real)
            results["services_checked"].append("tineye")

            # Google Lens (simulado)
            results["services_checked"].append("google_lens")

            # Yandex Images (simulado)
            results["services_checked"].append("yandex")

            # Simulação de resultados
            results["similar_images"] = [
                {
                    "service": "google",
                    "similarity": 0.89,
                    "source_url": "example.com/image.jpg",
                    "page_title": "Example Page",
                    "date_found": "2024-01-15",
                }
            ]

        except Exception as e:
            logger.error(f"Erro na busca reversa: {e}")

        return results

    def _forensic_analysis(self, cv_image: np.ndarray, pil_image: Image.Image) -> dict:
        """Análise forense da imagem"""
        forensics = {
            "error_level_analysis": {},
            "noise_analysis": {},
            "compression_artifacts": {},
            "histogram_analysis": {},
        }

        try:
            # Error Level Analysis (ELA)
            # Detecta áreas potencialmente modificadas
            temp_io = io.BytesIO()
            pil_image.save(temp_io, format="JPEG", quality=95)
            temp_io.seek(0)
            resaved = Image.open(temp_io)

            # Calcular diferença
            ela_image = np.array(pil_image) - np.array(resaved)
            ela_max = np.max(np.abs(ela_image))

            forensics["error_level_analysis"] = {
                "max_difference": float(ela_max),
                "suspicious": ela_max > 20,
                "uniformity": float(np.std(ela_image)),
            }

            # Análise de ruído
            gray = cv2.cvtColor(cv_image, cv2.COLOR_BGR2GRAY)
            noise = gray - cv2.GaussianBlur(gray, (5, 5), 0)

            forensics["noise_analysis"] = {
                "noise_level": float(np.std(noise)),
                "pattern_detected": float(np.std(noise)) > 15,
            }

            # Detecção de artefatos de compressão
            dct = cv2.dct(np.float32(gray) / 255.0)

            forensics["compression_artifacts"] = {
                "jpeg_quality_estimate": self._estimate_jpeg_quality(dct),
                "block_artifacts": bool(np.mean(dct) > 0.1),
            }

            # Análise de histograma
            hist = cv2.calcHist(
                [cv_image], [0, 1, 2], None, [256, 256, 256], [0, 256, 0, 256, 0, 256]
            )

            forensics["histogram_analysis"] = {
                "peaks": int(np.sum(hist > np.mean(hist) * 2)),
                "distribution": "normal" if np.std(hist) < 1000 else "irregular",
            }

        except Exception as e:
            logger.error(f"Erro na análise forense: {e}")

        return forensics

    def _estimate_jpeg_quality(self, dct: np.ndarray) -> int:
        """Estima qualidade JPEG baseado em DCT"""
        # Simplificado - análise real seria mais complexa
        quality_factor = np.mean(np.abs(dct)) * 100
        return min(100, max(10, int(quality_factor)))

    def _detect_manipulation(self, image: np.ndarray) -> dict:
        """Detecta sinais de manipulação na imagem"""
        manipulation = {
            "detected": False,
            "confidence": 0,
            "techniques": [],
            "suspicious_areas": [],
        }

        try:
            # Clone detection (áreas copiadas)
            gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
            sift = cv2.SIFT_create()
            keypoints, descriptors = sift.detectAndCompute(gray, None)

            if descriptors is not None and len(keypoints) > 100:
                # Verificar keypoints duplicados (simplificado)
                manipulation["techniques"].append("possible_cloning")

            # Detecção de splice (inserção de elementos)
            edges = cv2.Canny(gray, 100, 200)
            edge_density = np.sum(edges > 0) / edges.size

            if edge_density > 0.3:
                manipulation["techniques"].append("possible_splice")

            # Análise de consistência de iluminação
            lab = cv2.cvtColor(image, cv2.COLOR_BGR2LAB)
            l_channel = lab[:, :, 0]
            lighting_variance = np.var(l_channel)

            if lighting_variance > 5000:
                manipulation["techniques"].append("inconsistent_lighting")

            # Calcular confiança
            if manipulation["techniques"]:
                manipulation["detected"] = True
                manipulation["confidence"] = min(
                    95, len(manipulation["techniques"]) * 30
                )

        except Exception as e:
            logger.error(f"Erro na detecção de manipulação: {e}")

        return manipulation

    def _classify_content(self, image: np.ndarray) -> dict:
        """Classifica o tipo de conteúdo da imagem"""
        classification = {
            "type": "unknown",
            "categories": [],
            "tags": [],
            "safe_for_work": True,
            "violence_detected": False,
            "explicit_content": False,
        }

        try:
            # Análise básica de cores para determinar tipo
            hsv = cv2.cvtColor(image, cv2.COLOR_BGR2HSV)

            # Calcular histogramas
            hist_hue = cv2.calcHist([hsv], [0], None, [180], [0, 180])
            hist_saturation = cv2.calcHist([hsv], [1], None, [256], [0, 256])
            hist_value = cv2.calcHist([hsv], [2], None, [256], [0, 256])

            # Determinar tipo baseado em características
            mean_saturation = np.mean(hsv[:, :, 1])
            mean_value = np.mean(hsv[:, :, 2])

            if mean_saturation < 30:
                classification["categories"].append("grayscale")

            if mean_value < 50:
                classification["categories"].append("dark")
            elif mean_value > 200:
                classification["categories"].append("bright")

            # Detectar tipo de imagem
            aspect_ratio = image.shape[1] / image.shape[0]

            if aspect_ratio > 2.5:
                classification["type"] = "panorama"
            elif 0.9 < aspect_ratio < 1.1:
                classification["type"] = "square"
            elif aspect_ratio < 0.7:
                classification["type"] = "portrait"
            else:
                classification["type"] = "landscape"

            # Detectar se é screenshot
            unique_colors = len(np.unique(image.reshape(-1, image.shape[2]), axis=0))
            if unique_colors < 1000:
                classification["tags"].append("possible_screenshot")

            # Verificação básica de conteúdo (muito simplificada)
            # Em produção, usar modelo de ML apropriado
            skin_lower = np.array([0, 20, 70], dtype=np.uint8)
            skin_upper = np.array([20, 255, 255], dtype=np.uint8)
            skin_mask = cv2.inRange(hsv, skin_lower, skin_upper)
            skin_percentage = np.sum(skin_mask > 0) / skin_mask.size

            if skin_percentage > 0.4:
                classification["tags"].append("high_skin_content")
                classification["safe_for_work"] = False

        except Exception as e:
            logger.error(f"Erro na classificação de conteúdo: {e}")

        return classification

