import json
import sys
from time import sleep

import requests
from lxml import etree

headers = {'Content-Type': 'text/html; charset=utf-8', }


def init_parse():
    url = 'https://exist.ru/Catalog/Global/'
    rs = requests.get(url, headers=headers)
    if rs.status_code != 200:
        print('MAIN FAIL: ', rs.status_code)
        sys.exit(1)
    hp = etree.HTMLParser()
    t = etree.fromstring(rs.text, hp)

    links = dict()
    names = t.xpath('//div[@class="top-r"]//a')

    for name in names:
        if 'Cars' in name.attrib['href']:
            links[name.text] = 'https://exist.ru' + name.attrib['href'] + '?all=1'
    return links


def parse_links(links: dict):
    print('start parse')
    failed_parse_links = {}
    parsed_cars = {}

    for model, link in links.items():
        response = requests.get(link, headers=headers)
        if response.status_code != 200:
            print('FAIL PARSE ', model)
            failed_parse_links[model] = link
            continue

        htmlparser = etree.HTMLParser(encoding='UTF-8')
        tree = etree.fromstring(response.text, htmlparser)
        models = []

        x_names = tree.xpath('//div[@class="car-info car-info--catalogs"]//a')
        pass
        for x_name in x_names:
            car_name = x_name.text
            models_dict = dict()
            models_dict['name'] = car_name
            models_dict['model_link'] = 'https://exist.ru' + x_name.attrib.get('href')
            exist_id = models_dict['model_link'].split('/')[len(models_dict['model_link'].split('/'))-1]
            models_dict['model_img'] = f'https://img.exist.ru/img.jpg?Key={exist_id}&Size=600x400&MethodType=5'

            years = tree.xpath(
                f'//div[@class="car-info__car-name"]/a[text()="{car_name}"]/../../div[@class="car-info__car-years"]/*')
            try:
                models_dict['year_from'], models_dict['year_to'] = years[0].text, years[1].text
            except IndexError:
                models_dict['year_from'], models_dict['year_to'] = '', ''
            models.append(models_dict)

        parsed_cars[model] = models

        print(model, ' Parsed.')
        # sleep(1)
    return parsed_cars, failed_parse_links


def check_is_all_parsed(parsed_cars, failed_parse_links):
    if len(failed_parse_links) > 0:
        print('____', len(failed_parse_links), ' FAILED')
        print('wait')
        sleep(60)
        pc, fpl = parse_links(failed_parse_links)
        for k, c in pc.items():
            parsed_cars[k] = v
        check_is_all_parsed(parsed_cars, failed_parse_links)


def main():
    all_links = init_parse()
    parsed_cars, failed_parse_links = parse_links(all_links)
    check_is_all_parsed(parsed_cars, failed_parse_links)

    with open('result.json', 'w', encoding='utf8') as json_file:
        json.dump(parsed_cars, json_file, ensure_ascii=False)


if __name__ == '__main__':
    main()

