import time

import requests
import json


def create_agent_for_wildberries(authorization=None, page=0, sort="popular") -> dict:
    """
    Создание агента для работы.
    :param authorization:
    :param page:
    :param sort:
    :return dict:
    """
    headers = {
        'Accept': '*/*',
        'Accept-Language': 'ru-RU,ru;q=0.9,en-US;q=0.8,en;q=0.7',
        'Connection': 'keep-alive',
        'Origin': 'https://www.wildberries.ru',
        'Referer': f'https://www.wildberries.ru/catalog/0/search.aspx?page={page}&sort={sort}&search=',
        'Sec-Fetch-Dest': 'empty',
        'Sec-Fetch-Mode': 'cors',
        'Sec-Fetch-Site': 'cross-site',
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) '
                      'Chrome/116.0.0.0 Safari/537.36 OPR/102.0.0.0',
        'sec-ch-ua': '"Chromium";v="116", "Not)A;Brand";v="24", "Opera";v="102"',
        'sec-ch-ua-mobile': '?0',
        'sec-ch-ua-platform': '"Windows"',
        'authorization': authorization
    }
    return headers


def search_product_matches_in_categories(name_product: str) -> dict:
    """
    Возвращает словарь с id товара, категориями и количеством
    :param name_product:
    :return:
    """
    params = {
        'TestGroup': 'no_test',
        'TestID': 'no_test',
        'appType': '1',
        'curr': 'rub',
        'dest': '-1257786',
        'filters': 'xsubject',
        'query': name_product,
        'resultset': 'filters',
        'spp': '25',
        'suppressSpellcheck': 'false',
    }
    response = requests.get('https://search.wb.ru/exactmatch/ru/common/v4/search',
                            params=params, headers=create_agent_for_wildberries())
    return response.json()["data"]["filters"][0]["items"]


def find_products_by_name(name_product: str, sort="popular") -> dict:
    """
    Возвращает словарь найденных продуктов по названию продукта.
    :param name_product:
    :param sort:
    :return dict:
    """
    params = {
        'TestGroup': 'no_test',
        'TestID': 'no_test',
        'appType': '1',
        'curr': 'rub',
        'dest': '-1257786',
        'query': name_product,
        'resultset': 'catalog',
        'sort': sort,
        'spp': '25',
        'suppressSpellcheck': 'false',
    }
    response = requests.get('https://search.wb.ru/exactmatch/ru/common/v4/search',
                            params=params, headers=create_agent_for_wildberries())
    return response.json()["data"]["products"]


def get_position_product(product_name: str, product_id: int, max_page=70) -> int:
    """
    Поиск позиции продукта.
    :param product_name:
    :param product_id:
    :param max_page:
    :return int:
    """
    position = 0
    for page in range(0, max_page):
        params = {
            'appType': '1',
            'curr': 'rub',
            'dest': '-1257786',
            'query': product_name,
            'resultset': 'catalog',
            'spp': '25',
            'page': page + 1
        }
        try:
            data = requests.get('https://search.wb.ru/exactmatch/ru/common/v4/search',
                                params=params,
                                headers=create_agent_for_wildberries(page=page)).json()["data"]["products"]
            for product in data:
                position += 1
                if product['id'] == product_id:
                    return position
        except requests.exceptions.JSONDecodeError:
            print("Ошибка")
    else:
        return 0


def campaign_body(url: str, data: dict, api_key: str = None) -> dict:
    """
    Общее тело для возврата и обработки запросов.
    :param url:
    :param data:
    :param api_key:
    :return:
    """
    response: dict = requests.get(url, params=data,
                                  headers=create_agent_for_wildberries(authorization=api_key)).json()
    if response.get("code") == 204:
        return {"error": "Кампания не найдена"}
    elif response.get("code") == 401:
        return {"error": "Пустой авторизационный заголовок"}
    elif response.get("error") == 422:
        return {"error": "Ошибка обработки параметров запроса"}
    elif response.get("error") == "некорректный ид предмета":
        return {"error": "некорректный ид предмета"}
    elif response.get("error") == "Ошибка получения размещения в рекомендациях на главной":
        return {"error": "Ошибка получения размещения в рекомендациях на главной"}
    return response


def create_campaign(name: str, subject_id: int, refill: int, btype: int,
                    api_key: str = None, on_pause=False, type_company: int = 8):
    """
    Создание кампании автоматической рекламы.
    :param name:
    :param subject_id:
    :param refill:
    :param btype:
    :param api_key:
    :param on_pause:
    :param type_company:
    """
    data = {
        "type": type_company,  # Тип создаваемой кампании.
        "name": name,  # Название кампании (<=128 символов).
        "subjectId": subject_id,  # id предмета для кампании.
        "sum": refill,  # Сумма пополнения.
        "btype": btype,  # Тип списания. 0 - balance,
        "on_pause": on_pause  # Наличие паузы после создания кампании.
    }
    return campaign_body(url="https://advert-api.wb.ru/adv/v1/save-ad", data=data, api_key=api_key)


def create_campaign_in_search(campaign_name: str, groups: list, api_key: str = None) -> dict:
    """
    Создание кампании в поиске.
    :param campaign_name:
    :param groups:
    :param api_key:
    :return dict:
    """
    data = {
        "campaignName": campaign_name,  # len(Название кампании) <= 128.
        "groups": groups  # Продвигаемые предметы в списке. Одинаковые предметы. Количество групп не ограничено.
    }
    return campaign_body(url="https://advert-api.wb.ru/adv/v1/save-ad", data=data, api_key=api_key)


def delete_campaign(id_campaign: int, api_key: str = None) -> dict:
    """
    Удаление кампаний в статусе 4 - готова к запуску.
    :param id_campaign:
    :param api_key:
    :return:
    """
    data = {
        "id": id_campaign,  # id кампании.
    }
    return campaign_body(url="https://advert-api.wb.ru/adv/v1/save-ad", data=data, api_key=api_key)


def get_campaign(all_count_campaign: int, adverts: list, api_key: str = None) -> dict:
    """
    Получение кампаний поставщика.
    :param api_key:
    :param all_count_campaign:
    :param adverts:
    :return:
    """
    data = {
        "id": all_count_campaign,  # Общее количество кампаний всех статусов и типов.
        "adverts": adverts  # Массив кампаний.
    }
    return campaign_body(url="https://advert-api.wb.ru/adv/v1/save-ad", data=data, api_key=api_key)


def list_of_campaign(status: int, type_campaign: int, limit: int, offset: int,
                     order: str, direction: str, api_key: str = None) -> dict:
    """
    Список кампаний продавца.
    :param status:
    :param type_campaign:
    :param limit:
    :param offset:
    :param order:
    :param direction:
    :param api_key:
    :return dict:
    """
    data = {
        "status": status,  # Статус кампании.
        "type": type_campaign,  # Тип кампании.
        "limit": limit,  # Количество кампаний в ответе.
        "offset": offset,  # Смещение относительно первой кампании.
        "order": order,  # {"create": "по времени создания"), {"change": "Последнее изменение кампании",
        # "id": "индентификатор кампании"}
        "direction": direction  # {"desc": "От большего к меньшему", "asc": "От меньше к большему"}
    }
    return campaign_body(url="https://advert-api.wb.ru/adv/v1/save-ad", data=data, api_key=api_key)


def info_about_campaign(advert_id: int, type_campaign: int, status: int, create_time: str,
                        change_time: str, status_time: str, end_time: str, name: str,
                        params: list, search_pluse_state: bool, api_key: str = None,
                        daily_budget: int = 0) -> dict:
    """
    Информация об одной кампании.
    :return:
    """
    data = {
        "advertId": advert_id,
        "type": type_campaign,  # Тип кампании.
        "status": status,  # Статус кампании.
        "dailyBudget": daily_budget,  # Дневной бюджет. По умолчанию 0.
        "create_time": create_time,  # Время создания кампании.
        "change_time": change_time,  # Время последнего изменения кампании.
        "startTime": status_time,  # Дата запуска кампании.
        "endTime": end_time,  # Дата завершения кампании.
        "name": name,  # Название кампании.
        "params": params,  # Параметры кампании.
        "searchPluseState": search_pluse_state  # Активность фиксированных фраз(Для кампаний в поиске).

    }
    return campaign_body(url="https://advert-api.wb.ru/adv/v1/save-ad", data=data, api_key=api_key)


def calculation_position_for_product(product_name: str, product_id: int, bid: int, max_page=40) -> int:
    """
    Вычисляет приблизительную стоимость позиции за ставку.
    :param product_name:
    :param product_id:
    :param bid:
    :param max_page:
    :return int:
    """
    product_position = get_position_product(product_name, product_id, max_page)
    print(product_position)
    if product_position <= 100:
        page = 1
    else:
        page = product_position // 100
    data = get_all_position_auto_advertising_by_product(product_name, page)
    if product_position == 0:
        return -1000
    if len([data[value]["cpm"] for value in data]) >= 1:
        list_cpm = [data[value]["cpm"] for value in data]
        list_position = [data[value]["position"] - data[value]["promoPosition"] for value in data]
        median = round(sum(list_cpm) / sum(list_position), 2)
        if product_position <= 10:
            median *= 1000
            if round(product_position - bid / median) == 0:
                return 1
            if int(round(product_position - bid / median)) <= -0.1:
                return 1
            return int(round(product_position - bid / median))
        elif product_position <= 100:
            median *= 100
            if round(product_position - bid / median) == 0:
                return 1
            if int(round(product_position - bid / median)) <= -0.1:
                return 1
            return int(round(product_position - bid / median))
        elif product_position <= 1000:
            median *= 10
            if round(product_position - bid / median) == 0:
                return 1
            if int(round(product_position - bid / median)) <= -0.1:
                return 1
            return int(round(product_position - bid / median))
        return int(round(product_position - bid / median))
    else:
        return -1000


def get_all_position_auto_advertising_by_product(product_name: str, max_page=30) -> dict:
    """
    Вычисление приблизительной позиции продукта с помощью авторекламы.
    :param product_name:
    :param max_page:
    :return dict:
    """
    data = dict()
    for page in range(0, max_page):
        params = {
            'appType': '1',
            'curr': 'rub',
            'dest': '-1257786',
            'query': product_name,
            'resultset': 'catalog',
            'spp': '25',
            'page': page + 1
        }
        for product in requests.get('https://search.wb.ru/exactmatch/ru/common/v4/search',
                                    params=params,
                                    headers=create_agent_for_wildberries(page=page)).json()["data"]["products"]:
            if len(product["log"]) > 0:
                product_log = product['log']
                data[product["id"]] = {"cpm": product_log["cpm"],
                                       "position": product_log["position"],
                                       "promoPosition": product_log["promoPosition"]}
    if len(data) > 0:
        return data
    else:
        return {"error": "Wildberries вернул пустые данные"}


position_new = calculation_position_for_product("смартфон",184038056, 500)
if position_new == -1000:
    print("Нет данных")
else:
    print(f"Предполагаемая позиция после авторекламы: {int(position_new)}")
