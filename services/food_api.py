import aiohttp
from typing import List, Dict, Optional
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class FoodAPIClient:
    """
    Клиент для OpenFoodFacts API - база данных продуктов питания.

    OpenFoodFacts - открытая база >2.5M продуктов со всего мира.
    API бесплатный, без rate limits, поддерживает русские названия.

    Паттерн: External API Client с поиском
    """

    def __init__(self):
        self.search_url = "https://world.openfoodfacts.org/cgi/search.pl"
        self.product_url = "https://world.openfoodfacts.org/api/v2/product"

    async def search_products(
        self,
        query: str,
        limit: int = 5
    ) -> List[Dict]:
        """
        Ищет продукты по названию.

        Args:
            query: Название продукта (русский или английский)
                  Примеры: "молоко", "banana", "coca cola"
            limit: Максимум результатов (default 5)

        Returns:
            Список продуктов с полями:
            - product_name: str
            - nutriments: Dict с energy-kcal_100g
            - code: str (баркод)

        Паттерн: Filtered Results
        - Возвращаем только продукты с данными о калориях
        - Фильтруем пустые или неполные результаты
        """
        try:
            params = {
                "search_terms": query,
                "json": 1,
                "page_size": limit * 2,  # Запрашиваем больше для фильтрации
                "fields": "code,product_name,nutriments"
            }

            async with aiohttp.ClientSession() as session:
                async with session.get(
                    self.search_url,
                    params=params,
                    timeout=aiohttp.ClientTimeout(total=10)
                ) as response:

                    if response.status != 200:
                        logger.error(f"Food API error {response.status}")
                        return []

                    data = await response.json()
                    products = data.get("products", [])

                    # Фильтруем продукты с калориями
                    valid_products = []
                    for product in products:
                        if not product.get("nutriments"):
                            continue

                        nutriments = product["nutriments"]

                        # Проверяем наличие калорий (разные поля)
                        calories_per_100g = (
                            nutriments.get("energy-kcal_100g") or
                            nutriments.get("energy_100g", 0) / 4.184  # kJ to kcal
                        )

                        if calories_per_100g and calories_per_100g > 0:
                            valid_products.append({
                                "code": product.get("code", ""),
                                "product_name": product.get("product_name", "Unknown"),
                                "calories_per_100g": round(calories_per_100g, 1)
                            })

                        if len(valid_products) >= limit:
                            break

                    logger.info(
                        f"Food API: '{query}' → {len(valid_products)} products found"
                    )
                    return valid_products

        except Exception as e:
            logger.error(f"Food API search error: {e}")
            return []

    async def get_product_by_code(self, barcode: str) -> Optional[Dict]:
        """
        Получает подробную информацию о продукте по баркоду.

        Args:
            barcode: Баркод продукта (13 цифр обычно)

        Returns:
            Dict с полями product_name, nutriments или None
        """
        try:
            async with aiohttp.ClientSession() as session:
                async with session.get(
                    f"{self.product_url}/{barcode}",
                    timeout=aiohttp.ClientTimeout(total=10)
                ) as response:

                    if response.status != 200:
                        return None

                    data = await response.json()

                    if data.get("status") == 1:
                        return data.get("product")
                    else:
                        return None

        except Exception as e:
            logger.error(f"Food API barcode lookup failed: {e}")
            return None


# ============================================================================
# ПАТТЕРН: External Food API для AI-ботов
# ============================================================================
#
# **OpenFoodFacts vs платные API:**
#
# Бесплатные альтернативы:
# - OpenFoodFacts - отлично для международных продуктов
# - USDA FoodData Central - хорошо для американских продуктов
#
# Платные (если нужна высокая точность):
# - Nutritionix API ($$$) - большая база, хорошее покрытие русских продуктов
# - Edamam API ($$) - хорошее покрытие рецептов
#
# **Для русских продуктов:**
# - OpenFoodFacts покрытие ~60-70%
# - Fallback на LLM для непопулярных продуктов
# - Можно создать свою базу популярных продуктов (молоко, хлеб, etc.)
#
# **Для AI-ботов стратегия:**
# 1. Поиск в OpenFoodFacts (бесплатно, быстро)
# 2. Если не найдено → LLM estimation (платно, медленно)
# 3. Кеширование результатов LLM в локальной БД
# 4. Постепенно строим свою базу популярных продуктов
#
# Этот cascading fallback pattern оптимизирует cost vs accuracy.
# ============================================================================
